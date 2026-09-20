# Project Oracle — Complete Build Audit Report

> **Audit Date:** 2026-09-18
> **Repository:** `D:\Project`
> **Commits:** 3 total

> [!CAUTION]
> **Executive Summary:** Project Oracle is in **very early Phase 1** — approximately **8–10% of the intended system** has been built. Only the **document ingestion pipeline** (PDF → text → chunks) and the **Neo4j knowledge graph write layer** (schema + repository) are implemented. **Everything else** — all 6 agents, the entire retrieval system, GraphRAG, the frontend, backend API, LLM integration, debate/deliberation, symbolic verification, provenance, routing, and evaluation — is **completely missing**. There is no runnable application. There is no web UI. There is no API server. There is no LLM integration whatsoever.

---

## TASK 1 — Repository Inventory

### Git History (3 commits)

| Commit | Message |
|--------|---------|
| `8ddcb16` | Add initial project structure with configuration and connection setup for Neo4j |
| `2370221` | Add .gitignore and configuration settings for environment variables |
| `1375136` | Implement PDF ingestion and text cleaning modules |

### Complete File Inventory

| Path | Purpose | Technology | Oracle Component | Status | Actually Used? |
|------|---------|------------|------------------|--------|----------------|
| [`.env`](file:///d:/Project/.env) | Neo4j credentials | dotenv | Config | **IMPLEMENTED** | Yes — loaded by `settings.py` |
| [`.env.example`](file:///d:/Project/.env.example) | Template env file | — | Config | **PLACEHOLDER** (0 bytes) | No |
| [`.gitignore`](file:///d:/Project/.gitignore) | Git ignore rules | Git | Project setup | **IMPLEMENTED** | Yes |
| [`README.md`](file:///d:/Project/README.md) | Project README | Markdown | Documentation | **PLACEHOLDER** (0 bytes) | No |
| [`requirements.txt`](file:///d:/Project/requirements.txt) | Python dependencies | pip | Build | **IMPLEMENTED** | Partially — many deps unused |
| [`data/raw/Floods.pdf`](file:///d:/Project/data/raw/Floods.pdf) | Sample PDF (3.5 MB, 16 pages) | PDF | Document Ingestion | **IMPLEMENTED** | Yes — used in tests |
| `data/processed/` | Output directory | — | Ingestion | **PLACEHOLDER** (empty) | No |
| `data/metadata/` | Metadata storage | — | Ingestion | **PLACEHOLDER** (empty) | No |
| `docs/` | Documentation | — | Documentation | **PLACEHOLDER** (empty) | No |
| `notebooks/` | Jupyter notebooks | — | Evaluation | **PLACEHOLDER** (empty) | No |
| `reports/phase1/` | Phase 1 reports | — | Reporting | **PLACEHOLDER** (empty) | No |
| [`src/__init__.py`](file:///d:/Project/src/__init__.py) | Package init | Python | — | **SCAFFOLDED** (0 bytes) | Yes (import path) |
| [`src/config/settings.py`](file:///d:/Project/src/config/settings.py) | Neo4j config from env | Python / dataclasses | Config | **IMPLEMENTED** | Yes |
| [`src/ingestion/pdf_reader.py`](file:///d:/Project/src/ingestion/pdf_reader.py) | PDF text extraction | PyMuPDF | Document Ingestion | **IMPLEMENTED** | Yes |
| [`src/ingestion/text_cleaner.py`](file:///d:/Project/src/ingestion/text_cleaner.py) | Text normalization | Python regex | Document Ingestion | **IMPLEMENTED** | Yes |
| [`src/ingestion/chunker.py`](file:///d:/Project/src/ingestion/chunker.py) | Page-aware chunking | Python | Document Ingestion | **IMPLEMENTED** | Yes |
| [`src/knowledge_graph/connection.py`](file:///d:/Project/src/knowledge_graph/connection.py) | Neo4j driver wrapper | neo4j Python driver | Knowledge Graph | **IMPLEMENTED** | Yes |
| [`src/knowledge_graph/schema.py`](file:///d:/Project/src/knowledge_graph/schema.py) | KG schema constraints | Neo4j / Cypher | Knowledge Graph | **IMPLEMENTED** | Yes |
| [`src/knowledge_graph/repository.py`](file:///d:/Project/src/knowledge_graph/repository.py) | CRUD for graph nodes/rels | Neo4j / Cypher | Knowledge Graph | **IMPLEMENTED** | Partially (write-only) |
| [`src/agents/__init__.py`](file:///d:/Project/src/agents/__init__.py) | Agents package | Python | Agents | **PLACEHOLDER** (0 bytes) | No |
| [`src/evaluation/__init__.py`](file:///d:/Project/src/evaluation/__init__.py) | Evaluation package | Python | Evaluation | **PLACEHOLDER** (0 bytes) | No |
| [`src/extraction/__init__.py`](file:///d:/Project/src/extraction/__init__.py) | Extraction package | Python | Entity/Relation Extraction | **PLACEHOLDER** (0 bytes) | No |
| [`src/retrieval/__init__.py`](file:///d:/Project/src/retrieval/__init__.py) | Retrieval package | Python | Retrieval | **PLACEHOLDER** (0 bytes) | No |
| [`tests/test_connection.py`](file:///d:/Project/tests/test_connection.py) | Neo4j connectivity test | Python | Knowledge Graph | **IMPLEMENTED** (manual script) | Manual execution |
| [`tests/test_pdf_reader.py`](file:///d:/Project/tests/test_pdf_reader.py) | PDF reader test | Python | Ingestion | **IMPLEMENTED** (manual script) | Manual execution |
| [`tests/test_text_cleaner.py`](file:///d:/Project/tests/test_text_cleaner.py) | Text cleaner test | Python | Ingestion | **IMPLEMENTED** (manual script) | Manual execution |
| [`tests/test_chunker.py`](file:///d:/Project/tests/test_chunker.py) | Chunker test | Python | Ingestion | **IMPLEMENTED** (manual script) | Manual execution |
| [`tests/test_repository_manual.py`](file:///d:/Project/tests/test_repository_manual.py) | Repository smoke test | Python | Knowledge Graph | **IMPLEMENTED** (manual script) | Manual execution |

### Suspicious/Notable Observations

- **No pytest tests.** All "tests" are manual scripts (`if __name__ == "__main__"`) — not discoverable by any test runner.
- **Empty directories everywhere** — `docs/`, `notebooks/`, `reports/phase1/`, `data/processed/`, `data/metadata/` are all empty placeholder directories.
- **README.md is 0 bytes** — no documentation exists.
- **`.env.example` is 0 bytes** — no template for other developers.
- **`requirements.txt` lists unused heavy dependencies**: `sentence-transformers`, `torch`, `transformers`, `scikit-learn`, `scipy` are installed but imported **nowhere** in the codebase.

---

## TASK 2 — Current Tech Stack

### Frontend

> [!WARNING]
> **NO FRONTEND EXISTS.** There is no React, Vue, Angular, Next.js, HTML, CSS, JavaScript, or TypeScript code anywhere in the repository. No `package.json` exists. No `node_modules`. No UI of any kind.

### Backend

> [!WARNING]
> **NO BACKEND API EXISTS.** There is no FastAPI, Flask, Django, Express, or any HTTP server. No API endpoints. No server entry point. No `main.py` or `app.py`. The project cannot receive or serve HTTP requests.

### AI/LLM

> [!WARNING]
> **NO LLM INTEGRATION EXISTS.** Despite `transformers` and `sentence-transformers` being in requirements.txt, they are **not imported or used** anywhere. There is:
> - No Ollama integration
> - No OpenAI integration
> - No HuggingFace model loading
> - No embedding generation
> - No LLM prompt construction
> - No agent reasoning
> - Zero LLM-related code

### Agent Framework

> [!WARNING]
> **NO AGENT FRAMEWORK.** No LangChain, LangGraph, CrewAI, AutoGen, or custom orchestration. The `src/agents/__init__.py` is an empty 0-byte file.

### Database — Actual Stack

| Component | Technology | Status |
|-----------|------------|--------|
| Graph Database | **Neo4j** via `neo4j` Python driver v6.2.0 | **IMPLEMENTED** (connection + write operations) |
| Vector Database | None | **MISSING** |
| Relational DB | None | **MISSING** |
| Cache | None | **MISSING** |

### Retrieval — Actual Stack

| Component | Status |
|-----------|--------|
| Vector Retrieval | **MISSING** |
| Keyword/BM25 | **MISSING** |
| Graph Retrieval | **MISSING** (repository only writes, no read/query methods) |
| Hybrid Retrieval | **MISSING** |
| Reranking | **MISSING** |

### Actual Technology Used

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | 3.13 |
| PDF parsing | PyMuPDF | 1.28.2 |
| Graph DB | Neo4j Python driver | 6.2.0 |
| Config | python-dotenv | 1.2.3 |
| Data validation | pydantic | 2.13.4 |
| Data model | dataclasses (stdlib) | — |

---

## TASK 3 — End-to-End Execution Path

> [!CAUTION]
> **There is NO end-to-end execution path.** The system cannot process a user query. The chain breaks immediately at the very first step because there is no frontend, no API, and no query handler.

| Stage | Actual File/Function | What It Does | Status |
|-------|---------------------|--------------|--------|
| **User** | — | — | N/A |
| **Frontend** | — | — | **MISSING** |
| **API** | — | — | **MISSING** |
| **Query Analyzer** | — | — | **MISSING** |
| **Retriever** | — | — | **MISSING** |
| **Knowledge Graph** | [`repository.py`](file:///d:/Project/src/knowledge_graph/repository.py) — **WRITE ONLY** | Can create/update nodes and relationships | **PARTIALLY IMPLEMENTED** (no read/query) |
| **Router** | — | — | **MISSING** |
| **Agents** | — | — | **MISSING** |
| **Debate** | — | — | **MISSING** |
| **Decision Mediator** | — | — | **MISSING** |
| **Verifier** | — | — | **MISSING** |
| **Evidence** | — | — | **MISSING** |
| **Response** | — | — | **MISSING** |
| **Frontend** | — | — | **MISSING** |

### Where the chain breaks

```
User → ❌ BREAKS IMMEDIATELY — No frontend, no API, no entry point exists.
```

The only executable path that exists is a **manual script pipeline**:

```
Floods.pdf → PDFReader.read() → TextCleaner.clean_document() → DocumentChunker.chunk_document()
```

This produces `DocumentChunk` objects in memory but they are **NOT persisted anywhere** — not to Neo4j, not to a vector store, not to disk.

A separate manual script ([`test_repository_manual.py`](file:///d:/Project/tests/test_repository_manual.py)) can write hardcoded test nodes to Neo4j, but **the ingestion pipeline and the knowledge graph are not connected**.

---

## TASK 4 — Document Ingestion Audit

| Stage | Status | File/Function | Notes |
|-------|--------|---------------|-------|
| PDF Upload | **MISSING** | — | No upload endpoint or UI |
| PDF Parsing | **IMPLEMENTED** | [`pdf_reader.py → PDFReader.read()`](file:///d:/Project/src/ingestion/pdf_reader.py#L52-L106) | Uses PyMuPDF. Extracts text per page. |
| OCR | **MISSING** | — | PyMuPDF does text-layer extraction only. No OCR for scanned docs. |
| Text Extraction | **IMPLEMENTED** | [`pdf_reader.py`](file:///d:/Project/src/ingestion/pdf_reader.py) | Text-layer only |
| Page-Level Extraction | **IMPLEMENTED** | [`ExtractedPage`](file:///d:/Project/src/ingestion/pdf_reader.py#L7-L15) | Page numbers preserved |
| Metadata Extraction | **MISSING** | — | No title, author, date, etc. extraction |
| Document Classification | **MISSING** | — | No document type detection |
| Text Cleaning | **IMPLEMENTED** | [`text_cleaner.py → TextCleaner`](file:///d:/Project/src/ingestion/text_cleaner.py#L42-L77) | Handles hyphenation, whitespace, line endings |
| Chunking | **IMPLEMENTED** | [`chunker.py → DocumentChunker`](file:///d:/Project/src/ingestion/chunker.py#L26-L111) | 1200 chars max, 200 overlap, page-aware |
| Embedding Generation | **MISSING** | — | `sentence-transformers` is installed but **never imported** |
| Entity Extraction | **MISSING** | — | `src/extraction/` contains only empty `__init__.py` |
| Relationship Extraction | **MISSING** | — | — |
| Claim Extraction | **MISSING** | — | — |
| Provenance Creation | **PARTIALLY IMPLEMENTED** | Chunk IDs encode document + page | `DOC-{hash}-P{page}-C{index}` format, but no full provenance metadata |
| Graph Insertion | **MISSING** (as automated pipeline) | Repository exists but is not called from ingestion | Write methods exist but there is **no orchestrator** connecting chunks → graph |
| Vector Index Insertion | **MISSING** | — | — |

### Pipeline Trace

```
Floods.pdf
 ↓ IMPLEMENTED
PDFReader.read()
 ↓ IMPLEMENTED
ExtractedDocument (pages with text)
 ↓ IMPLEMENTED
TextCleaner.clean_document()
 ↓ IMPLEMENTED
CleanedDocument (normalized text)
 ↓ IMPLEMENTED
DocumentChunker.chunk_document()
 ↓ IMPLEMENTED
DocumentChunk[] (in memory)
 ↓ ❌ BREAKS HERE
 ↓ No embeddings generated
 ↓ No entities extracted
 ↓ No graph insertion
 ↓ No vector store insertion
```

> **Can a user add a new document without editing source code?** **NO.** There is no CLI command, no API endpoint, no upload mechanism. A developer would have to write Python code manually to process each PDF.

---

## TASK 5 — Knowledge Graph Audit

### Connection

| Question | Answer |
|----------|--------|
| Does the app connect to Neo4j? | **YES** — [`connection.py`](file:///d:/Project/src/knowledge_graph/connection.py) |
| How? | `neo4j.GraphDatabase.driver()` with bolt protocol |
| Configuration externalized? | **YES** — via `.env` file → `settings.py` |
| URI | `neo4j://127.0.0.1:7687` |
| Database | `neo4j` (default) |

### Actual Schema (Node Labels)

Defined in [`schema.py`](file:///d:/Project/src/knowledge_graph/schema.py#L36-L101):

| Node Label | Properties | Constraint |
|------------|------------|------------|
| `Document` | `id`, `title`, `source`, `document_type`, `publication_date` | `id IS UNIQUE` |
| `Chunk` | `id`, `text`, `page`, `chunk_index` | `id IS UNIQUE` |
| `Zone` | `id`, `name`, `description` | `id IS UNIQUE` |
| `Risk` | `id`, `type`, `severity`, `description` | `id IS UNIQUE` |
| `Infrastructure` | `id`, `name`, `type`, `description` | `id IS UNIQUE` |
| `Mitigation` | `id`, `name`, `type`, `description` | `id IS UNIQUE` |
| `Budget` | `id`, `amount`, `currency`, `fiscal_year` | `id IS UNIQUE` |
| `Policy` | `id`, `title`, `policy_type`, `description` | `id IS UNIQUE` |

### Actual Relationships

Defined in [`repository.py`](file:///d:/Project/src/knowledge_graph/repository.py#L116-L191):

| Source | Relationship | Target |
|--------|-------------|--------|
| `Document` | `CONTAINS` | `Chunk` |
| `Chunk` | `MENTIONS` | `Zone` |
| `Chunk` | `MENTIONS` | `Risk` |
| `Chunk` | `MENTIONS` | `Infrastructure` |
| `Chunk` | `MENTIONS` | `Mitigation` |
| `Zone` | `HAS_RISK` | `Risk` |
| `Risk` | `AFFECTS` | `Infrastructure` |
| `Infrastructure` | `REQUIRES` | `Mitigation` |
| `Budget` | `FUNDS` | `Mitigation` |
| `Policy` | `REGULATES` | `Infrastructure` |
| `Policy` | `REQUIRES` | `Mitigation` |

### Provenance in Graph

| Provenance Field | Stored? |
|-----------------|---------|
| Source document | Partially — `Document.source` property exists |
| Page | **YES** — `Chunk.page` |
| Chunk | **YES** — `Chunk.id`, `Document→CONTAINS→Chunk` |
| Timestamp | **NO** |
| Confidence | **NO** |
| Extraction method | **NO** |
| Source authority | **NO** |

### Indexes

- **8 uniqueness constraints** on node IDs (all defined via `IF NOT EXISTS`)
- **No vector indexes**
- **No full-text indexes**
- **No composite indexes**

### Read Queries

> [!CAUTION]
> **The repository has ZERO read/query operations.** [`repository.py`](file:///d:/Project/src/knowledge_graph/repository.py) contains only `upsert_*` and `link_*` methods. There is **no way to query, search, or retrieve data** from the knowledge graph through the application code. The only Cypher queries are MERGE/SET/RETURN statements for writes.

---

## TASK 6 — GraphRAG Audit

> **Is GraphRAG actually implemented?**
>
> **NO. GraphRAG is MISSING entirely.**

| GraphRAG Component | Status |
|-------------------|--------|
| Graph retrieval | **MISSING** — no read queries exist |
| Entity expansion | **MISSING** |
| Multi-hop traversal | **MISSING** |
| Graph context construction | **MISSING** |
| Community detection | **MISSING** |
| Graph summaries | **MISSING** |
| Relationship-aware retrieval | **MISSING** |
| Graph + vector retrieval | **MISSING** |
| Context ranking | **MISSING** |
| LLM integration | **MISSING** |

The system currently has a Neo4j graph database with a well-designed write layer, but it is **not a GraphRAG system**. It is simply a system that can write structured data to Neo4j. There is no retrieval, no context construction, no LLM reasoning over graph data.

The `src/retrieval/__init__.py` file is 0 bytes.

---

## TASK 7 — Hybrid Retrieval Audit

```
Vector:    NO — No embedding generation, no vector storage, no similarity search
Keyword:   NO — No BM25, no full-text search, no lexical matching
Graph:     NO — No graph query/read operations exist
Fusion:    NO — No result combination logic
Reranking: NO — No reranker
```

Despite `sentence-transformers` (6.0.0) and `torch` (2.13.0) being in `requirements.txt`, they are **never imported** anywhere in the codebase. Zero retrieval code exists.

---

## TASK 8 — Multi-Agent Audit

> [!CAUTION]
> **NO AGENTS EXIST.** The `src/agents/` directory contains only a 0-byte `__init__.py` file.

| Agent | File | Real LLM Agent? | Tools | Data Access | Called in Workflow? | Status |
|-------|------|-----------------|-------|-------------|--------------------|-|
| Risk Analysis Agent | — | NO | — | — | NO | **MISSING** |
| Infrastructure Planning Agent | — | NO | — | — | NO | **MISSING** |
| Budget Prioritization Agent | — | NO | — | — | NO | **MISSING** |
| Policy & Compliance Agent | — | NO | — | — | NO | **MISSING** |
| Mitigation & Preparedness Agent | — | NO | — | — | NO | **MISSING** |
| Decision Mediator / Synthesis Agent | — | NO | — | — | NO | **MISSING** |

There is no LLM integration, no prompts, no agent orchestration, no reasoning logic, and no multi-agent workflow anywhere in the repository.

---

## TASK 9 — Router Audit

> **Does a Query Router exist?** **NO.**

- No routing logic
- No intent classification
- No agent selection
- No LLM-based routing
- No deterministic routing rules
- No query analyzer

None of the four test queries (flood risk, drainage feasibility, policy compliance, multi-factor prioritization) can be processed.

---

## TASK 10 — Debate / Deliberation Audit

> **Does a Debate Manager exist?** **NO.**

- No multi-agent deliberation
- No independent position generation
- No critique mechanism
- No evidence challenge
- No conclusion revision
- No disagreement resolution
- No turn limits or stopping conditions
- No simulated or real debate of any kind

---

## TASK 11 — Symbolic Verification Audit

> **Does a verification layer exist?** **NO.**

- No Cypher validation
- No rule engine
- No constraint checking
- No entity existence verification
- No numerical validation
- No policy validation
- No provenance verification
- No claim extraction
- No claim-to-graph verification pipeline

The pipeline `Claim → Extraction → Cypher Validation → Evidence → Verdict` does **not exist**.

---

## TASK 12 — Provenance Audit

### What exists

The chunk ID scheme (`DOC-{hash}-P{page}-C{index}`) embeds document hash and page number, and the graph schema includes a `Document→CONTAINS→Chunk` relationship. This is the **only provenance mechanism**.

### What is missing

| Provenance Feature | Status |
|-------------------|--------|
| Claim → Chunk → Page → Document tracing | **MISSING** — No claims exist |
| Document name in response | **MISSING** — No response generation |
| Page citation | **MISSING** |
| Section reference | **MISSING** |
| Graph path evidence | **MISSING** |
| Claim evidence display | **MISSING** |
| Confidence scores | **MISSING** |
| Timestamp tracking | **MISSING** |

> **Verdict:** Provenance is **structural only** (IDs contain page info). It is not functional — no response ever cites a source because no responses are generated.

---

## TASK 13 — Frontend Audit

> [!CAUTION]
> **NO FRONTEND EXISTS.**

| Feature | File | Status | Backend Connected? | Mocked? |
|---------|------|--------|--------------------|---------|
| Chat interface | — | **MISSING** | — | — |
| Query submission | — | **MISSING** | — | — |
| Response display | — | **MISSING** | — | — |
| Source citations | — | **MISSING** | — | — |
| Evidence panel | — | **MISSING** | — | — |
| Graph visualization | — | **MISSING** | — | — |
| Agent status | — | **MISSING** | — | — |
| Recommendation display | — | **MISSING** | — | — |
| Confidence indicators | — | **MISSING** | — | — |
| Verification status | — | **MISSING** | — | — |
| Document upload | — | **MISSING** | — | — |
| Document management | — | **MISSING** | — | — |
| Error handling | — | **MISSING** | — | — |
| Loading states | — | **MISSING** | — | — |

There is no HTML, CSS, JavaScript, TypeScript, React, or any UI framework code anywhere in the repository. No `package.json`. No `node_modules`. No web server.

---

## TASK 14 — Backend API Audit

> [!CAUTION]
> **NO BACKEND API EXISTS.**

There are zero HTTP endpoints. No FastAPI, Flask, Django, or Express. No `main.py`, no `app.py`, no `server.py`. The project cannot be started as a server.

| Method | Endpoint | Purpose | Frontend Used? | Status |
|--------|----------|---------|----------------|--------|
| — | — | — | — | **NOTHING EXISTS** |

---

## Summary: What Is Built vs. What Is Needed

### ✅ What Actually Works (≈8–10% of intended system)

| Component | Quality |
|-----------|---------|
| PDF text extraction (PyMuPDF) | **Good** — clean, tested, handles errors |
| Text cleaning/normalization | **Good** — handles hyphenation, whitespace |
| Page-aware chunking with overlap | **Good** — deterministic IDs, configurable |
| Neo4j connection management | **Good** — context manager, verified |
| KG schema (8 constraints) | **Good** — idempotent application |
| KG repository (8 node types, 11 relationship types) | **Good** — well-structured write layer |
| Configuration from environment | **Good** — clean, required-env validation |

### ❌ What Is Completely Missing (≈90% of intended system)

| Category | Missing Components |
|----------|--------------------|
| **Frontend** | Entire web UI (chat, visualization, upload, citations) |
| **Backend** | API server, endpoints, request/response handling |
| **LLM** | Model integration, prompt engineering, inference |
| **Agents** | All 6 agents (5 domain + 1 synthesis) |
| **Orchestration** | Agent framework, workflow, routing |
| **Retrieval** | Vector, keyword, graph, hybrid, reranking |
| **GraphRAG** | Entity expansion, traversal, context construction |
| **Extraction** | Entity/relationship/claim extraction from text |
| **Embeddings** | Embedding generation and storage |
| **Debate** | Multi-agent deliberation system |
| **Verification** | Symbolic/rule-based fact checking |
| **Provenance** | End-to-end claim tracing |
| **Evaluation** | Quality/accuracy metrics |
| **Documentation** | README, architecture docs, API docs |
| **Ingestion orchestrator** | Pipeline connecting chunks → embeddings → entities → graph |
| **KG read operations** | Graph queries, search, subgraph retrieval |

### Architectural Maturity Rating

```
Document Ingestion:    ████████░░  80% (PDF→Text→Clean→Chunk, but no downstream pipeline)
Knowledge Graph:       ████░░░░░░  40% (Write layer only. No reads, no queries.)
Retrieval:             ░░░░░░░░░░   0%
Agents:                ░░░░░░░░░░   0%
LLM Integration:       ░░░░░░░░░░   0%
GraphRAG:              ░░░░░░░░░░   0%
Frontend:              ░░░░░░░░░░   0%
Backend API:           ░░░░░░░░░░   0%
Debate/Deliberation:   ░░░░░░░░░░   0%
Verification:          ░░░░░░░░░░   0%
Evaluation:            ░░░░░░░░░░   0%
Overall System:        █░░░░░░░░░  ~8%
```
