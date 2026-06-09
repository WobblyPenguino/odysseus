# Nova Improvement Proposals

Generated: 2026-06-07 00:19:50
Focus: make improvements to NOVA

## Available agent tools
[
  {
    "name": "status",
    "purpose": "show assistant status and workspace"
  },
  {
    "name": "list_files",
    "purpose": "list files under the current project"
  },
  {
    "name": "tree",
    "purpose": "show a project tree"
  },
  {
    "name": "read_file",
    "purpose": "read a project file"
  },
  {
    "name": "search_text",
    "purpose": "search text in project files"
  },
  {
    "name": "detect_project",
    "purpose": "detect project type"
  },
  {
    "name": "auto_verify",
    "purpose": "run an inferred verification command"
  },
  {
    "name": "verify",
    "purpose": "run a specific safe verification command"
  },
  {
    "name": "run_project",
    "purpose": "prepare/run current project preview"
  },
  {
    "name": "surgical_repair",
    "purpose": "apply targeted deterministic repairs to small errors"
  },
  {
    "name": "final_project_check",
    "purpose": "final requirement and syntax check"
  },
  {
    "name": "tool_create",
    "purpose": "create a safe custom helper tool if useful"
  },
  {
    "name": "tool_run",
    "purpose": "run a named custom tool"
  },
  {
    "name": "tool_help",
    "purpose": "inspect custom tool inputs and examples"
  },
  {
    "name": "tool_pipeline",
    "purpose": "run bounded safe sequential tool calls"
  },
  {
    "name": "safe_script_demo",
    "purpose": "return real deterministic local demo output"
  },
  {
    "name": "idle_lessons",
    "purpose": "read prior idle lessons from the assistant profile"
  },
  {
    "name": "topic_watchers",
    "purpose": "list saved internet topic watchers"
  },
  {
    "name": "topic_check",
    "purpose": "check a saved topic watcher when internet is enabled"
  },
  {
    "name": "tool_view",
    "purpose": "inspect custom tool source and metadata before using it"
  },
  {
    "name": "tool_use_guide",
    "purpose": "show the recommended tool sequence for building, testing and repairing"
  },
  {
    "name": "investigate_logs",
    "purpose": "read recent errors and write ERROR_INVESTIGATION.md"
  },
  {
    "name": "propose_improvements",
    "purpose": "propose safe changes to assistant/tool/project code from logs"
  },
  {
    "name": "write_file",
    "purpose": "write one file when a precise repair is needed"
  },
  {
    "name": "find_replace",
    "purpose": "make an exact targeted replacement"
  },
  {
    "name": "custom:project_health_snapshot",
    "purpose": "Summarises the current project structure and highlights simple test/UI coverage warnings",
    "risk": "read_only",
    "input_schema": {
      "subdir": "folder under workspace"
    }
  }
]

## Installed custom tools
[
  {
    "name": "project_health_snapshot",
    "description": "Summarises the current project structure and highlights simple test/UI coverage warnings",
    "input_schema": {
      "subdir": "folder under workspace"
    },
    "section": "Project Analysis",
    "risk": "read_only",
    "enabled": true,
    "created_at": "2026-06-06 03:38:58",
    "last_tested": "2026-06-06 03:38:58",
    "last_used": "2026-06-06 03:38:58",
    "created_by": "local_llm_or_fallback",
    "last_test_ok": true,
    "last_test_summary": "Project health snapshot: 1 files, 0 Python, 0 JS, 1 HTML, 0 tests.",
    "exists": true,
    "path": "C:\\Users\\Daniel\\.nova\\custom_tools\\project_health_snapshot.py"
  }
]

## Proposed changes
1. Target: `winlocalassistant/ollama.py`
   - Change: Improve prompt timeout/quarantine messaging and avoid recovery when no project files were written.
   - Command: `/llm-status`
   - Command: `/ollama-stop --confirm`
2. Target: `winlocalassistant/tools.py acceptance checks`
   - Change: Improve goal term extraction and ask clarifying questions when static acceptance is uncertain.
   - Command: `/interactive GOAL`
   - Command: `/reply ANSWER`
3. Target: `custom_tools`
   - Change: Add or repair small read-only analysis tools, then run /tool-test before agent use.
   - Command: `/custom-tools`
   - Command: `/tool-proposals`
   - Command: `/tool-view NAME`
   - Command: `/tool-test NAME`
4. Target: `recovery`
   - Change: Prefer surgical find/replace for small file errors and preserve best attempted state unless user asks to rollback.
   - Command: `/surgical-repair then /backtrack only if needed`

## Safe implementation workflow
## Default repair sequence
- 1. /self-check to confirm the running backend is the expected version.
- 2. /llm-status to see whether a prompt is truly active or only loaded in Ollama.
- 3. /project-open NAME to target the correct project before repair.
- 4. /run-project or /auto-verify to reproduce the issue.
- 5. /surgical-repair with the exact error for small syntax/runtime bugs.
- 6. /improve-project for agentic inspect → test → repair → final-check.
- 7. /backtrack only when surgical repair and focused LLM repair are insufficient.

## Custom tool workflow
- 1. /tool-create GOAL for a small read-only or project-analysis helper.
- 2. /tool-proposals to review anything not auto-installed.
- 3. /tool-view NAME or /tool-code NAME to inspect source before trust/use.
- 4. /tool-test NAME to run a safe smoke test.
- 5. /tool-run NAME => {"subdir":"."} to use it in the current project.
- 6. /tool-disable NAME if a tool is noisy; /tool-delete NAME if unsafe or useless.

## Build workflow
- 1. Use /fast for small apps and /long for larger apps with exports/search/history.
- 2. If requirements are unclear, use /interactive so the assistant asks before building.
- 3. After generation, use /run-project and Open in tab/popup to test companion files.
- 4. Use /continue for feature additions to the current project.
- 5. Use /final_project_check indirectly through /improve-project or /run-plan final step.

## Self-improvement workflow
- 1. /investigate-logs to summarize recent failures.
- 2. /propose-improvements to draft safe changes to assistant code/tools/projects.
- 3. /self-improve GOAL only for small source-code changes with backup and tests.
- 4. /version and /self-check after restart to confirm the fixed build is loaded.