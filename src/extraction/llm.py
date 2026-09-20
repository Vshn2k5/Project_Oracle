"""
LLM Provider Abstraction.

Allows for swapping different LLMs for structured extraction without
coupling the pipeline to a specific vendor's SDK.
"""

import abc
import json
import logging
from typing import Any, Type, TypeVar

from pydantic import BaseModel

from src.config.settings import Settings
from src.extraction.schemas import DocumentExtractionSchema

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMProviderError(RuntimeError):
    """Raised when the LLM provider fails to generate a valid response."""


class LLMProvider(abc.ABC):
    """Abstract interface for LLM structured extraction."""

    @abc.abstractmethod
    def extract_structured_data(
        self,
        text: str,
        schema: Type[T],
    ) -> T:
        """
        Extract structured data matching the given Pydantic schema.

        Args:
            text: The source text to extract from.
            schema: The Pydantic model class to validate against.

        Returns:
            An instance of the schema class.

        Raises:
            LLMProviderError: If the extraction fails or output is invalid.
        """
        pass


class GoogleGenAIProvider(LLMProvider):
    """Implementation for Google's Gemini API."""

    def __init__(self, api_key: str | None, model_name: str) -> None:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError(
                "google-genai package is required. "
                "Install it with `pip install google-genai`."
            ) from exc

        # The SDK automatically uses GOOGLE_API_KEY from the environment
        # if api_key is None, but we pass it explicitly if we have one.
        self.client = genai.Client(api_key=api_key) if api_key else genai.Client()
        self.model_name = model_name
        self._types = types

    def extract_structured_data(
        self,
        text: str,
        schema: Type[T],
    ) -> T:
        prompt = (
            "You are a strict data extraction system for an urban flood disaster "
            "preparedness knowledge graph.\n\n"
            "Extract entities, relationships, and claims from the following text.\n"
            "CRITICAL RULES:\n"
            "1. Use ONLY the provided text. Do not invent information.\n"
            "2. If an entity/relationship/claim is not present, return empty lists.\n"
            "3. Extract exact quotes for evidence_quote fields.\n"
            "4. Allowed Entity Types: Zone, Risk, Infrastructure, Mitigation, Budget, Policy, Project.\n"
            "5. Allowed Relationship Types: HAS_RISK, AFFECTS, REQUIRES, FUNDS, LOCATED_IN, ADDRESSES, REGULATES, APPLIES_TO.\n"
            "6. Claims must be standalone sentences asserting a fact found in the text.\n"
            f"--- TEXT START ---\n{text}\n--- TEXT END ---\n"
        )

        logger.debug("Requesting structured extraction from %s", self.model_name)

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=self._types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.0,
                ),
            )
        except Exception as exc:
            logger.error("LLM API call failed: %s", exc)
            raise LLMProviderError("LLM API call failed.") from exc

        if not response.text:
            raise LLMProviderError("LLM returned an empty response.")

        try:
            parsed_dict = json.loads(response.text)
            return schema.model_validate(parsed_dict)
        except Exception as exc:
            logger.error("Failed to parse LLM structured output: %s", exc)
            raise LLMProviderError(
                f"Failed to parse LLM structured output: {exc}"
            ) from exc


def create_llm_provider(settings: Settings) -> LLMProvider:
    """Factory to create the configured LLM provider."""
    provider_name = settings.llm_provider.lower()

    if provider_name == "google-genai":
        return GoogleGenAIProvider(
            api_key=settings.llm_api_key,
            model_name=settings.llm_model,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_name}")
