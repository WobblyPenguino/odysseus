NOVA v55.3.168 - START HERE

1. Extract the zip.
2. Double-click START_NOVA_HERE.bat.
3. Wait while Nova creates/uses .venv, loads the better model environment, runs validation, and opens the web UI.

Optional setup-only check:
  SETUP_NOVA_FIRST.bat

PowerShell direct:
  Set-ExecutionPolicy -Scope Process RemoteSigned
  .\start_nova_best_models.ps1 -Setup -Mode web

Better-PC local model profile:
  Main/code/chat/planner: qwen3-coder:30b
  Fast: gemma2:2b
  Vision: llama3.2-vision:11b
  Embeddings: nomic-embed-text:latest

Validation command:
  python -m winlocalassistant.validate --all

Startup hardening in v55.3.168:
  - Repairs incomplete .venv folders.
  - Prevents your browser from connecting to an older Nova server on port 8766.
  - Opens the calmer clean GUI with the current version badge visible.
