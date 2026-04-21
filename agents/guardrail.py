import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

SECRET_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("AWS Access Key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("AWS Secret Key", re.compile(r"""(?:aws_secret_access_key|secret_key)\s*[=:]\s*['"]?[A-Za-z0-9/+=]{40}['"]?""", re.IGNORECASE)),
    ("Generic API Key assignment", re.compile(r"""(?:api_key|apikey|api_secret|secret|token|password|passwd|pwd)\s*[=:]\s*['"][A-Za-z0-9_\-/.+=]{8,}['"]""", re.IGNORECASE)),
    ("Private Key Block", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
    ("GitHub Token", re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}")),
    ("Generic Secret in Env Style", re.compile(r"""(?:SECRET|TOKEN|PASSWORD|PASSWD|API_KEY)\s*=\s*['"][A-Za-z0-9_/+=.\-]{8,}['"]""", re.IGNORECASE)),
    ("Hex-encoded secret (32+ chars)", re.compile(r"""(?:key|secret|token)\s*[=:]\s*['"]?[0-9a-fA-F]{32,}['"]?""", re.IGNORECASE)),
    ("Bearer token literal", re.compile(r"""['"]Bearer\s+[A-Za-z0-9\-._~+/]+=*['"]""")),
    ("Connection string with password", re.compile(r"""(?:mysql|postgres|postgresql|mongodb|redis|amqp):\/\/[^:]+:[^@]+@""")),
]


@dataclass
class GuardrailResult:
    passed: bool
    secrets_found: list[dict] = field(default_factory=list)
    safety_prompt: str = ""
    summary: str = ""


class GuardrailAgent:
    """Pre-screening agent: checks for hardcoded secrets and builds a
    safety-check prompt for the LLM pipeline."""

    def __init__(self) -> None:
        logger.info("GuardrailAgent initialised")

    def _scan_secrets(self, code: str) -> list[dict]:
        findings: list[dict] = []
        for line_no, line in enumerate(code.splitlines(), start=1):
            for name, pattern in SECRET_PATTERNS:
                for match in pattern.finditer(line):
                    masked = match.group()[:6] + "****"
                    findings.append({
                        "pattern_name": name,
                        "line": line_no,
                        "matched_preview": masked,
                    })
                    logger.warning("Secret detected: %s on line %d", name, line_no)
        return findings

    @staticmethod
    def build_safety_prompt(code: str) -> str:
        return (
            "You are a code-safety pre-screening assistant. "
            "Evaluate the following code snippet for any obvious red flags "
            "such as obfuscated payloads, eval/exec misuse, shell injection vectors, "
            "or attempts to exfiltrate data. Respond with SAFE or UNSAFE and a one-line reason.\n\n"
            f"```\n{code}\n```"
        )

    def run(self, code: str) -> GuardrailResult:
        logger.info("GuardrailAgent: starting scan (%d chars)", len(code))
        secrets = self._scan_secrets(code)
        safety_prompt = self.build_safety_prompt(code)

        passed = len(secrets) == 0
        summary_parts: list[str] = []
        if secrets:
            summary_parts.append(f"⚠️  Found {len(secrets)} potential hardcoded secret(s).")
            for s in secrets:
                summary_parts.append(
                    f"  - [{s['pattern_name']}] line {s['line']}: {s['matched_preview']}"
                )
        else:
            summary_parts.append("✅ No hardcoded secrets detected.")

        result = GuardrailResult(
            passed=passed,
            secrets_found=secrets,
            safety_prompt=safety_prompt,
            summary="\n".join(summary_parts),
        )
        logger.info("GuardrailAgent: done — passed=%s, secrets=%d", passed, len(secrets))
        return result
