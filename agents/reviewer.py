import logging
from dataclasses import dataclass

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a senior software engineer performing a code review.
Focus on:
1. Code quality & readability
2. Naming conventions and consistency
3. Error handling and edge cases
4. Performance concerns
5. Best practices and design patterns
6. DRY / SOLID violations
7. Potential bugs or logic errors

Provide a structured review with sections: **Summary**, **Issues** (numbered list with severity: LOW/MEDIUM/HIGH), and **Suggestions**.
Be concise and actionable.
"""


@dataclass
class ReviewResult:
    review_text: str
    error: str | None = None


class CodeReviewerAgent:
    """LLM-based agent that reviews code for quality and best practices."""

    def __init__(self, model: str = "claude-sonnet-4-5", temperature: float = 0.2) -> None:
        self._model = model
        self._temperature = temperature
        logger.info("CodeReviewerAgent initialised (model=%s)", model)

    def _build_llm(self) -> ChatAnthropic:
        return ChatAnthropic(model=self._model, temperature=self._temperature)

    def run(self, code: str) -> ReviewResult:
        logger.info("CodeReviewerAgent: starting review (%d chars)", len(code))
        try:
            llm = self._build_llm()
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"Review the following code:\n\n```\n{code}\n```"),
            ]
            response = llm.invoke(messages)
            result = ReviewResult(review_text=response.content)
            logger.info("CodeReviewerAgent: review complete (%d chars output)", len(result.review_text))
            return result
        except Exception as exc:
            logger.exception("CodeReviewerAgent: LLM call failed")
            return ReviewResult(
                review_text="",
                error=f"Code review failed: {exc}",
            )
