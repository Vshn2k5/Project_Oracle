# Project Oracle

**Neuro-Symbolic GraphRAG-Based Multi-Agent Decision Support Framework for Urban Flood Disaster Preparedness and Infrastructure Planning.**

## Current Implementation Stage

**Foundation Hardening** — the base layers are implemented and tested:

- PDF document ingestion (extract → clean → chunk)
- Deterministic document identity (SHA-256)
- Neo4j knowledge graph with parameterized Cypher
- Domain schema: Document, Chunk, Zone, Risk, Infrastructure, Mitigation, Budget, Policy, Claim, Evidence, Project
- Write operations (single + batch UNWIND)
- Read operations (get, find, query, graph context)
- Shared domain models (document, knowledge graph, retrieval, agent, verification)
- Configuration via environment variables (dependency-injectable)

### Not Yet Implemented

- Entity / relationship extraction (LLM-based)
- Claim / evidence extraction
- Embedding pipeline
- Vector / keyword / graph retrieval
- GraphRAG orchestration
- Multi-agent reasoning system
- Verification engine
- API layer
- Frontend

## Repository Structure

```
src/
├── config/
│   └── settings.py           # Configuration (Settings dataclass)
├── ingestion/
│   ├── pdf_reader.py          # PDF → ExtractedDocument
│   ├── text_cleaner.py        # ExtractedDocument → CleanedDocument
│   └── chunker.py             # CleanedDocument → DocumentChunk[]
├── knowledge_graph/
│   ├── connection.py          # Neo4j driver management
│   ├── schema.py              # Graph constraints and indexes
│   └── repository.py          # Read/write/batch operations
├── models/
│   ├── document.py            # Document & embedding models
│   ├── knowledge_graph.py     # Entity, Relationship, Claim, Evidence
│   ├── retrieval.py           # RetrievedContext, GraphContext
│   ├── agent.py               # AgentResult, Recommendation
│   └── verification.py        # VerificationResult
├── extraction/                # (placeholder — future)
├── retrieval/                 # (placeholder — future)
├── agents/                    # (placeholder — future)
└── evaluation/                # (placeholder — future)

tests/
├── conftest.py                # Shared fixtures
├── test_settings.py           # Configuration tests
├── test_pdf_reader.py         # PDF reader tests
├── test_text_cleaner.py       # Text cleaner tests
├── test_chunker.py            # Chunker tests
├── test_models.py             # Domain model tests
├── test_repository.py         # Repository unit tests
├── test_schema.py             # Schema unit tests
└── integration/               # Neo4j integration tests
    ├── conftest.py
    ├── test_neo4j_connection.py
    ├── test_neo4j_repository.py
    └── test_neo4j_schema.py

data/raw/                      # Source PDF documents
```

## Configuration

Copy `.env.example` to `.env` and fill in your Neo4j credentials:

```bash
cp .env.example .env
```

Required environment variables:

| Variable | Description | Required |
|---|---|---|
| `NEO4J_URI` | Neo4j Bolt URI (e.g. `bolt://localhost:7687`) | Yes |
| `NEO4J_USERNAME` | Neo4j username | Yes |
| `NEO4J_PASSWORD` | Neo4j password | Yes |
| `NEO4J_DATABASE` | Neo4j database name (default: `neo4j`) | No |

Configuration can also be created directly in code:

```python
from src.config import Settings

settings = Settings(
    neo4j_uri="bolt://localhost:7687",
    neo4j_username="neo4j",
    neo4j_password="your-password",
)
```

## Running Tests

```bash
# Install dependencies
pip install -r requirements.txt
pip install pytest

# Run unit tests (no Neo4j required)
pytest tests/ -v -m "not integration"

# Run all tests including Neo4j integration
pytest tests/ -v

# Run with a specific marker
pytest tests/ -v -m integration
```

Some tests require `data/raw/Floods.pdf` to be present. They are skipped automatically when the file is absent.

## Running Ingestion

```python
from src.ingestion.pdf_reader import create_pdf_reader
from src.ingestion.text_cleaner import create_text_cleaner
from src.ingestion.chunker import create_document_chunker

reader = create_pdf_reader()
cleaner = create_text_cleaner()
chunker = create_document_chunker()

document = reader.read("data/raw/Floods.pdf")
cleaned = cleaner.clean_document(document)
chunks = chunker.chunk_document(cleaned)
```

## Connecting to Neo4j

```python
from src.config import Settings
from src.knowledge_graph.connection import create_neo4j_connection
from src.knowledge_graph.schema import apply_schema
from src.knowledge_graph.repository import KnowledgeGraphRepository

settings = Settings.from_environment()
connection = create_neo4j_connection(settings)
apply_schema(connection)

repo = KnowledgeGraphRepository(connection)
```

## Current Limitations

- No automated entity/relationship extraction — knowledge graph must be populated manually or via future extraction pipeline
- No embedding pipeline — `EmbeddedChunk` model exists but no embedding service
- No retrieval system — read operations provide primitives, but hybrid retrieval is not implemented
- No agent system — model contracts exist but agents are not implemented
- No verification engine
- No API or frontend
- Batch operations use UNWIND within a single transaction — not suitable for millions of records

## Dependencies

Core dependencies in use:
- `neo4j` — Neo4j Python driver
- `pymupdf` — PDF text extraction
- `python-dotenv` — Environment variable loading

Installed but reserved for future stages:
- `sentence-transformers`, `torch`, `transformers` — Embedding pipeline
- `scikit-learn`, `scipy`, `numpy` — ML utilities
- `pydantic` — Future API validation
- `typer`, `rich` — Future CLI
- `pandas` — Future data analysis
- `networkx` — Future graph analysis

## Next Implementation Stage

**Stage 2 — Extraction & Population:**
1. Define the Oracle query workload
2. Finalize ontology based on actual queries
3. Build entity/relationship extraction pipeline
4. Build claim/evidence extraction
5. Populate Neo4j from source documents
6. Validate graph completeness
