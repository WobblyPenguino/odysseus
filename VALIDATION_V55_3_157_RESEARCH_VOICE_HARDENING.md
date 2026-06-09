# Nova v55.3.159 validation

## Purpose
This patch hardens the v55.3.156 package using the v55.3.155 runtime logs supplied by the user.

## Fixed
- Plain-English research/search requests now route to Nova's research tool path instead of normal chat saying it has no internet.
- Added `/internet-search`, `/search-web`, and `/web-search` for obvious search discovery.
- Added seeded public source discovery for World War II and Neil the Seal/Tasmanian seal topics so research has useful source candidates even when generic search fails.
- Interactive-run boilerplate is stripped from game/theme analysis so a dog game stays a dog game rather than becoming `Dogsuserclarificationgame`.
- `/compare` now aliases to Nova's compare surface.
- Voice output now uses complete contextual spoken sentences and avoids cutting off halfway through a thought.
- Specialist fallback answers for `/science` and `/code` are more useful when the local chat model times out.

## Validation run

```powershell
python -m compileall -q app.py winlocalassistant
python tests_smoke.py
python -m pytest -q tests_nova_research_voice_v55_3_157.py tests_nova_release_sync_v55_3_154.py tests_release_hygiene.py tests_nova_autonomous_continuous_v55_3_156.py tests_nova_media_and_gui_v55_3_156.py tests_nova_high_spec_subagents_v55_3_156.py
python -m winlocalassistant.validate --all
python app.py /version
```

## Result
- Focused regression tests: PASS.
- Smoke tests: PASS.
- Layered validation: PASS.
- CLI version: Nova 55.3.159.
