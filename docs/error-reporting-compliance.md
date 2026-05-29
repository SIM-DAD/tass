# TASS — Error-Reporting Policy Compliance

Tracks TASS against the SIM DAD LLC Error-Reporting Policy
(`C:/life-os/llc/policies/error-reporting-policy.md`), section 10 checklist.

Status: 2026-05-29. Rewrote the homegrown SMTP reporter into the policy's
manual-submit, three-touchpoint `mailto:` flow.

## Checklist (policy section 10)

- [x] **Top-level exception handler installed.** `sys.excepthook` in
  `app.py:42` routes unhandled exceptions to `LiveCrashDialog` (touchpoint B).
- [ ] **Process-init crash dumper for segfault / hard-kill.** Deferred. A
  C-level segfault or OOM-kill cannot run the live dialog and cannot be turned
  into a section-4 schema report from Python. Touchpoint C still surfaces any
  report queued before the process died, but a hard kill that occurs before
  the Python handler runs leaves nothing to queue. Acceptable for v1.0: the
  dominant TASS crash class is Python exceptions, which the excepthook path
  fully covers. Candidate follow-up: `faulthandler.enable()` to a log file as
  a diagnostic-only aid (not a substitute for the schema'd report).
- [x] **Report-builder produces the section 4 schema and only that.**
  `services/error_reporter.py` `CrashReport` dataclass + `build_report()`.
  GPU fields (4.2) intentionally omitted — TASS does not use the GPU.
- [x] **Traceback redactor.** `error_reporter.redact_paths()` strips absolute
  paths (Windows drive, UNC, POSIX home) and reduces traceback frames to
  `<redacted-path>/<filename>`. Runs inside `build_report()` before render.
- [x] **Queue directory at the platform-appropriate path.**
  `%LOCALAPPDATA%\TASS\crash-queue\` via `platformdirs.user_data_dir`.
  Filename `YYYYMMDD-HHMMSS-<sha1prefix>.json`.
- [x] **Three dialogs (A, B, C).** `ui/crash_dialogs.py`:
  `FirstLaunchPrefDialog`, `LiveCrashDialog`, `PostRestartDialog`. Wired in
  `app.py` (`_launch` shows A once + C if queued reports exist; the excepthook
  shows B).
- [x] **Settings → Privacy panel.** `ui/settings_dialog.py` exposes
  `prompt_on_crash`, `queue_on_crash`, `remind_post_restart` plus a
  "View queued reports…" manager (`QueuedReportsDialog`).
- [x] **`mailto:` composer addresses the per-product inbox.**
  `error_reporter.compose_mailto()` → `support+tass@simdadllc.com`.
- [x] **No SMTP credentials, no third-party SDKs, no telemetry.** The SMTP
  path and the bundled `smtplib`/`EmailMessage` reporter were removed entirely.
- [x] **Privacy page includes the section 8 language.** `tass-web/privacy.html`
  section 3 corrected (it previously claimed "no crash reporting") + an
  "Error reports" disclosure added.
- [x] **EULA includes the section 9 clause.** `tass-web/eula.html` section 7.
- [ ] **Smoke test.** Automated service-layer tests pass
  (`tests/test_error_reporter.py`, 10 cases: schema, redaction, mailto, queue).
  Manual GUI smoke (raise an exception in a running build, confirm the dialog
  renders, confirm the mail client opens pre-populated, confirm no network
  traffic occurs without the Send click) is PENDING an owner click-through on
  the next build.

## Files changed

- `services/error_reporter.py` — full rewrite (SMTP → mailto: + report builder
  + redactor + queue).
- `ui/crash_dialogs.py` — new (touchpoints A/B/C + queued-reports manager).
- `ui/settings_dialog.py` — Privacy panel.
- `app.py` — excepthook routes to `LiveCrashDialog`; `_launch` shows A + C.
- `tests/test_error_reporter.py` — new.
- `tass-web/privacy.html`, `tass-web/eula.html` — section 8 / section 9 language.
