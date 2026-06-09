# Nova v55.3.162 research notes

Applied research-backed priorities:

- Ollama API supports `stream:false`, `keep_alive`, JSON/structured outputs and final timing fields; Nova should continue serialising same-model calls and recording throughput.
- Local inference stacks such as llama.cpp highlight quantization, partial offload, KV-cache behaviour and speculative decoding as efficiency levers; Nova should keep model profiles explicit and export future runtime profiles.
- Playwright visual comparison/screenshot workflows are appropriate for catching GUI regressions that unit tests miss.
- OpenTelemetry-style tracing supports replacing silent exception swallowing with structured observability that mistake-learning/self-repair can consume.

Implemented in this patch: /nova-efficiency-audit, focus-workspace GUI, validation markers, and docs output.
