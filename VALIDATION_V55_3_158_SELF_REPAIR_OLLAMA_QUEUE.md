# Nova v55.3.158 Self-Repair and Ollama Queue Validation

Changes:
- Adds bounded mistake-learning/self-repair guardian.
- Records failed tool results into local mistake memory.
- Adds /mistake-learning, /self-repair-status, /self-repair-permission, /self-repair-validate and /self-repair-now.
- Queues same-model Ollama calls instead of returning None or sending overlapping prompts.
- Keeps multi-agent deterministic work parallel while model calls are serialized through the model lane.

Validation commands:

```powershell
python -m compileall -q app.py winlocalassistant
python tests_smoke.py
python -m pytest -q tests_nova_self_repair_ollama_queue_v55_3_158.py tests_nova_research_voice_v55_3_157.py tests_nova_autonomous_continuous_v55_3_156.py tests_release_hygiene.py
python -m winlocalassistant.validate --all
python app.py /version
```
