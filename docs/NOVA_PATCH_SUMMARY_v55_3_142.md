# Nova v55.3.142 Orbit workspace drawer hotfix

This patch responds to GUI usability feedback from the Odysseus-inspired shell. It keeps backend routes and IDs stable while changing the presentation layer so panels dock and reserve space instead of covering the chat.

## Implemented

- Chats now open in a docked drawer panel, not the old floating popup.
- Left and right drawers toggle open/closed and shrink the chat area when open.
- Live Activity docks inside the chat column rather than covering the conversation.
- A mini Nova orb beside the top-left logo shows ready/listening/thinking/speaking state.
- Hey Nova now plays a stronger three-note ready cue when the wake word is accepted.
- Voice/wake replies can speak again without depending on a hidden audio button state.
- Theme opens a colour customizer for primary, secondary, background, panel, text and chat width settings.
- Odysseus-style app cards map existing Nova capabilities to Chat, Deep Research, Compare, Cookbook, Library/Files, Voice/State, Activity and Theme.

## Safety boundary

The patch is GUI/browser-side except for release metadata and tests. No shell execution, auto-apply, file mutation policy, project deletion, Jarvis/sidecar authority, or model routing permissions were broadened.
