# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: playwright/nova_runtime_usability.spec.js >> chat help drawers activity cannot cover composer
- Location: playwright/nova_runtime_usability.spec.js:25:1

# Error details

```
Test timeout of 45000ms exceeded.
```

```
Error: locator.click: Test timeout of 45000ms exceeded.
Call log:
  - waiting for locator('#novaCommandHelpButton').first()
    - locator resolved to <button type="button" class="tiny secondary" id="novaCommandHelpButton">help</button>
  - attempting click action
    2 × waiting for element to be visible, enabled and stable
      - element is not visible
    - retrying click action
    - waiting 20ms
    2 × waiting for element to be visible, enabled and stable
      - element is not visible
    - retrying click action
      - waiting 100ms
    71 × waiting for element to be visible, enabled and stable
       - element is not visible
     - retrying click action
       - waiting 500ms

```

# Page snapshot

```yaml
- generic [ref=e1]:
  - text: "? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ? ?"
  - main [ref=e2]:
    - complementary [ref=e3]:
      - generic [ref=e4]:
        - generic [ref=e5]:
          - generic [ref=e6]: ☰
          - button "● Wake listener issue to receive AI help for Nova state" [ref=e7] [cursor=pointer]:
            - generic [ref=e8]: ●
            - generic [ref=e9]: Wake listener issue to receive
            - button "AI help for Nova state" [ref=e10]: "? ?"
        - generic [ref=e11]:
          - button "＋ New Chat AI help for New Chat" [ref=e12] [cursor=pointer]:
            - generic [ref=e13]: ＋
            - generic [ref=e14]: New Chat
            - button "AI help for New Chat" [ref=e15]: "? ?"
          - button "⌕ Search / Commands AI help for Search / Commands" [ref=e16] [cursor=pointer]:
            - generic [ref=e17]: ⌕
            - generic [ref=e18]: Search / Commands
            - button "AI help for Search / Commands" [ref=e19]: "? ?"
          - button "▱ Chats › AI help for Chats" [ref=e20] [cursor=pointer]:
            - generic [ref=e21]: ▱
            - generic [ref=e22]: Chats
            - generic [ref=e23]: ›
            - button "AI help for Chats" [ref=e24]: "? ?"
          - button "▣ Projects AI help for Projects" [ref=e25] [cursor=pointer]:
            - generic [ref=e26]: ▣
            - generic [ref=e27]: Projects
            - button "AI help for Projects" [ref=e28]: "? ?"
          - button "▤ Files AI help for Files" [ref=e29] [cursor=pointer]:
            - generic [ref=e30]: ▤
            - generic [ref=e31]: Files
            - button "AI help for Files" [ref=e32]: "? ?"
          - button "⌘ Tools AI help for Tools" [ref=e33] [cursor=pointer]:
            - generic [ref=e34]: ⌘
            - generic [ref=e35]: Tools
            - button "AI help for Tools" [ref=e36]: "? ?"
          - button "⌕ Deep Research AI help for Deep Research" [ref=e37] [cursor=pointer]:
            - generic [ref=e38]: ⌕
            - generic [ref=e39]: Deep Research
            - button "AI help for Deep Research" [ref=e40]: "? ?"
          - button "◌ Voice / State AI help for Voice / State" [ref=e41] [cursor=pointer]:
            - generic [ref=e42]: ◌
            - generic [ref=e43]: Voice / State
            - button "AI help for Voice / State" [ref=e44]: "? ?"
          - button "▧ Live Activity AI help for Live Activity" [ref=e45] [cursor=pointer]:
            - generic [ref=e46]: ▧
            - generic [ref=e47]: Live Activity
            - button "AI help for Live Activity" [ref=e48]: "? ?"
          - button "▨ Output / Editor AI help for Output / Editor" [ref=e49] [cursor=pointer]:
            - generic [ref=e50]: ▨
            - generic [ref=e51]: Output / Editor
            - button "AI help for Output / Editor" [ref=e52]: "? ?"
          - button "∞ Workbench AI help for Workbench" [ref=e53] [cursor=pointer]:
            - generic [ref=e54]: ∞
            - generic [ref=e55]: Workbench
            - button "AI help for Workbench" [ref=e56]: "? ?"
        - generic [ref=e57]:
          - button "✓ Doctor AI help for Doctor" [ref=e58] [cursor=pointer]:
            - generic [ref=e59]: ✓
            - generic [ref=e60]: Doctor
            - button "AI help for Doctor" [ref=e61]: "? ?"
          - button "⚙ Settings AI help for Settings" [ref=e62] [cursor=pointer]:
            - generic [ref=e63]: ⚙
            - generic [ref=e64]: Settings
            - button "AI help for Settings" [ref=e65]: "? ?"
          - button "◐ Theme AI help for Theme" [ref=e66] [cursor=pointer]:
            - generic [ref=e67]: ◐
            - generic [ref=e68]: Theme
            - button "AI help for Theme" [ref=e69]: "? ?"
        - generic [ref=e70]:
          - generic [ref=e71]: "N"
          - generic [ref=e72]: local
          - button "⚙ AI help for ⚙" [ref=e73] [cursor=pointer]:
            - text: ⚙
            - button "AI help for ⚙" [ref=e74]: "??"
    - generic [ref=e75]:
      - generic [ref=e76]:
        - generic [ref=e77]: Nova v55.3.164
        - generic [ref=e78]: CYBERPUNK
        - generic [ref=e79]: Nova local model
        - generic [ref=e80]: 02:58 AM
        - generic [ref=e81]: · 1 msgs
        - generic [ref=e82]: idle
        - generic [ref=e83]:
          - button "clean AI help for clean" [ref=e84] [cursor=pointer]:
            - text: clean
            - button "AI help for clean" [ref=e85]: "? ?"
          - button "focus AI help for Close drawers and restore the chat canvas" [ref=e86] [cursor=pointer]:
            - text: focus
            - button "AI help for Close drawers and restore the chat canvas" [ref=e87]: "? ?"
          - button "routes AI help for Check backend command routes" [ref=e88] [cursor=pointer]:
            - text: routes
            - button "AI help for Check backend command routes" [ref=e89]: "? ?"
          - button "layout AI help for Check visible GUI drawer/chat geometry" [ref=e90] [cursor=pointer]:
            - text: layout
            - button "AI help for Check visible GUI drawer/chat geometry" [ref=e91]: "? ?"
          - button "reset UI AI help for Reset drawer/chat layout state and clear stale Nova browser cache/service worker without deleting project data" [ref=e92] [cursor=pointer]:
            - text: reset UI
            - button "AI help for Reset drawer/chat layout state and clear stale Nova browser cache/service worker without deleting project data" [ref=e93]: "? ?"
          - button "build AI help for Show patch/build identity so stale folders are obvious" [ref=e94] [cursor=pointer]:
            - text: build
            - button "AI help for Show patch/build identity so stale folders are obvious" [ref=e95]: "? ?"
          - button "commands AI help for commands" [ref=e96] [cursor=pointer]:
            - text: commands
            - button "AI help for commands" [ref=e97]: "? ?"
          - button "files AI help for files" [ref=e98] [cursor=pointer]:
            - text: files
            - button "AI help for files" [ref=e99]: "? ?"
          - button "activity AI help for activity" [ref=e100] [cursor=pointer]:
            - text: activity
            - button "AI help for activity" [ref=e101]: "? ?"
          - text: "?"
      - text: "? ? ? ? ? ? ? ? ? ? ? ? ? ? ... ..."
      - generic [ref=e102]:
        - generic [ref=e103]: "Provider: Local default"
        - generic [ref=e104]: "Advanced local: vLLM / SGLang / llama.cpp"
        - generic [ref=e105]: "Remote long-context: SubQ / NVIDIA NIM only with permission"
        - generic [ref=e106]: "Queue: per provider/model receipts"
        - button "Provider status" [ref=e107] [cursor=pointer]
        - button "Route explain" [ref=e108] [cursor=pointer]
        - button "Queue" [ref=e109] [cursor=pointer]
      - text: ... ... ... ... ... ... ... ... ... ... ...
      - generic [ref=e110]:
        - generic [ref=e111]:
          - heading "Nova" [level=1] [ref=e112]
          - paragraph [ref=e113]: Local AI workspace. Chat stays centred; projects, tools, voice, activity and output open as drawers instead of covering the whole screen.
          - generic [ref=e114]:
            - button "Build app" [ref=e115] [cursor=pointer]
            - button "Status" [ref=e116] [cursor=pointer]
            - button "Test checklist" [ref=e117] [cursor=pointer]
            - button "Projects" [ref=e118] [cursor=pointer]
        - generic [ref=e119]: "{\"reply\":\"Hi — Nova is responsive. If the local model is slow, I can still use deterministic commands right now.\\n\\nUseful quick checks:\\n- `/llm-status` to see whether Ollama/model calls are stuck.\\n- `/command-help code` for code/write/run commands.\\n- `/files` to inspect the workspace.\\n- `/code QUESTION` for coding help.\\n- `/verify python --version` to confirm command execution works.\",\"command_suggestions\":[{\"label\":\"LLM status\",\"command\":\"/llm-status\",\"reason\":\"Check whether Nova is actively prompting or Ollama is only loaded/stopping.\",\"risk\":\"low\",\"category\":\"llm\"},{\"label\":\"Interrupt current\",\"command\":\"/interrupt-current --confirm\",\"reason\":\"Stop a broken active Nova model request after review.\",\"risk\":\"medium\",\"category\":\"llm\"},{\"label\":\"Stop Ollama\",\"command\":\"/ollama-stop --confirm\",\"reason\":\"Unload a stale/stuck Ollama model after confirming no prompt should be running.\",\"risk\":\"medium\",\"category\":\"llm\"}]}"
      - generic [ref=e120]:
        - text: NOVA // CYBERPUNK CONTROL LINK
        - generic [ref=e121]:
          - button "+" [ref=e122] [cursor=pointer]
          - textbox "Ask Nova, attach files with +, or choose a mode such as research, image, Linux sandbox, or autonomous build." [active] [ref=e123]: hi
          - button "🎙️" [ref=e124] [cursor=pointer]
          - button "Send" [ref=e125] [cursor=pointer]
      - text: resize activity
  - dialog "Nova docked left drawer":
    - generic:
      - generic: Nova tools
      - generic: Projects, files, tools and commands stay here.
      - button "×"
    - generic:
      - generic:
        - heading "Odysseus-style apps mapped to Nova" [level=3]
        - generic:
          - generic:
            - text: Chat
            - button "New chat"
          - generic:
            - text: Deep research
            - button "Fill research"
          - generic:
            - text: Compare
            - button "Fill compare"
          - generic:
            - text: Cookbook
            - button "Workbench"
          - generic:
            - text: Library/files
            - button "Open files"
          - generic:
            - text: Voice/state
            - button "Open voice"
          - generic:
            - text: Activity
            - button "Dock activity"
          - generic:
            - text: Theme
            - button "Customize"
      - generic:
        - generic: Left panel
        - generic: Control Centre
        - generic:
          - button "Reset layout"
          - button "Hide"
      - generic: Quick controls
      - generic: Customisable shortcuts. Edit these to match your usual workflow.
      - generic:
        - button "Edit quick commands"
        - button "Reset quick commands"
        - button "Enable audio"
        - button "New chat"
      - generic:
        - generic:
          - generic:
            - button "Avatar"
            - button "Activity"
            - button "LLM status"
            - button "Fast app"
            - button "Long bug tracker"
            - button "Projects"
            - button "Test all"
            - button "Nova full test"
            - button "Completion audit"
            - button "Doctor"
            - button "Integration radar"
            - button "Release gate"
            - button "Massive system test"
            - button "Validation matrix"
            - button "Dependency check"
            - button "Release checklist"
            - button "Codebase advisor"
            - button "Release package"
            - button "Playwright scaffold"
            - button "Persona"
            - button "Model optimiser"
            - button "Voice audit"
            - button "Docker status"
            - button "Docker quick validate"
            - button "Sandbox status"
            - button "Less strict"
            - button "Research topic"
            - button "DB list"
            - button "Research DB schema"
            - button "DB merge"
            - button "Memory"
            - button "Receipts"
            - button "Role router"
            - button "Jarvis bridge"
            - button "Jarvis status"
            - button "Jarvis doctor"
            - button "Sidecar policy"
            - button "Sidecar preflight"
            - button "Workflow blueprint"
            - button "Bridge receipts"
            - button "Browser harness"
            - button "Jarvis test prompts"
            - button "Project memory"
            - button "Remember project"
            - button "Self guide"
            - button "New chat"
            - button "List chats"
            - button "Search chats"
            - button "Security watch"
            - button "Image setup"
            - button "Project target check"
      - separator
      - generic: Command Launcher
      - textbox "Search commands or type a goal"
      - generic:
        - generic:
          - text: Quick app
          - generic: Build
          - generic: Small project with basic checks
          - code: /fast make a tiny useful app
          - generic:
            - button "Fill input"
        - generic:
          - text: Full project
          - generic: Build
          - generic: Staged project workflow
          - code: /long make a useful local app with search, filters, local saving, JSON export and example data
          - generic:
            - button "Fill input"
        - generic:
          - text: Video plan
          - generic: Video
          - generic: Plan script, scenes, shots, audio and edit manifest
          - code: /video-plan 10 second cinematic trailer about Nova building a project
          - generic:
            - button "Fill input"
        - generic:
          - text: Video status
          - generic: Video
          - generic: Check FFmpeg, Node, ComfyUI and fallback video readiness
          - code: /video-status
          - generic:
            - button "Fill input"
        - generic:
          - text: Video validate
          - generic: Video
          - generic: Plan and validate a Nova video manifest before rendering
          - code: /video-validate 10 second cinematic trailer about Nova building a project
          - generic:
            - button "Fill input"
        - generic:
          - text: Continuous autonomous
          - generic: Autonomous
          - generic: Keep autonomous mode iterating after verified milestones until you stop it
          - code: /autonomous start --continuous improve Nova safely and keep choosing the next verified improvement
          - generic:
            - button "Fill input"
        - generic:
          - text: Safe subagents
          - generic: Autonomous
          - generic: Plan deterministic subagents while serialising local model calls
          - code: /subagents improve Nova without regressions
          - generic:
            - button "Fill input"
        - generic:
          - text: Authority controls
          - generic: Settings
          - generic: Show internet, mutation and shell gates before granting access
          - code: /authority-mode
          - generic:
            - button "Fill input"
      - separator
      - generic: Idle Self-Improvement
      - generic: Checking idle reports...
      - separator
      - generic: Local LLM status
      - generic: Checking Ollama...
      - generic: Recent local model context will appear here.
      - button "LLM status in chat"
      - button "Interrupt task"
      - button "Stop Ollama model"
      - separator
      - generic: Projects
      - generic: Projects are stored separately and can be reopened later.
      - generic:
        - textbox "Project name"
        - button "New"
      - generic:
        - button "Refresh projects"
        - button "Select all"
        - button "Clear"
        - button "Delete selected"
      - generic:
        - generic: Project files
        - generic: Open, download and zip project files from the left. The right inspector shows the selected file and before/after output.
        - generic:
          - button "Refresh files"
          - button "Zip project"
      - separator
      - generic: AI Toolbox
      - generic: Custom tools are separate from projects. The agent can create and run these when helpful.
      - generic:
        - textbox "Tool idea, e.g. count TODO comments"
        - button "Create"
      - generic:
        - textbox "Tool name"
        - 'textbox "Args: {text} or {\"text\":\"hello\"}"'
        - button "Run tool"
      - 'textbox "Pipeline JSON, e.g. [{\"tool\":\"tool_run\",\"args\":{\"name\":\"html_reference_checker\",\"args\":{\"subdir\":\".\"}}}]"'
      - generic:
        - button "Refresh tools"
        - button "Run pipeline"
        - button "Tool help"
        - button "Topic watchers"
      - separator
      - generic: Workspace
      - textbox "C:\\Users\\Daniel\\Documents\\Projects"
      - button "Set workspace"
      - paragraph: "Best: use a project folder, not your whole user folder."
  - button "fix UI" [ref=e126] [cursor=pointer]
```

# Test source

```ts
  1  | const { test, expect } = require('@playwright/test');
  2  | 
  3  | const baseURL = process.env.NOVA_TEST_BASE_URL || 'http://127.0.0.1:8766';
  4  | 
  5  | async function composerIsUsable(page) {
  6  |   const input = page.locator('#msg');
  7  |   await expect(input).toBeVisible();
  8  |   await input.click();
  9  |   await input.fill('what can you do?');
  10 |   const value = await input.inputValue();
  11 |   expect(value).toContain('what can you do');
  12 |   const box = await input.boundingBox();
  13 |   expect(box).toBeTruthy();
  14 |   const topElement = await page.evaluate(({x,y}) => {
  15 |     const el = document.elementFromPoint(x, y);
  16 |     return el ? { id: el.id, tag: el.tagName, classes: el.className } : null;
  17 |   }, { x: box.x + Math.min(20, box.width / 2), y: box.y + Math.min(10, box.height / 2) });
  18 |   expect(topElement).toBeTruthy();
  19 | }
  20 | 
  21 | function overlaps(a, b) {
  22 |   return a && b && a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y;
  23 | }
  24 | 
  25 | test('chat help drawers activity cannot cover composer', async ({ page }, testInfo) => {
  26 |   const html = await fetch(baseURL).then(r => r.text());
  27 |   await page.setContent(html, { waitUntil: 'domcontentloaded' });
  28 |   const input = page.locator('#msg');
  29 |   await expect(input).toBeVisible();
  30 |   await input.fill('hi');
  31 |   const chatResponse = await fetch(baseURL + '/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: 'hi' }) }).then(r => r.json());
  32 |   expect(chatResponse.reply || chatResponse.ok).toBeTruthy();
  33 |   const chatText = JSON.stringify(chatResponse);
  34 |   expect(chatText).toMatch(/Nova|Hi|hello|chat/i);
  35 |   await page.evaluate((text) => {
  36 |     const chat = document.querySelector('#chat, .chat, .messages');
  37 |     if (chat) { const div = document.createElement('div'); div.className = 'msg'; div.textContent = text; chat.appendChild(div); }
  38 |   }, chatText);
  39 | 
  40 |   const help = page.locator('#novaCommandHelpButton').first();
  41 |   if (await help.count()) {
> 42 |     await help.click();
     |                ^ Error: locator.click: Test timeout of 45000ms exceeded.
  43 |     await expect(page.locator('#novaCommandHelpOverlay')).toBeVisible();
  44 |     await page.locator('#novaCommandHelpSearch').fill('code');
  45 |     await expect(page.locator('#novaCommandHelpOverlay')).toContainText('/code');
  46 |     await page.locator('#novaCommandHelpOverlay button:has-text("Close")').click();
  47 |   }
  48 | 
  49 |   await page.evaluate(() => {
  50 |     const activity = document.getElementById('liveActivityPanel');
  51 |     if (activity) activity.classList.remove('is-minimized', 'collapsed', 'hidden');
  52 |     document.body.classList.add('orbit-open', 'orbit-drawer-open', 'nova-interaction-overhaul-v1');
  53 |     const drawer = document.getElementById('orbitDrawer');
  54 |     if (drawer) drawer.style.display = 'block';
  55 |     const right = document.getElementById('orbitRightDrawer');
  56 |     if (right) right.style.display = 'block';
  57 |     if (window.NovaInteractionOverhaul?.scanPanels) window.NovaInteractionOverhaul.scanPanels();
  58 |   });
  59 | 
  60 |   await composerIsUsable(page);
  61 |   const inputBox = await input.boundingBox();
  62 |   const panels = await page.locator('#liveActivityPanel, #orbitDrawer, #orbitRightDrawer').evaluateAll(nodes => nodes.map(n => {
  63 |     const style = getComputedStyle(n);
  64 |     const r = n.getBoundingClientRect();
  65 |     return { id: n.id, visible: style.display !== 'none' && style.visibility !== 'hidden' && r.width > 0 && r.height > 0, x: r.x, y: r.y, width: r.width, height: r.height };
  66 |   }));
  67 |   for (const panel of panels.filter(p => p.visible)) {
  68 |     expect(overlaps(inputBox, panel), `${panel.id} overlaps composer`).toBeFalsy();
  69 |   }
  70 |   await page.screenshot({ path: 'logs/runtime_usability_playwright.png', fullPage: true });
  71 | });
  72 | 
```