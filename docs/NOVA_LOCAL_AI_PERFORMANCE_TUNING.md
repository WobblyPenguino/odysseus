# Nova Local AI Performance Tuning

This document implements the safe parts of the uploaded performance research PDF.

## Commands

- `/perf-status` - inspect local AI runtime status, env flags and GPU tool availability.
- `/perf-tune-plan` - show the staged improvement plan and rollback notes.
- `/perf-benchmark` - show benchmark metrics and commands.
- `/perf-benchmark --write-scripts` - write `scripts/nova_perf_collect.ps1` and `scripts/nova_perf_probe.py`.
- `/perf-artifact-checklist` - show exactly what to upload for further tuning.

## What Nova sets automatically

Nova sets these only when the user has not already set them:

- `OLLAMA_FLASH_ATTENTION=1`
- `TOKENIZERS_PARALLELISM=false`
- `CUDA_LAUNCH_BLOCKING=0`
- `OMP_NUM_THREADS=<sensible default>`

## What Nova does not do automatically

- Windows Defender exclusions.
- Driver installation or rollback.
- Admin/elevated large-page configuration.
- Moving model files.
- Downloading or replacing models.

Those are manual because they affect security or system configuration.
