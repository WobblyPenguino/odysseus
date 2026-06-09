from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs"
EVIDENCE = ROOT / "docs" / "runtime_evidence"
LOGS.mkdir(exist_ok=True)
EVIDENCE.mkdir(parents=True, exist_ok=True)


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for(url: str, timeout: float = 30.0) -> bool:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        try:
            with urlopen(url, timeout=2) as resp:
                return 200 <= resp.status < 500
        except Exception:
            time.sleep(0.5)
    return False


def fetch_text(url: str, timeout: int = 10) -> str:
    with urlopen(url, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def post_json(url: str, payload: dict, timeout: int = 12) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def run_python_playwright(base: str, html: str, result: dict) -> int:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        result.update({"error": "python playwright is not installed", "exception": repr(exc), "fix": "Run .\\.venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt, then rerun release-readiness with .\\.venv\\Scripts\\python.exe"})
        return 1

    screenshot_path = EVIDENCE / "nova_runtime_usability_playwright.png"
    result["screenshot_path"] = str(screenshot_path)
    with sync_playwright() as p:
        executable = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH") or shutil_which_chromium()
        launch_kwargs = {
            "headless": True,
            "args": ["--no-sandbox", "--disable-dev-shm-usage", "--disable-web-security", "--allow-insecure-localhost", "--disable-gpu"],
        }
        if executable:
            launch_kwargs["executable_path"] = executable
        browser = p.chromium.launch(**launch_kwargs)
        try:
            page = browser.new_page(viewport={"width": 1366, "height": 900})
            page.set_content(html, wait_until="domcontentloaded", timeout=15000)
            result["steps"].append("browser rendered Nova HTML")

            input_box = page.locator("#msg")
            input_box.wait_for(state="visible", timeout=10000)
            input_box.fill("what can you do?")
            if "what can you do" not in input_box.input_value():
                raise AssertionError("composer could not be edited before drawers")
            result["steps"].append("composer editable before drawers")

            if page.locator("#novaCommandHelpButton").count() > 0:
                help_button = page.locator("#novaCommandHelpButton")
                if help_button.is_visible():
                    help_button.click()
                else:
                    page.evaluate("() => window.NovaInteractionOverhaul?.commandHelp && window.NovaInteractionOverhaul.commandHelp()")
                page.locator("#novaCommandHelpOverlay").wait_for(state="visible", timeout=5000)
                page.locator("#novaCommandHelpSearch").fill("code")
                overlay_text = page.locator("#novaCommandHelpOverlay").inner_text()
                if "/code" not in overlay_text:
                    raise AssertionError("command help search did not show /code")
                page.locator("#novaCommandHelpOverlay button", has_text="Close").click()
                result["steps"].append("searchable command help works")

            page.evaluate(
                """
                () => {
                  const activity = document.getElementById('liveActivityPanel');
                  if (activity) activity.classList.remove('is-minimized', 'collapsed', 'hidden');
                  document.body.classList.add('orbit-open', 'orbit-drawer-open', 'nova-interaction-overhaul-v1');
                  const drawer = document.getElementById('orbitDrawer');
                  if (drawer) drawer.style.display = 'block';
                  const right = document.getElementById('orbitRightDrawer');
                  if (right) right.style.display = 'block';
                  if (window.NovaInteractionOverhaul?.scanPanels) window.NovaInteractionOverhaul.scanPanels();
                }
                """
            )
            input_box.fill("composer remains usable")
            if "composer remains usable" not in input_box.input_value():
                raise AssertionError("composer not editable after drawers/activity")
            geometry = page.evaluate(
                """
                () => {
                  function rectOf(node){ const r=node.getBoundingClientRect(); return {x:r.x,y:r.y,width:r.width,height:r.height}; }
                  function overlaps(a,b){ return a && b && a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y; }
                  const input = document.getElementById('msg');
                  const inputRect = rectOf(input);
                  const panels = Array.from(document.querySelectorAll('#liveActivityPanel, #orbitDrawer, #orbitRightDrawer')).map(n => {
                    const style = getComputedStyle(n); const r = rectOf(n);
                    return {id:n.id, visible: style.display !== 'none' && style.visibility !== 'hidden' && r.width > 0 && r.height > 0, ...r, overlaps: overlaps(inputRect, r)};
                  });
                  return {inputRect, panels};
                }
                """
            )
            result["geometry"] = geometry
            overlaps = [pnl["id"] for pnl in geometry.get("panels", []) if pnl.get("visible") and pnl.get("overlaps")]
            if overlaps:
                raise AssertionError("panels overlap composer: " + ", ".join(overlaps))
            page.screenshot(path=str(screenshot_path), full_page=True)
            result["steps"].append("drawer/activity geometry does not cover composer")
            return 0
        finally:
            browser.close()


def shutil_which_chromium() -> str:
    import shutil

    for name in ["chromium", "chromium-browser", "google-chrome", "msedge", "chrome"]:
        exe = shutil.which(name)
        if exe:
            return exe
    candidates = [
        Path("/usr/lib/chromium/chromium"),
        Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(os.environ.get("PROGRAMFILES", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
    ]
    for path in candidates:
        if path and path.exists():
            return str(path)
    return ""


def main() -> int:
    port = free_port()
    base = f"http://localhost:{port}"
    env = os.environ.copy()
    env.setdefault("NOVA_APP_DIR", str(ROOT / ".nova_runtime" / "playwright"))
    env.setdefault("NOVA_LOCAL_MODEL_TIMEOUT_SEC", "1")
    env.setdefault("NOVA_CHAT_MODEL_TIMEOUT_SEC", "1")
    env.setdefault("NOVA_CODE_MODEL_TIMEOUT_SEC", "1")
    server_cmd = [sys.executable, "app.py", "--web", "--host", "127.0.0.1", "--port", str(port)]
    server_stdout_path = LOGS / "gui_runtime_server.stdout.txt"
    server_stderr_path = LOGS / "gui_runtime_server.stderr.txt"
    server_stdout = server_stdout_path.open("w", encoding="utf-8", errors="replace")
    server_stderr = server_stderr_path.open("w", encoding="utf-8", errors="replace")
    server = subprocess.Popen(server_cmd, cwd=ROOT, env=env, stdout=server_stdout, stderr=server_stderr, text=True)
    result = {"ok": False, "base_url": base, "server_cmd": server_cmd, "browser_test_returncode": None, "steps": [], "server_stdout_path": str(server_stdout_path), "server_stderr_path": str(server_stderr_path)}
    try:
        if not wait_for(base, timeout=35):
            out = server_stdout_path.read_text(encoding="utf-8", errors="replace") if server_stdout_path.exists() else ""
            err = server_stderr_path.read_text(encoding="utf-8", errors="replace") if server_stderr_path.exists() else ""
            result.update({"error": "server did not become ready", "server_stdout": out[-3000:], "server_stderr": err[-3000:]})
            return 1
        html = fetch_text(base)
        result["steps"].append("fetched server HTML")
        chat_response = post_json(base + "/chat", {"text": "hi"})
        chat_text = json.dumps(chat_response)
        if not chat_response.get("reply") or not any(word.lower() in chat_text.lower() for word in ["nova", "hi", "hello", "responsive"]):
            result.update({"error": "server chat did not produce useful reply", "chat_response": chat_response})
            return 1
        result["steps"].append("server chat returned useful reply")
        rc = run_python_playwright(base, html, result)
        result["browser_test_returncode"] = rc
        result["ok"] = rc == 0
        return rc
    except Exception as exc:
        result.update({"error": repr(exc)})
        return 1
    finally:
        try:
            server.terminate()
            server.wait(timeout=5)
        except Exception:
            try:
                server.kill()
            except Exception:
                pass
        try:
            server_stdout.close()
            server_stderr.close()
        except Exception:
            pass
        latest = LOGS / "gui_runtime_usability_latest.json"
        latest.write_text(json.dumps(result, indent=2), encoding="utf-8")
        (ROOT / "docs" / "NOVA_BROWSER_RUNTIME_TEST_LATEST.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        md = ["# Nova Browser Runtime Test", "", f"Status: **{'PASS' if result.get('ok') else 'FAIL'}**", f"Base URL: `{base}`", "", "## Steps"]
        md.extend(f"- {step}" for step in result.get("steps", []))
        if result.get("screenshot_path"):
            md.extend(["", f"Screenshot: `{result.get('screenshot_path')}`"])
        if result.get("error"):
            md.extend(["", f"Error: `{result.get('error')}`"])
        (ROOT / "docs" / "NOVA_BROWSER_RUNTIME_TEST_LATEST.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    rc = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(int(rc))
