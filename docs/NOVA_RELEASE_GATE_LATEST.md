# Nova Release Gate

OK: **True**
Summary: Nova release gate passed

## Doctor
- OK: **True**
- Summary: Nova doctor passed critical checks

## Commands
- `compileall`: passed
- `custom_tests`: passed
- `playwright_smoke`: passed

## Recommendations
- Run /nova-doctor before packaging every release.
- Run /release-gate before sharing a zip.
- For code-changing patches, run /docker-validate-patch and only promote hash-locked passing reports.
- If Docker is available, also run /docker-validate quick after /release-gate.
- If Nova is running in the browser and Playwright is installed, /release-gate now runs the GUI smoke test automatically.