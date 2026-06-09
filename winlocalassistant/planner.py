from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from .creation_intent import project_target_decision
from .safe_io import read_json_file


@dataclass
class PlanStep:
    title: str
    tool: str
    args: dict
    status: str = "pending"
    result_summary: str = ""


@dataclass
class Plan:
    goal: str
    steps: list[PlanStep]
    mode: str = "auto"

    def to_json(self) -> str:
        return json.dumps({"goal": self.goal, "mode": self.mode, "steps": [asdict(s) for s in self.steps]}, indent=2, ensure_ascii=False)

    def to_text(self) -> str:
        lines = [f"Plan mode: {self.mode}", f"Goal: {self.goal}", "", "Steps:"]
        for i, s in enumerate(self.steps, 1):
            lines.append(f"{i}. {s.title}")
        return "\n".join(lines)

    @classmethod
    def from_json(cls, text: str) -> "Plan":
        data = json.loads(text)
        return cls(goal=data["goal"], mode=data.get("mode", "auto"), steps=[PlanStep(**s) for s in data["steps"]])


def slugify(text: str, default: str = "GeneratedProject") -> str:
    words = re.findall(r"[A-Za-z0-9]+", text.title())
    stop = {"Make", "Build", "Create", "Generate", "Write", "A", "An", "The", "Useful", "Basic", "Simple", "Local"}
    words = [w for w in words if w not in stop]
    if not words:
        return default
    name = "".join(words[:5])
    return name[:48] or default


def _looks_like_build_request(goal: str) -> bool:
    if _looks_like_failure_feedback_request(goal):
        return False
    g = goal.lower()
    return any(k in g for k in [
        "make ", "build ", "create ", "generate ", "write ", "code ", "app", "game", "website",
        "tool", "program", "script", "dashboard", "calculator", "planner", "tracker", "assistant",
        "interactive", "story", "project", "prototype", "implement", "scaffold"
    ])


def _looks_like_edit_request(goal: str) -> bool:
    g = goal.lower().strip()
    if _looks_like_failure_feedback_request(goal):
        return False
    return g.startswith(("continue", "edit ", "fix ", "improve ", "update ", "change ", "add ", "patch ", "modify ", "expand ", "repair ")) or any(
        k in g for k in [
            "make it", "add a", "add an", "fix the", "improve the", "change the", "update the",
            "doesn't work", "doesnt work", "not working", "broken", "error", "failed",
            "unsafe attempt", "isn't working", "isnt working", "seems to be working"
        ]
    )


def _looks_like_failure_feedback_request(goal: str) -> bool:
    """User feedback about Nova's last run, not a new artifact request.

    Earlier builds treated phrases such as "you didn't make anything, why?
    fix it" as a new project goal because they contain words like "make"
    and "fix".  That created nonsense acceptance terms (for example
    requiring the generated code to contain the word "you") and started a
    candidate-refinement loop.
    """
    g = goal.lower().strip()
    g = re.sub(r"\s+", " ", g)
    complaint_markers = [
        "you didnt", "you didn't", "you did not", "didnt actually", "didn't actually",
        "did not actually", "didnt make", "didn't make", "did not make",
        "didnt give", "didn't give", "did not give", "nothing happened",
        "why did you", "why didnt", "why didn't", "why does it", "why is it",
        "it made nothing", "it didn't make", "it didnt make", "not actually make",
        "keeps repeating", "keeps looping", "candidate_refine", "model output did not",
    ]
    if any(m in g for m in complaint_markers):
        return True
    # Also catch terse follow-ups after a failed run, but avoid normal project requests.
    if "why" in g and "fix" in g and any(x in g for x in ["anything", "nothing", "actual", "actually", "loop", "repeat", "failed"]):
        return True
    return False




def _looks_like_project_library_review_request(goal: str) -> bool:
    """Detect broad requests to review/improve the existing project library.

    These are not requests to create a brand-new artifact. They should inspect
    registered/current projects and produce improvement guidance or safe targeted
    checks, avoiding the failure where Nova generated an unrelated stock app.
    """
    g = re.sub(r"\s+", " ", (goal or "").lower()).strip()
    if any(x in g for x in ["all our projects", "all my projects", "our projects", "my projects", "project library", "look at all projects"]):
        return any(x in g for x in ["identify", "improve", "need improvements", "what can we work on", "review", "audit", "make the improvements"])
    return False

def _looks_like_nova_functionality_test_request(goal: str) -> bool:
    """Detect requests to test Nova itself rather than create a new project.

    The v55.3.141 bug report showed "a test to test all of your functionality"
    being routed to ai_create_project. That phrase is a QA request about Nova, not
    an artifact request, so route it to deterministic test/audit tools instead of
    the local coding model.
    """
    g = re.sub(r"\s+", " ", (goal or "").lower()).strip()
    nova_markers = ["nova", "your functionality", "of your functionality", "all functionality", "everything you can do", "all of your tools"]
    test_markers = ["test", "check", "validate", "verify", "qa", "functionality"]
    return any(m in g for m in nova_markers) and any(t in g for t in test_markers)


def _looks_like_current_project_test_request(goal: str) -> bool:
    """Detect follow-up requests to test the currently-open generated project.

    The v55.3.144 bug report showed a follow-up like "and test each individual
    functionality..." after opening a project being misrouted into a brand-new
    project build. These requests should run deterministic verification tools on
    the current workspace instead of calling the local coding model again.
    """
    g = re.sub(r"\s+", " ", (goal or "").lower()).strip()
    if not any(x in g for x in ["test each", "each individual functionality", "validate the results", "ensure it works", "test every", "all functionality"]):
        return False
    if any(x in g for x in ["make a", "create a", "build a new", "generate a new", "write a new"]):
        return False
    return any(x in g for x in ["test", "validate", "verify", "ensure"])


def _looks_like_database_or_state_review_request(goal: str) -> bool:
    """Detect requests to review Nova's stored databases/state, not create an app.

    Users often say "database" when they mean Nova's state stores or even the
    current codebase/data layer. These requests should run deterministic audits
    and no-regression checks before any rewrite, instead of sending the phrase to
    ai_create_project.
    """
    g = re.sub(r"\s+", " ", (goal or "").lower()).strip()
    if any(x in g for x in ["make a database", "create a database app", "build a database app", "new database"]):
        return False
    review_markers = ["review", "audit", "inspect", "look", "sanity", "find", "improv", "rewrite", "regression"]
    db_markers = ["entire database", "assistant database", "nova database", "database layer", "database", "datastore", "data store", "project state"]
    return any(m in g for m in db_markers) and any(m in g for m in review_markers)



def _looks_like_repo_integration_request(goal: str) -> bool:
    """Detect requests to continue applying repo-inspired capability upgrades.

    These are Nova improvement/audit requests. They should route through the
    capability-manifest catalog, session evidence, and validation tools instead
    of blindly opening a coding-model edit loop.
    """
    g = re.sub(r"\s+", " ", (goal or "").lower()).strip()
    repo_markers = ["repo", "repos", "github", "openmontage", "open hands", "openhands", "browser-use", "mem0", "tabby", "livekit", "odysseus"]
    action_markers = ["integrat", "ideas", "capabil", "upgrade", "continue", "improv", "fix", "errors"]
    return any(m in g for m in repo_markers) and any(m in g for m in action_markers)

def _looks_like_plan_only(goal: str) -> bool:
    g = goal.lower()
    return g.startswith(("plan ", "strategy ", "scenario ")) or "scenario where" in g or "roadmap" in g


def _auto_mode(goal: str) -> str:
    g = goal.lower()
    long_markers = [
        "full", "complete", "comprehensive", "dashboard", "settings", "accounts", "multi", "database",
        "auth", "login", "roles", "charts", "analytics", "import", "export", "filters", "search",
        "history", "local saving", "test", "tests", "quality", "production", "polished"
    ]
    # Many requested features -> long plan, otherwise fast stream.
    feature_count = len([x for x in re.split(r",| and | with ", g) if len(x.strip()) > 3])
    if feature_count >= 5 or any(m in g for m in long_markers):
        return "long"
    return "fast"


def make_plan(goal: str, workspace: Path | None = None, last_error: dict | None = None, mode: str = "auto") -> Plan:
    """Return an executable plan.

    v15 adds build streams:
    - fast: fewer repair rounds, build the smallest useful working version.
    - long: requirements -> implementation -> test/repair -> review/improve -> final artifacts.
    - auto: choose fast or long from the prompt.
    """
    goal = (goal or "").strip() or "create a useful project"
    mode = (mode or "auto").lower().strip()
    if mode not in {"auto", "fast", "long"}:
        mode = "auto"
    selected_mode = _auto_mode(goal) if mode == "auto" else mode

    g_low = goal.lower().strip()

    if _looks_like_repo_integration_request(goal):
        steps = [
            PlanStep("Select repo-inspired capability manifests", "pipeline_catalog", {"goal": goal}),
            PlanStep("Inspect current project patterns before changes", "project_patterns", {"path": ".", "write": False}),
            PlanStep("Collect latest session evidence", "session_evidence", {"run_id": "latest", "limit": 120}),
            PlanStep("Run browser/GUI smoke preflight", "browser_smoke", {"path": "."}),
            PlanStep("Run bug review", "bug_review", {"focus": goal}),
            PlanStep("Run regression/functionality sweep", "regression_sweep", {"focus": goal}),
        ]
        return Plan(goal, steps, mode="repo_upgrade")

    if _looks_like_project_library_review_request(goal):
        steps = [
            PlanStep("List registered Nova projects", "projects", {}),
            PlanStep("Inspect recent project/activity evidence", "investigate_logs", {"focus": goal, "limit": 120}),
            PlanStep("Run regression/functionality sweep for the current workspace", "regression_sweep", {"focus": goal}),
            PlanStep("Run bug review before proposing changes", "bug_review", {"focus": goal}),
        ]
        return Plan(goal, steps, mode="project_library_review")

    if _looks_like_database_or_state_review_request(goal):
        steps = [
            PlanStep("Audit assistant database integrity", "assistant_db", {"action": "audit", "database": ""}),
            PlanStep("Audit current project state database", "project_state", {"path": ".", "kind": "audit"}),
            PlanStep("Run bug review before any rewrite", "bug_review", {"focus": goal}),
            PlanStep("Run regression/functionality sweep", "regression_sweep", {"focus": goal}),
        ]
        return Plan(goal, steps, mode="database_review")

    if _looks_like_current_project_test_request(goal):
        steps = [
            PlanStep("Run comprehensive user-flow QA", "user_test_suite", {"path": "."}),
            PlanStep("Run regression/functionality matrix", "regression_sweep", {"focus": goal}),
            PlanStep("Run bug review", "bug_review", {"focus": goal}),
            PlanStep("Run Nova doctor", "nova_doctor", {"goal": "general Nova reliability", "path": "."}),
        ]
        return Plan(goal, steps, mode="project_qa")

    if _looks_like_nova_functionality_test_request(goal):
        steps = [
            PlanStep("Run comprehensive user-flow QA", "user_test_suite", {"path": "."}),
            PlanStep("Run regression/functionality matrix", "regression_sweep", {"focus": goal}),
            PlanStep("Run bug review", "bug_review", {"focus": goal}),
            PlanStep("Run Nova doctor", "nova_doctor", {"goal": "general Nova reliability", "path": "."}),
        ]
        return Plan(goal, steps, mode="qa")

    if _looks_like_failure_feedback_request(goal):
        steps = [
            PlanStep("Investigate the recent failed build/model loop", "investigate_logs", {"focus": goal, "limit": 160}),
            PlanStep("Summarise candidate failure evidence", "candidate_failure_report", {"goal": goal, "path": "."}),
            PlanStep("Choose a non-redundant next repair strategy", "development_strategy", {"goal": goal, "last_failure": "user reported prior run produced no artifact or repeated candidate refinement"}),
            PlanStep("Prepare support context for the next retry", "support_report", {"focus": goal}),
        ]
        return Plan(goal, steps, mode="diagnose")

    if g_low.startswith(("run ", "open ", "interpret ")) or "run and interpret" in g_low:
        return Plan(goal, [PlanStep("Run/interpret current project", "run_project", {"path": "."})], mode="run")

    if last_error is not None:
        steps = [
            PlanStep("Repair the last failed build/test result in the current project", "ai_edit_project", {"goal": "Fix this error and keep the project working: " + json.dumps(last_error, ensure_ascii=False)[:5000], "build_mode": "long"}),
            PlanStep("Run/interpret project after repair", "run_project", {"path": "."}),
            PlanStep("Final developer check against user requirements", "final_project_check", {"path": ".", "goal": goal}),
            PlanStep("Zip repaired project", "zip_path", {"path": "."}),
        ]
        return Plan(goal, steps, mode="repair")

    if _looks_like_edit_request(goal):
        decision = None
        if workspace is not None:
            try:
                manifest_path = Path(workspace) / "PROJECT_MANIFEST.json"
                if manifest_path.exists():
                    manifest = read_json_file(manifest_path, {}, expected_type=dict, quarantine=True)
                    decision = project_target_decision(goal, {"goal": manifest.get("goal", ""), "name": Path(workspace).name})
            except Exception:
                decision = None
        if isinstance(decision, dict) and decision.get("decision") == "clarify":
            return Plan(goal, [PlanStep("Clarify whether to create a new project or modify the current one", "project_target_decision", {"goal": goal, "decision": decision})], mode="clarify")
        steps = [
            PlanStep("Read current project, apply requested edit, then test/repair", "ai_edit_project", {"goal": goal, "build_mode": selected_mode}),
            PlanStep("Run/interpret the edited project", "run_project", {"path": "."}),
            PlanStep("Final developer check against user requirements", "final_project_check", {"path": ".", "goal": goal}),
            PlanStep("Zip edited project", "zip_path", {"path": "."}),
        ]
        return Plan(goal, steps, mode=selected_mode)

    if _looks_like_plan_only(goal) and not _looks_like_build_request(goal):
        folder = slugify(goal, "ScenarioPlan")
        files = {
            f"{folder}/PLAN.md": f"# Plan\n\n## Goal\n\n{goal}\n\n## Steps\n\n1. Define the outcome.\n2. Identify constraints and available resources.\n3. Break the work into deliverables.\n4. Execute one deliverable at a time.\n5. Verify each result.\n6. Record errors and fallback actions.\n7. Package the final result.\n",
            f"{folder}/CHECKLIST.md": f"# Checklist\n\nGoal: {goal}\n\n- [ ] Confirm desired outcome\n- [ ] Collect inputs/files\n- [ ] Create first deliverable\n- [ ] Verify output\n- [ ] Fix errors\n- [ ] Zip or export result\n",
            f"{folder}/ITERATIONS.md": f"# Iterations\n\nInitial plan created for:\n\n> {goal}\n\nUse `/do build the first deliverable for this plan` to move from planning to implementation.\n",
        }
        steps = [
            PlanStep("Create human-readable planning files", "write_files", {"files": files}),
            PlanStep("Register planning project", "project_create", {"name": folder, "path": folder}),
            PlanStep("Open plan", "read_file", {"path": "PLAN.md"}),
            PlanStep("Zip planning project", "zip_path", {"path": "."}),
        ]
        return Plan(goal, steps, mode="plan")

    steps = [
        PlanStep("Extract requirements, generate code with local LLM, write files, test and repair", "ai_create_project", {"goal": goal, "build_mode": selected_mode}),
        PlanStep("Run/interpret the created project", "run_project", {"path": "."}),
        PlanStep("Final developer check against user requirements", "final_project_check", {"path": ".", "goal": goal}),
        PlanStep("Zip completed project", "zip_path", {"path": "."}),
    ]
    return Plan(goal, steps, mode=selected_mode)
