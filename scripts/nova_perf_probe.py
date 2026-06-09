from __future__ import annotations
import csv, json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "logs" / "nova_perf"
OUT.mkdir(parents=True, exist_ok=True)
COMMANDS = [
    [sys.executable, "app.py", "/version"],
    [sys.executable, "app.py", "/perf-status"],
    [sys.executable, "app.py", "/validation-status"],
    [sys.executable, "app.py", "/model-health"],
    [sys.executable, "app.py", "/do", "Explain how a binary search tree works in 120 words."],
    [sys.executable, "app.py", "/coding-plan", "Add a small regression test for command routing."],
]

def approx_tokens(text: str) -> int:
    return max(1, len(text.split()))

rows = []
for idx, cmd in enumerate(COMMANDS, 1):
    start = time.perf_counter()
    cp = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=240)
    elapsed = (time.perf_counter() - start) * 1000
    out_path = OUT / f"command_{idx:02d}.txt"
    out_path.write_text(cp.stdout + "\n\n--- STDERR ---\n" + cp.stderr, encoding="utf-8", errors="replace")
    rows.append({
        "index": idx,
        "command": " ".join(cmd),
        "returncode": cp.returncode,
        "wall_ms": round(elapsed, 2),
        "stdout_bytes": len(cp.stdout.encode("utf-8", errors="ignore")),
        "stderr_bytes": len(cp.stderr.encode("utf-8", errors="ignore")),
        "approx_output_tokens": approx_tokens(cp.stdout),
        "tokens_per_sec_rough": round(approx_tokens(cp.stdout) / max(elapsed / 1000, 0.001), 2),
        "output_file": str(out_path.relative_to(ROOT)),
    })
with (OUT / "command_timings.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader(); writer.writerows(rows)
summary = {"ok": all(r["returncode"] == 0 for r in rows), "rows": rows, "env": {k: ("<redacted>" if "TOKEN" in k else os.environ.get(k,"")) for k in ["OLLAMA_FLASH_ATTENTION","TOKENIZERS_PARALLELISM","CUDA_LAUNCH_BLOCKING","OMP_NUM_THREADS","OLLAMA_MODELS","NOVA_PERF_MODE"]}}
(OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
