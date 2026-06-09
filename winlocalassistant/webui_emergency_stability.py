from __future__ import annotations

"""Emergency usability stabilization for Nova's web UI.

This layer fixes the product-breaking issues seen in real user screenshots/logs:
- legacy /help wall instead of searchable command groups
- Live Activity covering chat/composer
- bottom composer overlap
- cluttered drawer menus showing every panel at once
- stale popup/right-panel blur

It is deliberately UI-only and applied after older theme/layout layers so it can
override prior experimental CSS without rewriting the legacy webui.
"""

EMERGENCY_STABILITY_CSS = r"""
/* v55.3.164 emergency stability v1: chat-first layout, clean drawers, non-overlapping activity/composer. */
body.nova-orbit-shell.nova-emergency-stability-v1{
  --nova-bottom-bar-h:96px!important;
  --nova-activity-compact-h:44px!important;
  --nova-activity-open-h:min(36vh,360px)!important;
  --nova-drawer-clean-width:min(430px,calc(100vw - var(--orbit-left,208px) - 30px))!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1 .chat-wrap{
  min-height:0!important;
  overflow:hidden!important;
  padding-bottom:0!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1 #chat{
  min-height:0!important;
  height:calc(100vh - var(--nova-bottom-bar-h) - 58px)!important;
  max-height:calc(100vh - var(--nova-bottom-bar-h) - 58px)!important;
  overflow:auto!important;
  padding-bottom:34px!important;
  scroll-padding-bottom:44px!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1 .composer{
  position:fixed!important;
  left:calc(var(--orbit-left,208px) + 22px)!important;
  right:22px!important;
  bottom:14px!important;
  width:auto!important;
  max-width:none!important;
  min-height:72px!important;
  max-height:var(--nova-bottom-bar-h)!important;
  z-index:560!important;
  transform:none!important;
  margin:0!important;
  overflow:visible!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1 .inputDock{
  grid-template-columns:42px minmax(0,1fr) 42px 70px!important;
  align-items:end!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1 .composerText{
  min-height:42px!important;
  max-height:82px!important;
  overflow:auto!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1 #liveActivityPanel,
body.nova-orbit-shell.nova-emergency-stability-v1 .activity{
  position:fixed!important;
  left:auto!important;
  right:18px!important;
  bottom:calc(var(--nova-bottom-bar-h) + 28px)!important;
  width:min(560px,calc(100vw - var(--orbit-left,208px) - 46px))!important;
  min-width:280px!important;
  height:var(--nova-activity-compact-h)!important;
  min-height:var(--nova-activity-compact-h)!important;
  max-height:var(--nova-activity-open-h)!important;
  overflow:hidden!important;
  resize:none!important;
  z-index:360!important;
  pointer-events:auto!important;
  opacity:.94!important;
  contain:layout paint!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1.novaActivityOpen #liveActivityPanel,
body.nova-orbit-shell.nova-emergency-stability-v1.novaActivityOpen .activity,
body.nova-orbit-shell.nova-emergency-stability-v1.orbit-activity-open #liveActivityPanel,
body.nova-orbit-shell.nova-emergency-stability-v1.orbit-activity-open .activity{
  height:var(--nova-activity-open-h)!important;
  min-height:160px!important;
  resize:both!important;
  overflow:hidden!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1 #liveActivityPanel #activityLog,
body.nova-orbit-shell.nova-emergency-stability-v1 .activity #activityLog{
  height:calc(100% - 54px)!important;
  max-height:calc(var(--nova-activity-open-h) - 54px)!important;
  overflow:auto!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1:not(.novaActivityOpen):not(.orbit-activity-open) #activityLog{
  display:none!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1 #activitySubtitle{
  white-space:nowrap!important;
  overflow:hidden!important;
  text-overflow:ellipsis!important;
  max-width:100%!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1 .activityHead{
  min-height:42px!important;
  padding:8px 12px!important;
  align-items:center!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1 #orbitDrawer{
  transform:translateX(calc(-100% - var(--orbit-left,208px) - 24px))!important;
  opacity:0!important;pointer-events:none!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1.orbitDrawerOpen #orbitDrawer{
  left:calc(var(--orbit-left,208px) + var(--orbit-safe-gap,14px))!important;
  transform:none!important;
  transition:none!important;
  opacity:1!important;
  visibility:visible!important;
  pointer-events:auto!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1 #orbitDrawer{
  width:var(--nova-drawer-clean-width)!important;
  max-width:var(--nova-drawer-clean-width)!important;
  height:calc(100vh - 32px)!important;
  top:16px!important;
  bottom:16px!important;
  overflow:hidden!important;
  z-index:520!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1 #orbitDrawer .orbitDrawerBody{
  height:calc(100% - 76px)!important;
  overflow:auto!important;
  padding-bottom:26px!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1 #orbitDrawer .novaHiddenByTarget,
body.nova-orbit-shell.nova-emergency-stability-v1 #orbitDrawer .novaDrawerHidden{
  display:none!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1 #orbitDrawer .orbitInlinePanel,
body.nova-orbit-shell.nova-emergency-stability-v1 #orbitDrawer .item,
body.nova-orbit-shell.nova-emergency-stability-v1 #orbitDrawer .card{
  margin-bottom:10px!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1 #orbitRightDrawer,
body.nova-orbit-shell.nova-emergency-stability-v1 #orbitRightDrawer *{
  filter:none!important;
  backdrop-filter:none!important;
  -webkit-backdrop-filter:none!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1 #orbitRightDrawer:not(.open){
  background:rgba(4,6,10,.98)!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1 .novaAiHelpDot{
  width:9px!important;height:9px!important;min-width:9px!important;min-height:9px!important;
  font-size:0!important;right:3px!important;top:3px!important;opacity:.20!important;
  border-radius:999px!important;transform:none!important;pointer-events:auto!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1 .novaAiHelpDot::after{content:'?';font-size:7px;line-height:9px;color:#fff6a3;}
body.nova-orbit-shell.nova-emergency-stability-v1 .novaAiHelpDot:hover,
body.nova-orbit-shell.nova-emergency-stability-v1 .novaAiHelpDot:focus{opacity:.90!important;}
body.nova-orbit-shell.nova-emergency-stability-v1 .topbar .row.wrap,
body.nova-orbit-shell.nova-emergency-stability-v1 #topQuickActions{
  gap:5px!important;overflow-x:auto!important;max-width:52vw!important;white-space:nowrap!important;
}
body.nova-orbit-shell.nova-emergency-stability-v1 .topbar button,
body.nova-orbit-shell.nova-emergency-stability-v1 #topQuickActions button{
  font-size:11px!important;padding:5px 8px!important;border-radius:9px!important;flex:0 0 auto!important;
}
.novaHelpHubOverlay{position:fixed;inset:0;background:rgba(0,0,0,.56);z-index:9800;display:none;align-items:center;justify-content:center;padding:18px;}
.novaHelpHubPanel{width:min(980px,calc(100vw - 44px));height:min(760px,calc(100vh - 44px));background:linear-gradient(180deg,rgba(8,10,16,.98),rgba(5,7,12,.99));border:1px solid rgba(245,230,66,.34);border-radius:18px;box-shadow:0 26px 90px rgba(0,0,0,.68);display:grid;grid-template-rows:auto auto minmax(0,1fr);overflow:hidden;}
.novaHelpHubHeader{display:flex;justify-content:space-between;gap:10px;align-items:center;padding:12px 14px;border-bottom:1px solid rgba(245,230,66,.24);}
.novaHelpHubHeader h2{margin:0;color:#f5e642;letter-spacing:.08em;text-transform:uppercase;}
.novaHelpHubSearch{padding:10px 14px;border-bottom:1px solid rgba(62,242,255,.16);}
.novaHelpHubSearch input{width:100%;}
.novaHelpHubGrid{overflow:auto;padding:12px 14px;display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px;align-content:start;}
.novaHelpHubCard{border:1px solid rgba(62,242,255,.20);border-radius:14px;background:rgba(7,10,16,.88);padding:10px;}
.novaHelpHubCard summary{cursor:pointer;color:#dfffff;font-weight:800;}
.novaHelpHubCard code{white-space:normal;word-break:break-word;}
.novaCapabilityStrip{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0 0;}
.novaCapabilityStrip button{font-size:11px!important;padding:5px 7px!important;}
.novaPanicReset{position:fixed;right:12px;bottom:calc(var(--nova-bottom-bar-h) + 84px);z-index:9000;border:1px solid rgba(245,230,66,.35)!important;background:rgba(245,230,66,.10)!important;color:#fff7a5!important;}
@media (max-width:900px){
 body.nova-orbit-shell.nova-emergency-stability-v1 .composer{left:12px!important;right:12px!important;bottom:10px!important;}
 body.nova-orbit-shell.nova-emergency-stability-v1 #liveActivityPanel,
 body.nova-orbit-shell.nova-emergency-stability-v1 .activity{left:12px!important;right:12px!important;width:auto!important;bottom:calc(var(--nova-bottom-bar-h) + 20px)!important;}
 body.nova-orbit-shell.nova-emergency-stability-v1 #orbitDrawer{left:10px!important;width:calc(100vw - 20px)!important;max-width:calc(100vw - 20px)!important;}
}
"""

EMERGENCY_STABILITY_JS = r"""
<script>
window.NovaEmergencyStability = window.NovaEmergencyStability || {version:'v55.3.164-legacy-continuity-v1',patchId:'legacy-continuity-regression-guard-v1'};
(function(){
  function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
  const HELP=[
    ['Chat','Say hi / ask a question','Normal chat now has deterministic quick replies if the local model times out.','hi'],
    ['Code','/code QUESTION','Ask for coding/debugging guidance without creating a project.','/code explain how to run a Python file'],
    ['Write file','/write PATH CONTENT','Create or overwrite one file in the safe workspace.','/write demo.txt hello'],
    ['Run command','/shell COMMAND','Run a local shell command in the workspace when mutation/tools are allowed.','/shell python --version'],
    ['Verify','/verify COMMAND','Run a command and detect obvious errors.','/verify python -m pytest -q tests_smoke.py'],
    ['Files','/files','List workspace files.','/files'],
    ['Search','/search TEXT','Search workspace files.','/search TODO'],
    ['Model','/llm-status','Check Ollama/model state before retrying or stopping a model.','/llm-status'],
    ['Help','/command-help QUERY','Search grouped help with what/why/how/examples.','/command-help code'],
    ['Layout','/gui-layout-status','Check GUI layout markers and runtime diagnostics.','/gui-layout-status'],
    ['Reset UI','reset UI button','Closes drawers/activity and clears stale layout cache only.','Click reset UI'],
    ['Activity','activity button','Open compact Live Activity without covering the composer.','Click activity'],
    ['Remote','/remote-access-test','Read-only remote setup preflight.','/remote-access-test'],
    ['Arcade','/arcade','Show local Nova Arcade games.','/arcade']
  ];
  function post(cmd){try{if(typeof quick==='function')return quick(cmd);const msg=document.getElementById('msg');if(msg){msg.value=cmd;msg.focus();}}catch(e){}}
  function addButton(id,label,fn){if(document.getElementById(id))return;const host=document.querySelector('.topbar .row.wrap')||document.querySelector('.topbar')||document.body;const b=document.createElement('button');b.id=id;b.type='button';b.className='tiny secondary';b.textContent=label;b.onclick=fn;host.appendChild(b);}
  function showHelp(){let ov=document.getElementById('novaHelpHubOverlay');if(!ov){ov=document.createElement('div');ov.id='novaHelpHubOverlay';ov.className='novaHelpHubOverlay';document.body.appendChild(ov);}const cards=HELP.map((h,i)=>'<details class="novaHelpHubCard" open data-search="'+esc(h.join(' ').toLowerCase())+'"><summary>'+esc(h[0])+' · <code>'+esc(h[1])+'</code></summary><p>'+esc(h[2])+'</p><p><b>Example:</b> <code>'+esc(h[3])+'</code></p><button type="button" data-use="'+esc(h[3])+'">Use</button></details>').join('');ov.innerHTML='<div class="novaHelpHubPanel"><div class="novaHelpHubHeader"><h2>Nova Help Hub</h2><div class="row wrap"><button type="button" data-use="/command-help">Full grouped help</button><button type="button" onclick="document.getElementById(\'novaHelpHubOverlay\').style.display=\'none\'">Close</button></div></div><div class="novaHelpHubSearch"><input id="novaHelpHubSearch" placeholder="Search chat, code, file, run, model, remote, gui" oninput="window.NovaEmergencyStability.filterHelp(this.value)"><div class="novaCapabilityStrip"><button data-use="hi">Test chat</button><button data-use="/code explain how to write and run code">Test code</button><button data-use="/write nova_test.txt hello">Test write</button><button data-use="/verify python --version">Test run</button><button data-use="/llm-status">Model status</button></div></div><div class="novaHelpHubGrid">'+cards+'</div></div>';ov.querySelectorAll('[data-use]').forEach(b=>b.onclick=()=>{ov.style.display='none';post(b.dataset.use);});ov.style.display='flex';setTimeout(()=>document.getElementById('novaHelpHubSearch')?.focus(),30);}
  function filterHelp(q){q=String(q||'').toLowerCase();document.querySelectorAll('#novaHelpHubOverlay details').forEach(d=>{d.style.display=!q||d.dataset.search.includes(q)?'block':'none';});}
  function cleanDrawer(target){try{const body=document.querySelector('#orbitDrawer .orbitDrawerBody');if(!body)return;const map={commands:['commandSearch'],projects:['projects'],files:['files'],tools:['customTools'],models:['llmStatus','novaModelStatusMini'],chats:['orbitChatsPanel'],theme:['orbitThemePanel'],apps:['orbitAppsPanel'],research:['orbitResearchPanel']};const ids=map[target]||[];if(!ids.length){body.querySelectorAll('.novaHiddenByTarget').forEach(x=>x.classList.remove('novaHiddenByTarget'));return;}let kept=0;Array.from(body.children).forEach(ch=>{const keep=ids.some(id=>ch.id===id||!!ch.querySelector('#'+CSS.escape(id)));ch.classList.toggle('novaHiddenByTarget',!keep);if(keep)kept++;});if(!kept){body.querySelectorAll('.novaHiddenByTarget').forEach(x=>x.classList.remove('novaHiddenByTarget'));}const first=ids.map(id=>document.getElementById(id)).find(Boolean);if(first)first.scrollIntoView({block:'start'});}catch(e){}}
  function patchDrawer(){if(window.__novaEmergencyDrawerPatch)return;window.__novaEmergencyDrawerPatch=1;const oldOpen=window.openOrbitDrawer;const oldToggle=window.toggleOrbitActivity;if(typeof oldOpen==='function'){window.openOrbitDrawer=function(target){const r=oldOpen.apply(this,arguments);setTimeout(()=>cleanDrawer(target||window.orbitDrawerTarget||'commands'),80);return r;};}
    if(typeof oldToggle==='function'){window.toggleOrbitActivity=function(force){const on=typeof force==='boolean'?force:!document.body.classList.contains('novaActivityOpen');document.body.classList.toggle('novaActivityOpen',on);document.body.classList.toggle('orbit-activity-open',on);try{if(typeof setActivityOpen==='function')setActivityOpen(on);}catch(e){};return on;};}
  }
  function minimizeActivityOnStartup(){try{document.body.classList.remove('novaActivityOpen','orbit-activity-open');if(typeof setActivityOpen==='function')setActivityOpen(false);const p=document.getElementById('liveActivityPanel');if(p){p.classList.add('is-minimized');} }catch(e){} }
  function addPanic(){if(document.getElementById('novaPanicReset'))return;const b=document.createElement('button');b.id='novaPanicReset';b.className='novaPanicReset tiny secondary';b.type='button';b.textContent='fix UI';b.title='Close cluttered popups/drawers and restore the chat composer';b.onclick=()=>{try{document.querySelectorAll('#novaHelpHubOverlay,#novaCommandHelpOverlay,.novaAiHelpPanel,.settingsPanel,.popupPanel').forEach(el=>{el.style.display='none';});document.body.classList.remove('orbitDrawerOpen','orbit-right-open','orbit-activity-open','novaActivityOpen');if(typeof setActivityOpen==='function')setActivityOpen(false);if(window.novaGuiHardenLayout)window.novaGuiHardenLayout();}catch(e){}};document.body.appendChild(b);}
  function diagnose(){const composer=document.querySelector('.composer');const activity=document.getElementById('liveActivityPanel')||document.querySelector('.activity');const chat=document.getElementById('chat');function rect(el){if(!el)return null;const r=el.getBoundingClientRect();const cs=getComputedStyle(el);return {x:r.x,y:r.y,w:r.width,h:r.height,bottom:r.bottom,right:r.right,display:cs.display,visibility:cs.visibility};}const c=rect(composer),a=rect(activity),ch=rect(chat);const warnings=[];if(c&&c.bottom>innerHeight+2)warnings.push('composer offscreen');if(c&&a&&document.body.classList.contains('novaActivityOpen')&&!(a.bottom<=c.y-6))warnings.push('activity overlaps composer');if(ch&&c&&ch.bottom>c.y+8)warnings.push('chat extends under composer; padding may be insufficient');return {ok:warnings.length===0,patchId:'legacy-continuity-regression-guard-v1',warnings,composer:c,activity:a,chat:ch,drawerOpen:document.body.classList.contains('orbitDrawerOpen')};}
  function init(){document.body.classList.add('nova-emergency-stability-v1');addButton('novaHelpHubButton','help hub',showHelp);addPanic();patchDrawer();minimizeActivityOnStartup();setTimeout(()=>{patchDrawer();if(window.novaGuiHardenLayout)window.novaGuiHardenLayout();},250);}
  window.NovaEmergencyStability={version:'v55.3.164-legacy-continuity-v1',patchId:'legacy-continuity-regression-guard-v1',showHelp,filterHelp,cleanDrawer,diagnose,minimizeActivityOnStartup};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
  setInterval(()=>{patchDrawer();},2000);
})();
</script>
"""


def apply_emergency_stability(html: str) -> str:
    if "emergency stability v1" not in html:
        html = html.replace("</style>", EMERGENCY_STABILITY_CSS + "\n</style>", 1)
    if "NovaEmergencyStability" not in html:
        html = html.replace("</body>", EMERGENCY_STABILITY_JS + "\n</body>", 1)
    return html
