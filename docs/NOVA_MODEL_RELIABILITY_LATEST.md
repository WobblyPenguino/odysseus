# Local Model Reliability

Overall: **DEGRADED/ATTENTION**
Recent attempts: 2
Recent rejections: 2
Recent failures: 9

## Recommendations
- Stop repeating the same prompt after two rejections; switch to prompt-contract + candidate tournament or deterministic template fallback.
- Use /model-output-coach and /model-fallback-strategy before another local model retry.