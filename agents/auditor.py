import logging
from dataclasses import dataclass

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a senior application security engineer conducting a security audit.
Analyse the code for OWASP Top 10 vulnerabilities and other security issues.
Focus on:
1. **Injection** (SQL, NoSQL, OS command, LDAP)
2. **Broken Authentication** (weak credentials, session issues)
3. **Sensitive Data Exposure** (logging secrets, plaintext storage)
4. **XML External Entities (XXE)**
5. **Broken Access Control**
6. **Security Misconfiguration**
7. **Cross-Site Scripting (XSS)**
8. **Insecure Deserialization**
9. **Using Components with Known Vulnerabilities**
10. **Insufficient Logging & Monitoring**

Also check for:
- Path traversal
- Race conditions
- Unsafe use of eval/exec
- Insecure randomness

Provide a structured report with sections: **Summary**, **Findings** (numbered list with severity: LOW/MEDIUM/HIGH/CRITICAL and the OWASP category), and **Remediation Steps**.
Be concise and actionable.
"""


@dataclass
class AuditResult:
    audit_text: str
    error: str | None = None


class SecurityAuditorAgent:
    """LLM-based agent that audits code for OWASP security vulnerabilities."""

    def __init__(self, model: str = "claude-sonnet-4-5", temperature: float = 0.1) -> None:
        self._model = model
        self._temperature = temperature
        logger.info("SecurityAuditorAgent initialised (model=%s)", model)

    def _build_llm(self) -> ChatAnthropic:
        return ChatAnthropic(model=self._model, temperature=self._temperature)

    def run(self, code: str) -> AuditResult:
        logger.info("SecurityAuditorAgent: starting audit (%d chars)", len(code))
        try:
            llm = self._build_llm()
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"Audit the following code for security vulnerabilities:\n\n```\n{code}\n```"),
            ]
            response = llm.invoke(messages)
            result = AuditResult(audit_text=response.content)
            logger.info("SecurityAuditorAgent: audit complete (%d chars output)", len(result.audit_text))
            return result
        except Exception as exc:
            logger.exception("SecurityAuditorAgent: LLM call failed")
            return AuditResult(
                audit_text="",
                error=f"Security audit failed: {exc}",
            )
