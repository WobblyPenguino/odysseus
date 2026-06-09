# Nova v55.3.164 Scheduling Control Plane

Nova now includes a safe local scheduler control plane inspired by the supplied scheduling architecture report.

## Implemented

- `/schedule-task TEXT [=> WHEN]` creates local scheduled task records.
- `/schedule-status [STATUS]` lists local scheduler records.
- `/schedule-confirm TASK_ID` confirms medium/high-risk tasks.
- `/schedule-cancel TASK_ID` cancels tasks.
- `/task-decompose TEXT` builds a validated DAG/subtask plan.
- `/scheduling-audit` verifies sanitizer, confirmation, retry/backoff and DAG controls.

## Safety model

The scheduler stores and validates tasks; it does not run arbitrary shell commands. User text is treated as data, prompt-injection patterns are blocked, medium/high-risk tasks require confirmation, and all changes create local audit events.

## Validation

Run:

```powershell
python -m pytest -q tests_nova_scheduler_v55_3_164.py
python -m winlocalassistant.validate --all
python app.py /version
```
