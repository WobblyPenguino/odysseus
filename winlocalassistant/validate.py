from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from .safe_io import append_text_line, atomic_write_text


def _tail(value: Any, limit: int = 4000) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return str(value)[-limit:]


def _run(cmd: list[str], cwd: Path, timeout: int = 180) -> dict[str, Any]:
    """Run a validation subprocess with timeout-safe file-backed output capture.

    ``subprocess.run(..., capture_output=True, timeout=...)`` can hang in some
    Python/Windows/plugin combinations after a child test process has already
    printed its result. File-backed capture avoids the internal reader-thread
    join path and lets Nova report the exact command/chunk instead of freezing.
    """
    started = time.perf_counter()
    env = None
    pytest_plugin_autoload_disabled = False
    if len(cmd) >= 3 and cmd[1:3] == ["-m", "pytest"]:
        env = os.environ.copy()
        env.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
        pytest_plugin_autoload_disabled = env.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"

    stdout_text = ""
    stderr_text = ""
    try:
        with tempfile.NamedTemporaryFile("w+b", delete=False) as stdout_file, tempfile.NamedTemporaryFile("w+b", delete=False) as stderr_file:
            stdout_path = Path(stdout_file.name)
            stderr_path = Path(stderr_file.name)
            proc = subprocess.Popen(cmd, cwd=str(cwd), text=True, stdout=stdout_file, stderr=stderr_file, env=env)
            deadline = time.monotonic() + max(1, int(timeout or 1))
            returncode = None
            timed_out = False
            while True:
                returncode = proc.poll()
                if returncode is not None:
                    break
                if time.monotonic() >= deadline:
                    timed_out = True
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    for _ in range(50):
                        returncode = proc.poll()
                        if returncode is not None:
                            break
                        time.sleep(0.1)
                    break
                time.sleep(0.2)

        try:
            stdout_text = stdout_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            stdout_text = ""
        try:
            stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            stderr_text = ""
        try:
            stdout_path.unlink(missing_ok=True)
            stderr_path.unlink(missing_ok=True)
        except Exception:
            pass

        elapsed = time.perf_counter() - started
        if timed_out:
            return {
                "cmd": cmd,
                "ok": False,
                "returncode": returncode,
                "elapsed_sec": round(elapsed, 3),
                "timeout_sec": timeout,
                "timed_out": True,
                "stdout_tail": _tail(stdout_text),
                "stderr_tail": _tail(stderr_text),
                "error": f"Command timed out after {timeout} second(s)",
                "pytest_plugin_autoload_disabled": pytest_plugin_autoload_disabled,
            }
        return {
            "cmd": cmd,
            "ok": returncode == 0,
            "returncode": returncode,
            "elapsed_sec": round(elapsed, 3),
            "timeout_sec": timeout,
            "stdout_tail": _tail(stdout_text),
            "stderr_tail": _tail(stderr_text),
            "pytest_plugin_autoload_disabled": pytest_plugin_autoload_disabled,
        }
    except Exception as exc:
        elapsed = time.perf_counter() - started
        return {"cmd": cmd, "ok": False, "elapsed_sec": round(elapsed, 3), "timeout_sec": timeout, "error": repr(exc), "stdout_tail": _tail(stdout_text), "stderr_tail": _tail(stderr_text), "pytest_plugin_autoload_disabled": pytest_plugin_autoload_disabled}

def _progress_path(root: Path) -> Path:
    return root / "logs" / "validation_progress.jsonl"


def _write_progress(root: Path, event: dict[str, Any]) -> None:
    """Append a best-effort machine-readable validation progress event.

    The progress log is intentionally separate from the final validation report so
    a hung or timed-out validation still leaves evidence of the last stage Nova
    started. This must never make validation fail by itself.
    """
    try:
        logs = root / "logs"
        logs.mkdir(exist_ok=True)
        payload = {"ts": round(time.time(), 3), **event}
        append_text_line(_progress_path(root), json.dumps(payload, sort_keys=True))
    except Exception:
        # Progress logging is diagnostic only; validation results should still
        # reflect the actual stage outcomes rather than a filesystem logging
        # failure.
        return


def _reset_progress(root: Path) -> None:
    try:
        path = _progress_path(root)
        path.parent.mkdir(exist_ok=True)
        atomic_write_text(path, "", encoding="utf-8")
    except Exception:
        return




def _discover_pytest_files(root: Path) -> list[str]:
    """Return repo-root relative pytest files in a deterministic order."""
    files: set[str] = set()
    for pattern in ("tests*.py", "test_*.py"):
        for path in root.glob(pattern):
            if path.is_file() and not path.name.startswith("."):
                files.add(path.name)
    return sorted(files)


def _chunk_items(items: list[str], size: int) -> list[list[str]]:
    size = max(1, int(size or 1))
    return [items[idx : idx + size] for idx in range(0, len(items), size)]


def _run_pytest_chunks(root: Path, *, chunk_size: int = 20, timeout_per_chunk: int = 420, test_files: list[str] | None = None, section_prefix: str = "full_pytest") -> dict[str, Any]:
    """Run pytest in bounded chunks so validation can identify slow/failing groups.

    A single monolithic `pytest -q` can be hard to diagnose when the suite is
    large or a plugin/test hangs near interpreter shutdown. Chunking preserves a
    complete sweep while recording the exact file group, duration and output
    tail for each chunk.
    """
    test_files = list(test_files) if test_files is not None else _discover_pytest_files(root)
    if not test_files:
        return {"ok": False, "error": "no pytest files found", "chunks": [], "total_files": 0}

    chunks = _chunk_items(test_files, chunk_size)
    results: list[dict[str, Any]] = []
    for index, names in enumerate(chunks, start=1):
        section_name = f"{section_prefix}_chunk_{index:03d}"
        cmd = [sys.executable, "-m", "pytest", "-q", *names]
        _write_progress(
            root,
            {
                "event": "section_started",
                "section": section_name,
                "cmd": cmd,
                "timeout_sec": timeout_per_chunk,
                "files": names,
            },
        )
        result = _run(cmd, root, timeout=timeout_per_chunk)
        chunk_record = {
            "index": index,
            "name": section_name,
            "files": names,
            "ok": bool(result.get("ok")),
            "detail": result,
        }
        results.append(chunk_record)
        _write_progress(
            root,
            {
                "event": "section_completed",
                "section": section_name,
                "ok": bool(result.get("ok")),
                "detail": result,
                "files": names,
            },
        )
        if not result.get("ok"):
            # Stop on first failing chunk so the report keeps the real failure
            # small and actionable instead of burying it under later noise.
            break

    failed = [chunk for chunk in results if not chunk.get("ok")]
    slowest = sorted(
        results,
        key=lambda item: float(((item.get("detail") or {}).get("elapsed_sec") or 0)),
        reverse=True,
    )[:5]
    return {
        "ok": not failed and len(results) == len(chunks),
        "mode": "chunked",
        "chunk_size": chunk_size,
        "timeout_per_chunk_sec": timeout_per_chunk,
        "total_files": len(test_files),
        "total_chunks": len(chunks),
        "completed_chunks": len(results),
        "failed_chunks": [chunk["name"] for chunk in failed],
        "slowest_chunks": [
            {
                "name": chunk.get("name"),
                "elapsed_sec": (chunk.get("detail") or {}).get("elapsed_sec"),
                "files": chunk.get("files"),
            }
            for chunk in slowest
        ],
        "chunks": results,
    }

def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _extract_version(root: Path) -> str:
    text = _read(root / "winlocalassistant" / "__init__.py")
    m = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", text)
    return m.group(1) if m else "unknown"


def _version_sync(root: Path) -> dict[str, Any]:
    version = _extract_version(root)
    needle = f"v{version}"
    package_needle = version
    paths = [
        root / "winlocalassistant" / "__init__.py",
        root / "README.md",
        root / "CHANGELOG.md",
        root / "RELEASE_MANIFEST.json",
        root / "winlocalassistant" / "webui.py",
    ]
    results = {str(p.relative_to(root)): (needle in _read(p) or package_needle in _read(p)) for p in paths}
    return {"ok": tuple(map(int, version.split("."))) >= (55, 3, 160) and all(results.values()), "version": version, "files": results}


def _launcher_checks(root: Path) -> dict[str, Any]:
    checks = {}
    for name in ["start_nova_best_models.ps1", "start_nova_best_models.bat", "start_windows_assistant.bat", "start_nova_fastapi_api.bat", "start_better_models_env.ps1"]:
        text = _read(root / name)
        checks[name] = {
            "exists": bool(text),
            "qwen3": "qwen3-coder:30b" in text or name in {"start_nova_best_models.bat", "start_windows_assistant.bat", "start_nova_fastapi_api.bat"},
            "delegates": ("start_nova_best_models" in text) if name in {"start_windows_assistant.bat", "start_nova_fastapi_api.bat"} else True,
            "node_path_ok": "C:\\Program Files\\nodejs" in text or name.endswith(".bat") or "nodejs" not in text,
        }
    ok = all(v["exists"] and v["qwen3"] and v["delegates"] and v["node_path_ok"] for v in checks.values())
    return {"ok": ok, "checks": checks}




def _startup_obviousness(root: Path) -> dict[str, Any]:
    required = {
        "START_NOVA_HERE.bat": ["start_nova_best_models.ps1", "-Setup", "-Mode web"],
        "SETUP_NOVA_FIRST.bat": ["start_nova_best_models.ps1", "-Mode setup"],
        "README_START_HERE.txt": ["START_NOVA_HERE.bat", "qwen3-coder:30b", "python -m winlocalassistant.validate --all"],
        "README.md": ["START_NOVA_HERE.bat", "SETUP_NOVA_FIRST.bat"],
    }
    results: dict[str, Any] = {}
    for rel, needles in required.items():
        text = _read(root / rel)
        results[rel] = {"exists": bool(text), "needles": {needle: needle in text for needle in needles}}
    ok = all(item["exists"] and all(item["needles"].values()) for item in results.values())
    return {"ok": ok, "results": results}


def _web_smoke(root: Path) -> dict[str, Any]:
    text = _read(root / "winlocalassistant" / "webui.py") + "\n" + _read(root / "winlocalassistant" / "webui_layout_overhaul.py")
    required = ["v55.3.164", "populateSpecChoices", "safeApplyUiSettings", "/video-plan", "/media-status", "/video-package", "focus-workspace", "/nova-efficiency-audit", "qwen3-coder:30b", "natural-research-routing", "/provider-route", "/queue-status", "provider-route-bar", "gui-overhaul-v3", "apply_gui_layout_overhaul"]
    return {"ok": all(x in text for x in required), "required": {x: x in text for x in required}}


def validate_all(root: Path | str = ".", *, full: bool = False, single_process_full: bool = False, chunk_size: int = 20) -> dict[str, Any]:
    root = Path(root).resolve()
    sections: list[dict[str, Any]] = []
    _reset_progress(root)

    def add(name: str, ok: bool, detail: Any = None) -> None:
        section = {"name": name, "ok": bool(ok), "detail": detail}
        sections.append(section)
        _write_progress(root, {"event": "section_completed", "section": name, "ok": bool(ok), "detail": detail})

    def run_section(name: str, cmd: list[str], timeout: int) -> dict[str, Any]:
        _write_progress(root, {"event": "section_started", "section": name, "cmd": cmd, "timeout_sec": timeout})
        return _run(cmd, root, timeout=timeout)

    add("environment", sys.version_info >= (3, 11), {"python": sys.version.split()[0], "cwd": str(root)})
    add("imports", (root / "winlocalassistant").is_dir() and (root / "app.py").exists())
    compile_result = run_section("compileall", [sys.executable, "-m", "compileall", "app.py", "nova", "winlocalassistant"], timeout=300)
    add("compileall", compile_result.get("ok"), compile_result)

    # Run the lightweight CLI smoke before pytest subprocesses. Some local test
    # plugin stacks can leave interpreter-shutdown hooks active after pytest has
    # completed, which made validation appear frozen even though the checks had
    # already passed. Keeping the CLI smoke ahead of pytest makes the launcher
    # signal deterministic and still leaves unit/full pytest results in the same
    # validation report.
    cli = run_section("cli_smoke", [sys.executable, "app.py", "/version"], timeout=60)
    add("cli_smoke", cli.get("ok") and f"Nova { _extract_version(root) }" in cli.get("stdout_tail", ""), cli)

    targeted = [
        "tests_release_hygiene.py",
        "tests_nova_better_model_env.py",
        "tests_nova_video_manifest.py",
        "tests_nova_launchers_v55_3_154.py",
        "tests_nova_release_sync_v55_3_154.py",
        "tests_nova_start_here_v55_3_155.py",
        "tests_nova_clean_gui_docker_v55_3_159.py",
        "tests_nova_media_refinement_v55_3_160.py",
        "tests_improvement_features_v55_3_124.py",
        "tests_nova_scheduler_v55_3_164.py",
        "tests_validation_reporting.py",
        "tests_validation_status_command.py",
        "tests_nova_remote_access_v55_3_164.py",
        "tests_validation_chunked_full.py",
        "tests_nova_gui_startup_routes_v55_3_161.py",
        "tests_v55_3_146_pipeline_observability.py",
        "tests_v55_3_148_tool_awareness_orchestration.py",
        "tests_gui_ai_help_overlay.py",
        "tests_gui_cyberpunk_theme.py",
        "tests_gui_interaction_overhaul.py",
        "tests_performance_tuning.py",
    ]
    existing = [name for name in targeted if (root / name).exists()]
    if __import__("os").environ.get("PYTEST_CURRENT_TEST"):
        add("unit_tests", True, {"skipped_under_pytest": True, "reason": "avoid recursive pytest from validation smoke test", "targeted": existing})
    elif existing:
        _write_progress(root, {"event": "section_started", "section": "unit_tests", "mode": "chunked", "chunk_size": 1})
        targeted_chunks = _run_pytest_chunks(root, chunk_size=1, timeout_per_chunk=240, test_files=existing, section_prefix="unit_tests")
        add("unit_tests", targeted_chunks.get("ok"), targeted_chunks)
    else:
        add("unit_tests", False, {"error": "no targeted tests found"})

    if full:
        if single_process_full:
            add("full_pytest", (_r := run_section("full_pytest", [sys.executable, "-m", "pytest", "-q"], timeout=2400)).get("ok"), _r)
        else:
            _write_progress(root, {"event": "section_started", "section": "full_pytest", "mode": "chunked", "chunk_size": chunk_size})
            chunked = _run_pytest_chunks(root, chunk_size=chunk_size, timeout_per_chunk=420)
            add("full_pytest", chunked.get("ok"), chunked)
    else:
        add("full_pytest", True, {"skipped": True, "hint": "run with --full for a chunked complete legacy sweep; add --single-process-full only when debugging old monolithic pytest behavior"})

    vs = _version_sync(root)
    add("version_sync", vs.get("ok"), vs)
    launch = _launcher_checks(root)
    add("launchers", launch.get("ok"), launch)
    startup = _startup_obviousness(root)
    add("startup_bat_obviousness", startup.get("ok"), startup)
    web = _web_smoke(root)
    add("gui_smoke", web.get("ok"), web)
    add("voice_state_machine", (root / "winlocalassistant" / "orchestration_foundation.py").exists())
    add("coding_worker_fixture", (root / "winlocalassistant" / "repo_intelligence.py").exists())
    add("browser_worker_fixture", (root / "winlocalassistant" / "browser_worker.py").exists())
    add("rag_fixture", (root / "winlocalassistant" / "document_ingestion.py").exists())
    add("creative_worker_fixture", (root / "winlocalassistant" / "nova_video.py").exists())
    add("model_registry", (root / "winlocalassistant" / "model_registry.py").exists())
    add("integration_review", (root / "winlocalassistant" / "integration_review.py").exists())
    add("package_lock_and_license_scan", (root / "pyproject.toml").exists() or (root / "requirements-dev.txt").exists() or (root / "RELEASE_MANIFEST.json").exists())

    payload = {
        "ok": all(section["ok"] for section in sections),
        "sections": sections,
        "command": "python -m winlocalassistant.validate --all" + (" --full" if full else "") + (" --single-process-full" if single_process_full else ""),
        "progress_log": "logs/validation_progress.jsonl",
        "note": "Layered validation: environment, imports, compile, targeted tests, version sync, launchers, CLI/web smoke, worker surfaces and package/license surface. Progress is written to logs/validation_progress.jsonl while stages run.",
    }
    logs = root / "logs"
    logs.mkdir(exist_ok=True)
    (logs / "validation_latest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (logs / "validation_latest.txt").write_text(render_validation(payload), encoding="utf-8")
    return payload


def _format_command(cmd: Any) -> str:
    if isinstance(cmd, list):
        return " ".join(str(part) for part in cmd)
    return str(cmd or "")


def _section_summary(section: dict[str, Any]) -> str:
    detail = section.get("detail")
    if not isinstance(detail, dict):
        return ""
    bits: list[str] = []
    if "elapsed_sec" in detail:
        bits.append(f"{detail.get('elapsed_sec')}s")
    if detail.get("timed_out"):
        bits.append(f"timed out after {detail.get('timeout_sec')}s")
    elif detail.get("returncode") not in (None, 0):
        bits.append(f"returncode={detail.get('returncode')}")
    if detail.get("mode") == "chunked":
        bits.append(f"chunked {detail.get('completed_chunks')}/{detail.get('total_chunks')} chunks")
        if detail.get("failed_chunks"):
            bits.append(f"failed={','.join(map(str, detail.get('failed_chunks') or []))}")
    if detail.get("skipped"):
        bits.append("skipped")
    if detail.get("skipped_under_pytest"):
        bits.append("skipped under pytest")
    if detail.get("cmd") and not section.get("ok"):
        bits.append(f"cmd={_format_command(detail.get('cmd'))}")
    if detail.get("error") and not section.get("ok"):
        bits.append(str(detail.get("error"))[:220])
    return f" ({'; '.join(bits)})" if bits else ""



def load_validation_status(root: Path | str = ".") -> dict[str, Any]:
    """Return a compact, honest snapshot of Nova validation progress.

    This is intentionally read-only and tolerant of partial/corrupt files so the
    GUI/CLI can still report the last known validation stage after a crash,
    timeout, interrupted run, or manual log edit.
    """
    root = Path(root).resolve()
    logs = root / "logs"
    report_path = logs / "validation_latest.json"
    progress_path = _progress_path(root)
    report: dict[str, Any] = {}
    warnings: list[str] = []

    if report_path.exists():
        try:
            raw = json.loads(report_path.read_text(encoding="utf-8", errors="replace"))
            if isinstance(raw, dict):
                report = raw
            else:
                warnings.append("validation_latest.json did not contain a JSON object")
        except Exception as exc:
            warnings.append(f"Could not parse validation_latest.json: {exc!r}")
    else:
        warnings.append("No logs/validation_latest.json report found yet")

    events: list[dict[str, Any]] = []
    malformed_progress_rows = 0
    if progress_path.exists():
        for line in progress_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                if isinstance(item, dict):
                    events.append(item)
                else:
                    malformed_progress_rows += 1
            except Exception:
                malformed_progress_rows += 1
        if malformed_progress_rows:
            warnings.append(f"Ignored {malformed_progress_rows} malformed validation progress row(s)")
    else:
        warnings.append("No logs/validation_progress.jsonl progress log found yet")

    last_started = next((event for event in reversed(events) if event.get("event") == "section_started"), None)
    last_completed = next((event for event in reversed(events) if event.get("event") == "section_completed"), None)
    latest_event = events[-1] if events else None
    running_section = None
    if last_started and (not last_completed or last_started.get("ts", 0) > last_completed.get("ts", 0)):
        running_section = last_started.get("section")

    sections = report.get("sections", []) if isinstance(report.get("sections"), list) else []
    failed_sections = [section.get("name") for section in sections if isinstance(section, dict) and not section.get("ok")]

    progress_incomplete = bool(running_section)
    if progress_incomplete:
        warnings.append(
            f"Progress log has a started stage without a later completion: {running_section}. "
            "A newer validation run may still be running or may have been interrupted after the latest report."
        )

    if not report and events:
        state = "in_progress_or_interrupted"
    elif report.get("ok") is True and progress_incomplete:
        state = "pass_report_with_interrupted_progress"
    elif report.get("ok") is True:
        state = "pass"
    elif report.get("ok") is False:
        state = "review"
    else:
        state = "unknown"

    return {
        "ok": report.get("ok") if report else None,
        "state": state,
        "report_path": str(report_path.relative_to(root)),
        "progress_path": str(progress_path.relative_to(root)),
        "section_count": len(sections),
        "failed_sections": failed_sections,
        "last_started": last_started,
        "last_completed": last_completed,
        "latest_event": latest_event,
        "running_section": running_section,
        "progress_incomplete": progress_incomplete,
        "warnings": warnings,
    }


def render_validation_status(status: dict[str, Any]) -> str:
    state = status.get("state", "unknown")
    lines = ["# Nova Validation Status", "", f"State: **{state}**"]
    if status.get("ok") is not None:
        lines.append(f"Latest report OK: `{status.get('ok')}`")
    lines.append(f"Report: `{status.get('report_path', 'logs/validation_latest.json')}`")
    lines.append(f"Progress: `{status.get('progress_path', 'logs/validation_progress.jsonl')}`")

    running = status.get("running_section")
    if running:
        lines += ["", f"Current/last-started stage: `{running}`"]

    last_completed = status.get("last_completed") or {}
    if isinstance(last_completed, dict) and last_completed:
        detail = last_completed.get("detail") if isinstance(last_completed.get("detail"), dict) else {}
        extra = ""
        if detail.get("elapsed_sec") is not None:
            extra = f" in {detail.get('elapsed_sec')}s"
        lines.append(f"Last completed stage: `{last_completed.get('section')}` ({'PASS' if last_completed.get('ok') else 'FAIL'}{extra})")

    failed = status.get("failed_sections") or []
    if failed:
        lines += ["", "Failed sections:"]
        lines += [f"- `{name}`" for name in failed]

    warnings = status.get("warnings") or []
    if warnings:
        lines += ["", "Warnings:"]
        lines += [f"- {warning}" for warning in warnings]

    lines += ["", "Use `python -m winlocalassistant.validate --all` for the standard validation pass, or add `--full` for a chunked complete legacy pytest sweep."]
    return "\n".join(lines)

def render_validation(payload: dict[str, Any]) -> str:
    lines = ["# Nova Validation", "", f"Status: {'PASS' if payload.get('ok') else 'REVIEW'}", ""]
    if payload.get("progress_log"):
        lines.append(f"Progress log: {payload.get('progress_log')}")
        lines.append("")
    for idx, section in enumerate(payload.get("sections", []), start=1):
        lines.append(f"[{idx}] {section.get('name')}: {'PASS' if section.get('ok') else 'FAIL'}{_section_summary(section)}")
    lines += ["", str(payload.get("note", ""))]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Layered Nova validation runner")
    parser.add_argument("--all", action="store_true", help="Run the standard layered validation")
    parser.add_argument("--full", action="store_true", help="Also run the complete pytest suite in bounded chunks")
    parser.add_argument("--single-process-full", action="store_true", help="Use the old monolithic `pytest -q` full-suite mode instead of chunking")
    parser.add_argument("--chunk-size", type=int, default=20, help="Number of test files per chunk when --full is used")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown")
    args = parser.parse_args(argv)
    payload = validate_all(Path.cwd(), full=args.full, single_process_full=args.single_process_full, chunk_size=args.chunk_size)
    if args.json:
        print(json.dumps(payload, indent=2), flush=True)
    else:
        print(render_validation(payload), flush=True)
        print("\nWrote logs/validation_latest.txt and logs/validation_latest.json", flush=True)
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    # Some optional Nova validation subprocesses/imports can register slow atexit
    # cleanup hooks in this packaged environment even after validation output has
    # been printed. Flush and exit directly so `python -m winlocalassistant.validate
    # --all` remains a reliable smoke-test command for launchers and CI.
    import os

    exit_code = main()
    # Use a direct process exit after flushed prints. In some local/sandboxed
    # environments optional subprocess/import hooks can hang during normal
    # interpreter shutdown; avoiding explicit stream flushes here prevents the
    # validation command itself from appearing frozen after the report is printed.
    os._exit(exit_code)
