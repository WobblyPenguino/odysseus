# Nova v55.3.153 Integration Review Upgrade

This patch extends Nova's repo-integration foundation with testable planning layers inspired by the 6 June 2026 integration blueprint:

- repo intelligence / RepoMap for coding work
- patch plans with validation commands before edits
- browser-worker dry-run plans with read-only defaults and approval gates
- document ingestion/chunking/search with local MarkItDown compatibility when installed
- local model role registry that prevents embedding/vision models from being selected for chat/code
- comprehensive integration review command and validation sections

The code stays adapter-first: it does not copy external repo code or run risky browser/system actions.
