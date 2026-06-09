# Nova v55.3.144 patch summary

Focus: Orbit live-activity, voice cue, project-routing and readability hotfix.

## Fixed
- Routed broad project-library review requests to project inspection/QA instead of new app generation.
- Routed explicit functionality-validation follow-ups to QA mode instead of `ai_create_project`.
- Added visible message timestamps and collapsed terminal/evidence indicators for assistant replies.
- Opened/polled Live Activity immediately while Nova is working so long tasks show progress before completion.
- Improved Live Activity contrast for dark Orbit mode.
- Reduced redundant voice/transcript sub-panel spam while keeping full traces in the Voice/State drawer.
- Made the Hey Nova ready cue more visible and added browser-audio unlock/fallback status.
- Tightened spoken summaries so Nova reads only useful short status, not IDs, JSON, logs or long technical details.
- Updated service-worker/cache-busting markers so the new Orbit shell loads on first open/refresh.

## Validation targets
- Startup validation quick gate.
- Doctor/release hygiene.
- Command verifier.
- Bug review and regression sweep.
- Dedicated v55.3.144 GUI/routing regression tests.
