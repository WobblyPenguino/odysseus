# Nova v55.3.164 SubQ / NVIDIA / local runtime integration

This note converts the uploaded SubQ and local-runtime PDFs into Nova-local-assistant implementation work. References to "Nova" in the PDFs were treated as design targets for this local assistant only; any unrelated product named Nova was ignored.

## Integrated decisions

- **Adapter-first provider layer:** SubQ, NVIDIA NIM, OpenRouter, vLLM, SGLang, llama.cpp and local Gemma-style servers are model-provider lanes, not random one-off call sites.
- **Local-first default:** Ollama remains the default private provider. Remote lanes require explicit `/allow-internet on` and environment API keys.
- **Remote long-context boundary:** SubQ is represented as an optional remote long-context coprocessor for huge repositories, large documents and months-long state, not as a local Ollama replacement.
- **NVIDIA local lane:** vLLM and SGLang are modeled as advanced local OpenAI-compatible servers for stronger NVIDIA systems. TensorRT-LLM/Triton remain scale-up guidance, not default desktop dependencies.
- **Provider queue receipts:** New commands expose provider/model queue state and dry-run validation commands.
- **Official/open models only:** Nova does not help obtain cracked/jailbroken model variants. Local Gemma-style integration is for official/open checkpoints served by legitimate runtimes.

## New commands

- `/provider-status` - shows local/default, advanced local, and remote provider lanes.
- `/provider-route GOAL` - explains which provider lane Nova would choose and why.
- `/provider-test [PROVIDER]` - prints a dry-run validation command for Ollama, SubQ, NVIDIA NIM, vLLM, SGLang, llama.cpp or local Gemma.
- `/queue-status` - shows provider/model queue receipts.
- `/queue-drain` - explains safe cancellation/drain behavior.

## Environment variables

- `SUBQ_API_KEY` for SubQ remote long-context calls.
- `NVIDIA_NIM_API_KEY` for NVIDIA NIM OpenAI-compatible calls.
- `OPENROUTER_API_KEY` for OpenRouter.

Remote providers are only active when `/allow-internet on` is set. Keys stay server-side and are not put into browser JavaScript or downloadable config.

## Manual validation commands

```powershell
python -m compileall -q app.py winlocalassistant
python -m pytest -q tests_nova_provider_runtime_v55_3_163.py tests_nova_efficiency_focus_v55_3_162.py tests_release_hygiene.py
python -m winlocalassistant.validate --all
python app.py /version
```

Inside Nova:

```text
/provider-status
/provider-route review this entire repo and months of history
/provider-test ollama
/provider-test subq
/provider-test nvidia-nim
/queue-status
```
