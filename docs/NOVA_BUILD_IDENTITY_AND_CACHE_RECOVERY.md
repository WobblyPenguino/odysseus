# Nova Build Identity and Cache Recovery

Nova keeps the compatibility version `55.3.164` across several safe patches. That preserves launchers and old tests, but it can make a stale browser/server look like the newest patch.

Use these checks when debugging GUI or backend mismatch problems:

```text
/build-info
/gui-layout-status
/validation-status
```

The GUI header also includes a `build` button. `/api/version` and `/api/build-info` return the same patch ID and source fingerprint.

## Browser reset

Click `reset UI`. It clears layout-only localStorage keys, Nova shell caches and old service-worker registrations. It does not delete project files, memory, logs, remote profiles or custom tools.

Expected current Patch ID:

```text
gui-reset-adaptive-routing-build-identity-v1
```
