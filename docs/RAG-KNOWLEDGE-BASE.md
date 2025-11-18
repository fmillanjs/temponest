# RAG Knowledge Base Management

**Version**: 1.0
**Last Updated**: 2025-11-18
**Status**: Production Ready

## Overview

This document explains how to manage the RAG (Retrieval Augmented Generation) knowledge base for the TempoNest agentic platform. The RAG system grounds agent responses in documented best practices, ensuring citations and improving response quality.

## Architecture

```
┌─────────────────┐
│   Documents     │ (Markdown, PDF, DOCX, TXT)
│  /docker/docs/  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Ingestion     │ (Watchdog-based monitoring)
│    Service      │ - Extracts text
└────────┬────────┘ - Chunks (512 tokens, 50 overlap)
         │          - Generates embeddings (nomic-embed-text)
         ▼
┌─────────────────┐
│     Qdrant      │ (Vector database)
│  agentic_know   │ - 768-dim vectors
│   ledge         │ - COSINE distance
└────────┬────────┘ - Metadata + content
         │
         ▼
┌─────────────────┐
│  Agents         │ (Developer, QA, Security, etc.)
│   RAG Queries   │ - Top-K=5, Min score=0.7
└─────────────────┘ - Requires 2+ citations

```

## Current Status

- **Vectors**: 124 (from 10 starter documents)
- **Collection**: `agentic_knowledge`
- **Citation Requirement**: Enabled (`REQUIRE_CITATIONS=true`)
- **Services**: All healthy and running

## Starter Documents

The knowledge base includes 10 curated documents (16,600+ words):

1. **fastapi-best-practices.md** (27 chunks)
   - Pydantic models, dependency injection, JWT auth
   - Async database operations, error handling

2. **database-schema-design.md** (26 chunks)
   - SQLAlchemy ORM patterns
   - Relationships, migrations, query optimization

3. **react-component-patterns.md** (27 chunks)
   - Functional components, hooks, Context API
   - Performance optimization, TypeScript patterns

4. **security-best-practices.md** (14 chunks)
   - OWASP Top 10 vulnerabilities
   - Authentication, input validation, security headers

5. **pytest-testing-patterns.md** (6 chunks)
   - Fixtures, parametrized tests, async testing
   - Mocking, FastAPI testing

6. **docker-containerization.md** (3 chunks)
   - Multi-stage builds, docker-compose
   - Health checks, best practices

7. **ui-design-system.md** (3 chunks)
   - Typography, colors, spacing
   - Accessibility guidelines (WCAG)

8. **api-error-handling.md** (5 chunks)
   - HTTP status codes, error responses
   - FastAPI exception handlers

9. **ci-cd-workflows.md** (4 chunks)
   - GitHub Actions workflows
   - Testing, deployment automation

10. **ux-research-methods.md** (9 chunks)
    - User personas, journey maps
    - Usability testing, interview guides

## Management Scripts

All scripts are located in `./scripts/` and are executable:

### 1. Setup Knowledge Base

```bash
./scripts/setup-knowledge-base.sh
```

**Purpose**: Initial setup and ingestion verification

**What it does**:
- Verifies all 10 starter documents exist
- Checks ingestion service and Qdrant status
- Monitors ingestion progress
- Reports vector count and readiness

**When to use**: First-time setup or after adding new documents

### 2. Verify RAG Health

```bash
./scripts/verify-rag-health.sh
```

**Purpose**: Health check for the entire RAG system

**Checks**:
- Qdrant connectivity
- Collection existence and vector count
- Minimum vector requirement (100+)
- Ingestion service status
- Citation requirements configuration

**When to use**: Regular health checks, troubleshooting

### 3. Download External Docs

```bash
./scripts/download-external-docs.sh
```

**Purpose**: Download documentation from external sources

**Downloads**:
- FastAPI docs (from GitHub)
- React docs (from react.dev repo)
- OWASP Top 10 (latest markdown)
- pytest docs (RST/MD files)

**Output**: `docker/documents/external/`

**When to use**: Expanding knowledge base with official documentation

### 4. Update Knowledge Base

```bash
./scripts/update-knowledge-base.sh
```

**Purpose**: Refresh external documentation and re-ingest

**What it does**:
- Runs `download-external-docs.sh`
- Restarts ingestion service
- Waits for processing
- Verifies new vector count

**When to use**: Monthly/quarterly updates to keep docs current

## Adding New Documents

### Manual Addition

1. Add files to `/docker/documents/`:
   ```bash
   cp my-new-doc.md docker/documents/
   ```

2. Ingestion happens automatically (watchdog monitors directory)

3. Verify ingestion:
   ```bash
   ./scripts/verify-rag-health.sh
   ```

### Supported Formats

- **Markdown** (.md) - Recommended, converts to plain text
- **Plain Text** (.txt) - Direct ingestion
- **PDF** (.pdf) - Extracted via pypdf
- **Word** (.docx, .doc) - Extracted via python-docx

### Document Guidelines

**Content**:
- Focus on best practices, patterns, and guidelines
- Include code examples where relevant
- 2000-3000 words per document (ideal)
- Clear headings and structure

**Metadata** (add at top of markdown):
```markdown
**Version**: 1.0
**Last Updated**: YYYY-MM-DD
**Tags**: tag1, tag2, tag3
**Source**: [Source Name](URL)
```

## Chunking Strategy

Documents are automatically chunked during ingestion:

- **Chunk Size**: 512 tokens (~380 words)
- **Overlap**: 50 tokens (~38 words)
- **Sentence Boundary**: Chunks break at sentence endings when possible

Example:
```
Document (2000 words) → ~5-6 chunks
Each chunk: 380 words with 38-word overlap
```

## Citation Requirements

When `REQUIRE_CITATIONS=true` (current setting):

- Agents MUST retrieve at least **2 citations** with score ≥ **0.7**
- Citations include: source document, content snippet, relevance score
- Responses without sufficient citations are rejected

**Configuration** (`docker/.env`):
```bash
RAG_TOP_K=5              # Retrieve top 5 most relevant chunks
RAG_MIN_SCORE=0.7        # Minimum relevance score (0.0-1.0)
REQUIRE_CITATIONS=true   # Enforce citation requirement
```

## Troubleshooting

### No Vectors After Adding Documents

**Symptoms**: `verify-rag-health.sh` shows 0 or low vector count

**Solutions**:
1. Check ingestion logs:
   ```bash
   docker logs agentic-ingestion --tail 100
   ```

2. Restart ingestion service:
   ```bash
   docker-compose -f docker/docker-compose.yml restart ingestion
   ```

3. Verify file permissions:
   ```bash
   chmod 644 docker/documents/*.md
   ```

### Agents Failing with Citation Errors

**Symptoms**: Agent responses rejected, "insufficient citations" error

**Solutions**:
1. Check vector count (needs 100+ for reliable results):
   ```bash
   curl -s http://localhost:6333/collections/agentic_knowledge | jq '.result.points_count'
   ```

2. Temporarily disable citation requirement (testing only):
   ```bash
   # In docker/.env
   REQUIRE_CITATIONS=false

   # Restart agents
   docker-compose -f docker/docker-compose.yml restart agents
   ```

3. Add more relevant documents to improve coverage

### Ingestion Service Not Processing

**Symptoms**: Documents added but not appearing in Qdrant

**Common Issues**:
1. **File permissions**: Files must be readable (644 or better)
2. **Service not running**: Check with `docker ps | grep ingestion`
3. **Ollama not accessible**: Embeddings require Ollama for nomic-embed-text

**Debug**:
```bash
# Check if service is running
docker ps | grep agentic-ingestion

# Check Ollama connectivity
docker exec agentic-ingestion curl -s http://ollama:11434/api/version

# Check file visibility inside container
docker exec agentic-ingestion ls -la /data/documents/
```

## Maintenance Schedule

### Weekly
- Run `verify-rag-health.sh` to check system status
- Review ingestion logs for errors

### Monthly
- Run `update-knowledge-base.sh` to refresh external docs
- Review and update starter documents if needed
- Check Qdrant collection size and performance

### Quarterly
- Audit document relevance and accuracy
- Remove outdated or deprecated content
- Add new documents for emerging technologies/patterns

## API Usage

### Query Qdrant Directly

**Get collection info**:
```bash
curl -s http://localhost:6333/collections/agentic_knowledge | jq '.result | {points_count, status}'
```

**Search for similar content**:
```bash
curl -X POST http://localhost:6333/collections/agentic_knowledge/points/search \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, ...],  # 768-dim embedding
    "limit": 5,
    "score_threshold": 0.7
  }'
```

### Test Agent with RAG

**Generate test JWT**:
```bash
python3 << 'EOF'
import jwt
from datetime import datetime, timedelta

payload = {
    "sub": "test-user",
    "tenant_id": "test",
    "email": "test@example.com",
    "roles": ["admin"],
    "permissions": ["execute:agents"],
    "is_superuser": True,
    "exp": datetime.utcnow() + timedelta(hours=1)
}

token = jwt.encode(payload, "CHANGE-ME-IN-PRODUCTION-USE-LONG-RANDOM-STRING", algorithm="HS256")
print(token)
EOF
```

**Call agent**:
```bash
curl -X POST http://localhost:9000/developer/run \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Explain FastAPI dependency injection",
    "context": {"type": "educational"},
    "idempotency_key": "test-001"
  }'
```

## Technical Details

### Embedding Model

- **Model**: nomic-embed-text
- **Dimensions**: 768
- **Provider**: Ollama (local)
- **Distance Metric**: COSINE

### Qdrant Configuration

- **Host**: http://qdrant:6333 (internal), http://localhost:6333 (external)
- **Collection**: agentic_knowledge
- **Index**: Automatically created on first vector insert

### Ingestion Process

1. **File Detection**: Watchdog monitors `/data/documents`
2. **Text Extraction**: Format-specific extractors (markdown, PDF, DOCX)
3. **Chunking**: Split into 512-token chunks with 50-token overlap
4. **Embedding**: Generate 768-dim vectors via Ollama
5. **Storage**: Upsert to Qdrant with metadata
6. **Deduplication**: Document hash prevents duplicate ingestion

## Advanced Configuration

### Custom Chunking

Edit `services/ingestion/ingest.py`:
```python
CHUNK_SIZE = 512      # Tokens per chunk
CHUNK_OVERLAP = 50    # Overlap tokens
```

### Citation Thresholds

Edit `docker/.env`:
```bash
RAG_TOP_K=10          # Retrieve more candidates
RAG_MIN_SCORE=0.8     # Higher quality threshold
```

### Multiple Collections

To create topic-specific collections:

1. Add collection name to ingestion config
2. Update RAG query logic to target specific collections
3. Use collection prefixes (e.g., `backend_knowledge`, `frontend_knowledge`)

## References

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Nomic Embed Text](https://huggingface.co/nomic-ai/nomic-embed-text-v1)
- [FastAPI RAG Patterns](https://fastapi.tiangolo.com/)

## Support

For issues or questions:
1. Check `docker logs agentic-ingestion`
2. Run `./scripts/verify-rag-health.sh`
3. Review this documentation
4. Check system health: `curl http://localhost:9000/health`
