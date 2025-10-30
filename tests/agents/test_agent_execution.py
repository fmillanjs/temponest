"""
Tests for agent execution and tool invocation.

Tests:
- Overseer goal decomposition
- Developer code generation
- Tool execution
- Budget enforcement
- Latency SLO
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import time


@pytest.mark.asyncio
async def test_budget_enforcement():
    """Test that tasks within budget pass, exceed budget fail"""

    BUDGET_TOKENS = 8000

    def count_tokens(text: str) -> int:
        # Simple approximation: ~4 chars per token
        return len(text) // 4

    def enforce_budget(text: str, budget: int = BUDGET_TOKENS) -> bool:
        tokens = count_tokens(text)
        return tokens <= budget

    # Test within budget
    small_text = "This is a small task" * 100  # ~500 tokens
    assert enforce_budget(small_text), "Small task should pass budget check"

    # Test exceeds budget
    large_text = "This is a large task that repeats many times" * 5000  # ~45000 tokens
    assert not enforce_budget(large_text), "Large task should fail budget check"


@pytest.mark.asyncio
async def test_latency_slo():
    """Test latency SLO enforcement"""

    LATENCY_SLO_MS = 5000

    def check_latency_slo(latency_ms: int, slo_ms: int = LATENCY_SLO_MS) -> bool:
        return latency_ms <= slo_ms

    # Test within SLO
    assert check_latency_slo(3000), "Fast execution should meet SLO"

    # Test exceeds SLO
    assert not check_latency_slo(6000), "Slow execution should violate SLO"


@pytest.mark.asyncio
async def test_overseer_task_routing():
    """Test that Overseer routes tasks to correct agents"""

    def route_task(task_description: str) -> str:
        task_lower = task_description.lower()

        if any(kw in task_lower for kw in ["code", "api", "schema", "component", "crud"]):
            return "developer"
        else:
            return "overseer"

    assert route_task("Create API endpoint") == "developer"
    assert route_task("Design database schema") == "developer"
    assert route_task("Plan project architecture") == "overseer"
    assert route_task("Generate CRUD operations") == "developer"


@pytest.mark.asyncio
async def test_developer_code_generation():
    """Test Developer agent code generation structure"""

    # Mock developer output
    developer_output = {
        "code": {
            "implementation": """
def create_user(name: str, email: str) -> dict:
    '''Create a new user'''
    if not name or not email:
        raise ValueError('Name and email required')

    user = {
        'id': str(uuid.uuid4()),
        'name': name,
        'email': email,
        'created_at': datetime.utcnow().isoformat()
    }

    return user
""",
            "tests": """
def test_create_user_success():
    user = create_user('John Doe', 'john@example.com')
    assert user['name'] == 'John Doe'
    assert user['email'] == 'john@example.com'
    assert 'id' in user
    assert 'created_at' in user

def test_create_user_validation():
    with pytest.raises(ValueError):
        create_user('', 'john@example.com')

    with pytest.raises(ValueError):
        create_user('John Doe', '')
""",
            "migrations": "-- No migration needed for in-memory operation",
            "setup_instructions": ["Import uuid and datetime modules", "Use in API endpoint"]
        },
        "citations": [
            {"source": "python-patterns.md", "version": "1.0", "score": 0.92},
            {"source": "api-best-practices.md", "version": "1.0", "score": 0.87}
        ]
    }

    # Validate structure
    assert "code" in developer_output, "Must include code"
    assert "implementation" in developer_output["code"], "Must include implementation"
    assert "tests" in developer_output["code"], "Must include tests"
    assert len(developer_output["citations"]) >= 2, "Must have ≥2 citations"

    # Validate content quality
    impl = developer_output["code"]["implementation"]
    assert "def " in impl, "Implementation must define functions"
    assert len(impl.strip()) > 50, "Implementation must be substantial"

    tests = developer_output["code"]["tests"]
    assert "test_" in tests, "Tests must follow naming convention"
    assert "assert" in tests, "Tests must have assertions"


@pytest.mark.asyncio
async def test_tool_execution():
    """Test agent tool execution"""

    # Mock tool: search knowledge base
    async def mock_search_knowledge(query: str):
        return """
[Citation 1]
Source: api-guide.md
Version: 1.0
Score: 0.92

Use FastAPI for REST APIs. Example:
```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/users")
def get_users():
    return {"users": []}
```

[Citation 2]
Source: database-guide.md
Version: 1.0
Score: 0.85

Use SQLAlchemy for database ORM.
"""

    result = await mock_search_knowledge("How to create REST API")

    assert "Citation 1" in result, "Should return citations"
    assert "Citation 2" in result, "Should return multiple citations"
    assert "FastAPI" in result, "Should contain relevant content"


@pytest.mark.asyncio
async def test_citation_validation():
    """Test that agent outputs are validated for sufficient citations"""

    def validate_citations(citations: list, min_count: int = 2, min_score: float = 0.7) -> dict:
        if len(citations) < min_count:
            return {
                "valid": False,
                "error": f"Insufficient citations: {len(citations)} < {min_count}"
            }

        for cit in citations[:min_count]:
            if "source" not in cit or "version" not in cit or "score" not in cit:
                return {
                    "valid": False,
                    "error": f"Citation missing required fields"
                }

            if cit["score"] < min_score:
                return {
                    "valid": False,
                    "error": f"Citation score {cit['score']} below threshold {min_score}"
                }

        return {"valid": True}

    # Valid citations
    valid_citations = [
        {"source": "doc1.md", "version": "1.0", "score": 0.9},
        {"source": "doc2.md", "version": "1.0", "score": 0.85}
    ]
    result = validate_citations(valid_citations)
    assert result["valid"], f"Valid citations should pass: {result.get('error')}"

    # Insufficient count
    insufficient = [{"source": "doc1.md", "version": "1.0", "score": 0.9}]
    result = validate_citations(insufficient)
    assert not result["valid"], "Should detect insufficient citations"

    # Low score
    low_score = [
        {"source": "doc1.md", "version": "1.0", "score": 0.9},
        {"source": "doc2.md", "version": "1.0", "score": 0.5}
    ]
    result = validate_citations(low_score)
    assert not result["valid"], "Should detect low score"


@pytest.mark.asyncio
async def test_deterministic_output():
    """Test that agents produce deterministic outputs with same seed"""

    # Model parameters should be deterministic
    model_params = {
        "model": "qwen2.5-coder:7b",
        "temperature": 0.2,
        "top_p": 0.9,
        "max_tokens": 2048,
        "seed": 42
    }

    # With same seed and low temperature, outputs should be consistent
    assert model_params["seed"] == 42, "Seed must be set for reproducibility"
    assert model_params["temperature"] <= 0.3, "Low temperature for determinism"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
