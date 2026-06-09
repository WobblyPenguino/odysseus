# Nova Build Quality Report

Overall: **ATTENTION**
Score: **62.5%**
Root: `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530`
Goal: notes app

## Checks
- ❌ **has_entrypoint** — Project has index.html or another obvious entrypoint.
- ❌ **html_links_js** — HTML should reference app.js for browser apps.
- ❌ **button_handler_wiring** — Inline handlers and common button IDs should exist in JS.
- ✅ **localstorage_when_requested** — localStorage is implemented when requested.
- ✅ **json_export_when_requested** — JSON export uses JSON.stringify plus Blob/download evidence when requested.
- ✅ **readme_claims_true** — README claims should have matching implementation evidence.
- ✅ **no_unrelated_dodge_default** — Reject unrelated Dodge Game/default-game leakage.
- ✅ **manual_test_clarity** — README/TEST_REPORT explain how to run or verify.

## Recommendations
- Fix has_entrypoint: Project has index.html or another obvious entrypoint.
- Fix html_links_js: HTML should reference app.js for browser apps.
- Fix button_handler_wiring: Inline handlers and common button IDs should exist in JS.