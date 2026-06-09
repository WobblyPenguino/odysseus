from __future__ import annotations

"""Small, dependency-free LLM training lab helpers for Nova.

This module does **not** train a model.  It gives Nova a safe local planning and
inspection layer inspired by from-scratch LLM education repos: data checks,
token/parameter estimates, stage plans, and host-safe smoke evidence.  Heavy
training remains an explicit user action outside Nova's release gate.
"""

import argparse
import json
import math
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .safe_io import atomic_write_json, atomic_write_text

LLM_LAB_SCHEMA_VERSION = 1
LATEST_JSON = Path("docs") / "NOVA_LLM_TRAINING_LAB_LATEST.json"
LATEST_MD = Path("docs") / "NOVA_LLM_TRAINING_LAB_LATEST.md"
TEXT_SUFFIXES = {".txt", ".md", ".jsonl", ".json", ".py", ".js", ".ts", ".html", ".css", ".csv"}
DEFAULT_PROMPTS = [
    "explain what attention does in one paragraph",
    "write a tiny Python function and one test",
    "summarise a short technical note",
]


@dataclass(frozen=True)
class DatasetStats:
    path: str
    exists: bool
    inspected_files: int
    text_files: int
    skipped_files: int
    total_bytes: int
    total_lines: int
    non_empty_lines: int
    unique_line_ratio: float
    approx_tokens: int
    warnings: list[str]
    sample_files: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _parse_number(text: str | int | float | None, default: int) -> int:
    if text is None or text == "":
        return default
    if isinstance(text, (int, float)):
        return int(text)
    raw = str(text).strip().lower().replace(",", "")
    match = re.fullmatch(r"([0-9]*\.?[0-9]+)\s*([kmbt]?)", raw)
    if not match:
        return default
    value = float(match.group(1))
    suffix = match.group(2)
    scale = {"": 1, "k": 1_000, "m": 1_000_000, "b": 1_000_000_000, "t": 1_000_000_000_000}[suffix]
    return int(value * scale)


def _format_count(n: int | float) -> str:
    n = float(n)
    for suffix, scale in [("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)]:
        if abs(n) >= scale:
            return f"{n / scale:.2f}{suffix}".rstrip("0").rstrip(".")
    return str(int(n))


def _iter_candidate_files(path: Path, max_files: int) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    count = 0
    for item in sorted(path.rglob("*")):
        if count >= max_files:
            break
        if item.is_file():
            count += 1
            yield item


def inspect_dataset(path: str | Path, *, max_files: int = 200, max_file_bytes: int = 2_000_000) -> DatasetStats:
    target = Path(path).expanduser().resolve()
    if not target.exists():
        return DatasetStats(
            path=str(target), exists=False, inspected_files=0, text_files=0, skipped_files=0,
            total_bytes=0, total_lines=0, non_empty_lines=0, unique_line_ratio=0.0,
            approx_tokens=0, warnings=["Path does not exist."], sample_files=[])

    inspected = text_files = skipped = bytes_total = lines_total = non_empty = char_total = 0
    sample_files: list[str] = []
    seen_lines: set[str] = set()
    repeated_or_empty = 0
    warnings: list[str] = []

    for file_path in _iter_candidate_files(target, max_files=max_files):
        inspected += 1
        if file_path.suffix.lower() not in TEXT_SUFFIXES:
            skipped += 1
            continue
        try:
            size = file_path.stat().st_size
            if size > max_file_bytes:
                skipped += 1
                warnings.append(f"Skipped oversized file: {file_path.name} ({size} bytes).")
                continue
            raw = file_path.read_bytes()
            if b"\x00" in raw[:2048]:
                skipped += 1
                warnings.append(f"Skipped likely-binary file: {file_path.name}.")
                continue
            text = raw.decode("utf-8", errors="replace")
        except Exception as exc:
            skipped += 1
            warnings.append(f"Skipped unreadable file {file_path.name}: {exc!r}.")
            continue
        text_files += 1
        bytes_total += len(text.encode("utf-8", errors="replace"))
        char_total += len(text)
        if len(sample_files) < 8:
            sample_files.append(str(file_path))
        for line in text.splitlines():
            lines_total += 1
            stripped = line.strip()
            if stripped:
                non_empty += 1
                if stripped in seen_lines:
                    repeated_or_empty += 1
                else:
                    seen_lines.add(stripped)
            else:
                repeated_or_empty += 1

    approx_tokens = max(0, int(char_total / 4))
    unique_ratio = 0.0 if non_empty == 0 else round(min(1.0, len(seen_lines) / max(1, non_empty)), 3)
    if text_files == 0:
        warnings.append("No text-like training files were found.")
    if approx_tokens and approx_tokens < 50_000:
        warnings.append("Dataset is tiny; use it for pipeline smoke tests, not serious pretraining.")
    if unique_ratio and unique_ratio < 0.7:
        warnings.append("Many repeated lines detected; deduplicate before training.")
    if inspected >= max_files:
        warnings.append(f"Inspection stopped at {max_files} files; run on a narrower dataset folder for exact stats.")

    return DatasetStats(
        path=str(target), exists=True, inspected_files=inspected, text_files=text_files,
        skipped_files=skipped, total_bytes=bytes_total, total_lines=lines_total,
        non_empty_lines=non_empty, unique_line_ratio=unique_ratio,
        approx_tokens=approx_tokens, warnings=warnings, sample_files=sample_files)


def estimate_training_budget(params: str | int = "124m", tokens: str | int = "10m", *, seq_len: int = 1024, batch_size: int = 4, dtype_bytes: int = 2) -> dict[str, Any]:
    param_count = _parse_number(params, 124_000_000)
    token_count = _parse_number(tokens, 10_000_000)
    # Rough educational estimates: parameters, gradients, optimizer states and
    # activations.  They are intentionally conservative and labelled as rough.
    param_mem_gb = param_count * dtype_bytes / 1e9
    train_mem_gb = param_count * 14 / 1e9  # weights + grads + Adam-like states, rough fp16/bf16 training budget
    hidden_guess = max(256, int(math.sqrt(param_count / 12)))
    layer_guess = max(4, min(48, int(round(math.log10(max(param_count, 10_000)) * 3))))
    activation_gb = batch_size * seq_len * hidden_guess * layer_guess * dtype_bytes * 4 / 1e9
    total_gb = round(train_mem_gb + activation_gb + 2.0, 2)
    steps = math.ceil(token_count / max(1, batch_size * seq_len))
    checkpoint_gb = round(param_count * dtype_bytes / 1e9, 2)
    consumer_gpu_ok = total_gb <= 16
    return {
        "ok": True,
        "params": param_count,
        "tokens": token_count,
        "seq_len": seq_len,
        "batch_size": batch_size,
        "dtype_bytes": dtype_bytes,
        "estimated_steps": steps,
        "rough_inference_weight_gb": round(param_mem_gb, 2),
        "rough_training_vram_gb": total_gb,
        "rough_checkpoint_gb": checkpoint_gb,
        "consumer_16gb_gpu_feasible_for_smoke": consumer_gpu_ok,
        "recommendation": (
            "Feasible for an educational tiny/small from-scratch run on a 16GB GPU if code is efficient and batch size is small."
            if consumer_gpu_ok else
            "Too large for comfortable from-scratch training on a 16GB GPU; use a tiny smoke model, LoRA/finetuning, or cloud/multi-GPU."
        ),
    }


def build_training_plan(goal: str = "learn and safely experiment with LLM training", *, hardware: str = "consumer 16GB GPU") -> dict[str, Any]:
    phases = [
        {"phase": "1. Data", "purpose": "Collect a small legal/local text dataset, inspect size, duplicates and format.", "nova_check": "/llm-lab dataset PATH"},
        {"phase": "2. Tokenizer", "purpose": "Start with an existing tokenizer or tiny educational BPE experiment before any expensive run.", "nova_check": "confirm vocab size and sample encoding/decoding"},
        {"phase": "3. Architecture", "purpose": "Use a tiny GPT-style config first, then scale only after loss curves and generation smoke tests behave.", "nova_check": "/llm-lab estimate 13m 5m"},
        {"phase": "4. Pretraining smoke", "purpose": "Train on a tiny slice only to prove dataloader, checkpoints, resume, logging and generation work.", "nova_check": "save loss, sample output and checkpoint hash"},
        {"phase": "5. Finetuning", "purpose": "Prefer SFT or task-specific finetuning for usefulness; avoid expensive from-scratch unless educational.", "nova_check": "hold out eval prompts and regression tests"},
        {"phase": "6. Evaluation", "purpose": "Run deterministic prompt tests, safety checks, hallucination checks and code/file task checks before routing into Nova.", "nova_check": "/model-calibration --bench and Nova eval packs"},
        {"phase": "7. Routing", "purpose": "Use the trained model only for roles it passes; keep fallback to the proven chat/code model.", "nova_check": "/llm-status and /release-readiness --full"},
    ]
    guardrails = [
        "Do not train on private chats, secrets, API keys, passwords or copyrighted dumps you do not have rights to use.",
        "Do not let training scripts overwrite Nova source or release files; run in a separate experiments folder.",
        "Keep the first run tiny and checkpointed; expensive runs need explicit confirmation and host evidence.",
        "Treat from-scratch models as educational unless evaluation proves they beat your existing Ollama models for a specific Nova role.",
    ]
    return {"ok": True, "goal": goal.strip() or "learn LLM training", "hardware": hardware, "phases": phases, "guardrails": guardrails}


def build_lab_report(root: str | Path = ".", *, goal: str = "", dataset: str = "", params: str = "124m", tokens: str = "10m") -> dict[str, Any]:
    root_path = Path(root).expanduser().resolve()
    (root_path / "docs").mkdir(parents=True, exist_ok=True)
    plan = build_training_plan(goal or "Nova-safe local LLM training experiment")
    estimate = estimate_training_budget(params=params, tokens=tokens)
    dataset_stats = inspect_dataset(root_path / dataset).to_dict() if dataset else None
    payload = {
        "schema_version": LLM_LAB_SCHEMA_VERSION,
        "ok": True,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "root": str(root_path),
        "inspiration": [
            "rasbt/LLMs-from-scratch: educational GPT-like model pipeline",
            "FareedKhan-dev/train-llm-from-scratch: end-to-end data-to-generation and post-training stages",
            "karpathy/llm.c: small reproducible training/debugging emphasis",
        ],
        "plan": plan,
        "estimate": estimate,
        "dataset": dataset_stats,
        "recommended_commands": [
            "/llm-lab plan learn tiny GPT training",
            "/llm-lab dataset data/my_texts",
            "/llm-lab estimate 13m 5m",
            "python -m winlocalassistant.llm_training_lab --root . --plan",
            "python -m winlocalassistant.release_readiness --root . --full",
        ],
    }
    atomic_write_json(root_path / LATEST_JSON, payload, ensure_ascii=True)
    atomic_write_text(root_path / LATEST_MD, render_lab_markdown(payload))
    return payload


def render_lab_markdown(payload: dict[str, Any]) -> str:
    plan = payload.get("plan") or {}
    estimate = payload.get("estimate") or {}
    lines = [
        "# Nova LLM Training Lab",
        "",
        "Purpose: Nova-safe planning, dataset inspection and training-budget estimates for educational LLM experiments.",
        f"Created: `{payload.get('created_at', '')}`",
        f"Root: `{payload.get('root', '')}`",
        "",
        "## Inspired by",
    ]
    for item in payload.get("inspiration") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Training plan"])
    lines.append(f"Goal: {plan.get('goal', '')}")
    for phase in plan.get("phases") or []:
        lines.append(f"- **{phase.get('phase')}** — {phase.get('purpose')} Nova check: `{phase.get('nova_check')}`")
    lines.extend(["", "## Guardrails"])
    for rule in plan.get("guardrails") or []:
        lines.append(f"- {rule}")
    lines.extend(["", "## Rough budget estimate"])
    if estimate:
        lines.append(f"- Parameters: `{_format_count(int(estimate.get('params', 0)))}`")
        lines.append(f"- Tokens: `{_format_count(int(estimate.get('tokens', 0)))}`")
        lines.append(f"- Estimated steps: `{estimate.get('estimated_steps')}`")
        lines.append(f"- Rough training VRAM: `{estimate.get('rough_training_vram_gb')} GB`")
        lines.append(f"- Recommendation: {estimate.get('recommendation')}")
    dataset = payload.get("dataset")
    if dataset:
        lines.extend(["", "## Dataset inspection"])
        lines.append(f"- Path: `{dataset.get('path')}`")
        lines.append(f"- Text files: `{dataset.get('text_files')}` / inspected `{dataset.get('inspected_files')}`")
        lines.append(f"- Approx tokens: `{_format_count(int(dataset.get('approx_tokens') or 0))}`")
        lines.append(f"- Unique-line ratio: `{dataset.get('unique_line_ratio')}`")
        for warning in dataset.get("warnings") or []:
            lines.append(f"- Warning: {warning}")
    lines.extend(["", "## Commands"])
    for cmd in payload.get("recommended_commands") or []:
        lines.append(f"- `{cmd}`")
    return "\n".join(lines).strip() + "\n"


def render_command(rest: str = "", *, root: str | Path = ".") -> str:
    raw = (rest or "").strip()
    parts = raw.split()
    action = (parts[0].lower() if parts else "plan")
    root_path = Path(root).expanduser().resolve()
    if action in {"plan", "status", "recipe"}:
        goal = raw.split(maxsplit=1)[1] if len(parts) > 1 else "Nova-safe local LLM training experiment"
        return render_lab_markdown(build_lab_report(root_path, goal=goal))
    if action in {"dataset", "data", "inspect"}:
        target = raw.split(maxsplit=1)[1] if len(parts) > 1 else "."
        payload = build_lab_report(root_path, goal="dataset inspection", dataset=target)
        return render_lab_markdown(payload)
    if action in {"estimate", "budget", "vram"}:
        params = parts[1] if len(parts) > 1 else "124m"
        tokens = parts[2] if len(parts) > 2 else "10m"
        payload = build_lab_report(root_path, goal="training budget estimate", params=params, tokens=tokens)
        return render_lab_markdown(payload)
    if action in {"help", "--help", "?"}:
        return (
            "# Nova LLM Training Lab\n\n"
            "Commands:\n"
            "- `/llm-lab plan GOAL` — safe from-scratch/SFT training roadmap.\n"
            "- `/llm-lab dataset PATH` — inspect local text data size, duplicates and warnings.\n"
            "- `/llm-lab estimate 13m 5m` — rough parameter/token/VRAM estimate.\n"
            "- `python -m winlocalassistant.llm_training_lab --root . --plan` — CLI report.\n"
        )
    return f"Unknown /llm-lab action `{action}`. Use `/llm-lab help`."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Nova-safe LLM training lab report")
    parser.add_argument("--root", default=".")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--dataset", default="")
    parser.add_argument("--params", default="124m")
    parser.add_argument("--tokens", default="10m")
    args = parser.parse_args(argv)
    payload = build_lab_report(args.root, goal="CLI LLM training lab report", dataset=args.dataset, params=args.params, tokens=args.tokens)
    print(render_lab_markdown(payload))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
