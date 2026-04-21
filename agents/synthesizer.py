import logging
from dataclasses import dataclass

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a technical lead synthesizing results from multiple automated code analysis agents.
You will receive:
1. A guardrail pre-screening result (secret detection)
2. A code quality review
3. A security audit

Your job is to produce a single, unified report that:
- Starts with an **Overall Risk Rating** (LOW / MEDIUM / HIGH / CRITICAL)
- Highlights the most important findings across all agents
- De-duplicates overlapping issues
- Prioritises items by severity
- Ends with a concise **Action Plan** (numbered steps in order of priority)

Keep the final report clear, well-structured, and under 500 words.
"""


@dataclass
class SynthesisResult:
    report: str
    error: str | None = None


class SynthesizerAgent:
    """Merges outputs from guardrail, reviewer, and auditor into one report."""

    def __init__(self, model: str = "claude-sonnet-4-5", temperature: float = 0.2) -> None:
        self._model = model
        self._temperature = temperature
        logger.info("SynthesizerAgent initialised (model=%s)", model)

    def _build_llm(self) -> ChatAnthropic:
        return ChatAnthropic(model=self._model, temperature=self._temperature)

    def run(
        self,
        guardrail_summary: str,
        review_text: str,
        audit_text: str,
    ) -> SynthesisResult:
        logger.info("SynthesizerAgent: synthesizing reports")
        combined = (
            "## Guardrail Pre-Screening\n"
            f"{guardrail_summary}\n\n"
            "## Code Quality Review\n"
            f"{review_text}\n\n"
            "## Security Audit\n"
            f"{audit_text}\n"
        )
        try:
            llm = self._build_llm()
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"Synthesize the following agent reports into a single unified report:\n\n{combined}"),
            ]
            response = llm.invoke(messages)
            result = SynthesisResult(report=response.content)
            logger.info("SynthesizerAgent: synthesis complete (%d chars)", len(result.report))
            return result
        except Exception as exc:
            logger.exception("SynthesizerAgent: LLM call failed")
            return SynthesisResult(
                report="",
                error=f"Synthesis failed: {exc}",
            )
