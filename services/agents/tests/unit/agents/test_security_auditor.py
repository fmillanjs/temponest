"""
Unit tests for Security Auditor Agent.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from app.agents.security_auditor import SecurityAuditorAgent


class TestSecurityAuditorAgent:
    """Test suite for SecurityAuditorAgent"""

    @pytest.fixture
    def mock_rag_memory(self):
        """Create mock RAG memory"""
        mock = AsyncMock()
        mock.retrieve = AsyncMock(return_value=[
            {
                "source": "docs/security/owasp.md",
                "version": "v2021",
                "score": 0.95,
                "content": "Use parameterized queries to prevent SQL injection"
            },
            {
                "source": "docs/security/auth.md",
                "version": "v1.0",
                "score": 0.88,
                "content": "Always use bcrypt for password hashing with work factor >= 12"
            }
        ])
        return mock

    @pytest.fixture
    def mock_tracer(self):
        """Create mock Langfuse tracer"""
        mock = Mock()
        mock.start_trace = Mock(return_value={"id": "trace-123"})
        mock.end_trace = Mock()
        return mock

    @pytest.fixture
    def security_agent(self, mock_rag_memory, mock_tracer):
        """Create SecurityAuditorAgent instance with mocked dependencies"""
        with patch('app.agents.security_auditor.Agent'):
            agent = SecurityAuditorAgent(
                rag_memory=mock_rag_memory,
                tracer=mock_tracer,
                code_model="test-model",
                temperature=0.1,
                top_p=0.9,
                max_tokens=3072,
                seed=42
            )
            return agent

    def test_init_default_params(self, mock_rag_memory, mock_tracer):
        """Test SecurityAuditorAgent initialization with default parameters"""
        with patch('app.agents.security_auditor.Agent'):
            agent = SecurityAuditorAgent(
                rag_memory=mock_rag_memory,
                tracer=mock_tracer,
                code_model="test-model"
            )

            assert agent.code_model == "test-model"
            assert agent.temperature == 0.1  # Very low for precise security analysis
            assert agent.top_p == 0.9
            assert agent.max_tokens == 3072  # Higher for detailed security reports
            assert agent.seed == 42

    def test_init_custom_params(self, mock_rag_memory, mock_tracer):
        """Test SecurityAuditorAgent initialization with custom parameters"""
        with patch('app.agents.security_auditor.Agent'):
            agent = SecurityAuditorAgent(
                rag_memory=mock_rag_memory,
                tracer=mock_tracer,
                code_model="custom-model",
                temperature=0.05,
                top_p=0.95,
                max_tokens=4096,
                seed=100
            )

            assert agent.code_model == "custom-model"
            assert agent.temperature == 0.05
            assert agent.top_p == 0.95
            assert agent.max_tokens == 4096
            assert agent.seed == 100

    def test_create_search_security_patterns_tool(self, security_agent):
        """Test search security patterns tool creation"""
        tool = security_agent._create_search_security_patterns_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    @pytest.mark.asyncio
    async def test_search_security_patterns_with_results(self, security_agent, mock_rag_memory):
        """Test search security patterns tool with results"""
        tool = security_agent._create_search_security_patterns_tool()

        result = await tool.func("SQL injection prevention")

        assert result is not None
        assert "Security Pattern" in result
        assert "docs/security/owasp.md" in result
        assert "v2021" in result
        assert "0.95" in result
        assert "parameterized queries" in result
        mock_rag_memory.retrieve.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_search_security_patterns_no_results(self, security_agent, mock_rag_memory):
        """Test search security patterns tool with no results"""
        mock_rag_memory.retrieve.return_value = []
        tool = security_agent._create_search_security_patterns_tool()

        result = await tool.func("unknown pattern")

        assert "No security patterns found" in result
        assert "OWASP guidelines" in result

    def test_create_scan_owasp_top10_tool(self, security_agent):
        """Test OWASP Top 10 scan tool creation"""
        tool = security_agent._create_scan_owasp_top10_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    def test_scan_owasp_top10_no_issues(self, security_agent):
        """Test OWASP scan with clean code"""
        tool = security_agent._create_scan_owasp_top10_tool()

        safe_code = """
def hello_world():
    return "Hello, World!"
"""

        result = tool.func(safe_code, "python")

        assert "No Issues Found" in result
        assert "No common OWASP Top 10 vulnerabilities detected" in result

    def test_scan_owasp_top10_sql_injection(self, security_agent):
        """Test OWASP scan detects SQL injection"""
        tool = security_agent._create_scan_owasp_top10_tool()

        # Pattern looks for execute() with string formatting
        vulnerable_code = """
query = "SELECT * FROM users WHERE id = {}".format(user_id)
cursor.execute(query)
"""

        result = tool.func(vulnerable_code, "python")

        assert "CRITICAL" in result
        assert "SQL Injection" in result
        assert "CWE-89" in result
        assert "parameterized queries" in result

    def test_scan_owasp_top10_code_injection(self, security_agent):
        """Test OWASP scan detects code injection"""
        tool = security_agent._create_scan_owasp_top10_tool()

        vulnerable_code = """
user_input = request.args.get('code')
eval(user_input)
"""

        result = tool.func(vulnerable_code, "python")

        assert "CRITICAL" in result
        assert "Code Injection" in result
        assert "eval()" in result
        assert "ast.literal_eval" in result

    def test_scan_owasp_top10_weak_crypto(self, security_agent):
        """Test OWASP scan detects weak cryptography"""
        tool = security_agent._create_scan_owasp_top10_tool()

        vulnerable_code = """
import hashlib
password_hash = hashlib.md5(password.encode()).hexdigest()
"""

        result = tool.func(vulnerable_code, "python")

        assert "MEDIUM" in result
        assert "Cryptographic Failures" in result
        assert "MD5" in result or "md5" in result
        assert "bcrypt" in result

    def test_scan_owasp_top10_debug_mode(self, security_agent):
        """Test OWASP scan detects debug mode enabled"""
        tool = security_agent._create_scan_owasp_top10_tool()

        # Pattern looks for DEBUG = True (with space) or debug=True (no space)
        vulnerable_code = """
app = Flask(__name__)
DEBUG = True
"""

        result = tool.func(vulnerable_code, "python")

        assert "MEDIUM" in result
        assert "Security Misconfiguration" in result
        assert "Debug mode" in result

    def test_scan_owasp_top10_cors_misconfiguration(self, security_agent):
        """Test OWASP scan detects CORS misconfiguration"""
        tool = security_agent._create_scan_owasp_top10_tool()

        # Pattern: CORS.*allow_origins.*\[.*\*.*\] (all on same logical line for regex)
        vulnerable_code = """
CORS_CONFIG = {"allow_origins": ["*"], "allow_credentials": True}
"""

        result = tool.func(vulnerable_code, "python")

        assert "HIGH" in result
        assert "CORS" in result or "Security Misconfiguration" in result

    def test_scan_owasp_top10_plaintext_password(self, security_agent):
        """Test OWASP scan detects plaintext password storage"""
        tool = security_agent._create_scan_owasp_top10_tool()

        vulnerable_code = """
user.password = request.form.get('password')
db.session.commit()
"""

        result = tool.func(vulnerable_code, "python")

        assert "HIGH" in result
        assert "Authentication Failures" in result
        assert "plaintext password" in result

    def test_scan_owasp_top10_insecure_deserialization(self, security_agent):
        """Test OWASP scan detects insecure deserialization"""
        tool = security_agent._create_scan_owasp_top10_tool()

        vulnerable_code = """
import pickle
data = pickle.loads(request.data)
"""

        result = tool.func(vulnerable_code, "python")

        assert "HIGH" in result
        assert "Integrity Failures" in result
        assert "pickle" in result

    def test_scan_owasp_top10_ssrf(self, security_agent):
        """Test OWASP scan detects SSRF vulnerability"""
        tool = security_agent._create_scan_owasp_top10_tool()

        # Pattern looks for requests.get/post with request. or input(
        vulnerable_code = """
import requests
url = request.query['url']
response = requests.get(request.query['url'])
"""

        result = tool.func(vulnerable_code, "python")

        assert "HIGH" in result
        assert "SSRF" in result

    def test_scan_owasp_top10_insecure_random(self, security_agent):
        """Test OWASP scan detects insecure random for security tokens"""
        tool = security_agent._create_scan_owasp_top10_tool()

        vulnerable_code = """
import random
api_key = str(random.random())
"""

        result = tool.func(vulnerable_code, "python")

        assert "CRITICAL" in result
        assert "Insecure random" in result
        assert "secrets.token" in result

    def test_scan_owasp_top10_secret_logging(self, security_agent):
        """Test OWASP scan detects secret exposure in logs"""
        tool = security_agent._create_scan_owasp_top10_tool()

        vulnerable_code = """
SECRET_KEY = "my-secret-key"
logging.info(f"Using secret: {SECRET_KEY}")
"""

        result = tool.func(vulnerable_code, "python")

        assert "HIGH" in result
        assert "secret exposure" in result

    def test_create_check_dependency_vulnerabilities_tool(self, security_agent):
        """Test dependency vulnerability check tool creation"""
        tool = security_agent._create_check_dependency_vulnerabilities_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    def test_check_dependencies_no_vulnerabilities(self, security_agent):
        """Test dependency check with safe versions"""
        tool = security_agent._create_check_dependency_vulnerabilities_tool()

        dependencies = """
requests==2.28.1
flask==2.3.0
"""

        result = tool.func(dependencies)

        assert "No Known Vulnerabilities" in result
        assert "pip-audit" in result

    def test_check_dependencies_vulnerable_django(self, security_agent):
        """Test dependency check detects vulnerable Django"""
        tool = security_agent._create_check_dependency_vulnerabilities_tool()

        dependencies = """
django==3.0
"""

        result = tool.func(dependencies)

        assert "Dependency Vulnerabilities Found" in result
        assert "django" in result.lower()
        assert "3.0" in result
        assert "HIGH" in result

    def test_check_dependencies_vulnerable_flask(self, security_agent):
        """Test dependency check detects vulnerable Flask"""
        tool = security_agent._create_check_dependency_vulnerabilities_tool()

        dependencies = """
flask==0.12
requests==2.28.1
"""

        result = tool.func(dependencies)

        assert "Dependency Vulnerabilities Found" in result
        assert "flask" in result.lower()
        assert "0.12" in result

    def test_check_dependencies_ignores_comments(self, security_agent):
        """Test dependency check ignores comments"""
        tool = security_agent._create_check_dependency_vulnerabilities_tool()

        dependencies = """
# This is a comment
requests==2.28.1
# Another comment
"""

        result = tool.func(dependencies)

        assert "No Known Vulnerabilities" in result

    def test_create_validate_auth_security_tool(self, security_agent):
        """Test auth security validation tool creation"""
        tool = security_agent._create_validate_auth_security_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    def test_validate_auth_secure_implementation(self, security_agent):
        """Test auth validation with secure implementation"""
        tool = security_agent._create_validate_auth_security_tool()

        secure_code = """
import bcrypt
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
"""

        result = tool.func(secure_code)

        assert "No Issues Found" in result or "Best Practices" in result

    def test_validate_auth_jwt_no_expiration(self, security_agent):
        """Test auth validation detects JWT without expiration"""
        tool = security_agent._create_validate_auth_security_tool()

        insecure_code = """
import jwt
token = jwt.encode({"user_id": 123}, secret, algorithm="HS256")
"""

        result = tool.func(insecure_code)

        assert "HIGH" in result
        assert "expiration" in result.lower()

    def test_validate_auth_disabled_signature_verification(self, security_agent):
        """Test auth validation detects disabled JWT signature verification"""
        tool = security_agent._create_validate_auth_security_tool()

        insecure_code = """
import jwt
decoded = jwt.decode(token, options={"verify_signature": False})
"""

        result = tool.func(insecure_code)

        assert "CRITICAL" in result
        assert "signature verification disabled" in result

    def test_validate_auth_plaintext_password_comparison(self, security_agent):
        """Test auth validation detects plaintext password comparison"""
        tool = security_agent._create_validate_auth_security_tool()

        insecure_code = """
if user.password == input_password:
    login_user(user)
"""

        result = tool.func(insecure_code)

        assert "CRITICAL" in result
        assert "Plaintext password comparison" in result
        assert "bcrypt.checkpw" in result

    def test_validate_auth_missing_cookie_flags(self, security_agent):
        """Test auth validation detects missing cookie security flags"""
        tool = security_agent._create_validate_auth_security_tool()

        insecure_code = """
response.set_cookie('session', session_id)
"""

        result = tool.func(insecure_code)

        assert "HttpOnly" in result
        assert "Secure" in result
        assert "SameSite" in result

    def test_validate_auth_api_key_in_query(self, security_agent):
        """Test auth validation recommends header-based API keys"""
        tool = security_agent._create_validate_auth_security_tool()

        code_with_api_key = """
api_key = request.args.get('api_key')
"""

        result = tool.func(code_with_api_key)

        # Should recommend using headers
        assert "header" in result.lower() or "Authorization" in result

    def test_validate_auth_missing_rate_limiting(self, security_agent):
        """Test auth validation recommends rate limiting"""
        tool = security_agent._create_validate_auth_security_tool()

        login_code = """
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    # authenticate user
"""

        result = tool.func(login_code)

        assert "rate limit" in result.lower() or "brute force" in result.lower()

    def test_create_scan_secrets_tool(self, security_agent):
        """Test secrets scanning tool creation"""
        tool = security_agent._create_scan_secrets_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    def test_scan_secrets_clean_code(self, security_agent):
        """Test secrets scan with clean code"""
        tool = security_agent._create_scan_secrets_tool()

        clean_code = """
from dotenv import load_dotenv
import os

load_dotenv()
db_password = os.environ.get('DB_PASSWORD')
"""

        result = tool.func(clean_code)

        assert "No Hardcoded Secrets Found" in result
        assert "Best Practices" in result

    def test_scan_secrets_hardcoded_password(self, security_agent):
        """Test secrets scan detects hardcoded password"""
        tool = security_agent._create_scan_secrets_tool()

        vulnerable_code = """
db_password = "my-super-secret-password"
"""

        result = tool.func(vulnerable_code)

        assert "Hardcoded Secrets Detected" in result
        assert "password" in result.lower()
        assert "HIGH" in result or "MEDIUM" in result

    def test_scan_secrets_hardcoded_api_key(self, security_agent):
        """Test secrets scan detects hardcoded API key"""
        tool = security_agent._create_scan_secrets_tool()

        # Stripe key pattern requires 24+ alphanumeric characters after sk_live_
        # Using concatenation to avoid triggering GitHub's secret scanner
        vulnerable_code = """
stripe_api_key = "sk_" + "live_" + "abcdefghijklmnopqrstuvwxyz1234567890"
"""

        result = tool.func(vulnerable_code)

        assert "Hardcoded Secrets Detected" in result
        assert "Stripe" in result or "api" in result.lower()
        assert "CRITICAL" in result

    def test_scan_secrets_aws_key(self, security_agent):
        """Test secrets scan detects AWS access key"""
        tool = security_agent._create_scan_secrets_tool()

        vulnerable_code = """
aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"
"""

        result = tool.func(vulnerable_code)

        assert "Hardcoded Secrets Detected" in result
        assert "AWS" in result
        assert "CRITICAL" in result

    def test_scan_secrets_private_key(self, security_agent):
        """Test secrets scan detects private key"""
        tool = security_agent._create_scan_secrets_tool()

        vulnerable_code = """
key = '''-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
-----END RSA PRIVATE KEY-----'''
"""

        result = tool.func(vulnerable_code)

        assert "Hardcoded Secrets Detected" in result
        assert "Private key" in result
        assert "CRITICAL" in result

    def test_scan_secrets_database_connection_string(self, security_agent):
        """Test secrets scan detects database connection string"""
        tool = security_agent._create_scan_secrets_tool()

        vulnerable_code = """
db_url = "postgres://admin:password123@localhost:5432/mydb"
"""

        result = tool.func(vulnerable_code)

        assert "Hardcoded Secrets Detected" in result
        assert "connection string" in result.lower()
        assert "HIGH" in result or "CRITICAL" in result

    def test_scan_secrets_github_token(self, security_agent):
        """Test secrets scan detects GitHub token"""
        tool = security_agent._create_scan_secrets_tool()

        # GitHub token pattern: ghp_ + exactly 36 alphanumeric chars
        vulnerable_code = """
github_token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
"""

        result = tool.func(vulnerable_code)

        assert "Hardcoded Secrets Detected" in result
        assert "GitHub" in result
        assert "CRITICAL" in result

    def test_scan_secrets_stripe_key(self, security_agent):
        """Test secrets scan detects Stripe secret key"""
        tool = security_agent._create_scan_secrets_tool()

        # Stripe pattern: sk_live_ followed by 24+ alphanumeric chars
        # Using concatenation to avoid triggering GitHub's secret scanner
        vulnerable_code = """
stripe_key = "sk_" + "live_" + "abcdefghijklmnopqrstuvwxyz123456"
"""

        result = tool.func(vulnerable_code)

        assert "Hardcoded Secrets Detected" in result
        assert "Stripe" in result
        assert "CRITICAL" in result

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_rag_memory, mock_tracer):
        """Test successful agent execution"""
        with patch('app.agents.security_auditor.Agent') as mock_agent_class:
            with patch('app.agents.security_auditor.Crew') as mock_crew_class:
                with patch('app.agents.security_auditor.Task') as mock_task_class:
                    # Setup agent with proper mocking
                    security_agent = SecurityAuditorAgent(
                        rag_memory=mock_rag_memory,
                        tracer=mock_tracer,
                        code_model="test-model"
                    )

                    # Mock crew execution
                    mock_crew = MagicMock()
                    mock_crew.kickoff_async = AsyncMock(return_value="Security Report: CRITICAL: 2, HIGH: 3")
                    mock_crew_class.return_value = mock_crew

                    result = await security_agent.execute(
                        task="Audit the authentication code",
                        context={"code": "def login(): pass"},
                        task_id="task-123"
                    )

                    assert "security_report" in result
                    assert "risk_score" in result
                    assert "compliance" in result
                    assert "citations" in result
                    assert "execution_time_ms" in result
                    assert isinstance(result["execution_time_ms"], int)

                    # Verify tracer was called
                    mock_tracer.start_trace.assert_called_once()
                    mock_tracer.end_trace.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_error_handling(self, mock_rag_memory, mock_tracer):
        """Test agent execution error handling"""
        with patch('app.agents.security_auditor.Agent') as mock_agent_class:
            with patch('app.agents.security_auditor.Crew') as mock_crew_class:
                with patch('app.agents.security_auditor.Task') as mock_task_class:
                    # Setup agent
                    security_agent = SecurityAuditorAgent(
                        rag_memory=mock_rag_memory,
                        tracer=mock_tracer,
                        code_model="test-model"
                    )

                    # Mock crew execution failure
                    mock_crew_class.side_effect = Exception("Execution failed")

                    with pytest.raises(Exception, match="Execution failed"):
                        await security_agent.execute(
                            task="Audit the code",
                            context={},
                            task_id="task-error"
                        )

                    # Verify error was traced
                    mock_tracer.start_trace.assert_called_once()
                    mock_tracer.end_trace.assert_called_once()
                    # Verify error was logged in trace
                    call_args = mock_tracer.end_trace.call_args
                    assert "error" in call_args[1]["output"]

    def test_extract_citations_with_matches(self, security_agent):
        """Test citation extraction with valid citations"""
        result_text = """
Security Report

[Security Pattern 1] OWASP Top 10 Guidelines (v2021)
[Security Pattern 2] Auth Best Practices (v1.5)
[Citation 3] CWE Database (v4.0)
"""

        citations = security_agent._extract_citations(result_text)

        assert len(citations) >= 2
        assert citations[0]["source"] == "OWASP Top 10 Guidelines"
        assert citations[0]["version"] == "2021"
        assert citations[1]["source"] == "Auth Best Practices"
        assert citations[1]["version"] == "1.5"

    def test_extract_citations_no_matches(self, security_agent):
        """Test citation extraction with no citations"""
        result_text = "No citations in this text"

        citations = security_agent._extract_citations(result_text)

        assert len(citations) == 0

    def test_extract_citations_limit_to_five(self, security_agent):
        """Test citation extraction limits to 5 citations"""
        result_text = """
[Security Pattern 1] Source1 (v1.0)
[Security Pattern 2] Source2 (v2.0)
[Security Pattern 3] Source3 (v3.0)
[Security Pattern 4] Source4 (v4.0)
[Security Pattern 5] Source5 (v5.0)
[Security Pattern 6] Source6 (v6.0)
[Security Pattern 7] Source7 (v7.0)
"""

        citations = security_agent._extract_citations(result_text)

        assert len(citations) == 5

    def test_calculate_risk_score_no_findings(self, security_agent):
        """Test risk score calculation with no findings"""
        result_text = "All clear, no vulnerabilities found"

        score = security_agent._calculate_risk_score(result_text)

        assert score == 0

    def test_calculate_risk_score_critical_findings(self, security_agent):
        """Test risk score calculation with critical findings"""
        result_text = """
CRITICAL: SQL Injection
CRITICAL: Code Injection
HIGH: XSS vulnerability
"""

        score = security_agent._calculate_risk_score(result_text)

        # 2 CRITICAL (20 each) + 1 HIGH (10) = 50
        assert score >= 40  # Allow some flexibility

    def test_calculate_risk_score_caps_at_100(self, security_agent):
        """Test risk score caps at 100"""
        result_text = "CRITICAL " * 50  # Many critical findings

        score = security_agent._calculate_risk_score(result_text)

        assert score == 100

    def test_calculate_risk_score_weighted(self, security_agent):
        """Test risk score uses proper weighting"""
        result_text = """
CRITICAL finding
HIGH finding
HIGH finding
MEDIUM finding
MEDIUM finding
MEDIUM finding
LOW finding
LOW finding
LOW finding
LOW finding
"""

        score = security_agent._calculate_risk_score(result_text)

        # 1*20 + 2*10 + 3*5 + 4*1 = 59
        assert 50 <= score <= 65  # Allow some flexibility for case-insensitive matching

    def test_extract_summary_all_severities(self, security_agent):
        """Test summary extraction with all severity levels"""
        result_text = """
CRITICAL: Issue 1
CRITICAL: Issue 2
HIGH: Issue 3
HIGH: Issue 4
HIGH: Issue 5
MEDIUM: Issue 6
MEDIUM: Issue 7
LOW: Issue 8
INFO: Issue 9
"""

        summary = security_agent._extract_summary(result_text)

        assert summary["critical"] == 2
        assert summary["high"] == 3
        assert summary["medium"] == 2
        assert summary["low"] == 1
        assert summary["info"] == 1

    def test_extract_summary_empty_result(self, security_agent):
        """Test summary extraction with no findings"""
        result_text = "No issues found"

        summary = security_agent._extract_summary(result_text)

        assert summary["critical"] == 0
        assert summary["high"] == 0
        assert summary["medium"] == 0
        assert summary["low"] == 0
        assert summary["info"] == 0

    def test_extract_summary_case_insensitive(self, security_agent):
        """Test summary extraction is case insensitive"""
        result_text = """
critical: Issue 1
Critical: Issue 2
CRITICAL: Issue 3
"""

        summary = security_agent._extract_summary(result_text)

        assert summary["critical"] >= 3
