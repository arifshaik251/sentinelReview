import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.orchestrator import Orchestrator, PipelineResult
from agents.guardrail import GuardrailResult
from agents.reviewer import ReviewResult, CodeReviewerAgent
from agents.auditor import AuditResult, SecurityAuditorAgent
from agents.synthesizer import SynthesisResult, SynthesizerAgent


CLEAN_CODE = """
def add(a, b):
    return a + b
"""

SECRET_CODE = """
API_KEY = "AKIAIOSFODNN7EXAMPLE"
def get_data():
    pass
"""


def _mock_reviewer_run(code):
    return ReviewResult(review_text="Mock review: code looks fine.")


def _mock_auditor_run(code):
    return AuditResult(audit_text="Mock audit: no critical issues.")


def _mock_synthesizer_run(guardrail_summary, review_text, audit_text):
    return SynthesisResult(report="Mock synthesis: overall LOW risk.")


class TestOrchestrator:
    def _make_orchestrator(self, parallel=True):
        orch = Orchestrator(model="claude-sonnet-4-5", parallel=parallel)
        orch._reviewer.run = _mock_reviewer_run
        orch._auditor.run = _mock_auditor_run
        orch._synthesizer.run = _mock_synthesizer_run
        return orch

    def test_pipeline_clean_code(self):
        orch = self._make_orchestrator()
        result = orch.run(CLEAN_CODE)
        assert isinstance(result, PipelineResult)
        assert result.guardrail.passed
        assert result.review.review_text == "Mock review: code looks fine."
        assert result.audit.audit_text == "Mock audit: no critical issues."
        assert result.synthesis.report == "Mock synthesis: overall LOW risk."
        assert not result.has_errors

    def test_pipeline_with_secrets(self):
        orch = self._make_orchestrator()
        result = orch.run(SECRET_CODE)
        assert not result.guardrail.passed
        assert len(result.guardrail.secrets_found) >= 1
        assert result.synthesis is not None

    def test_pipeline_sequential_mode(self):
        orch = self._make_orchestrator(parallel=False)
        result = orch.run(CLEAN_CODE)
        assert result.review.review_text == "Mock review: code looks fine."
        assert not result.has_errors

    def test_pipeline_parallel_mode(self):
        orch = self._make_orchestrator(parallel=True)
        result = orch.run(CLEAN_CODE)
        assert result.review is not None
        assert result.audit is not None

    def test_reviewer_error_propagated(self):
        orch = self._make_orchestrator()
        orch._reviewer.run = lambda code: ReviewResult(review_text="", error="LLM timeout")
        result = orch.run(CLEAN_CODE)
        assert result.has_errors
        assert any("LLM timeout" in e for e in result.errors)

    def test_auditor_error_propagated(self):
        orch = self._make_orchestrator()
        orch._auditor.run = lambda code: AuditResult(audit_text="", error="Rate limited")
        result = orch.run(CLEAN_CODE)
        assert result.has_errors
        assert any("Rate limited" in e for e in result.errors)

    def test_synthesis_error_propagated(self):
        orch = self._make_orchestrator()
        orch._synthesizer.run = lambda **kw: SynthesisResult(report="", error="Synthesis failed")
        result = orch.run(CLEAN_CODE)
        assert result.has_errors

    def test_pipeline_result_has_all_fields(self):
        orch = self._make_orchestrator()
        result = orch.run(CLEAN_CODE)
        assert result.guardrail is not None
        assert result.review is not None
        assert result.audit is not None
        assert result.synthesis is not None

    def test_empty_code(self):
        orch = self._make_orchestrator()
        result = orch.run("")
        assert result.guardrail.passed
        assert result.synthesis is not None


class TestPipelineResult:
    def test_has_errors_true(self):
        pr = PipelineResult(errors=["something broke"])
        assert pr.has_errors

    def test_has_errors_false(self):
        pr = PipelineResult()
        assert not pr.has_errors
