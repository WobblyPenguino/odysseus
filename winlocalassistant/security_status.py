from __future__ import annotations

import json
import platform
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .safe_io import atomic_write_json, atomic_write_text


def _run(cmd: list[str], timeout: int = 8) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"ok": proc.returncode == 0, "returncode": proc.returncode, "stdout": proc.stdout[-8000:], "stderr": proc.stderr[-3000:], "command": " ".join(cmd[:4])}
    except Exception as exc:
        return {"ok": False, "returncode": -1, "stdout": "", "stderr": repr(exc), "command": " ".join(cmd[:4])}


def _parse_json(stdout: str) -> Any:
    try:
        if not stdout or not stdout.strip():
            return None
        return json.loads(stdout)
    except Exception:
        return None


def _ps(script: str, timeout: int = 12) -> dict[str, Any]:
    return _run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script], timeout=timeout)


def _summarise_av_products(obj: Any) -> list[dict[str, Any]]:
    if obj is None:
        return []
    rows = obj if isinstance(obj, list) else [obj]
    out: list[dict[str, Any]] = []
    for row in rows:
        if isinstance(row, dict):
            out.append({
                "name": str(row.get("displayName") or row.get("Name") or "unknown"),
                "state": str(row.get("productState") or row.get("State") or ""),
                "path": str(row.get("pathToSignedProductExe") or row.get("Path") or ""),
            })
    return out


def _summarise_listening_ports(stdout: str) -> list[dict[str, Any]]:
    ports: list[dict[str, Any]] = []
    for line in (stdout or "").splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 5 and parts[0].upper().startswith("TCP"):
            local = parts[1]
            state = parts[3] if len(parts) > 3 else ""
            pid = parts[-1]
            if "LISTEN" in state.upper() or "LISTENING" in state.upper():
                ports.append({"local": local, "pid": pid, "state": state})
    return ports[:80]


def build_security_status() -> dict[str, Any]:
    """Defensive-only local security status and triage.

    This is intentionally read-only. It inventories local defensive tooling,
    firewall state, listening services and Nova/Docker lab context. It does not
    attack, scan external targets, exploit, or claim to stop every threat.
    """
    is_windows = platform.system().lower().startswith("win")
    processes: list[str] = []
    av_notes: list[str] = []
    raw: dict[str, Any] = {}
    av_products: list[dict[str, Any]] = []
    firewall_profiles: Any = None
    listening_ports: list[dict[str, Any]] = []
    docker_context = {"wla_sandboxes_seen": False, "containers": []}

    if is_windows:
        task = _run(["cmd", "/c", "tasklist"], timeout=12)
        raw["tasklist"] = task
        text = (task.get("stdout") or "").lower()
        for name in ["avg", "avgui", "avgsvc", "msmpeng", "securityhealthservice", "sense", "windefend", "mbam", "crowdstrike", "sentinel", "sophos", "carbonblack"]:
            if name in text:
                processes.append(name)
        defender = _ps("Get-MpComputerStatus | Select-Object AMServiceEnabled,AntivirusEnabled,RealTimeProtectionEnabled,AntispywareEnabled,NISEnabled,QuickScanAge,FullScanAge | ConvertTo-Json -Compress", timeout=14)
        raw["defender_status"] = defender
        defender_obj = _parse_json(defender.get("stdout", ""))
        if defender.get("ok"):
            av_notes.append("Windows Defender status query succeeded.")
            if isinstance(defender_obj, dict):
                if defender_obj.get("AntivirusEnabled") is False or defender_obj.get("RealTimeProtectionEnabled") is False:
                    av_notes.append("Windows Defender reports antivirus or real-time protection disabled; verify in Windows Security.")
        else:
            av_notes.append("Windows Defender status query was unavailable or blocked.")
        av = _ps("Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | Select-Object displayName,productState,pathToSignedProductExe | ConvertTo-Json -Compress", timeout=14)
        raw["antivirus_products"] = av
        av_products = _summarise_av_products(_parse_json(av.get("stdout", "")))
        if av_products:
            av_notes.append("Windows Security Center reported installed antivirus products: " + ", ".join(p.get("name", "unknown") for p in av_products[:6]))
        fw = _ps("Get-NetFirewallProfile | Select-Object Name,Enabled,DefaultInboundAction,DefaultOutboundAction | ConvertTo-Json -Compress", timeout=14)
        raw["firewall_profiles"] = fw
        firewall_profiles = _parse_json(fw.get("stdout", ""))
        netstat = _run(["cmd", "/c", "netstat -ano -p tcp"], timeout=12)
        raw["listening_ports"] = netstat
        listening_ports = _summarise_listening_ports(netstat.get("stdout", ""))
        docker = _run(["docker", "ps", "--format", "{{json .}}"], timeout=8)
        raw["docker_ps"] = docker
        if docker.get("ok"):
            containers = []
            for line in (docker.get("stdout") or "").splitlines():
                obj = _parse_json(line)
                if isinstance(obj, dict):
                    containers.append({"name": obj.get("Names"), "image": obj.get("Image"), "network": obj.get("Networks"), "status": obj.get("Status")})
            docker_context = {"wla_sandboxes_seen": any(str(c.get("name", "")).startswith("wla-") for c in containers), "containers": containers[:20]}
    else:
        ps = _run(["ps", "aux"], timeout=8)
        raw["ps"] = ps
        text = (ps.get("stdout") or "").lower()
        for name in ["clamd", "freshclam", "falcon", "sentinel", "defender", "avg", "sophos"]:
            if name in text:
                processes.append(name)
        ss = _run(["sh", "-lc", "ss -ltnp 2>/dev/null || netstat -ltnp 2>/dev/null || true"], timeout=10)
        raw["listening_ports"] = ss

    risk_notes: list[str] = []
    if listening_ports:
        externalish = [p for p in listening_ports if not str(p.get("local", "")).startswith(("127.", "[::1]", "localhost"))]
        if externalish:
            risk_notes.append(f"{len(externalish)} TCP listeners are not obviously loopback-only. Verify they are expected.")
    if not processes and not av_products:
        risk_notes.append("No common AV/EDR process names were detected by the lightweight inventory.")
    if docker_context.get("wla_sandboxes_seen"):
        risk_notes.append("Nova Docker sandboxes are running; inspect /sandbox-status before defensive lab work.")

    ok = bool(processes or av_products or any(v.get("ok") for v in raw.values() if isinstance(v, dict)))
    recommendations = [
        "Use this as a defensive inventory, not an offensive response system.",
        "For suspicious activity, preserve logs first, disconnect risky network access if needed, then run trusted AV/EDR tooling.",
        "Use /sandbox-status and /docker-status to inspect Nova containers before running any lab tools.",
        "Use Kali tools only against owned/local lab targets or systems you have explicit permission to test.",
        "For active compromise concerns, use Windows Security/AVG quarantine features and trusted incident-response guidance rather than automated retaliation.",
    ]
    payload = {
        "ok": ok,
        "summary": "Defensive security inventory completed" if ok else "Security tooling inventory incomplete",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "platform": platform.platform(),
        "detected_processes": sorted(set(processes)),
        "antivirus_products": av_products,
        "firewall_profiles": firewall_profiles,
        "listening_ports": listening_ports,
        "docker_context": docker_context,
        "notes": av_notes,
        "risk_notes": risk_notes,
        "recommendations": recommendations,
        "raw": raw,
    }
    out_dir = APP_DIR / "security_reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(out_dir / "security_status_latest.json", payload, ensure_ascii=False)
    atomic_write_text(out_dir / "security_status_latest.md", render_security_status(payload))
    return payload


def render_security_status(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Defensive Security Status",
        "",
        f"Generated: {payload.get('generated_at','')}",
        f"Platform: `{payload.get('platform','')}`",
        f"Overall: {'OK' if payload.get('ok') else 'CHECK'}",
        "",
        "## Detected defensive processes/tools",
    ]
    procs = payload.get("detected_processes") or []
    if procs:
        lines += [f"- `{p}`" for p in procs]
    else:
        lines.append("- No common AV/EDR process names detected by the lightweight check.")
    products = payload.get("antivirus_products") or []
    lines += ["", "## Antivirus products reported by OS"]
    if products:
        for prod in products:
            lines.append(f"- **{prod.get('name','unknown')}** state `{prod.get('state','')}`")
    else:
        lines.append("- No Security Center antivirus product list was available from this check.")
    lines += ["", "## Firewall profiles"]
    fw = payload.get("firewall_profiles")
    fw_rows = fw if isinstance(fw, list) else ([fw] if isinstance(fw, dict) else [])
    if fw_rows:
        for row in fw_rows:
            lines.append(f"- {row.get('Name','profile')}: enabled={row.get('Enabled')} inbound={row.get('DefaultInboundAction')} outbound={row.get('DefaultOutboundAction')}")
    else:
        lines.append("- Firewall profile data unavailable from this check.")
    ports = payload.get("listening_ports") or []
    lines += ["", "## Listening TCP services snapshot"]
    if ports:
        for p in ports[:25]:
            lines.append(f"- `{p.get('local')}` pid `{p.get('pid')}` state `{p.get('state')}`")
        if len(ports) > 25:
            lines.append(f"- ...and {len(ports)-25} more listener(s) in the JSON report.")
    else:
        lines.append("- No listening TCP snapshot available from this lightweight check.")
    dc = payload.get("docker_context") or {}
    lines += ["", "## Nova/Docker lab context", f"- Nova sandboxes seen: **{bool(dc.get('wla_sandboxes_seen'))}**"]
    for c in (dc.get("containers") or [])[:10]:
        lines.append(f"- `{c.get('name')}` image `{c.get('image')}` network `{c.get('network')}` status `{c.get('status')}`")
    lines += ["", "## Risk notes"]
    notes = payload.get("risk_notes") or []
    lines += [f"- {n}" for n in notes] if notes else ["- No lightweight risk notes were raised."]
    lines += ["", "## Notes"]
    lines += [f"- {n}" for n in (payload.get("notes") or ["No notes."])]
    lines += ["", "## Defensive next steps"]
    lines += [f"- {n}" for n in (payload.get("recommendations") or [])]
    lines += ["", "This report is defensive-only. It does not authorise offensive action, external scanning, or retaliation."]
    return "\n".join(lines)
