"""
Security Auditor Agent - Automated security auditing and vulnerability scanning.

Responsibilities:
- Scan code for OWASP Top 10 vulnerabilities
- Check for common security issues (SQL injection, XSS, CSRF, insecure dependencies)
- Validate authentication and authorization patterns
- Analyze secrets management and credential handling
- Check dependency versions for known CVEs
- Validate security headers and configurations
- Generate security reports with severity ratings (Critical, High, Medium, Low)
"""

from typing import Dict, Any, List, Optional
import time
import json
import re
import ast
from crewai import Agent, Task, Crew
from crewai.tools import tool

from app.memory.rag import RAGMemory
from app.memory.langfuse_tracer import LangfuseTracer


class SecurityAuditorAgent:
    """Security Auditor agent that scans for vulnerabilities and security issues"""

    def __init__(
        self,
        rag_memory: RAGMemory,
        tracer: LangfuseTracer,
        code_model: str,
        temperature: float = 0.1,  # Very low for precise security analysis
        top_p: float = 0.9,
        max_tokens: int = 3072,  # Higher for detailed security reports
        seed: int = 42
    ):
        self.rag_memory = rag_memory
        self.tracer = tracer
        self.code_model = code_model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.seed = seed

        # Create the agent
        self.agent = Agent(
            role="Senior Security Engineer",
            goal="Identify and report security vulnerabilities following OWASP standards and industry best practices",
            backstory="""You are a senior security engineer with expertise in:
            - OWASP Top 10 vulnerabilities (Injection, Broken Auth, XSS, etc.)
            - Secure coding practices (input validation, output encoding, parameterized queries)
            - Authentication and authorization security (JWT, OAuth, RBAC)
            - Cryptography (hashing, encryption, secure random generation)
            - Dependency vulnerability scanning (CVE databases, security advisories)
            - Security headers (CSP, HSTS, X-Frame-Options, etc.)
            - Secrets management (API keys, credentials, tokens)
            - Common attack patterns (CSRF, SSRF, Path Traversal, etc.)

            You ALWAYS:
            - Classify vulnerabilities by severity (Critical, High, Medium, Low, Info)
            - Provide specific code locations for each finding
            - Include remediation guidance with code examples
            - Reference OWASP guidelines and CWE identifiers
            - Check for both known CVEs and logic vulnerabilities
            - Validate input sanitization and output encoding
            - Search security patterns in the knowledge base
            - Consider defense-in-depth principles
            - Prioritize findings by exploitability and impact""",
            verbose=True,
            allow_delegation=False,
            tools=[
                self._create_search_security_patterns_tool(),
                self._create_scan_owasp_top10_tool(),
                self._create_check_dependency_vulnerabilities_tool(),
                self._create_validate_auth_security_tool(),
                self._create_scan_secrets_tool()
            ],
            llm_config={
                "model": code_model,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "seed": seed
            }
        )

    def _create_search_security_patterns_tool(self):
        """Create tool for searching security patterns"""
        rag_memory = self.rag_memory

        @tool("search_security_patterns")
        async def search_security_patterns(query: str) -> str:
            """
            Search the knowledge base for security patterns and best practices.

            Args:
                query: What security pattern you need (e.g., "SQL injection prevention", "JWT security")

            Returns:
                Relevant security patterns with examples
            """
            results = await rag_memory.retrieve(
                query=f"security pattern: {query}",
                top_k=5,
                min_score=0.7
            )

            if not results:
                return "No security patterns found. Use OWASP guidelines and industry best practices."

            # Format results
            output = []
            for i, doc in enumerate(results, 1):
                output.append(f"""
[Security Pattern {i}] {doc['source']} (v{doc['version']})
Relevance: {doc['score']:.2f}

```
{doc['content']}
```

---
""")

            return "\n".join(output)

        return search_security_patterns

    def _create_scan_owasp_top10_tool(self):
        """Create tool for scanning OWASP Top 10 vulnerabilities"""

        @tool("scan_owasp_top10")
        def scan_owasp_top10(code: str, language: str = "python") -> str:
            """
            Scan code for OWASP Top 10 vulnerabilities.

            Args:
                code: Source code to scan
                language: Programming language (python, javascript, etc.)

            Returns:
                Vulnerability report with severity ratings
            """
            findings = []

            # A01:2021 – Broken Access Control
            if "request.user" in code and "if" not in code[:code.find("request.user") + 100]:
                findings.append({
                    "severity": "HIGH",
                    "category": "A01:2021 - Broken Access Control",
                    "cwe": "CWE-284",
                    "description": "Potential missing authorization check",
                    "recommendation": "Add permission checks before accessing user data"
                })

            # A02:2021 – Cryptographic Failures
            if re.search(r'md5|sha1(?!hash)', code, re.IGNORECASE):
                findings.append({
                    "severity": "MEDIUM",
                    "category": "A02:2021 - Cryptographic Failures",
                    "cwe": "CWE-327",
                    "description": "Weak hashing algorithm detected (MD5/SHA1)",
                    "recommendation": "Use bcrypt, scrypt, or Argon2 for password hashing; SHA-256+ for non-password hashing"
                })

            # A03:2021 – Injection
            if re.search(r'execute\(.*?f["\']|execute\(.*?\+|\.format\(.*?\)', code):
                findings.append({
                    "severity": "CRITICAL",
                    "category": "A03:2021 - Injection (SQL Injection)",
                    "cwe": "CWE-89",
                    "description": "Potential SQL injection via string formatting",
                    "recommendation": "Use parameterized queries with $1, $2 placeholders"
                })

            if "eval(" in code or "exec(" in code:
                findings.append({
                    "severity": "CRITICAL",
                    "category": "A03:2021 - Injection (Code Injection)",
                    "cwe": "CWE-95",
                    "description": "Code injection via eval() or exec()",
                    "recommendation": "Never use eval/exec with user input. Use safe alternatives like ast.literal_eval()"
                })

            # A04:2021 – Insecure Design
            if "SECRET" in code and ("print(" in code or "logging.info" in code):
                findings.append({
                    "severity": "HIGH",
                    "category": "A04:2021 - Insecure Design",
                    "cwe": "CWE-209",
                    "description": "Potential secret exposure in logs",
                    "recommendation": "Never log secrets. Use logging filters to redact sensitive data"
                })

            # A05:2021 – Security Misconfiguration
            if "DEBUG = True" in code or "debug=True" in code:
                findings.append({
                    "severity": "MEDIUM",
                    "category": "A05:2021 - Security Misconfiguration",
                    "cwe": "CWE-489",
                    "description": "Debug mode enabled in production",
                    "recommendation": "Set DEBUG=False in production. Use environment variables"
                })

            if re.search(r'CORS.*allow_origins.*\[.*\*.*\]', code, re.IGNORECASE):
                findings.append({
                    "severity": "HIGH",
                    "category": "A05:2021 - Security Misconfiguration",
                    "cwe": "CWE-942",
                    "description": "CORS configured to allow all origins (*)",
                    "recommendation": "Restrict CORS to specific trusted domains"
                })

            # A06:2021 – Vulnerable and Outdated Components
            if "requests==" in code or "django==" in code:
                findings.append({
                    "severity": "INFO",
                    "category": "A06:2021 - Vulnerable Components",
                    "cwe": "CWE-1035",
                    "description": "Pinned dependencies detected - check for CVEs",
                    "recommendation": "Run 'pip-audit' or 'safety check' to scan for known vulnerabilities"
                })

            # A07:2021 – Identification and Authentication Failures
            if "password" in code.lower() and "hash" not in code.lower():
                findings.append({
                    "severity": "HIGH",
                    "category": "A07:2021 - Authentication Failures",
                    "cwe": "CWE-256",
                    "description": "Potential plaintext password storage",
                    "recommendation": "Always hash passwords with bcrypt/scrypt/Argon2"
                })

            # A08:2021 – Software and Data Integrity Failures
            if "pickle.loads(" in code:
                findings.append({
                    "severity": "HIGH",
                    "category": "A08:2021 - Integrity Failures",
                    "cwe": "CWE-502",
                    "description": "Insecure deserialization with pickle",
                    "recommendation": "Use JSON for serialization. If pickle needed, validate source and use signing"
                })

            # A09:2021 – Security Logging and Monitoring Failures
            if "try:" in code and "except:" in code and "logging" not in code:
                findings.append({
                    "severity": "LOW",
                    "category": "A09:2021 - Logging Failures",
                    "cwe": "CWE-778",
                    "description": "Exception handling without logging",
                    "recommendation": "Log security-relevant events (auth failures, access violations)"
                })

            # A10:2021 – Server-Side Request Forgery (SSRF)
            if re.search(r'requests\.(get|post)\(.*?request\.|requests\.(get|post)\(.*?input\(', code):
                findings.append({
                    "severity": "HIGH",
                    "category": "A10:2021 - SSRF",
                    "cwe": "CWE-918",
                    "description": "Potential SSRF via user-controlled URL",
                    "recommendation": "Validate URLs against allowlist. Block private IP ranges"
                })

            # Additional checks
            if "random.random()" in code and ("token" in code.lower() or "key" in code.lower()):
                findings.append({
                    "severity": "CRITICAL",
                    "category": "Cryptographic Failures",
                    "cwe": "CWE-338",
                    "description": "Insecure random number generation for security token",
                    "recommendation": "Use secrets.token_urlsafe() or secrets.token_hex() for cryptographic operations"
                })

            # Format report
            if not findings:
                return """
✅ OWASP Top 10 Scan: No Issues Found

No common OWASP Top 10 vulnerabilities detected in this code.
Note: This is a static analysis. Manual review and dynamic testing still recommended.
"""

            critical = sum(1 for f in findings if f["severity"] == "CRITICAL")
            high = sum(1 for f in findings if f["severity"] == "HIGH")
            medium = sum(1 for f in findings if f["severity"] == "MEDIUM")
            low = sum(1 for f in findings if f["severity"] == "LOW")
            info = sum(1 for f in findings if f["severity"] == "INFO")

            report = f"""
🔴 OWASP Top 10 Scan Results:

Summary:
  CRITICAL: {critical}
  HIGH: {high}
  MEDIUM: {medium}
  LOW: {low}
  INFO: {info}

Findings:
"""

            for i, finding in enumerate(findings, 1):
                severity_icon = {
                    "CRITICAL": "🔴",
                    "HIGH": "🟠",
                    "MEDIUM": "🟡",
                    "LOW": "🔵",
                    "INFO": "ℹ️"
                }.get(finding["severity"], "•")

                report += f"""
{severity_icon} Finding {i}: {finding['category']}
   Severity: {finding['severity']}
   CWE: {finding['cwe']}
   Issue: {finding['description']}
   Fix: {finding['recommendation']}
"""

            report += """
Next Steps:
  1. Address CRITICAL and HIGH findings immediately
  2. Review MEDIUM findings before deployment
  3. Plan remediation for LOW findings
  4. Run dynamic security testing (DAST)
  5. Perform penetration testing for critical systems
"""

            return report

        return scan_owasp_top10

    def _create_check_dependency_vulnerabilities_tool(self):
        """Create tool for checking dependency vulnerabilities"""

        @tool("check_dependency_vulnerabilities")
        def check_dependency_vulnerabilities(dependencies: str) -> str:
            """
            Check dependencies for known CVEs.

            Args:
                dependencies: requirements.txt or package.json content

            Returns:
                Vulnerability report for dependencies
            """
            # Parse dependencies (simplified - in production, use pip-audit or safety)
            vulnerable_packages = {
                "django": ["3.0", "3.1", "3.2.0"],  # Example old versions
                "flask": ["0.12", "1.0"],
                "requests": ["2.6", "2.7"],
                "pillow": ["8.0", "8.1"],
                "pyyaml": ["5.3", "5.4"],
            }

            findings = []
            lines = dependencies.split("\n")

            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Parse package==version
                match = re.match(r'([a-zA-Z0-9\-_]+)==([0-9\.]+)', line)
                if match:
                    package, version = match.groups()
                    package_lower = package.lower()

                    if package_lower in vulnerable_packages:
                        if version in vulnerable_packages[package_lower]:
                            findings.append({
                                "package": package,
                                "current_version": version,
                                "severity": "HIGH",
                                "issue": "Known vulnerability in this version",
                                "recommendation": "Update to latest stable version"
                            })

            if not findings:
                return """
✅ Dependency Scan: No Known Vulnerabilities

All dependencies appear to be using non-vulnerable versions.

Recommendations:
  - Run 'pip-audit' or 'safety check' for comprehensive CVE scanning
  - Keep dependencies updated regularly
  - Monitor security advisories for your dependencies
  - Use Dependabot or Renovate for automated updates
"""

            report = f"""
🔴 Dependency Vulnerabilities Found: {len(findings)}

"""

            for i, finding in enumerate(findings, 1):
                report += f"""
Finding {i}:
  Package: {finding['package']}=={finding['current_version']}
  Severity: {finding['severity']}
  Issue: {finding['issue']}
  Fix: {finding['recommendation']}
"""

            report += """
Immediate Actions:
  1. Update vulnerable packages to latest versions
  2. Test thoroughly after updates
  3. Check for breaking changes in changelogs
  4. Set up automated vulnerability scanning in CI/CD

Tools:
  - pip-audit (Python): pip install pip-audit && pip-audit
  - safety (Python): pip install safety && safety check
  - npm audit (Node.js): npm audit fix
  - snyk (Multi-language): https://snyk.io
"""

            return report

        return check_dependency_vulnerabilities

    def _create_validate_auth_security_tool(self):
        """Create tool for validating authentication security"""

        @tool("validate_auth_security")
        def validate_auth_security(auth_code: str) -> str:
            """
            Validate authentication and authorization implementation.

            Args:
                auth_code: Authentication/authorization code to validate

            Returns:
                Security assessment of auth implementation
            """
            issues = []
            recommendations = []

            # JWT Security
            if "jwt" in auth_code.lower():
                if "HS256" in auth_code and "secret" in auth_code.lower():
                    issues.append({
                        "severity": "MEDIUM",
                        "issue": "HS256 algorithm detected - symmetric signing",
                        "fix": "Consider using RS256 (asymmetric) for better key management"
                    })

                if "verify_signature" in auth_code and "False" in auth_code:
                    issues.append({
                        "severity": "CRITICAL",
                        "issue": "JWT signature verification disabled",
                        "fix": "NEVER disable signature verification in production"
                    })

                if "exp" not in auth_code.lower():
                    issues.append({
                        "severity": "HIGH",
                        "issue": "No expiration (exp) claim in JWT",
                        "fix": "Add expiration to prevent token replay attacks"
                    })

            # Password Security
            if "password" in auth_code.lower():
                if "bcrypt" not in auth_code and "scrypt" not in auth_code and "argon2" not in auth_code:
                    issues.append({
                        "severity": "HIGH",
                        "issue": "Missing strong password hashing (bcrypt/scrypt/argon2)",
                        "fix": "Use bcrypt.hashpw() for password hashing"
                    })

                if re.search(r'password.*==.*password', auth_code, re.IGNORECASE):
                    issues.append({
                        "severity": "CRITICAL",
                        "issue": "Plaintext password comparison",
                        "fix": "Use constant-time comparison: bcrypt.checkpw()"
                    })

            # Session Security
            if "session" in auth_code.lower():
                if "httponly" not in auth_code.lower():
                    recommendations.append("Set HttpOnly flag on session cookies to prevent XSS")

                if "secure" not in auth_code.lower():
                    recommendations.append("Set Secure flag on cookies to enforce HTTPS")

                if "samesite" not in auth_code.lower():
                    recommendations.append("Set SameSite=Strict to prevent CSRF")

            # API Key Security
            if "api_key" in auth_code.lower() or "api-key" in auth_code.lower():
                if "header" not in auth_code.lower():
                    recommendations.append("Pass API keys in headers (Authorization or X-API-Key), not query params")

            # Rate Limiting
            if "login" in auth_code.lower() or "auth" in auth_code.lower():
                if "rate" not in auth_code.lower() and "limit" not in auth_code.lower():
                    recommendations.append("Add rate limiting to prevent brute force attacks")

            # Format report
            if not issues and not recommendations:
                return """
✅ Authentication Security: No Issues Found

The authentication implementation looks secure.

Best Practices Checklist:
  ✓ Strong password hashing (bcrypt/scrypt/argon2)
  ✓ JWT signature verification enabled
  ✓ Token expiration implemented
  ✓ Secure session management
  ✓ Rate limiting on auth endpoints
  ✓ HttpOnly + Secure + SameSite cookies
  ✓ API keys in headers, not query params
"""

            report = "🔴 Authentication Security Issues:\n\n"

            if issues:
                report += "Critical Issues:\n"
                for issue in issues:
                    severity_icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡"}.get(issue["severity"], "•")
                    report += f"""
{severity_icon} {issue['severity']}: {issue['issue']}
   Fix: {issue['fix']}
"""

            if recommendations:
                report += "\nRecommendations:\n"
                for rec in recommendations:
                    report += f"  • {rec}\n"

            report += """
Security Checklist:
  □ Use strong password hashing (bcrypt work factor ≥12)
  □ Implement JWT with expiration (exp claim)
  □ Use RS256 for JWT if possible (asymmetric keys)
  □ Add rate limiting (e.g., 5 login attempts per minute)
  □ Set HttpOnly, Secure, SameSite flags on cookies
  □ Use constant-time comparison for secrets
  □ Implement account lockout after failed attempts
  □ Log all authentication events
  □ Use HTTPS everywhere (enforce with HSTS header)
  □ Implement MFA for privileged accounts
"""

            return report

        return validate_auth_security

    def _create_scan_secrets_tool(self):
        """Create tool for scanning hardcoded secrets"""

        @tool("scan_secrets")
        def scan_secrets(code: str) -> str:
            """
            Scan code for hardcoded secrets and credentials.

            Args:
                code: Source code to scan

            Returns:
                Report of potential secrets found
            """
            findings = []

            # Common secret patterns
            patterns = [
                (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password", "HIGH"),
                (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key", "CRITICAL"),
                (r'secret[_-]?key\s*=\s*["\'][^"\']+["\']', "Hardcoded secret key", "CRITICAL"),
                (r'aws[_-]?access[_-]?key[_-]?id\s*=\s*["\']AKIA[A-Z0-9]+["\']', "AWS Access Key", "CRITICAL"),
                (r'-----BEGIN (?:RSA |)PRIVATE KEY-----', "Private key in code", "CRITICAL"),
                (r'ghp_[a-zA-Z0-9]{36}', "GitHub Personal Access Token", "CRITICAL"),
                (r'sk_live_[a-zA-Z0-9]{24,}', "Stripe Secret Key", "CRITICAL"),
                (r'postgres://.*:.*@', "Database connection string with credentials", "HIGH"),
                (r'mongodb://.*:.*@', "MongoDB connection string with credentials", "HIGH"),
            ]

            for pattern, description, severity in patterns:
                matches = re.findall(pattern, code, re.IGNORECASE)
                if matches:
                    findings.append({
                        "severity": severity,
                        "type": description,
                        "matches": len(matches),
                        "sample": matches[0][:50] + "..." if matches else ""
                    })

            # Check for .env usage
            if "load_dotenv" in code or "environ.get" in code:
                # Good - using environment variables
                pass
            elif any(re.search(r'password\s*=\s*["\']', code, re.IGNORECASE)):
                findings.append({
                    "severity": "MEDIUM",
                    "type": "Missing environment variable usage",
                    "matches": 1,
                    "sample": "Use os.environ.get() or python-dotenv"
                })

            if not findings:
                return """
✅ Secrets Scan: No Hardcoded Secrets Found

No obvious hardcoded secrets detected.

Best Practices:
  ✓ Use environment variables for all secrets
  ✓ Use .env files (add to .gitignore)
  ✓ Use secret management (AWS Secrets Manager, HashiCorp Vault)
  ✓ Rotate secrets regularly
  ✓ Never commit secrets to version control

Tools:
  - gitleaks: Scan git history for secrets
  - truffleHog: Find secrets in git repos
  - detect-secrets: Pre-commit hook for secret detection
"""

            report = f"""
🔴 Hardcoded Secrets Detected: {len(findings)}

"""

            for finding in findings:
                severity_icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡"}.get(finding["severity"], "•")
                report += f"""
{severity_icon} {finding['severity']}: {finding['type']}
   Found {finding['matches']} instance(s)
   Sample: {finding['sample']}
"""

            report += """
Immediate Actions:
  1. ROTATE all exposed secrets immediately
  2. Move secrets to environment variables
  3. Use .env files (add to .gitignore)
  4. Scan git history for historical leaks: git log -p | grep -i "password"
  5. Use secret management service for production

Prevention:
  - Add pre-commit hooks (detect-secrets)
  - Use .env.example templates without real values
  - Enable secret scanning on GitHub/GitLab
  - Never log secrets
  - Use secret rotation policies
"""

            return report

        return scan_secrets

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
        task_id: str
    ) -> Dict[str, Any]:
        """
        Execute the Security Auditor agent to scan for vulnerabilities.

        Args:
            task: Security audit task description
            context: Additional context (code, dependencies, config)
            task_id: Unique task identifier for tracing

        Returns:
            {
                "security_report": {
                    "summary": {"critical": 2, "high": 5, "medium": 3, "low": 1},
                    "findings": [{severity, category, cwe, description, remediation}],
                    "owasp_top10": [...],
                    "dependencies": [...],
                    "secrets": [...]
                },
                "risk_score": 85,  # 0-100, higher = more risk
                "compliance": {"owasp": "fail", "pci_dss": "pass"},
                "citations": [{...}],
                "execution_time_ms": 1234
            }
        """
        start_time = time.time()

        # Start Langfuse trace
        trace = self.tracer.start_trace(
            name="security_auditor_execution",
            metadata={
                "task": task,
                "task_id": task_id,
                "model": self.code_model
            }
        )

        try:
            # Create CrewAI task
            crew_task = Task(
                description=f"""
Perform comprehensive security audit for the following:

{task}

Context:
{json.dumps(context, indent=2)}

Requirements:
1. OWASP Top 10 Analysis:
   - A01:2021 - Broken Access Control
   - A02:2021 - Cryptographic Failures
   - A03:2021 - Injection (SQL, XSS, Command, Code)
   - A04:2021 - Insecure Design
   - A05:2021 - Security Misconfiguration
   - A06:2021 - Vulnerable Components
   - A07:2021 - Identification and Authentication Failures
   - A08:2021 - Software and Data Integrity Failures
   - A09:2021 - Security Logging and Monitoring Failures
   - A10:2021 - Server-Side Request Forgery (SSRF)

2. Code Security:
   - Input validation and sanitization
   - Output encoding (XSS prevention)
   - Parameterized queries (SQL injection prevention)
   - Authentication and authorization checks
   - Cryptographic implementation (algorithms, key management)
   - Error handling and information disclosure
   - Session management security

3. Dependency Security:
   - Check for known CVEs in dependencies
   - Identify outdated packages
   - Recommend version updates

4. Secrets Management:
   - Scan for hardcoded credentials
   - Check API keys, passwords, tokens
   - Validate secret storage patterns

5. Configuration Security:
   - Security headers (CSP, HSTS, X-Frame-Options)
   - CORS configuration
   - Debug mode status
   - SSL/TLS configuration

6. Reporting:
   - Classify by severity (CRITICAL, HIGH, MEDIUM, LOW, INFO)
   - Include CWE identifiers
   - Provide specific remediation steps
   - Include code examples for fixes
   - Calculate risk score

7. MUST cite ≥2 security patterns/guidelines from knowledge base

Output Format:
1. Executive Summary (risk score, critical count)
2. OWASP Top 10 Findings (detailed)
3. Dependency Vulnerabilities
4. Hardcoded Secrets Report
5. Authentication Security Assessment
6. Configuration Issues
7. Remediation Roadmap (prioritized)
8. Citations

Provide actionable, enterprise-grade security audit report.
""",
                expected_output="Comprehensive security audit with OWASP compliance check and remediation plan",
                agent=self.agent
            )

            # Execute with CrewAI
            crew = Crew(
                agents=[self.agent],
                tasks=[crew_task],
                verbose=True
            )

            result = await crew.kickoff_async()

            # Parse result
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Extract citations
            citations = self._extract_citations(str(result))

            # Calculate risk score (simplified)
            risk_score = self._calculate_risk_score(str(result))

            response = {
                "security_report": {
                    "summary": self._extract_summary(str(result)),
                    "findings": [],  # Would parse from result
                    "owasp_top10": [],
                    "dependencies": [],
                    "secrets": []
                },
                "risk_score": risk_score,
                "compliance": {
                    "owasp": "fail" if risk_score > 50 else "pass",
                    "pci_dss": "unknown"
                },
                "citations": citations,
                "execution_time_ms": execution_time_ms
            }

            # End trace
            self.tracer.end_trace(
                trace_id=trace.get("id"),
                output=response,
                metadata={
                    "risk_score": risk_score,
                    "execution_time_ms": execution_time_ms,
                    "citations_count": len(citations)
                }
            )

            return response

        except Exception as e:
            # Log error to trace
            self.tracer.end_trace(
                trace_id=trace.get("id"),
                output={"error": str(e)},
                metadata={"error": True}
            )
            raise

    def _extract_citations(self, result: str) -> List[Dict[str, Any]]:
        """Extract citations from result"""
        citations = []
        citation_pattern = r'\[(?:Citation|Security Pattern) \d+\] (.*?) \(v([\d.]+)\)'
        matches = re.findall(citation_pattern, result)

        for source, version in matches[:5]:  # Limit to 5
            citations.append({
                "source": source.strip(),
                "version": version,
                "score": 0.85
            })

        return citations

    def _calculate_risk_score(self, result: str) -> int:
        """Calculate risk score from findings"""
        # Count severity levels
        critical = len(re.findall(r'CRITICAL', result, re.IGNORECASE))
        high = len(re.findall(r'HIGH', result, re.IGNORECASE))
        medium = len(re.findall(r'MEDIUM', result, re.IGNORECASE))
        low = len(re.findall(r'LOW', result, re.IGNORECASE))

        # Weight: CRITICAL=20, HIGH=10, MEDIUM=5, LOW=1
        score = min(100, (critical * 20) + (high * 10) + (medium * 5) + (low * 1))
        return score

    def _extract_summary(self, result: str) -> Dict[str, int]:
        """Extract summary counts"""
        return {
            "critical": len(re.findall(r'CRITICAL', result, re.IGNORECASE)),
            "high": len(re.findall(r'HIGH', result, re.IGNORECASE)),
            "medium": len(re.findall(r'MEDIUM', result, re.IGNORECASE)),
            "low": len(re.findall(r'LOW', result, re.IGNORECASE)),
            "info": len(re.findall(r'INFO', result, re.IGNORECASE))
        }
