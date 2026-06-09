# GUI Cockpit v2 Preview

Mode: `gui-feature-coverage`
Classic preserved: **True**

## Layout
- **left**: Chat, Projects, Build, Validate, Repair, Sandbox, Autonomous, Research, Memory, Settings
- **center**: Prompt, Plan, Candidate, Files, Validation, Final Output
- **right**: Model status, Current trace, Autonomous state, Warnings, Next best action
- **bottom**: Attach, Mic, Mic test, Send, Model progress

## Regression rules
- classic mode remains default
- every classic feature mapped before cockpit default
- run /gui-regression-test and /gui-visual-test before default switch