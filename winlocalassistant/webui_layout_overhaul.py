from __future__ import annotations

"""Small, isolated Web UI layout override layer.

Legacy compatibility marker retained: gui-overhaul-v4-wide-left-rail.

The historical ``webui.py`` file is intentionally kept stable because many
legacy tests depend on its exact route names and compatibility markers.  New
layout fixes live here so future humans/agents can adjust the GUI without
searching through the large generated HTML string.
"""

GUI_LAYOUT_OVERHAUL_CSS = r"""
/* v55.3.164 GUI layout overhaul v4: wide readable left rail + drawer/chat split, no drawer rail overlap, no ghost right panel. */
body.nova-orbit-shell.gui-overhaul-v3{
  --orbit-left-collapsed:58px!important;
  --orbit-left-wide:208px!important;
  --orbit-left:var(--orbit-left-wide)!important;
  --orbit-drawer-width:clamp(310px,20vw,380px)!important;
  --orbit-right-width:clamp(320px,22vw,430px)!important;
  --orbit-chat-max:1320px!important;
  --orbit-safe-gap:14px!important;
  background:#05050c!important;
}
body.nova-orbit-shell.gui-overhaul-v3 main[data-ui-overhaul]{
  width:100vw!important;
  max-width:none!important;
  height:100vh!important;
  grid-template-columns:var(--orbit-left) 0 minmax(0,1fr) 0 0!important;
  gap:0!important;
  overflow:hidden!important;
  background:radial-gradient(circle at 62% 22%,rgba(85,32,121,.12),transparent 34%),#05050c!important;
}
body.nova-orbit-shell.gui-overhaul-v3 .sidebar.card{
  grid-column:1!important;
  width:var(--orbit-left)!important;
  min-width:var(--orbit-left)!important;
  max-width:var(--orbit-left)!important;
  z-index:260!important;
  overflow:hidden!important;
  background:rgba(11,8,19,.98)!important;
  border-right:1px solid rgba(203,55,255,.28)!important;
}
body.nova-orbit-shell.gui-overhaul-v3 #orbitNav{
  width:var(--orbit-left)!important;
  min-width:var(--orbit-left)!important;
  max-width:var(--orbit-left)!important;
  padding:12px 10px!important;
  overflow:hidden!important;
  box-sizing:border-box!important;
}
/* Wide permanent left rail: labels stay readable instead of being clipped behind the drawer. */
body.nova-orbit-shell.gui-overhaul-v3 #orbitNav .orbitNavButton{
  width:100%!important;
  min-width:0!important;
  max-width:100%!important;
  justify-content:flex-start!important;
  gap:8px!important;
  padding:8px 9px!important;
  overflow:hidden!important;
  white-space:nowrap!important;
  text-align:left!important;
}
body.nova-orbit-shell.gui-overhaul-v3 #orbitNav .orbitNavButton .label{
  display:inline-block!important;
  min-width:0!important;
  max-width:148px!important;
  overflow:hidden!important;
  text-overflow:ellipsis!important;
  white-space:nowrap!important;
  font-size:11px!important;
  line-height:1.1!important;
}
body.nova-orbit-shell.gui-overhaul-v3 #orbitNav .orbitNavButton .plus,
body.nova-orbit-shell.gui-overhaul-v3 #orbitNav .orbitNavButton small{
  display:inline-block!important;
  margin-left:auto!important;
  max-width:18px!important;
  overflow:hidden!important;
}
body.nova-orbit-shell.gui-overhaul-v3 #orbitNav .orbitLogo{
  display:none!important;
  width:0!important;
  max-width:0!important;
  overflow:hidden!important;
}
body.nova-orbit-shell.gui-overhaul-v3 #orbitNav .orbitProfile span{
  display:block!important;
  max-width:148px!important;
  overflow:hidden!important;
  text-overflow:ellipsis!important;
  white-space:nowrap!important;
}
body.nova-orbit-shell.gui-overhaul-v3 #orbitNav .orbitNavButton .ico{
  width:18px!important;
  min-width:18px!important;
  margin:0!important;
  font-size:15px!important;
  text-align:center!important;
}
body.nova-orbit-shell.gui-overhaul-v3 #edgeRail,
body.nova-orbit-shell.gui-overhaul-v3 #edgeRailToggle{
  z-index:300!important;
}
body.nova-orbit-shell.gui-overhaul-v3 .chat-wrap.card{
  grid-column:3!important;
  width:100%!important;
  min-width:0!important;
  overflow:hidden!important;
  border-left:0!important;
  border-right:0!important;
  background:transparent!important;
}
body.nova-orbit-shell.gui-overhaul-v3 #chat{
  width:100%!important;
  max-width:none!important;
  margin:0!important;
  box-sizing:border-box!important;
  padding:18px 36px 148px 36px!important;
  background:transparent!important;
}
body.nova-orbit-shell.gui-overhaul-v3.orbitDrawerOpen #chat{
  padding-left:calc(var(--orbit-drawer-width) + var(--orbit-left) + 28px)!important;
}
body.nova-orbit-shell.gui-overhaul-v3.orbit-right-open #chat{
  padding-right:calc(var(--orbit-right-width) + 34px)!important;
}
body.nova-orbit-shell.gui-overhaul-v3.orbitDrawerOpen.orbit-right-open #chat{
  padding-left:calc(var(--orbit-drawer-width) + var(--orbit-left) + 28px)!important;
  padding-right:calc(var(--orbit-right-width) + 34px)!important;
}
body.nova-orbit-shell.gui-overhaul-v3 .msg,
body.nova-orbit-shell.gui-overhaul-v3 .name{
  width:min(100%,var(--orbit-chat-max))!important;
  max-width:var(--orbit-chat-max)!important;
}
body.nova-orbit-shell.gui-overhaul-v3.orbitDrawerOpen .msg,
body.nova-orbit-shell.gui-overhaul-v3.orbitDrawerOpen .name{
  max-width:min(1240px,calc(100vw - var(--orbit-left) - var(--orbit-drawer-width) - 92px))!important;
}
body.nova-orbit-shell.gui-overhaul-v3 .composer{
  position:fixed!important;
  left:50%!important;
  right:auto!important;
  bottom:18px!important;
  transform:translateX(-50%)!important;
  width:min(920px,calc(100vw - var(--orbit-left) - 132px))!important;
  max-width:calc(100vw - var(--orbit-left) - 132px)!important;
  margin:0!important;
}
body.nova-orbit-shell.gui-overhaul-v3.orbitDrawerOpen .composer{
  position:fixed!important;
  width:min(920px,calc(100vw - var(--orbit-left) - var(--orbit-drawer-width) - 86px))!important;
  left:calc(var(--orbit-left) + var(--orbit-drawer-width) + ((100vw - var(--orbit-left) - var(--orbit-drawer-width))/2))!important;
  right:auto!important;
  bottom:18px!important;
  transform:translateX(-50%)!important;
}
body.nova-orbit-shell.gui-overhaul-v3.orbit-right-open .composer{
  width:min(880px,calc(100vw - var(--orbit-left) - var(--orbit-right-width) - 100px))!important;
  left:calc(var(--orbit-left) + ((100vw - var(--orbit-left) - var(--orbit-right-width))/2))!important;
}
body.nova-orbit-shell.gui-overhaul-v3.orbitDrawerOpen.orbit-right-open .composer{
  width:min(820px,calc(100vw - var(--orbit-left) - var(--orbit-drawer-width) - var(--orbit-right-width) - 100px))!important;
  left:calc(var(--orbit-left) + var(--orbit-drawer-width) + ((100vw - var(--orbit-left) - var(--orbit-drawer-width) - var(--orbit-right-width))/2))!important;
}
/* Drawer is a docked overlay beside the icon rail, never on top of the rail. */
body.nova-orbit-shell.gui-overhaul-v3 #orbitDrawer,
body.nova-orbit-shell.gui-overhaul-v3 #orbitRightDrawer{
  position:fixed!important;
  top:36px!important;
  height:calc(100vh - 44px)!important;
  display:block!important;
  opacity:0!important;
  pointer-events:none!important;
  overflow:hidden!important;
  background:linear-gradient(180deg,rgba(20,13,30,.99),rgba(8,6,14,.99))!important;
  border:1px solid rgba(203,55,255,.38)!important;
  box-shadow:0 26px 90px rgba(0,0,0,.76),0 0 60px rgba(203,55,255,.20)!important;
  backdrop-filter:blur(12px)!important;
  z-index:240!important;
  transition:transform .15s ease,opacity .15s ease!important;
  box-sizing:border-box!important;
}
body.nova-orbit-shell.gui-overhaul-v3 #orbitDrawer{
  left:calc(var(--orbit-left) + var(--orbit-safe-gap))!important;
  right:auto!important;
  width:var(--orbit-drawer-width)!important;
  max-width:calc(100vw - var(--orbit-left) - 2 * var(--orbit-safe-gap))!important;
  transform:translateX(calc(-100% - var(--orbit-left) - 24px))!important;
  border-radius:0 16px 16px 0!important;
}
body.nova-orbit-shell.gui-overhaul-v3.orbitDrawerOpen #orbitDrawer{
  transform:translateX(0)!important;
  opacity:1!important;
  pointer-events:auto!important;
}
body.nova-orbit-shell.gui-overhaul-v3 #orbitRightDrawer{
  right:var(--orbit-safe-gap)!important;
  left:auto!important;
  width:var(--orbit-right-width)!important;
  max-width:calc(100vw - var(--orbit-left) - 2 * var(--orbit-safe-gap))!important;
  transform:translateX(calc(100% + 32px))!important;
  border-radius:16px 0 0 16px!important;
  visibility:hidden!important;
}
body.nova-orbit-shell.gui-overhaul-v3.orbit-right-open #orbitRightDrawer{
  transform:translateX(0)!important;
  opacity:1!important;
  pointer-events:auto!important;
  visibility:visible!important;
}
body.nova-orbit-shell.gui-overhaul-v3:not(.orbit-right-open) #orbitRightDrawer{
  opacity:0!important;
  visibility:hidden!important;
  pointer-events:none!important;
}
body.nova-orbit-shell.gui-overhaul-v3 #orbitDrawer .orbitDrawerBody,
body.nova-orbit-shell.gui-overhaul-v3 #orbitRightDrawer .orbitDrawerBody{
  height:calc(100% - 52px)!important;
  overflow:auto!important;
  background:transparent!important;
  scrollbar-gutter:stable!important;
}
body.nova-orbit-shell.gui-overhaul-v3 #orbitDrawer .orbitDrawerHeader,
body.nova-orbit-shell.gui-overhaul-v3 #orbitRightDrawer .orbitDrawerHeader{
  background:rgba(11,7,18,.99)!important;
  border-bottom:1px solid rgba(203,55,255,.40)!important;
}
body.nova-orbit-shell.gui-overhaul-v3 #orbitLegacyDrawer,
body.nova-orbit-shell.gui-overhaul-v3 #orbitLegacyDrawer .card,
body.nova-orbit-shell.gui-overhaul-v3 #orbitLegacyDrawer .artifact,
body.nova-orbit-shell.gui-overhaul-v3 #orbitLegacyDrawer .item,
body.nova-orbit-shell.gui-overhaul-v3 #orbitLegacyDrawer .projectItem,
body.nova-orbit-shell.gui-overhaul-v3 #orbitLegacyDrawer .toolItem,
body.nova-orbit-shell.gui-overhaul-v3 #orbitLegacyDrawer .orbitInlinePanel{
  background:rgba(12,9,19,.94)!important;
  color:#dffbff!important;
  border-color:rgba(203,55,255,.30)!important;
}
body.nova-orbit-shell.gui-overhaul-v3 #orbitLegacyDrawer .card *,
body.nova-orbit-shell.gui-overhaul-v3 #orbitLegacyDrawer .artifact *,
body.nova-orbit-shell.gui-overhaul-v3 #orbitLegacyDrawer .item *,
body.nova-orbit-shell.gui-overhaul-v3 #orbitLegacyDrawer .projectItem *,
body.nova-orbit-shell.gui-overhaul-v3 #orbitLegacyDrawer .toolItem *{
  color:inherit;
}
body.nova-orbit-shell.gui-overhaul-v3 #orbitLegacyDrawer input,
body.nova-orbit-shell.gui-overhaul-v3 #orbitLegacyDrawer textarea,
body.nova-orbit-shell.gui-overhaul-v3 #orbitLegacyDrawer select{
  background:#08060d!important;
  color:#e1fbff!important;
  border:1px solid rgba(145,246,255,.28)!important;
}
/* Kill historical blank/grey right-side panes unless the user explicitly opens the inspector. */
body.nova-orbit-shell.gui-overhaul-v3:not(.orbit-right-open) .rightbar.card,
body.nova-orbit-shell.gui-overhaul-v3:not(.orbit-right-open) #orbitRightDrawer .rightbar,
body.nova-orbit-shell.gui-overhaul-v3:not(.orbit-right-open) #orbitSubChat,
body.nova-orbit-shell.gui-overhaul-v3 #chatsPopup{
  display:none!important;
  visibility:hidden!important;
}
body.nova-orbit-shell.gui-overhaul-v3 #orbitRightDrawer .rightbar,
body.nova-orbit-shell.gui-overhaul-v3 #orbitRightDrawer .rightbar.card{
  display:block!important;
  background:transparent!important;
  box-shadow:none!important;
  border:0!important;
  padding:0!important;
  overflow:visible!important;
}
body.nova-orbit-shell.gui-overhaul-v3 #orbitRightDrawer .assistantBoxPanel,
body.nova-orbit-shell.gui-overhaul-v3 #orbitRightDrawer .transparentOutputPanel,
body.nova-orbit-shell.gui-overhaul-v3 #orbitRightDrawer .communicationCentre,
body.nova-orbit-shell.gui-overhaul-v3 #orbitRightDrawer .voiceGuardCard,
body.nova-orbit-shell.gui-overhaul-v3 #orbitRightDrawer .item,
body.nova-orbit-shell.gui-overhaul-v3 #orbitRightDrawer textarea,
body.nova-orbit-shell.gui-overhaul-v3 #orbitRightDrawer .codepreview{
  background:rgba(11,8,18,.92)!important;
  color:#dffbff!important;
  border-color:rgba(203,55,255,.30)!important;
  box-shadow:none!important;
}
body.nova-orbit-shell.gui-overhaul-v3 .popupPanel,
body.nova-orbit-shell.gui-overhaul-v3 .settingsPanel{
  z-index:340!important;
}
@media(max-width:1100px){
  body.nova-orbit-shell.gui-overhaul-v3{
  --orbit-left-collapsed:58px!important;
  --orbit-left-wide:208px!important;--orbit-left:54px!important;--orbit-drawer-width:calc(100vw - 74px)!important;--orbit-right-width:calc(100vw - 74px)!important;}
  body.nova-orbit-shell.gui-overhaul-v3 #chat{padding-left:14px!important;padding-right:14px!important;}
  body.nova-orbit-shell.gui-overhaul-v3.orbitDrawerOpen #chat{padding-left:14px!important;}
  body.nova-orbit-shell.gui-overhaul-v3 .composer,
  body.nova-orbit-shell.gui-overhaul-v3.orbitDrawerOpen .composer{left:50%!important;right:auto!important;bottom:12px!important;transform:translateX(-50%)!important;width:calc(100vw - var(--orbit-left) - 28px)!important;}
}
"""

GUI_LAYOUT_OVERHAUL_JS = r"""
<script>
window.NovaGuiOverhaulV3 = window.NovaGuiOverhaulV3 || {version:'v55.3.164-gui-overhaul-v10-legacy-continuity', patchId:'legacy-continuity-regression-guard-v1', storageVersion:'v55.3.164-legacy-continuity-v1'};
(function(){
  function rect(id){
    const el=document.getElementById(id);
    if(!el)return null;
    const r=el.getBoundingClientRect();
    const cs=getComputedStyle(el);
    return {x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom,display:cs.display,visibility:cs.visibility,opacity:cs.opacity,position:cs.position};
  }
  function resetStaleLayoutStorage(){
    try{
      const key='novaGuiLayoutStorageVersion';
      const wanted=window.NovaGuiOverhaulV3.storageVersion;
      if(localStorage.getItem(key)===wanted) return false;
      const staleKeys=['wlaLeftPanelWidth','wlaRightPanelWidth','wlaCollapseleft','wlaCollapseright','wlaCollapseactivity','wlaEdgeRailOpen','novaFocusLayoutApplied','novaCalmLayoutApplied','wlaMiddlePanelHeights','novaFocusWorkspace','wlaControlDrawerCollapsed'];
      staleKeys.forEach(k=>{try{localStorage.removeItem(k);}catch(e){}});
      localStorage.setItem(key,wanted);
      document.body.dataset.novaLayoutAutoReset='1';
      return true;
    }catch(e){return false;}
  }
  function hardenLayout(){
    try{
      resetStaleLayoutStorage();
      document.body.classList.remove('gui-overhaul-v2');
      document.body.classList.add('gui-overhaul-v3');
      /* A stale right drawer was producing the grey/blank right panel. Start closed; only user clicks reopen it. */
      if(!document.body.dataset.novaRightUserOpened){ document.body.classList.remove('orbit-right-open'); }
      const left = document.getElementById('orbitDrawer');
      const right = document.getElementById('orbitRightDrawer');
      if(left){ left.setAttribute('aria-label','Nova docked left drawer'); left.setAttribute('data-layout-role','overlay-left-drawer'); }
      if(right){ right.setAttribute('aria-label','Nova docked right inspector'); right.setAttribute('data-layout-role','overlay-right-drawer'); }
      document.querySelectorAll('#orbitNav .orbitNavButton').forEach(function(btn){
        const label = btn.querySelector('.label');
        if(label){ btn.setAttribute('title', label.textContent.trim()); }
      });
    }catch(e){}
  }
  function diagnose(){
    hardenLayout();
    const rail=rect('orbitNav')||rect('edgeRail');
    const left=rect('orbitDrawer');
    const right=rect('orbitRightDrawer');
    const chat=rect('chat');
    const composerEl=document.querySelector('.composer, .composerPanel, #composer');
    const composer=composerEl?(()=>{const r=composerEl.getBoundingClientRect();const cs=getComputedStyle(composerEl);return {x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom,display:cs.display,visibility:cs.visibility,position:cs.position};})():null;
    const warnings=[];
    if(rail&&rail.w < 190&&window.innerWidth > 1100){ warnings.push('left rail is too narrow for readable labels'); }
    const leftOpen = !!(left && Number(left.opacity || '0') > 0.05 && left.visibility !== 'hidden');
    if(rail&&left&&leftOpen&&document.body.classList.contains('orbitDrawerOpen')&&left.x < rail.right + 4){ warnings.push('left drawer overlaps navigation rail'); }
    if(right&&right.visibility!=='hidden'&&!document.body.classList.contains('orbit-right-open')){ warnings.push('right drawer visible while closed'); }
    if(composer&&composer.right > window.innerWidth + 2){ warnings.push('composer extends off right edge'); }
    if(chat&&chat.w < Math.min(900, window.innerWidth * 0.48)){ warnings.push('chat canvas is unusually narrow'); }
    return {ok:warnings.length===0, version:window.NovaGuiOverhaulV3.version, patchId:window.NovaGuiOverhaulV3.patchId, storageVersion:window.NovaGuiOverhaulV3.storageVersion, autoReset:document.body.dataset.novaLayoutAutoReset==='1', warnings, viewport:{w:window.innerWidth,h:window.innerHeight}, rail, leftDrawer:left, rightDrawer:right, chat, composer, bodyClass:document.body.className};
  }
  window.novaGuiHardenLayout = hardenLayout;
  window.novaGuiLayoutDiagnose = diagnose;
  window.NovaGuiOverhaulV3.hardenLayout = hardenLayout;
  window.NovaGuiOverhaulV3.diagnose = diagnose;
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', hardenLayout);
  else hardenLayout();
  setTimeout(hardenLayout, 250);
  setTimeout(hardenLayout, 1000);
})();
</script>
"""


def apply_gui_layout_overhaul(html: str) -> str:
    """Inject the modular CSS/JS layer into Nova's legacy static HTML."""
    if "gui-overhaul-v3" not in html:
        html = html.replace(
            'body class="nova-orbit-shell clean-workspace calm-workspace focus-workspace gui-sanity-rescue"',
            'body class="nova-orbit-shell clean-workspace calm-workspace focus-workspace gui-sanity-rescue gui-overhaul-v3"',
        )
    if "GUI layout overhaul v3" not in html:
        html = html.replace("</style>", GUI_LAYOUT_OVERHAUL_CSS + "\n</style>", 1)
    if "NovaGuiOverhaulV3" not in html:
        html = html.replace("</body>", GUI_LAYOUT_OVERHAUL_JS + "\n</body>", 1)
    return html
