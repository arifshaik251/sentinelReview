import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.guardrail import GuardrailAgent, GuardrailResult


class TestGuardrailSecretDetection:
    def setup_method(self):
        self.agent = GuardrailAgent()

    def test_detects_aws_access_key(self):
        code = 'aws_key = "AKIAIOSFODNN7EXAMPLE"'
        result = self.agent.run(code)
        assert not result.passed
        assert len(result.secrets_found) >= 1
        names = [s["pattern_name"] for s in result.secrets_found]
        assert any("AWS" in n for n in names)

    def test_detects_aws_secret_key(self):
        code = 'aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"'
        result = self.agent.run(code)
        assert not result.passed
        assert any("AWS Secret" in s["pattern_name"] or "Generic" in s["pattern_name"] for s in result.secrets_found)

    def test_detects_generic_api_key(self):
        code = 'api_key = "sk-abc123def456ghi789jkl012"'
        result = self.agent.run(code)
        assert not result.passed
        names = [s["pattern_name"] for s in result.secrets_found]
        assert any("API Key" in n or "Generic" in n for n in names)

    def test_detects_private_key_block(self):
        code = "-----BEGIN RSA PRIVATE KEY-----\nMIIE...stuff..."
        result = self.agent.run(code)
        assert not result.passed
        names = [s["pattern_name"] for s in result.secrets_found]
        assert any("Private Key" in n for n in names)

    def test_detects_github_token(self):
        code = 'token = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklm"'
        result = self.agent.run(code)
        assert not result.passed
        names = [s["pattern_name"] for s in result.secrets_found]
        assert any("GitHub" in n or "Generic" in n for n in names)

    def test_detects_connection_string(self):
        code = 'db_url = "postgres://admin:p4ssword@db.host.com:5432/mydb"'
        result = self.agent.run(code)
        assert not result.passed
        names = [s["pattern_name"] for s in result.secrets_found]
        assert any("Connection" in n for n in names)

    def test_detects_bearer_token(self):
        code = 'headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc"}'
        result = self.agent.run(code)
        assert not result.passed

    def test_clean_code_passes(self):
        code = """
import os

def greet(name: str) -> str:
    return f"Hello, {name}!"

DB_HOST = os.environ.get("DB_HOST", "localhost")
"""
        result = self.agent.run(code)
        assert result.passed
        assert len(result.secrets_found) == 0

    def test_env_var_reference_passes(self):
        code = 'api_key = os.environ["API_KEY"]'
        result = self.agent.run(code)
        assert result.passed

    def test_empty_code_passes(self):
        result = self.agent.run("")
        assert result.passed
        assert len(result.secrets_found) == 0

    def test_summary_format_with_secrets(self):
        code = 'API_KEY = "AKIAIOSFODNN7EXAMPLE"'
        result = self.agent.run(code)
        assert "⚠️" in result.summary
        assert "secret" in result.summary.lower()

    def test_summary_format_clean(self):
        code = "x = 1 + 2"
        result = self.agent.run(code)
        assert "✅" in result.summary

    def test_multiple_secrets_on_different_lines(self):
        code = (
            'API_KEY = "AKIAIOSFODNN7EXAMPLE"\n'
            'SECRET = "super_duper_secret_value_12345"\n'
        )
        result = self.agent.run(code)
        assert not result.passed
        assert len(result.secrets_found) >= 2

    def test_safety_prompt_is_generated(self):
        code = "print('hello')"
        result = self.agent.run(code)
        assert result.safety_prompt
        assert "hello" in result.safety_prompt

    def test_result_dataclass_fields(self):
        result = self.agent.run("x = 1")
        assert isinstance(result, GuardrailResult)
        assert isinstance(result.passed, bool)
        assert isinstance(result.secrets_found, list)
        assert isinstance(result.safety_prompt, str)
        assert isinstance(result.summary, str)

    def test_masked_preview_doesnt_leak_full_secret(self):
        code = 'password = "ThisIsAVeryLongPasswordThatShouldBeMasked"'
        result = self.agent.run(code)
        if result.secrets_found:
            for s in result.secrets_found:
                assert "****" in s["matched_preview"]
                assert len(s["matched_preview"]) < 40
