# Nova Local Autonomy Research Latest

Goal:
Make Nova more like a local coding agent that can continue improving itself safely until stopped, without relying only on manually prewritten task candidates.

Key design lessons:
- Use isolated source+test tasks, not broad open-ended edits.
- Generate tasks from evidence: roadmap, task summaries, failures, audits, research notes, validation reports.
- Prefer one small reversible patch per cycle.
- Use protected-file rules and required changed-file contracts.
- Run targeted tests, baseline tests, validation, diff review, generated-noise cleanup, and clean-git checks before commit.
- Stop on task-pool exhaustion, repeated failures, dirty git, protected-file edits, test failure, low-significance patch, no-change patch, or broad risky edits.
- Keep all autonomous work local-first and bounded.
- Never install external tools or connect to browser/remote systems without explicit approval.

Next implementation direction:
1. Add a pure autonomous candidate factory.
2. Feed it local evidence.
3. Have it generate JSON candidate drafts.
4. Validate generated candidates using existing candidate validators.
5. Only then wire it into the task loop as the fallback when the pool is exhausted.

Important:
This is not yet unrestricted overnight autonomy. It is a safer task-generation layer that makes the loop less dependent on manual seed tasks.
