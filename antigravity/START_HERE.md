# Start Here — Antigravity

1. Open the **actual existing project folder** containing `ai_detector_bypass.py`, `web_ui.py`, `requirements.txt`, `run.sh`, and README.
2. Read this whole upgrade pack, beginning with `MASTER_IMPLEMENTATION_PROMPT.md`.
3. Before edits: inspect files, run existing app/tests, record baseline, and create a git branch or checkpoint.
4. Do not replace the project wholesale. Implement in phases, keep the CLI and web app functional, and adapt architecture to the current repo.
5. Use environment variables for provider credentials. Never hard-code keys or commit `.env` files.
6. If no API key is configured, the application must still run in a clear local/demo mode with deterministic basic editing tools; it must not silently pretend an LLM was used.
7. Complete tests and provide a final report: files changed, features, tests run/results, setup instructions, env vars, known limitations, and next recommended phase.
