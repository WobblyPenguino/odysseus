from pathlib import Path

from winlocalassistant.eventlog import tail_jsonl
from winlocalassistant.efficiency_profiler import read_efficiency_samples, EFFICIENCY_LOG_PATH
from winlocalassistant.interaction_learning import InteractionLesson, load_interaction_lessons
from winlocalassistant.safe_io import append_jsonl, tail_jsonl_rows, tail_text_lines


def test_tail_text_lines_reads_only_recent_lines(tmp_path: Path):
    path = tmp_path / "large.log"
    path.write_text("".join(f"line-{i}\n" for i in range(2000)), encoding="utf-8")
    assert tail_text_lines(path, 3) == ["line-1997", "line-1998", "line-1999"]
    assert tail_text_lines(path, 0) == []


def test_tail_jsonl_rows_skips_bad_and_non_dict_rows(tmp_path: Path):
    path = tmp_path / "rows.jsonl"
    path.write_text('{"a":1}\nnot-json\n[1,2]\n{"b":2}\n', encoding="utf-8")
    assert tail_jsonl_rows(path, 5) == [{"a": 1}, {"b": 2}]


def test_event_tail_jsonl_handles_malformed_ts_without_crashing(tmp_path: Path):
    path = tmp_path / "activity.jsonl"
    path.write_text('{"ts":"bad","kind":"x","message":"bad ts"}\n{"ts":999,"kind":"y","message":"ok"}\n', encoding="utf-8")
    rows = tail_jsonl(path, limit=5, since_ts=1.0)
    assert len(rows) == 1
    assert rows[0]["kind"] == "y"


def test_efficiency_reader_uses_tail_and_ignores_malformed(tmp_path: Path, monkeypatch):
    path = tmp_path / "efficiency_metrics.jsonl"
    path.write_text('bad\n{"kind":"tool","name":"/status","wall_ms":1}\n', encoding="utf-8")
    import winlocalassistant.efficiency_profiler as ep
    monkeypatch.setattr(ep, "EFFICIENCY_LOG_PATH", path)
    assert ep.read_efficiency_samples(limit=10) == [{"kind": "tool", "name": "/status", "wall_ms": 1}]


def test_interaction_lessons_loader_uses_jsonl_tail(tmp_path: Path):
    path = tmp_path / "lessons.jsonl"
    for i in range(80):
        append_jsonl(path, {
            "timestamp": str(i),
            "user_request": f"request {i}",
            "intent": "general",
            "tool_used": "test",
            "outcome": "ok",
            "user_feedback": "",
            "lesson": f"lesson {i}",
            "tags": [],
        })
    lessons = load_interaction_lessons(path, limit=3)
    assert [lesson.timestamp for lesson in lessons] == ["77", "78", "79"]
