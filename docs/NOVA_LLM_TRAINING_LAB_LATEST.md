# Nova LLM Training Lab

Purpose: Nova-safe planning, dataset inspection and training-budget estimates for educational LLM experiments.
Created: `2026-06-09 23:43:01`
Root: `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530`

## Inspired by
- rasbt/LLMs-from-scratch: educational GPT-like model pipeline
- FareedKhan-dev/train-llm-from-scratch: end-to-end data-to-generation and post-training stages
- karpathy/llm.c: small reproducible training/debugging emphasis

## Training plan
Goal: training budget estimate
- **1. Data** — Collect a small legal/local text dataset, inspect size, duplicates and format. Nova check: `/llm-lab dataset PATH`
- **2. Tokenizer** — Start with an existing tokenizer or tiny educational BPE experiment before any expensive run. Nova check: `confirm vocab size and sample encoding/decoding`
- **3. Architecture** — Use a tiny GPT-style config first, then scale only after loss curves and generation smoke tests behave. Nova check: `/llm-lab estimate 13m 5m`
- **4. Pretraining smoke** — Train on a tiny slice only to prove dataloader, checkpoints, resume, logging and generation work. Nova check: `save loss, sample output and checkpoint hash`
- **5. Finetuning** — Prefer SFT or task-specific finetuning for usefulness; avoid expensive from-scratch unless educational. Nova check: `hold out eval prompts and regression tests`
- **6. Evaluation** — Run deterministic prompt tests, safety checks, hallucination checks and code/file task checks before routing into Nova. Nova check: `/model-calibration --bench and Nova eval packs`
- **7. Routing** — Use the trained model only for roles it passes; keep fallback to the proven chat/code model. Nova check: `/llm-status and /release-readiness --full`

## Guardrails
- Do not train on private chats, secrets, API keys, passwords or copyrighted dumps you do not have rights to use.
- Do not let training scripts overwrite Nova source or release files; run in a separate experiments folder.
- Keep the first run tiny and checkpointed; expensive runs need explicit confirmation and host evidence.
- Treat from-scratch models as educational unless evaluation proves they beat your existing Ollama models for a specific Nova role.

## Rough budget estimate
- Parameters: `13.00M`
- Tokens: `5.00M`
- Estimated steps: `1221`
- Rough training VRAM: `2.9 GB`
- Recommendation: Feasible for an educational tiny/small from-scratch run on a 16GB GPU if code is efficient and batch size is small.

## Commands
- `/llm-lab plan learn tiny GPT training`
- `/llm-lab dataset data/my_texts`
- `/llm-lab estimate 13m 5m`
- `python -m winlocalassistant.llm_training_lab --root . --plan`
- `python -m winlocalassistant.release_readiness --root . --full`
