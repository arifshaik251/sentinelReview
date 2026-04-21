# SentinelReview — Multi-Agent Code Review & Security Audit
**Project Report | Junior FDE Pre-screening Assignment**

## 1. Multi-Agent Architecture
SentinelReview uses a **hierarchical and parallel orchestration pattern** to ensure both depth of analysis and efficiency.
- **The Orchestrator:** Acts as the central brain, managing state and routing data between specialized agents.
- **Guardrail Agent (Sequential):** The first line of defense. It performs deterministic checks (regex-based secret scanning) and LLM-based safety intent analysis before allowing further processing.
- **Code Reviewer Agent (Parallel):** Focuses on "clean code" principles, PEP 8/standards, and logical efficiency.
- **Security Auditor Agent (Parallel):** Specialized in identifying OWASP Top 10 vulnerabilities (Injection, Broken Access Control, etc.).
- **Synthesizer Agent:** Merges the findings from the Reviewer and Auditor into a unified, developer-friendly report.

**Justification:** By separating security from quality, we allow each agent to have a focused "system prompt," reducing hallucinations and increasing technical depth.

## 2. Security, Safety, and Guardrails
- **Input Validation:** The Guardrail agent flags hardcoded AWS keys, private keys, and high-entropy strings before they are sent to the LLM.
- **Prompt Injection Protection:** The system uses typed Python `dataclass` result objects (`GuardrailResult`, `ReviewResult`, `AuditResult`, `SynthesisResult`) combined with section-locked system prompts (Summary / Issues / Remediation). Downstream agents consume only named fields, so an attacker cannot break the pipeline by injecting instructions into the LLM output.
- **Data Privacy:** Local PII/Secret scanning happens *before* any data is sent to external AI providers (Anthropic).

## 3. Implementation Approach
- **Frameworks:** Python, Streamlit (UI), LangChain/LangGraph (Orchestration).
- **Coordination:** The Orchestrator uses a `ThreadPoolExecutor` to run the Reviewer and Auditor in parallel, significantly reducing total latency.
- **Error Handling:** Implemented retry logic for LLM API calls and graceful fallbacks if an agent fails to return valid JSON.

## 4. Use of AI / LLMs and Collaboration
- **Reasoning:** Anthropic **Claude 3.5 Sonnet** is used for the complex reasoning required to understand multi-file logic and security context. Claude's stronger adherence to structured system prompts reduces prompt-injection surface and yields more consistent section-based outputs.
- **Collaboration:** The Synthesizer acts as a "critic" that resolves conflicting feedback (e.g., if the Reviewer suggests a change that the Auditor flags as risky).
- **Trade-off:** We chose a **Controlled Autonomy** model where the Orchestrator maintains strict control over the execution flow, ensuring the system remains predictable and safe for production environments.
