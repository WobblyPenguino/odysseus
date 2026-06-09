# PDF Review Implementation Notes

Reviewed:

- `docs/NOVA_PROPOSED_CHANGES_AND_VALIDATION_V55_3_41.pdf`
- `docs/NOVA_v55_3_39_proposed_changes_and_validation_plan.pdf`

Implemented from the review:

- Bare `python -m pytest ...` verification now works by allowing explicit dev-test dependency installation and installing the declared pytest dependency.
- PDF ingestion now uses `pypdf` directly, so future Nova document ingestion can read these PDFs instead of falling back to raw PDF bytes.
- Image setup guidance is now a dedicated `/image-setup-wizard` path with make/edit test commands, SD WebUI/Diffusers setup, ComfyUI status caveat, and honest draft-vs-real-generation boundaries.
- Image command routing now has regression coverage for real `/image-generate` and `/image-edit` success responses.

Already present in the current codebase:

- Defensive-only security status/triage boundaries.
- Optional Playwright release-gate behavior when dependencies and a running Nova server are available.
- Project-target clarification for vague or ambiguous creation/edit requests.
- Manifest-first video planning and local proof preview artifacts.
