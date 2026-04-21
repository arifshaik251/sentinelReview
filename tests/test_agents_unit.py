"""Unit tests for reviewer, auditor, and synthesizer with mocked LLMs."""
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.reviewer import CodeReviewerAgent, ReviewResult
from agents.auditor import SecurityAuditorAgent, AuditResult
from agents.synthesizer import SynthesizerAgent, SynthesisResult


class TestCodeReviewerAgent:
    @patch.object(CodeReviewerAgent, "_build_llm")
    def test_run_success(self, mock_build):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="Looks good. No issues found.")
        mock_build.return_value = mock_llm

        agent = CodeReviewerAgent()
        result = agent.run("def hello(): pass")
        assert isinstance(result, ReviewResult)
        assert result.review_text == "Looks good. No issues found."
        assert result.error is None

    @patch.object(CodeReviewerAgent, "_build_llm")
    def test_run_llm_exception(self, mock_build):
        mock_build.side_effect = RuntimeError("API down")

        agent = CodeReviewerAgent()
        result = agent.run("def hello(): pass")
        assert result.error is not None
        assert "API down" in result.error
        assert result.review_text == ""


class TestSecurityAuditorAgent:
    @patch.object(SecurityAuditorAgent, "_build_llm")
    def test_run_success(self, mock_build):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="SQL injection found on line 5.")
        mock_build.return_value = mock_llm

        agent = SecurityAuditorAgent()
        result = agent.run("cursor.execute(f'SELECT * FROM users WHERE id={uid}')")
        assert isinstance(result, AuditResult)
        assert "SQL injection" in result.audit_text
        assert result.error is None

    @patch.object(SecurityAuditorAgent, "_build_llm")
    def test_run_llm_exception(self, mock_build):
        mock_build.side_effect = ValueError("Invalid key")

        agent = SecurityAuditorAgent()
        result = agent.run("code")
        assert result.error is not None
        assert "Invalid key" in result.error


class TestSynthesizerAgent:
    @patch.object(SynthesizerAgent, "_build_llm")
    def test_run_success(self, mock_build):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="Overall: MEDIUM risk. Fix SQL injection first.")
        mock_build.return_value = mock_llm

        agent = SynthesizerAgent()
        result = agent.run(
            guardrail_summary="No secrets found.",
            review_text="Code quality is acceptable.",
            audit_text="SQL injection on line 5.",
        )
        assert isinstance(result, SynthesisResult)
        assert "MEDIUM" in result.report
        assert result.error is None

    @patch.object(SynthesizerAgent, "_build_llm")
    def test_run_llm_exception(self, mock_build):
        mock_build.side_effect = ConnectionError("timeout")

        agent = SynthesizerAgent()
        result = agent.run(
            guardrail_summary="clean",
            review_text="ok",
            audit_text="ok",
        )
        assert result.error is not None
        assert "timeout" in result.error
