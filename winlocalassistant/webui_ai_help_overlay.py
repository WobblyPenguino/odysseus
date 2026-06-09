from __future__ import annotations

"""Inline AI help overlay for Nova's static Web UI.

The legacy Web UI is a large HTML string.  This module injects a small isolated
CSS/JS layer that adds semi-transparent help dots to interactive elements and
panels without rewriting the main interface.
"""

AI_HELP_OVERLAY_CSS = r"""
/* v55.3.164 AI contextual help overlay: tiny semi-transparent guide symbols. */
.nova-ai-help-enabled [data-nova-ai-help-ready="1"]{position:relative!important;}
.novaAiHelpDot{
  position:absolute!important;
  top:3px!important;
  right:3px!important;
  width:15px!important;
  height:15px!important;
  border-radius:999px!important;
  border:1px solid rgba(145,246,255,.38)!important;
  background:rgba(7,6,16,.58)!important;
  color:#dffbff!important;
  display:inline-grid!important;
  place-items:center!important;
  font-size:9px!important;
  font-weight:900!important;
  line-height:1!important;
  cursor:help!important;
  z-index:9!important;
  opacity:.54!important;
  box-shadow:0 0 10px rgba(145,246,255,.20)!important;
  pointer-events:auto!important;
  user-select:none!important;
}
.novaAiHelpDot:hover,.novaAiHelpDot:focus{opacity:1!important;background:rgba(91,40,142,.92)!important;outline:1px solid rgba(203,55,255,.55)!important;}
input + .novaAiHelpDot, textarea + .novaAiHelpDot, select + .novaAiHelpDot{position:relative!important;display:inline-grid!important;margin-left:-20px!important;top:-1px!important;right:auto!important;vertical-align:middle!important;}
.novaAiHelpPanel{
  position:fixed!important;
  right:18px!important;
  bottom:86px!important;
  width:min(420px,calc(100vw - 40px))!important;
  max-height:min(62vh,580px)!important;
  overflow:auto!important;
  z-index:9999!important;
  background:linear-gradient(180deg,rgba(18,13,28,.96),rgba(7,6,14,.96))!important;
  color:#dffbff!important;
  border:1px solid rgba(203,55,255,.45)!important;
  border-radius:18px!important;
  box-shadow:0 30px 100px rgba(0,0,0,.78),0 0 54px rgba(203,55,255,.22)!important;
  backdrop-filter:blur(14px)!important;
  padding:14px!important;
  font-family:var(--orbit-font,ui-monospace,monospace)!important;
}
.novaAiHelpPanel h3{margin:0 0 7px!important;color:#f05bff!important;font-size:15px!important;}
.novaAiHelpPanel .small{font-size:11px!important;color:#9fc5d1!important;line-height:1.35!important;}
.novaAiHelpPanel .row{display:flex!important;flex-wrap:wrap!important;gap:7px!important;margin-top:10px!important;}
.novaAiHelpPanel button{font-size:11px!important;border-radius:999px!important;padding:6px 9px!important;border:1px solid rgba(145,246,255,.35)!important;background:rgba(145,246,255,.09)!important;color:#eaffff!important;}
.novaAiHelpPanel code{display:block!important;white-space:pre-wrap!important;background:rgba(0,0,0,.22)!important;border:1px solid rgba(145,246,255,.20)!important;border-radius:10px!important;padding:7px!important;margin-top:8px!important;font-size:11px!important;}
.novaAiHelpPanel .close{position:absolute!important;top:8px!important;right:10px!important;width:24px!important;height:24px!important;padding:0!important;}
"""

AI_HELP_OVERLAY_JS = r"""
<script>
window.NovaGuiAiHelp = window.NovaGuiAiHelp || {version:'v55.3.164-ai-context-help-v1', enabled:true};
(function(){
  const MAX_DOTS = 260;
  function textOf(el){
    try{return (el.getAttribute('aria-label')||el.getAttribute('title')||el.getAttribute('placeholder')||el.dataset.command||el.textContent||el.value||'').trim().replace(/\s+/g,' ').slice(0,180);}catch(e){return '';}
  }
  function commandOf(el){
    try{
      return (el.dataset.command||el.getAttribute('data-command')||el.getAttribute('onclick')||'').trim().slice(0,220);
    }catch(e){return '';}
  }
  function contextFor(el){
    const label=textOf(el)||el.id||el.tagName;
    return {
      label,
      id:el.id||'',
      tag:el.tagName||'',
      role:el.getAttribute('role')||'',
      title:el.getAttribute('title')||'',
      aria:el.getAttribute('aria-label')||'',
      placeholder:el.getAttribute('placeholder')||'',
      command:commandOf(el),
      classes:String(el.className||'').slice(0,160),
      panel:(el.closest('#orbitDrawer,#orbitRightDrawer,#orbitNav,#chat,.composer,#liveActivityPanel')||{}).id||''
    };
  }
  function encodeContext(ctx){
    try{return encodeURIComponent(JSON.stringify(ctx));}catch(e){return encodeURIComponent(String(ctx.label||'GUI element'));}
  }
  function ensurePanel(){
    let panel=document.getElementById('novaAiHelpPanel');
    if(panel)return panel;
    panel=document.createElement('div');
    panel.id='novaAiHelpPanel';
    panel.className='novaAiHelpPanel';
    panel.style.display='none';
    document.body.appendChild(panel);
    return panel;
  }
  function openHelp(el){
    const ctx=contextFor(el);
    const encoded=encodeContext(ctx);
    const panel=ensurePanel();
    panel.style.display='block';
    panel.innerHTML='<button class="close" onclick="document.getElementById(\'novaAiHelpPanel\').style.display=\'none\'">×</button>'+
      '<h3>AI help: '+esc(ctx.label||'GUI element')+'</h3>'+
      '<div class="small">Tiny contextual help for the selected Nova GUI element. It can explain the control or ask Nova to plan how to use/build with it.</div>'+
      '<code>'+esc(JSON.stringify(ctx,null,2))+'</code>'+
      '<div class="row">'+
      '<button onclick="quick(\'/gui-ai-help '+encoded+'\')">Explain this</button>'+
      '<button onclick="quick(\'/tool-use-plan use this GUI element: '+escAttr(ctx.label||'element')+'\')">AI plan</button>'+
      '<button onclick="quick(\'/pipeline-route use this GUI element: '+escAttr(ctx.label||'element')+'\')">Pipeline</button>'+
      '<button onclick="quick(\'/role-router use this GUI element: '+escAttr(ctx.label||'element')+'\')">Role</button>'+
      '<button onclick="navigator.clipboard&&navigator.clipboard.writeText('+JSON.stringify(JSON.stringify(ctx))+')">Copy context</button>'+
      '</div>';
  }
  function shouldDecorate(el){
    if(!el||el.classList&&el.classList.contains('novaAiHelpDot'))return false;
    if(el.closest&&el.closest('#novaAiHelpPanel,.novaAiHelpDot'))return false;
    if(el.dataset&&el.dataset.novaAiHelpScanned==='1')return false;
    const tag=(el.tagName||'').toLowerCase();
    if(['button','input','textarea','select'].includes(tag))return true;
    if(el.matches&&el.matches('.orbitNavButton,.commandItem,.projectItem,.toolItem,.card,.composer,#chat,#orbitDrawer,#orbitRightDrawer,#liveActivityPanel'))return true;
    return false;
  }
  function decorate(el){
    if(!shouldDecorate(el))return;
    el.dataset.novaAiHelpScanned='1';
    el.dataset.novaAiHelpReady='1';
    const dot=document.createElement('span');
    dot.className='novaAiHelpDot';
    dot.setAttribute('role','button');
    dot.setAttribute('tabindex','0');
    dot.setAttribute('aria-label','AI help for '+(textOf(el)||el.id||el.tagName));
    dot.textContent='?';
    dot.addEventListener('click',function(ev){ev.preventDefault();ev.stopPropagation();openHelp(el);});
    dot.addEventListener('keydown',function(ev){if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();ev.stopPropagation();openHelp(el);}});
    try{el.appendChild(dot);}catch(e){try{el.insertAdjacentElement('afterend',dot);}catch(_){}}
  }
  function scan(){
    try{
      document.body.classList.add('nova-ai-help-enabled');
      const nodes=[...document.querySelectorAll('button,input,textarea,select,.orbitNavButton,.commandItem,.projectItem,.toolItem,.composer,#chat,#orbitDrawer,#orbitRightDrawer,#liveActivityPanel')];
      nodes.slice(0,MAX_DOTS).forEach(decorate);
      window.NovaGuiAiHelp.count=document.querySelectorAll('.novaAiHelpDot').length;
    }catch(e){window.NovaGuiAiHelp.error=String(e);}  
  }
  window.novaGuiAiHelpScan=scan;
  window.novaGuiAiHelpForElement=openHelp;
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',scan);else scan();
  setTimeout(scan,450);setTimeout(scan,1500);setInterval(scan,4500);
})();
</script>
"""


def apply_ai_help_overlay(html: str) -> str:
    if "v55.3.164 AI contextual help overlay" not in html:
        html = html.replace("</style>", AI_HELP_OVERLAY_CSS + "\n</style>", 1)
    if "NovaGuiAiHelp" not in html:
        html = html.replace("</body>", AI_HELP_OVERLAY_JS + "\n</body>", 1)
    return html
