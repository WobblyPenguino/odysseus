from __future__ import annotations

import json

from .command_help import COMMANDS

"""GUI interaction fixes for Nova.

This layer is browser/UI-only. It fixes panel stacking, help dots, live activity
stability, chat code blocks, local model status and autonomous visibility
without changing backend tool routes.
"""

INTERACTION_OVERHAUL_CSS = r"""
/* v55.3.164 interaction overhaul v1: panel safety, live activity stability, clean help dots. */
body.nova-orbit-shell.nova-interaction-overhaul-v1{--nova-composer-safe:118px!important;--nova-panel-gap:14px!important;}
body.nova-orbit-shell.nova-interaction-overhaul-v1 #orbitRightDrawer,
body.nova-orbit-shell.nova-interaction-overhaul-v1 #orbitRightDrawer *,
body.nova-orbit-shell.nova-interaction-overhaul-v1 .rightbar,
body.nova-orbit-shell.nova-interaction-overhaul-v1 .rightbar *{filter:none!important;backdrop-filter:none!important;-webkit-backdrop-filter:none!important;}
body.nova-orbit-shell.nova-interaction-overhaul-v1 #orbitRightDrawer{background:linear-gradient(180deg,rgba(8,10,16,.98),rgba(7,8,12,.98))!important;}
body.nova-orbit-shell.nova-interaction-overhaul-v1 .rightbar.card{opacity:1!important;}
#novaMicListenerStatus,#novaModelStatusMini{border:1px solid rgba(62,242,255,.28)!important;background:rgba(5,8,14,.86)!important;color:#dffbff!important;border-radius:14px!important;padding:8px 10px!important;margin:8px 0!important;font-size:12px!important;box-shadow:0 0 18px rgba(62,242,255,.08)!important;}
#novaMicListenerStatus b,#novaModelStatusMini b{color:#f5e642!important;text-transform:uppercase;letter-spacing:.08em;}
#novaMicListenerStatus .state,#novaModelStatusMini .state{display:inline-block;border-radius:999px;padding:2px 7px;margin-left:6px;background:rgba(62,242,255,.12);border:1px solid rgba(62,242,255,.24);}
body.nova-orbit-shell.nova-interaction-overhaul-v1 .activity,
body.nova-orbit-shell.nova-interaction-overhaul-v1 #liveActivityPanel{position:fixed!important;left:calc(var(--orbit-left,208px) + 18px)!important;right:18px!important;bottom:calc(var(--nova-composer-safe) + 10px)!important;width:auto!important;max-width:calc(100vw - var(--orbit-left,208px) - 36px)!important;height:clamp(190px,34vh,430px)!important;max-height:calc(100vh - 210px)!important;min-height:120px!important;overflow:hidden!important;resize:both!important;z-index:210!important;border-radius:18px!important;background:linear-gradient(180deg,rgba(8,10,16,.98),rgba(7,7,12,.98))!important;border:1px solid rgba(245,230,66,.20)!important;box-shadow:0 20px 80px rgba(0,0,0,.52),0 0 32px rgba(245,230,66,.08)!important;contain:layout paint!important;}
body.nova-orbit-shell.nova-interaction-overhaul-v1 .activity.is-minimized,
body.nova-orbit-shell.nova-interaction-overhaul-v1 #liveActivityPanel.is-minimized{height:48px!important;min-height:48px!important;resize:none!important;}
body.nova-orbit-shell.nova-interaction-overhaul-v1 .activity #activityLog,
body.nova-orbit-shell.nova-interaction-overhaul-v1 #liveActivityPanel #activityLog{height:calc(100% - 58px)!important;overflow:auto!important;scroll-behavior:smooth!important;padding-right:8px!important;}
body.nova-orbit-shell.nova-interaction-overhaul-v1 .activityHead,
body.nova-orbit-shell.nova-interaction-overhaul-v1 #liveActivityPanel .activityHead{position:sticky!important;top:0!important;z-index:3!important;background:linear-gradient(180deg,rgba(9,11,16,.98),rgba(9,11,16,.92))!important;border-bottom:1px solid rgba(245,230,66,.22)!important;cursor:move!important;}
body.nova-orbit-shell.nova-interaction-overhaul-v1 .run{overflow:hidden!important;}
body.nova-orbit-shell.nova-interaction-overhaul-v1 .run summary{min-height:36px!important;}
body.nova-orbit-shell.nova-interaction-overhaul-v1 .runbody{max-height:280px!important;overflow:auto!important;}
body.nova-orbit-shell.nova-interaction-overhaul-v1 .composer{z-index:260!important;}
body.nova-orbit-shell.nova-interaction-overhaul-v1 .novaAiHelpDot{width:11px!important;height:11px!important;min-width:11px!important;min-height:11px!important;font-size:7px!important;top:-4px!important;right:-4px!important;opacity:.34!important;background:rgba(245,230,66,.14)!important;color:#fff48a!important;border-color:rgba(245,230,66,.32)!important;box-shadow:0 0 8px rgba(245,230,66,.16)!important;}
body.nova-orbit-shell.nova-interaction-overhaul-v1 .novaAiHelpDot:hover,body.nova-orbit-shell.nova-interaction-overhaul-v1 .novaAiHelpDot:focus{opacity:.94!important;}
body.nova-orbit-shell.nova-interaction-overhaul-v1 button,body.nova-orbit-shell.nova-interaction-overhaul-v1 .orbitNavButton{position:relative!important;}
body.nova-orbit-shell.nova-interaction-overhaul-v1 button{padding-right:14px!important;}
.novaPanelResizeHandle{position:absolute!important;right:3px!important;bottom:3px!important;width:16px!important;height:16px!important;cursor:nwse-resize!important;z-index:999!important;opacity:.55!important;background:linear-gradient(135deg,transparent 0 45%,rgba(245,230,66,.9) 48% 58%,transparent 62%),linear-gradient(135deg,transparent 0 65%,rgba(62,242,255,.7) 68% 78%,transparent 82%)!important;}
.novaMovablePanel{position:fixed!important;}
.msgNav{display:inline-flex!important;gap:3px!important;margin-left:6px!important;vertical-align:middle!important;}
.msgNav button{padding:1px 5px!important;border-radius:7px!important;font-size:10px!important;line-height:1.2!important;opacity:.62!important;background:rgba(62,242,255,.08)!important;border:1px solid rgba(62,242,255,.20)!important;color:#dffbff!important;}
.msgNav button:hover,.msgNav button:focus{opacity:1!important;}
.novaCodeBox{position:relative!important;margin:10px 0!important;border:1px solid rgba(62,242,255,.24)!important;border-radius:14px!important;overflow:hidden!important;background:#040609!important;}
.novaCodeBoxHeader{display:flex!important;justify-content:space-between!important;gap:10px!important;align-items:center!important;background:rgba(245,230,66,.08)!important;color:#fff48a!important;border-bottom:1px solid rgba(245,230,66,.18)!important;padding:5px 8px!important;font-size:11px!important;text-transform:uppercase!important;letter-spacing:.06em!important;}
.novaCodeBox pre{margin:0!important;padding:11px!important;max-height:52vh!important;overflow:auto!important;background:#040609!important;color:#dffbff!important;white-space:pre!important;}
.novaCodeCopy{font-size:10px!important;padding:3px 7px!important;}
.novaCommandHelpOverlay,.novaAutonomousGuardOverlay{position:fixed!important;inset:0!important;z-index:9900!important;display:none;align-items:center;justify-content:center;padding:22px!important;background:rgba(0,0,0,.58)!important;}
.novaCommandHelpPanel,.novaAutonomousGuardPanel{width:min(960px,calc(100vw - 44px))!important;max-height:86vh!important;overflow:auto!important;border-radius:20px!important;padding:16px!important;background:linear-gradient(180deg,rgba(8,10,16,.98),rgba(9,11,17,.98))!important;color:#e8ffff!important;border:1px solid rgba(245,230,66,.28)!important;box-shadow:0 30px 120px rgba(0,0,0,.72)!important;}
.novaCommandGrid{display:grid!important;grid-template-columns:repeat(auto-fit,minmax(250px,1fr))!important;gap:10px!important;}
.novaCommandGrid details{border:1px solid rgba(62,242,255,.20)!important;border-radius:12px!important;padding:8px!important;background:rgba(62,242,255,.04)!important;}
.novaCommandGrid summary{cursor:pointer!important;color:#fff48a!important;font-weight:800!important;}
.novaRichCard{border:1px solid rgba(62,242,255,.22);border-radius:14px;padding:10px;margin:8px 0;background:rgba(62,242,255,.05);}
.novaRichCard b{color:#fff48a;display:block;margin-bottom:5px;}
body.nova-autonomous-guard-active .chat-wrap,body.nova-autonomous-guard-active .sidebar.card,body.nova-autonomous-guard-active #orbitDrawer,body.nova-autonomous-guard-active #orbitRightDrawer{filter:grayscale(.35) brightness(.55)!important;}
"""

INTERACTION_OVERHAUL_JS = r"""
<script>
window.NovaInteractionOverhaul = window.NovaInteractionOverhaul || {version:'v55.3.164-interaction-overhaul-v1', patchId:'gui-autonomous-interaction-fix-v1'};
(function(){
  const SAFE_COMMANDS = __NOVA_COMMANDS_JSON__;
  function esc(s){return String(s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
  function postCommand(cmd){try{const msg=document.getElementById('msg'); if(msg){msg.value=cmd;} if(typeof send==='function') return send(); return fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:cmd})});}catch(e){console.warn(e);}}
  function ensureTopButton(id,label,fn){if(document.getElementById(id))return;const holder=document.querySelector('.topbar .row,.smartActions,.topbar')||document.body;const b=document.createElement('button');b.id=id;b.className='tiny secondary';b.textContent=label;b.type='button';b.onclick=fn;holder.appendChild(b);}
  function ensureStatusBoxes(){const target=document.querySelector('#orbitNav,.sidebar.card,.rightbar.card,#orbitRightDrawer .orbitDrawerBody')||document.body;if(!document.getElementById('novaMicListenerStatus')){const box=document.createElement('div');box.id='novaMicListenerStatus';box.innerHTML='<b>Mic / Listener</b> <span class="state">checking</span><div class="small">Waiting for browser microphone and wake-listener state.</div>';target.appendChild(box);}if(!document.getElementById('novaModelStatusMini')){const box=document.createElement('div');box.id='novaModelStatusMini';box.innerHTML='<b>Local model</b> <span class="state">checking</span><div class="small">Polling Ollama status without blocking UI.</div>';target.appendChild(box);}}
  function updateMicStatus(){const box=document.getElementById('novaMicListenerStatus'); if(!box)return;let state='unavailable', detail='Browser has not granted microphone access or devices cannot be enumerated.';try{const voice=String(document.querySelector('.voiceStatus,#voiceStatus,#rightVoiceStatus')?.textContent||'').trim();const listening=!!document.querySelector('.voiceBtn.listening,.listening');if(listening){state='listening'; detail='Wake/listener UI indicates active listening.';}else if(/disabled|unavailable|cannot enumerate|denied|blocked/i.test(voice)){state='disabled'; detail=voice || detail;}else if(/ready|wake/i.test(voice)){state='waiting'; detail=voice;}else if(voice){state='idle'; detail=voice;}}catch(e){state='error'; detail=String(e);}box.innerHTML='<b>Mic / Listener</b> <span class="state">'+esc(state)+'</span><div class="small">'+esc(detail)+'</div>';}
  async function updateModelMini(){const box=document.getElementById('novaModelStatusMini'); if(!box)return;try{const r=await fetch('/api/llm-status',{cache:'no-store'}); const j=await r.json(); const d=j.data||{}; const lock=d.winlocalassistant_model_lock||{};const busy=!!(lock.busy||lock.prompt_active); const status=!j.ok?'unavailable':(busy?'running':'idle');const models=(d.active_models||d.installed_models||[]); const active=(models[0]&&String(models[0].name||models[0].model||''))||d.chat_model||d.model||'local model';let extra=busy?('Active request: '+(lock.busy_desc||'local model prompt')):('Model: '+active);if(d.raw)extra+=' · '+String(d.raw).split('\n')[0].slice(0,90);box.innerHTML='<b>Local model</b> <span class="state">'+esc(status)+'</span><button class="tiny secondary" type="button" onclick="window.NovaInteractionOverhaul.updateModelMini()">Refresh</button><div class="small">'+esc(extra)+'</div>';}catch(e){box.innerHTML='<b>Local model</b> <span class="state">offline</span><div class="small">Ollama/API status unavailable: '+esc(e)+'</div>';}}
  function addMessageNav(){document.querySelectorAll('.msg .name:not([data-nav-ready="1"])').forEach(name=>{name.dataset.navReady='1';const nav=document.createElement('span');nav.className='msgNav';nav.innerHTML='<button type="button" aria-label="Previous message">↑</button><button type="button" aria-label="Next message">↓</button>';nav.children[0].onclick=()=>{const msg=name.closest('.msg');let p=msg&&msg.previousElementSibling;while(p&&!p.classList.contains('msg'))p=p.previousElementSibling;if(p)p.scrollIntoView({behavior:'smooth',block:'center'});};nav.children[1].onclick=()=>{const msg=name.closest('.msg');let n=msg&&msg.nextElementSibling;while(n&&!n.classList.contains('msg'))n=n.nextElementSibling;if(n)n.scrollIntoView({behavior:'smooth',block:'center'});};name.appendChild(nav);});}
  function enhanceCodeBlocks(){document.querySelectorAll('.bubble pre.codeblock:not([data-codebox-ready="1"]),.bubble pre.jsonblock:not([data-codebox-ready="1"])').forEach(pre=>{pre.dataset.codeboxReady='1';const wrapper=document.createElement('div');wrapper.className='novaCodeBox';const lang=pre.classList.contains('jsonblock')?'json':'code';const header=document.createElement('div');header.className='novaCodeBoxHeader';header.innerHTML='<span>'+lang+'</span><button type="button" class="novaCodeCopy">Copy</button>';pre.parentNode.insertBefore(wrapper,pre);wrapper.appendChild(header);wrapper.appendChild(pre);header.querySelector('button').onclick=()=>navigator.clipboard&&navigator.clipboard.writeText(pre.innerText||'');});}
  function renderSafeComponents(){document.querySelectorAll('.bubble:not([data-rich-safe-ready="1"])').forEach(b=>{b.dataset.richSafeReady='1';b.innerHTML=b.innerHTML.replace(/\[\[nova-card\s+title="([^"]{1,80})"\]\]([\s\S]*?)\[\[\/nova-card\]\]/g,(_,title,body)=>'<div class="novaRichCard"><b>'+esc(title)+'</b><div>'+esc(body).replace(/\n/g,'<br>')+'</div></div>');b.querySelectorAll('script,iframe,object,embed').forEach(x=>x.remove());});}
  function makeMovableResizable(el){if(!el||el.dataset.novaMoveResize==='1')return; el.dataset.novaMoveResize='1';const handle=el.querySelector('.activityHead,.orbitDrawerHeader,.panelHeader,summary,h3')||el;handle.style.cursor='move';let start=null;handle.addEventListener('pointerdown',ev=>{if(ev.target.closest('button,input,textarea,select,a'))return; const r=el.getBoundingClientRect(); start={x:ev.clientX,y:ev.clientY,l:r.left,t:r.top,w:r.width,h:r.height}; try{handle.setPointerCapture(ev.pointerId)}catch(e){}; ev.preventDefault();});handle.addEventListener('pointermove',ev=>{if(!start)return; let l=start.l+ev.clientX-start.x,t=start.t+ev.clientY-start.y; l=Math.max(4,Math.min(window.innerWidth-80,l)); t=Math.max(4,Math.min(window.innerHeight-60,t)); el.classList.add('novaMovablePanel'); el.style.left=l+'px'; el.style.top=t+'px'; el.style.right='auto'; el.style.bottom='auto';});handle.addEventListener('pointerup',()=>{start=null; clampPanel(el);});if(!el.querySelector(':scope > .novaPanelResizeHandle')){const rh=document.createElement('span');rh.className='novaPanelResizeHandle';el.appendChild(rh); let rs=null; rh.addEventListener('pointerdown',ev=>{const r=el.getBoundingClientRect();rs={x:ev.clientX,y:ev.clientY,w:r.width,h:r.height};try{rh.setPointerCapture(ev.pointerId)}catch(e){};ev.preventDefault();ev.stopPropagation();});rh.addEventListener('pointermove',ev=>{if(!rs)return;el.style.width=Math.max(240,Math.min(window.innerWidth-20,rs.w+ev.clientX-rs.x))+'px';el.style.height=Math.max(90,Math.min(window.innerHeight-20,rs.h+ev.clientY-rs.y))+'px';});rh.addEventListener('pointerup',()=>{rs=null;clampPanel(el);});}}
  function clampPanel(el){try{const r=el.getBoundingClientRect();let l=Math.max(4,Math.min(window.innerWidth-80,r.left));let t=Math.max(4,Math.min(window.innerHeight-60,r.top));el.style.left=l+'px';el.style.top=t+'px';}catch(e){}}
  function scanPanels(){['liveActivityPanel','orbitDrawer','orbitRightDrawer','novaAiHelpPanel'].forEach(id=>makeMovableResizable(document.getElementById(id)));document.querySelectorAll('.popupPanel,.settingsPanel,.novaCommandHelpPanel').forEach(makeMovableResizable);}
  function commandHelp(){let ov=document.getElementById('novaCommandHelpOverlay'); if(!ov){ov=document.createElement('div');ov.id='novaCommandHelpOverlay';ov.className='novaCommandHelpOverlay';document.body.appendChild(ov);} const q='<input id="novaCommandHelpSearch" placeholder="Search commands, e.g. model, remote, gui" oninput="window.NovaInteractionOverhaul.filterCommandHelp(this.value)">';const rows=SAFE_COMMANDS.map(c=>'<details data-search="'+esc((c.group+' '+c.cmd+' '+c.what+' '+c.why+' '+c.example).toLowerCase())+'"><summary>'+esc(c.group)+' · <code>'+esc(c.cmd)+'</code></summary><p><b>What:</b> '+esc(c.what)+'</p><p><b>Why:</b> '+esc(c.why)+'</p><p><b>Example:</b> <code>'+esc(c.example)+'</code></p><button type="button" data-cmd="'+esc(c.example)+'">Use example</button></details>').join('');ov.innerHTML='<div class="novaCommandHelpPanel"><div class="row wrap"><h2>Nova Command Help</h2><button type="button" class="tiny secondary" onclick="document.getElementById(\'novaCommandHelpOverlay\').style.display=\'none\'">Close</button></div><p class="small">Searchable, grouped help. Expand a command to see what it does, why it is useful, and example usage.</p>'+q+'<div class="novaCommandGrid">'+rows+'</div></div>';ov.querySelectorAll('button[data-cmd]').forEach(b=>b.onclick=()=>postCommand(b.dataset.cmd));ov.style.display='flex';}
  function filterCommandHelp(q){q=String(q||'').toLowerCase();document.querySelectorAll('#novaCommandHelpOverlay details').forEach(d=>{d.style.display=!q||d.dataset.search.includes(q)?'block':'none';});}
  async function updateAutonomousGuard(){let ov=document.getElementById('novaAutonomousGuardOverlay'); if(!ov){ov=document.createElement('div');ov.id='novaAutonomousGuardOverlay';ov.className='novaAutonomousGuardOverlay';document.body.appendChild(ov);} try{const r=await fetch('/api/autonomous-status',{cache:'no-store'});const j=await r.json();const s=j.state||{};const active=!!(s.enabled||s.running||s.stop_requested);document.body.classList.toggle('nova-autonomous-guard-active',active);if(!active){ov.style.display='none';return;} const events=(s.events||[]).slice(-10).reverse().map(e=>'<div class="small">• '+esc(e.time||'')+' '+esc(e.message||e.kind||'event')+'</div>').join(''); ov.innerHTML='<div class="novaAutonomousGuardPanel"><h2>Autonomous mode active</h2><p><b>Run:</b> '+esc(s.current_run_id||'(starting)')+'</p><p><b>Status:</b> '+esc(s.phase||'running')+' · '+esc(s.current_action||'Working')+'</p><p><b>Tool:</b> '+esc(s.current_tool||s.last_tool||'selecting tool')+'</p><p><b>Why:</b> '+esc(s.current_thought||s.current_detail||'Bounded autonomous cycle in progress')+'</p><p><b>Changing:</b> '+esc(s.resolved_target||s.goal||'No file/action reported yet')+'</p><p><b>Next:</b> '+esc(s.next_strategy_hint||'Wait for bounded step, validation, or stop request.')+'</p><div class="row wrap"><button type="button" class="danger" data-cmd="/autonomous stop">Stop autonomous</button><button type="button" data-cmd="/autonomous status">Status</button><button type="button" data-cmd="/activity">Logs</button><button type="button" onclick="document.getElementById(\'novaAutonomousGuardOverlay\').style.display=\'none\'">Hide overlay</button></div><h3>Recent log</h3>'+events+'</div>';ov.querySelectorAll('button[data-cmd]').forEach(b=>b.onclick=()=>postCommand(b.dataset.cmd)); ov.style.display='flex';}catch(e){/* advisory overlay must never break the GUI */}}
  function init(){document.body.classList.add('nova-interaction-overhaul-v1');ensureTopButton('novaCommandHelpButton','help',commandHelp);ensureStatusBoxes(); updateMicStatus(); updateModelMini(); addMessageNav(); enhanceCodeBlocks(); renderSafeComponents(); scanPanels(); updateAutonomousGuard();}
  window.NovaInteractionOverhaul={version:'v55.3.164-interaction-overhaul-v1',patchId:'gui-autonomous-interaction-fix-v1',commandHelp,filterCommandHelp,useCommand:postCommand,updateModelMini,updateMicStatus,addMessageNav,enhanceCodeBlocks,renderSafeComponents,scanPanels,updateAutonomousGuard};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
  setInterval(()=>{updateMicStatus();addMessageNav();enhanceCodeBlocks();renderSafeComponents();scanPanels();},1600);setInterval(updateModelMini,6500); setInterval(updateAutonomousGuard,2500);
})();
</script>
"""

def _commands_json_for_js() -> str:
    rows = [
        {
            "group": item.category,
            "cmd": item.command,
            "what": item.what,
            "why": item.why,
            "example": item.example,
        }
        for item in COMMANDS
    ]
    return json.dumps(rows, ensure_ascii=True)

def apply_interaction_overhaul(html: str) -> str:
    if "interaction overhaul v1" not in html:
        html = html.replace("</style>", INTERACTION_OVERHAUL_CSS + "\n</style>", 1)
    if "NovaInteractionOverhaul" not in html:
        js = INTERACTION_OVERHAUL_JS.replace("__NOVA_COMMANDS_JSON__", _commands_json_for_js())
        html = html.replace("</body>", js + "\n</body>", 1)
    return html
