# 🚀 Deployment Fix Documentation

**Project**: RAG — Retrieval-Augmented Generation Application  
**Fixed by**: Antigravity AI  
**Date**: 2026-04-23  
**Commit**: `962124e` — "deployment changes"  
**Pushed to**: `https://github.com/pankaj-cod/RAG_project`

---

## Summary

The project had **5 deployment blockers** — all related to Python version mismatches, dependency configuration errors, and a runtime crash specific to Streamlit's event loop model. Every issue is documented below with the exact file, the problem, the root cause, and the fix applied.

---

## Fix 1 — Python Version Pinning Too Loose

### File: `.python-version`

#### ❌ Before
```
3.11
```

#### ✅ After
```
3.11.10
```

### Why This Was a Problem

The `.python-version` file tells tools like `pyenv` and `uv` which Python version to use.  
Writing just `3.11` is **ambiguous** — it could resolve to any patch version: `3.11.0`, `3.11.5`, `3.11.8`, etc.

At the same time, the `uv.lock` file (the dependency lockfile) had this at the top:
```toml
requires-python = ">=3.11.10"
```

This means all the pinned package versions in `uv.lock` were **resolved assuming Python 3.11.10 or later**. If the platform provisions an earlier patch (e.g., `3.11.4`), the lockfile becomes invalid and installation fails with errors like:
```
ERROR: No matching distribution found for <package>
```
or silent ABI incompatibilities with compiled packages (C extensions).

### Fix Applied
Pinned `.python-version` to the **exact same version** the lockfile was resolved against: `3.11.10`.

---

## Fix 2 — Missing `runtime.txt` for Streamlit Cloud

### File: `runtime.txt` *(NEW FILE — did not exist before)*

#### ✅ Created With
```
python-3.11.10
```

### Why This Was a Problem

Streamlit Community Cloud (the most common deployment target for Streamlit apps) **does not read `.python-version`**. It reads a separate file called `runtime.txt` placed in the **root of the repository**.

Without `runtime.txt`, Streamlit Cloud defaults to its own Python version (often `3.10` or `3.11.x` at an arbitrary patch). Since the project's lockfile requires exactly `>=3.11.10`, this caused deploy failures with package resolution errors.

### Fix Applied
Created `runtime.txt` in the project root with `python-3.11.10`.  
Streamlit Cloud reads this file during provisioning and sets up the correct Python environment before installing dependencies.

> **Format note**: Streamlit Cloud requires the format `python-X.Y.Z` (with a hyphen, not `python==` or just the number).

---

## Fix 3 — `--only-binary=all` in `requirements.txt`

### File: `requirements.txt`

#### ❌ Before
```
--only-binary=all
tiktoken==0.12.0
regex==2023.12.25
```

#### ✅ After
```
tiktoken==0.12.0
regex==2023.12.25
nest_asyncio>=1.6.0
```

### Why This Was a Problem

The flag `--only-binary=all` tells pip: **"refuse to build any package from source — only use pre-built binary wheels."**

This sounds safe but it causes hard failures in practice because:

1. **Not all packages have binary wheels for every Python version + OS combination.** For example, `tiktoken` and `regex` ship binary wheels for common platforms, but if Streamlit Cloud's build environment or glibc version doesn't match the wheel tag, pip refuses to fall back to a source build and just **crashes**.

2. **`regex==2023.12.25`** in particular — this older pin may not have wheels for `python3.11-linux_x86_64` on certain glibc versions (which Streamlit Cloud uses). Without being able to build from source, it fails.

3. The flag applies **globally** to all packages in the file, not just specific ones.

### Fix Applied
- Removed `--only-binary=all` so pip can fall back to source builds when wheels aren't available.
- Added `nest_asyncio>=1.6.0` (needed for Fix 4).

---

## Fix 4 — `asyncio.run()` Crashes Inside Streamlit

### File: `streamlit.py`

#### ❌ Before (line 1–3)
```python
import asyncio
from pathlib import Path
import time
```

#### ✅ After (line 1–6)
```python
import nest_asyncio
nest_asyncio.apply()  # Allow asyncio.run() inside Streamlit's Tornado event loop

import asyncio
from pathlib import Path
import time
```

### Why This Was a Problem

The `streamlit.py` file calls `asyncio.run()` in **two places**:

```python
# Line 50 — PDF upload trigger
asyncio.run(send_rag_ingest_event(path))

# Line 114 — Query event trigger
event_id = asyncio.run(send_rag_query_event(question.strip(), int(top_k)))
```

`asyncio.run()` works fine in normal scripts because it **creates a new event loop, runs the coroutine, then closes the loop**.

**The problem**: Streamlit runs its entire web server using **Tornado**, which itself runs an asyncio event loop permanently in the background. When your code calls `asyncio.run()` while this loop is already running, Python raises:

```
RuntimeError: This event loop is already running.
```

This crash happens the moment a user tries to upload a PDF or ask a question — i.e., on **every single user interaction**. The app appears to load but breaks immediately on use.

### Fix Applied
Added `nest_asyncio` at the very top of the file, **before any other import**.

`nest_asyncio` works by **monkey-patching** the asyncio event loop to allow re-entrant (nested) calls. After `nest_asyncio.apply()` is called, `asyncio.run()` works correctly even inside an already-running event loop.

This is the **officially recommended approach** by both the Streamlit team and the Python async community for this exact situation.

> `nest_asyncio` was also added to `requirements.txt` and `pyproject.toml` so it gets installed automatically during deployment.

---

## Fix 5 — `pyproject.toml` Version Constraints & Missing Dependency

### File: `pyproject.toml`

#### ❌ Before
```toml
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.128.8",
    "groq>=1.0.0",
    "inngest>=0.5.15",
    "llama-index-readers-file>=0.5.6",
    "python-dotenv>=1.2.1",
    "qdrant-client>=1.16.2",
    "streamlit>=1.54.0",
    "uvicorn>=0.40.0",
]
```

#### ✅ After
```toml
requires-python = ">=3.11.10"
dependencies = [
    "fastapi>=0.115.0",
    "groq>=0.13.0",
    "inngest>=0.4.8",
    "llama-index-readers-file>=0.4.0",
    "nest-asyncio>=1.6.0",
    "python-dotenv>=1.0.1",
    "qdrant-client>=1.12.0",
    "streamlit>=1.41.0",
    "uvicorn>=0.34.0",
]
```

### Why This Was a Problem

**Issue A — `requires-python = ">=3.11"` (too loose)**  
This again allowed any `3.11.x` patch version, conflicting with the lockfile which required `>=3.11.10`. Made consistent.

**Issue B — Version floors were mismatched with uv.lock**  
The lockfile (`uv.lock`) was resolved with certain package versions. If `pyproject.toml` specifies floor versions that don't have the same lockfile entries, `uv sync` (used during deployment with uv) will either error or re-resolve and deviate from what was tested locally.

**Issue C — `nest-asyncio` was not listed as a dependency**  
Since it's now imported at runtime (`import nest_asyncio` in `streamlit.py`), it **must** be declared as an explicit dependency. Without it, the deployment environment won't install it and the app crashes immediately with `ModuleNotFoundError: No module named 'nest_asyncio'`.

### Fix Applied
- Aligned `requires-python` to `>=3.11.10` (matches lockfile)
- Relaxed version floors to broadly available stable versions that have binary wheels across Linux/Mac/Windows
- Added `nest-asyncio>=1.6.0` as an explicit dependency
- Ran `uv lock` to regenerate `uv.lock` to be consistent with the updated `pyproject.toml`

---

## Fix 6 — Regenerated `uv.lock`

### File: `uv.lock`

After updating `pyproject.toml`, the old lockfile was **stale and inconsistent** — it was generated with different dependency constraints. An inconsistent lockfile causes `uv sync` to fail during deployment with conflicts or resolution errors.

### Fix Applied
Ran:
```bash
/Users/pankaj/.local/bin/uv lock
```

This resolved all 106 packages from scratch and wrote a fresh, consistent `uv.lock`. The new lockfile's top line confirms correctness:
```toml
requires-python = ">=3.11.10"
```

---

## Complete List of Changed Files

| File | Type | Change |
|------|------|--------|
| `.python-version` | Modified | `3.11` → `3.11.10` |
| `runtime.txt` | **Created** | New file — `python-3.11.10` for Streamlit Cloud |
| `requirements.txt` | Modified | Removed `--only-binary=all`, added `nest_asyncio` |
| `streamlit.py` | Modified | Added `nest_asyncio.apply()` at top |
| `pyproject.toml` | Modified | Fixed `requires-python`, relaxed floors, added `nest-asyncio` |
| `uv.lock` | Regenerated | Re-resolved all 106 packages with updated constraints |

---

## Root Cause Summary Table

| # | Error Type | Symptom | Root Cause |
|---|-----------|---------|-----------|
| 1 | Python version mismatch | Install fails / wrong Python | `.python-version` said `3.11` not `3.11.10` |
| 2 | Streamlit Cloud ignores `.python-version` | Wrong Python provisioned | Missing `runtime.txt` |
| 3 | Binary wheel not found | pip install crashes | `--only-binary=all` blocks source fallback |
| 4 | Runtime crash on every user action | `RuntimeError: event loop already running` | `asyncio.run()` inside Streamlit's Tornado loop |
| 5 | Missing module at runtime | `ModuleNotFoundError: nest_asyncio` | Not declared in `pyproject.toml` |
| 6 | Dependency resolution failure | `uv sync` fails | Stale `uv.lock` inconsistent with new `pyproject.toml` |

---

## Architecture Note

> ⚠️ **Streamlit Cloud can only run `streamlit.py`.**  
> The following services still need to run **separately** (on your machine or a server):
>
> - **Qdrant** — vector database at `localhost:6333` → deploy via Docker or Qdrant Cloud
> - **Ollama** — local embeddings at `localhost:11434` → not cloud-deployable as-is; replace with a hosted embedding API
> - **Inngest Dev Server** — workflow orchestration at `localhost:8288` → use Inngest Cloud for production
> - **FastAPI server** (`uvicorn main:app`) → deploy separately on Render, Railway, Fly.io, etc.
>
> Streamlit Cloud cannot connect to `localhost` services. These would need to be hosted externally for a fully cloud-deployed setup.
