# Nova Verified Self-Change Flow

Nova can now apply selected low-risk self-changes through a deterministic gate instead of pretending a simulated patch was applied.

## Flow

1. `plan` lists available change sets and their exact file targets.
2. `preview` shows the unified diff before mutation.
3. `apply --confirm` writes the change only after path allow-list checks.
4. Nova creates backups under `.nova_backups/verified_changes/`.
5. Nova runs validation commands.
6. If validation fails, Nova restores the backup or removes newly created files.
7. A JSON receipt is written under `docs/NOVA_VERIFIED_CHANGE_RECEIPT_LATEST.json`.

## Safety rules

- No absolute paths.
- No path traversal.
- No writes to `.git`, runtime data, logs, uploads, generated artefacts, virtual environments, build folders or dependency folders.
- Only safe text/code suffixes are allowed.
- Current built-in changes are low-risk documentation/report changes.
- Future code-writing changes should be added as explicit named change sets with tests attached.
