# Nova LLM-from-scratch inspired training lab

This patch adapts the useful *ideas* from public LLM-from-scratch projects into Nova without copying their code or adding expensive training as a hidden background feature.

## What Nova adds

- `/llm-lab plan GOAL` — safe roadmap for a tiny educational model, SFT experiment, or evaluation route.
- `/llm-lab dataset PATH` — local text dataset inspection: text-file count, bytes, approximate tokens, duplicate-line signal and warnings.
- `/llm-lab estimate PARAMS TOKENS` — rough training-step and VRAM estimate, for example `/llm-lab estimate 13m 5m`.
- `python -m winlocalassistant.llm_training_lab --root . --plan` — CLI report that writes `docs/NOVA_LLM_TRAINING_LAB_LATEST.md/json`.
- Release-readiness now includes a required LLM training lab smoke contract.

## Why it is intentionally not a full trainer

From-scratch training can be expensive, slow and easy to misuse. Nova should not silently download datasets, start multi-hour GPU jobs, or train on private files. This lab focuses on planning, inspection, estimation and routing decisions. Actual training should happen in a separate experiment folder with explicit commands and saved evidence.

## Safe workflow

1. Start with a tiny local dataset that you are allowed to use.
2. Run `/llm-lab dataset PATH`.
3. Run `/llm-lab estimate 13m 5m` before trying anything larger.
4. Use a tiny smoke model to prove dataloader, checkpoint, resume, logging and generation.
5. Prefer SFT or role-specific fine-tuning for usefulness; treat from-scratch models as educational until evaluation proves otherwise.
6. Route any trained model into Nova only after `/model-calibration --bench` and `/release-readiness --full` pass.

## Guardrails

- Do not train on secrets, passwords, API keys, private chats or files you do not have rights to use.
- Do not run training inside the Nova source folder.
- Do not replace Nova's working chat/code models unless benchmarks prove the new model is reliable.
- Keep deterministic fallback enabled.
