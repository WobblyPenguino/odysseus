# Nova Model Calibration

Status: **READY**
Summary: Ollama and GPU tooling are visible; use benchmark rows to tune chat/code/autonomous timeouts.
Root: `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530`

## Host probes
- **PASS** `ollama_list`: `ollama list` (0.031s)
  - `NAME                       ID              SIZE      MODIFIED   `
  - `gemma3:12b                 f4031aab637d    8.1 GB    3 days ago    `
  - `nomic-embed-text:latest    0a109f422b47    274 MB    3 days ago    `
- **PASS** `ollama_ps`: `ollama ps` (0.016s)
  - `NAME    ID    SIZE    PROCESSOR    CONTEXT    UNTIL`
- **PASS** `nvidia_smi`: `nvidia-smi` (0.047s)
  - `-----+------------------------+----------------------+`
  - `| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |`
  - `| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |`

## Chat benchmark evidence
- Live benchmark rows were not run during release-readiness. Run `python -m winlocalassistant.model_calibration --root . --bench` on the Windows Nova PC for real timings.

## Recommended local tuning flow
- `ollama list`
- `ollama ps`
- `nvidia-smi`
- `python -m winlocalassistant.model_calibration --root . --bench`
- `python -m winlocalassistant.release_readiness --root . --full`
