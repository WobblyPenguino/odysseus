from pathlib import Path

from winlocalassistant.code_review_audit import run_code_review, write_code_review_report
from winlocalassistant.code_repair_audit import write_code_repair_audit_report
from winlocalassistant.codebase_integrity_audit import run_codebase_integrity_audit, write_codebase_integrity_report
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore


def test_codebase_integrity_audit_runs_on_repo():
    report = run_codebase_integrity_audit(Path('.'))
    assert report.files_scanned > 0
    assert report.modules_imported > 0
    assert report.tests_detected > 0
    assert report.decision in {"pass", "warn", "block"}
    assert any("Python file" in check or "Imported" in check for check in report.passed_checks)


def test_codebase_integrity_command_is_available(tmp_path):
    config = AssistantConfig(workspace=str(Path('.').resolve()))
    app = AssistantCore(config)
    text = app.handle_command('/codebase-audit .')
    assert 'Codebase integrity decision' in text or 'Whole Codebase Integrity Audit' in text


def test_code_review_todo_scan_ignores_strings(tmp_path):
    root = tmp_path
    pkg = root / 'winlocalassistant'
    pkg.mkdir()
    (pkg / '__init__.py').write_text('', encoding='utf-8')
    (pkg / 'sample.py').write_text('''
def example():
    text = "build a todo app"
    return text
''', encoding='utf-8')
    report = run_code_review(root)
    assert not [f for f in report.findings if f.title == 'Open TODO/FIXME/HACK marker']


def test_code_review_todo_scan_flags_comments(tmp_path):
    root = tmp_path
    pkg = root / 'winlocalassistant'
    pkg.mkdir()
    (pkg / '__init__.py').write_text('', encoding='utf-8')
    (pkg / 'sample.py').write_text('''
def example():
    # TODO: tighten validation
    return 1
''', encoding='utf-8')
    report = run_code_review(root)
    assert [f for f in report.findings if f.title == 'Open TODO/FIXME/HACK marker']


def test_audit_report_filenames_do_not_collide(tmp_path):
    root = tmp_path
    pkg = root / 'winlocalassistant'
    pkg.mkdir()
    (pkg / '__init__.py').write_text('', encoding='utf-8')
    (pkg / 'sample.py').write_text('def ok():\n    return 1\n', encoding='utf-8')
    md1, js1, _ = write_code_review_report(root)
    md2, js2, _ = write_code_review_report(root)
    assert md1 != md2
    assert js1 != js2
    rmd1, rjs1, _ = write_code_repair_audit_report(root)
    rmd2, rjs2, _ = write_code_repair_audit_report(root)
    assert rmd1 != rmd2
    assert rjs1 != rjs2
    imd1, ijs1, _ = write_codebase_integrity_report(root)
    imd2, ijs2, _ = write_codebase_integrity_report(root)
    assert imd1 != imd2
    assert ijs1 != ijs2


def test_codebase_integrity_cache_invalidates_after_python_edit(tmp_path):
    root = tmp_path
    pkg = root / 'winlocalassistant'
    pkg.mkdir()
    (pkg / '__init__.py').write_text('', encoding='utf-8')
    sample = pkg / 'sample.py'
    sample.write_text('def first():\n    return 1\n', encoding='utf-8')

    first = run_codebase_integrity_audit(root)
    sample.write_text('def first():\n    return 1\n\ndef test_new_signal():\n    assert True\n', encoding='utf-8')
    second = run_codebase_integrity_audit(root)

    assert second.tests_detected == first.tests_detected + 1
    assert second.files_scanned == first.files_scanned



def test_codebase_integrity_ignores_virtualenv_and_runtime_artifacts(tmp_path):
    root = tmp_path
    pkg = root / 'winlocalassistant'
    pkg.mkdir()
    (pkg / '__init__.py').write_text('', encoding='utf-8')
    (pkg / 'sample.py').write_text('def ok():\n    return 1\n', encoding='utf-8')
    bad_venv = root / '.venv' / 'Lib' / 'site-packages' / 'broken.py'
    bad_venv.parent.mkdir(parents=True)
    bad_venv.write_text('def broken(:\n', encoding='utf-8')
    bad_runtime = root / '.nova_runtime' / 'generated.py'
    bad_runtime.parent.mkdir(parents=True)
    bad_runtime.write_text('def runtime_broken(:\n', encoding='utf-8')

    report = run_codebase_integrity_audit(root)

    assert report.files_scanned == 2
    assert not any('.venv' in issue.path or '.nova_runtime' in issue.path for issue in report.issues)
