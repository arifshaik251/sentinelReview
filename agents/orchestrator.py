import logging
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field

from agents.guardrail import GuardrailAgent, GuardrailResult
from agents.reviewer import CodeReviewerAgent, ReviewResult
from agents.auditor import SecurityAuditorAgent, AuditResult
from agents.synthesizer import SynthesizerAgent, SynthesisResult

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    guardrail: GuardrailResult | None = None
    review: ReviewResult | None = None
    audit: AuditResult | None = None
    synthesis: SynthesisResult | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


class Orchestrator:
    """Manages the multi-agent review pipeline.

    Flow:
        1. GuardrailAgent — regex secret scan + safety prompt
        2. CodeReviewerAgent + SecurityAuditorAgent — run in parallel
        3. SynthesizerAgent — merge all results into a unified report
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-5",
        parallel: bool = True,
    ) -> None:
        self._guardrail = GuardrailAgent()
        self._reviewer = CodeReviewerAgent(model=model)
        self._auditor = SecurityAuditorAgent(model=model)
        self._synthesizer = SynthesizerAgent(model=model)
        self._parallel = parallel
        logger.info(
            "Orchestrator initialised (model=%s, parallel=%s)", model, parallel
        )

    def run(self, code: str) -> PipelineResult:
        result = PipelineResult()

        # --- Step 1: Guardrail ---
        logger.info("Orchestrator: step 1 — guardrail pre-screening")
        guardrail_result = self._guardrail.run(code)
        result.guardrail = guardrail_result

        # --- Step 2: Reviewer + Auditor (parallel or sequential) ---
        logger.info("Orchestrator: step 2 — code review & security audit (parallel=%s)", self._parallel)
        if self._parallel:
            review_result, audit_result = self._run_parallel(code)
        else:
            review_result, audit_result = self._run_sequential(code)

        result.review = review_result
        result.audit = audit_result

        if review_result.error:
            result.errors.append(review_result.error)
        if audit_result.error:
            result.errors.append(audit_result.error)

        # --- Step 3: Synthesis ---
        logger.info("Orchestrator: step 3 — synthesis")
        review_text = review_result.review_text if not review_result.error else f"[Error] {review_result.error}"
        audit_text = audit_result.audit_text if not audit_result.error else f"[Error] {audit_result.error}"

        synthesis_result = self._synthesizer.run(
            guardrail_summary=guardrail_result.summary,
            review_text=review_text,
            audit_text=audit_text,
        )
        result.synthesis = synthesis_result

        if synthesis_result.error:
            result.errors.append(synthesis_result.error)

        logger.info("Orchestrator: pipeline complete (errors=%d)", len(result.errors))
        return result

    def _run_parallel(self, code: str) -> tuple:
        with ThreadPoolExecutor(max_workers=2) as pool:
            review_future: Future = pool.submit(self._reviewer.run, code)
            audit_future: Future = pool.submit(self._auditor.run, code)
            review_result = review_future.result()
            audit_result = audit_future.result()
        return review_result, audit_result

    def _run_sequential(self, code: str) -> tuple:
        review_result = self._reviewer.run(code)
        audit_result = self._auditor.run(code)
        return review_result, audit_result
