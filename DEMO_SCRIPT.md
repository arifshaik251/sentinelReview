# 🎤 3-Minute Demo Script — SentinelReview

Use this for your in-person presentation (Wipro Plano) or a recorded Loom
walkthrough. Timings are approximate; practise once out loud.

---

## ⏱️ 0:00 – 0:25 — Hook & problem statement
> "Code review and security audit are two jobs usually done by two different
> people with two different mindsets. Our assignment: build a multi-agent
> system that does both — safely and in parallel.
>
> I built **SentinelReview** — a hierarchical multi-agent pipeline that
> takes any code snippet and returns a single prioritised risk report in
> about 10 seconds."

👉 Show the Streamlit home screen.

---

## ⏱️ 0:25 – 0:55 — Architecture in one breath
> "Five specialised agents. The **Orchestrator** is the brain. First, the
> **Guardrail** runs a pure-regex secret scan locally — so API keys or
> private keys *never leave the machine*. Then the **Code Reviewer** and
> **Security Auditor** run **in parallel** via a thread pool, each with its
> own focused system prompt — one for quality, one for OWASP Top-10.
> Finally the **Synthesizer** de-duplicates and prioritises everything into
> a unified report."

👉 Show the Mermaid diagram in README.md or your architecture slide.

Key talking point:
- **"Why separate the reviewer from the auditor?"** → focused prompts =
  fewer hallucinations, deeper technical findings, and easier to evolve
  (swap models per agent if needed).

---

## ⏱️ 0:55 – 2:00 — Live demo (the juicy part)

1. **Paste "clean" code first** (see SAMPLE_PROMPTS.md → Input D).
   > "No secrets. No critical findings. Overall risk LOW. Good — the
   > system doesn't cry wolf."

2. **Paste the triple-threat snippet** (Input A).
   > "Notice the Guardrail tab flags the AWS key *before* anything hits
   > Anthropic — the key is masked in logs."

3. **Click through tabs** → Unified Report → Guardrail → Code Review →
   Security Audit.
   > "The Auditor correctly identifies SQL injection and command injection
   > under OWASP A03. The Reviewer catches separate quality issues.
   > The Synthesizer merges both into a single **CRITICAL** action plan."

4. **Toggle the `Run in parallel` checkbox off** and re-run.
   > "Sequential mode — notice roughly 2× the wall-clock time. Small tweak,
   > measurable improvement."

---

## ⏱️ 2:00 – 2:35 — Security & guardrails
> "Three layers of defence:
> 1. **Local-first secret scanning** — regex runs *before* any LLM call.
> 2. **Structured dataclass outputs** — downstream agents consume typed
>    fields, not free-form LLM text, limiting prompt-injection surface.
> 3. **Error isolation** — an agent failure is captured in
>    `PipelineResult.errors`; the pipeline never crashes end-to-end.
>
> Data handling: Anthropic API key is pulled from `ANTHROPIC_API_KEY`, never
> committed. `.gitignore` blocks `.env`. Nothing is logged to disk."

---

## ⏱️ 2:35 – 2:55 — Trade-offs & what's next
> "I chose **controlled autonomy** over fully autonomous agents — the
> Orchestrator holds the state machine, so behaviour is predictable and
> testable. Thirty-five unit and integration tests pass on every push.
>
> Next iterations: Tree-sitter-based per-language static analysis before
> the LLM, per-agent model selection (e.g. Claude Opus for Auditor, Claude Haiku
> for Reviewer), and a diff-mode that reviews only changed lines in a PR."

---

## ⏱️ 2:55 – 3:00 — Close
> "Live demo URL is in the README. Repo link is in my email reply.
> Happy to dive into any agent's internals. Thank you!"

---

## 🧯 Backup answers if they ask…

**Q: Why not LangGraph / CrewAI / AutoGen?**
> I started with a custom orchestrator to keep control over the state
> machine explicit — it's ~100 lines and fully typed. LangGraph would be my
> next step once I add conditional branching (e.g. skip Auditor on pure
> config files).

**Q: How would you prevent an attacker from injecting instructions in
the code itself?**
> Two ways already in place: (1) the code is always wrapped in a fenced
> block in the user message, and (2) agent outputs are parsed as structured
> sections. A third defence I'd add: an "instruction detection" pre-filter
> in the Guardrail that flags code containing natural-language imperatives
> targeting the model.

**Q: Cost?**
> ~1–2 k tokens per run on Claude 3.5 Sonnet ≈ $0.01 per review. Parallelism
> doesn't increase cost, only reduces latency.

**Q: Can it scale to a whole repo?**
> Today it's single-snippet. Scaling path: chunk by file, a Planner agent
> picks top-N risky files first (based on Guardrail hits + size + recency),
> then fan-out to Reviewer/Auditor per chunk, and the Synthesizer runs at
> the repo level.

**Q: How do you test agents that call an LLM?**
> `tests/test_agents_unit.py` mocks `_build_llm()` via `unittest.mock.patch`
> so we can assert success *and* exception paths without spending tokens.
> The Orchestrator tests swap the three LLM agents with lambdas and verify
> pipeline wiring only.
