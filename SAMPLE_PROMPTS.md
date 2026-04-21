# 📝 Sample Prompts & Test Inputs

This appendix shows **exactly** what each agent receives and the kinds of code
snippets that best demonstrate the pipeline during a live demo. Use any of
the *Demo Inputs* below by pasting them into the Streamlit text area.

---

## 1. System prompts used by each LLM agent

### 1a. Code Reviewer Agent (`agents/reviewer.py`)
```
You are a senior software engineer performing a code review.
Focus on:
1. Code quality & readability
2. Naming conventions and consistency
3. Error handling and edge cases
4. Performance concerns
5. Best practices and design patterns
6. DRY / SOLID violations
7. Potential bugs or logic errors

Provide a structured review with sections:
**Summary**, **Issues** (numbered list with severity: LOW/MEDIUM/HIGH),
and **Suggestions**. Be concise and actionable.
```

### 1b. Security Auditor Agent (`agents/auditor.py`)
```
You are a senior application security engineer conducting a security audit.
Analyse the code for OWASP Top 10 vulnerabilities and other security issues.
Focus on:
1. Injection (SQL, NoSQL, OS command, LDAP)
2. Broken Authentication
3. Sensitive Data Exposure
4. XML External Entities (XXE)
5. Broken Access Control
6. Security Misconfiguration
7. Cross-Site Scripting (XSS)
8. Insecure Deserialization
9. Using Components with Known Vulnerabilities
10. Insufficient Logging & Monitoring

Also check for: path traversal, race conditions, unsafe eval/exec,
insecure randomness.

Provide a structured report with sections: **Summary**, **Findings**
(numbered list with severity LOW/MEDIUM/HIGH/CRITICAL and OWASP category),
and **Remediation Steps**. Be concise and actionable.
```

### 1c. Synthesizer Agent (`agents/synthesizer.py`)
```
You are a technical lead synthesizing results from multiple automated
code analysis agents. You will receive:
1. A guardrail pre-screening result (secret detection)
2. A code quality review
3. A security audit

Your job is to produce a single, unified report that:
- Starts with an Overall Risk Rating (LOW / MEDIUM / HIGH / CRITICAL)
- Highlights the most important findings across all agents
- De-duplicates overlapping issues
- Prioritises items by severity
- Ends with a concise Action Plan (numbered steps in order of priority)

Keep the final report clear, well-structured, and under 500 words.
```

### 1d. Guardrail Agent (no LLM — pure regex)
Detects and masks these secret types **before any data leaves the machine**:

| Pattern | Example matched |
|---|---|
| AWS Access Key | `AKIAIOSFODNN7EXAMPLE` |
| AWS Secret Key | `aws_secret_access_key = "wJalrXUtnFEMI/..."` |
| Generic API Key | `api_key = "sk-abc123..."` |
| Private Key Block | `-----BEGIN RSA PRIVATE KEY-----` |
| GitHub Token | `ghp_ABCDEFGHIJKL...` |
| Env-style Secret | `SECRET = "super_duper_secret"` |
| Hex secret (32+) | `key = "a1b2c3...32hex..."` |
| Bearer token literal | `"Bearer eyJhbGciOi..."` |
| DB connection string | `postgres://user:pass@host/db` |

---

## 2. Demo inputs — copy any of these into the UI

### 🔴 Demo Input A — "The Triple Threat" (best 1-minute demo)
Triggers **all three** agents: guardrail catches a secret, reviewer catches
style issues, auditor catches SQL injection + command injection.

```python
import os, sqlite3

DB_PASSWORD = "super_secret_123"
API_KEY = "AKIAIOSFODNN7EXAMPLE"

def get_user(username):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE name = '{username}'"
    cursor.execute(query)
    return cursor.fetchone()

def run_command(user_input):
    os.system(f"echo {user_input}")
```
**Expected outcome:**
Overall Risk → **CRITICAL**
Guardrail → 2 secrets masked (AWS key + hardcoded password)
Auditor → SQL injection (A03) + OS command injection (A03) + hardcoded creds (A07)
Reviewer → missing type hints, no connection close, no docstrings

---

### 🟡 Demo Input B — Deserialization + weak crypto
```python
import pickle, hashlib

def load_session(blob: bytes):
    return pickle.loads(blob)   # insecure deserialization

def hash_password(pwd: str) -> str:
    return hashlib.md5(pwd.encode()).hexdigest()  # weak hash
```
**Expected outcome:** HIGH risk — A08 Insecure Deserialization + A02 Cryptographic Failure.

---

### 🟡 Demo Input C — Path traversal + XSS
```python
from flask import Flask, request, send_file
app = Flask(__name__)

@app.route("/download")
def download():
    filename = request.args.get("file")
    return send_file(f"/var/data/{filename}")   # path traversal

@app.route("/greet")
def greet():
    name = request.args.get("name")
    return f"<h1>Hello {name}</h1>"             # reflected XSS
```
**Expected outcome:** HIGH risk — path traversal + A03 XSS.

---

### 🟢 Demo Input D — Clean code (shows the "pass" path)
```python
import os
from hashlib import sha256

def hash_password(pwd: str, salt: bytes) -> str:
    """Return a salted SHA-256 hash of the password."""
    return sha256(salt + pwd.encode("utf-8")).hexdigest()

DB_HOST = os.environ.get("DB_HOST", "localhost")
```
**Expected outcome:** Guardrail ✅ clean • Reviewer: LOW minor suggestions
• Auditor: no critical findings • Overall Risk → **LOW**.

---

## 3. Tips for a strong live demo
1. Start with **Input D** (clean code) to show "no false positives".
2. Switch to **Input A** to show the *CRITICAL* path end-to-end.
3. Open the **Guardrail tab** first — explain *"secrets never left the machine"*.
4. Toggle **parallel=OFF** once to show ~2× latency gain.
5. End on the **Unified Report tab** — point out the prioritised Action Plan.
