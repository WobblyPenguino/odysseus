from __future__ import annotations

"""Cyberpunk 2077 inspired visual skin for Nova's Web UI.

This module only injects presentation-layer CSS/JS so it can be iterated on
without disturbing routes, commands or layout safety logic.
"""

CYBERPUNK_THEME_CSS = r"""
/* v55.3.164 cyberpunk GUI makeover v1: neon yellow/cyan/magenta shell with angular chrome. */
body.nova-orbit-shell.nova-theme-cyberpunk2077{
  --cp-bg:#06070b!important;
  --cp-bg2:#0a0c12!important;
  --cp-panel:rgba(12,14,20,.88)!important;
  --cp-panel-2:rgba(16,19,27,.95)!important;
  --cp-ink:#d8ffff!important;
  --cp-muted:#7fb8c7!important;
  --cp-yellow:#f5e642!important;
  --cp-yellow-2:#ffd83d!important;
  --cp-cyan:#3ef2ff!important;
  --cp-cyan-2:#8ff7ff!important;
  --cp-pink:#ff4fd8!important;
  --cp-red:#ff5d73!important;
  --cp-green:#7eff95!important;
  background:radial-gradient(circle at 18% 16%,rgba(255,79,216,.16),transparent 22%),radial-gradient(circle at 82% 8%,rgba(62,242,255,.14),transparent 24%),linear-gradient(180deg,#07080d,#040507)!important;
  color:var(--cp-ink)!important;
}
body.nova-orbit-shell.nova-theme-cyberpunk2077::before{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background:repeating-linear-gradient(180deg,rgba(255,255,255,.018) 0 1px,transparent 1px 4px),linear-gradient(90deg,rgba(245,230,66,.06),transparent 24%,transparent 76%,rgba(62,242,255,.05));
  opacity:.42;mix-blend-mode:screen;
}
body.nova-orbit-shell.nova-theme-cyberpunk2077::after{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background:linear-gradient(transparent 97%,rgba(62,242,255,.08) 100%),linear-gradient(90deg,transparent 97%,rgba(255,79,216,.08) 100%);
  background-size:100% 28px,28px 100%;opacity:.18;
}
body.nova-orbit-shell.nova-theme-cyberpunk2077 main[data-ui-overhaul]{
  position:relative;z-index:1;
  background:linear-gradient(180deg,rgba(5,7,11,.82),rgba(5,7,11,.96))!important;
}
body.nova-orbit-shell.nova-theme-cyberpunk2077 .topbar,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .toolbar,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .header,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .toprow{
  background:linear-gradient(90deg,rgba(255,79,216,.10),rgba(8,12,17,.96) 22%,rgba(8,12,17,.97) 78%,rgba(62,242,255,.12))!important;
  border-bottom:1px solid rgba(62,242,255,.24)!important;
  box-shadow:0 0 0 1px rgba(245,230,66,.10) inset,0 8px 30px rgba(0,0,0,.40)!important;
}
body.nova-orbit-shell.nova-theme-cyberpunk2077 .sidebar.card,
body.nova-orbit-shell.nova-theme-cyberpunk2077 #orbitDrawer,
body.nova-orbit-shell.nova-theme-cyberpunk2077 #orbitRightDrawer,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .card,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .artifact,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .item,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .assistantBoxPanel,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .transparentOutputPanel,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .communicationCentre,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .voiceGuardCard,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .codepreview,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .popupPanel,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .settingsPanel{
  background:linear-gradient(180deg,rgba(10,12,18,.94),rgba(7,9,14,.96))!important;
  color:var(--cp-ink)!important;
  border:1px solid rgba(62,242,255,.26)!important;
  box-shadow:0 0 0 1px rgba(255,79,216,.10) inset,0 0 26px rgba(62,242,255,.08),0 18px 40px rgba(0,0,0,.42)!important;
}
body.nova-orbit-shell.nova-theme-cyberpunk2077 .sidebar.card,
body.nova-orbit-shell.nova-theme-cyberpunk2077 #orbitDrawer,
body.nova-orbit-shell.nova-theme-cyberpunk2077 #orbitRightDrawer,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .msg,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .composer,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .card{
  clip-path:polygon(0 0,calc(100% - 14px) 0,100% 14px,100% 100%,14px 100%,0 calc(100% - 14px));
}
body.nova-orbit-shell.nova-theme-cyberpunk2077 #chat .name,
body.nova-orbit-shell.nova-theme-cyberpunk2077 #chat .msg{
  background:linear-gradient(180deg,rgba(8,11,18,.94),rgba(12,15,23,.90))!important;
  border:1px solid rgba(62,242,255,.22)!important;
  box-shadow:0 0 0 1px rgba(245,230,66,.05) inset,0 0 18px rgba(62,242,255,.05)!important;
}
body.nova-orbit-shell.nova-theme-cyberpunk2077 .msg.you,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .you .msg{
  border-color:rgba(245,230,66,.34)!important;
  box-shadow:0 0 0 1px rgba(245,230,66,.08) inset,0 0 18px rgba(245,230,66,.08)!important;
}
body.nova-orbit-shell.nova-theme-cyberpunk2077 #orbitNav .orbitNavButton,
body.nova-orbit-shell.nova-theme-cyberpunk2077 button,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .chip,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .btn{
  border:1px solid rgba(62,242,255,.28)!important;
  background:linear-gradient(180deg,rgba(18,22,32,.94),rgba(9,12,17,.96))!important;
  color:#f7ffff!important;
  text-shadow:0 0 8px rgba(62,242,255,.25)!important;
  box-shadow:0 0 0 1px rgba(255,79,216,.08) inset!important;
}
body.nova-orbit-shell.nova-theme-cyberpunk2077 #orbitNav .orbitNavButton.active,
body.nova-orbit-shell.nova-theme-cyberpunk2077 button.primary,
body.nova-orbit-shell.nova-theme-cyberpunk2077 button.send,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .sendBtn,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .btn-primary{
  background:linear-gradient(90deg,rgba(245,230,66,.94),rgba(255,217,61,.96))!important;
  color:#161714!important;
  border-color:rgba(255,240,120,.84)!important;
  text-shadow:none!important;
  box-shadow:0 0 26px rgba(245,230,66,.18)!important;
}
body.nova-orbit-shell.nova-theme-cyberpunk2077 button:hover,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .orbitNavButton:hover{
  border-color:rgba(255,79,216,.44)!important;
  box-shadow:0 0 0 1px rgba(255,79,216,.12) inset,0 0 22px rgba(255,79,216,.10)!important;
}
body.nova-orbit-shell.nova-theme-cyberpunk2077 input,
body.nova-orbit-shell.nova-theme-cyberpunk2077 textarea,
body.nova-orbit-shell.nova-theme-cyberpunk2077 select{
  background:rgba(5,7,12,.92)!important;
  color:#ecfeff!important;
  border:1px solid rgba(62,242,255,.28)!important;
  caret-color:var(--cp-yellow)!important;
  box-shadow:0 0 0 1px rgba(62,242,255,.05) inset!important;
}
body.nova-orbit-shell.nova-theme-cyberpunk2077 input:focus,
body.nova-orbit-shell.nova-theme-cyberpunk2077 textarea:focus,
body.nova-orbit-shell.nova-theme-cyberpunk2077 select:focus{
  outline:none!important;
  border-color:rgba(245,230,66,.60)!important;
  box-shadow:0 0 0 1px rgba(245,230,66,.16) inset,0 0 18px rgba(245,230,66,.10)!important;
}
body.nova-orbit-shell.nova-theme-cyberpunk2077 .composer{
  background:linear-gradient(180deg,rgba(8,10,14,.96),rgba(10,13,19,.98))!important;
  border:1px solid rgba(62,242,255,.30)!important;
  box-shadow:0 0 0 1px rgba(255,79,216,.08) inset,0 14px 50px rgba(0,0,0,.46),0 0 22px rgba(62,242,255,.08)!important;
}
body.nova-orbit-shell.nova-theme-cyberpunk2077 .composer::before{
  content:'NOVA // CYBERPUNK CONTROL LINK';
  display:block;
  font-size:10px;letter-spacing:.22em;text-transform:uppercase;
  color:rgba(245,230,66,.86);margin-bottom:8px;
}
body.nova-orbit-shell.nova-theme-cyberpunk2077 #orbitNav .orbitNavButton .label,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .muted,
body.nova-orbit-shell.nova-theme-cyberpunk2077 small{
  color:var(--cp-muted)!important;
}
body.nova-orbit-shell.nova-theme-cyberpunk2077 .novaVersionBadge,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .versionBadge{
  background:linear-gradient(90deg,rgba(62,242,255,.16),rgba(255,79,216,.18))!important;
  color:#ecffff!important;border:1px solid rgba(62,242,255,.30)!important;
}
body.nova-orbit-shell.nova-theme-cyberpunk2077 .orbitSectionTitle,
body.nova-orbit-shell.nova-theme-cyberpunk2077 h1,
body.nova-orbit-shell.nova-theme-cyberpunk2077 h2,
body.nova-orbit-shell.nova-theme-cyberpunk2077 h3{
  color:var(--cp-yellow)!important;
  letter-spacing:.06em!important;
  text-transform:uppercase!important;
  text-shadow:0 0 10px rgba(245,230,66,.14)!important;
}
body.nova-orbit-shell.nova-theme-cyberpunk2077 a{color:var(--cp-cyan-2)!important;}
body.nova-orbit-shell.nova-theme-cyberpunk2077 ::selection{background:rgba(255,79,216,.28)!important;color:#fff!important;}
body.nova-orbit-shell.nova-theme-cyberpunk2077 ::-webkit-scrollbar{width:12px;height:12px;}
body.nova-orbit-shell.nova-theme-cyberpunk2077 ::-webkit-scrollbar-track{background:#07090d;}
body.nova-orbit-shell.nova-theme-cyberpunk2077 ::-webkit-scrollbar-thumb{background:linear-gradient(180deg,rgba(245,230,66,.65),rgba(255,79,216,.60));border:2px solid #07090d;border-radius:10px;}
body.nova-orbit-shell.nova-theme-cyberpunk2077 .novaAiHelpDot{
  background:rgba(245,230,66,.16)!important;
  color:#fff587!important;
  border-color:rgba(245,230,66,.36)!important;
  box-shadow:0 0 12px rgba(245,230,66,.22)!important;
}
body.nova-orbit-shell.nova-theme-cyberpunk2077 .novaAiHelpPanel{
  background:linear-gradient(180deg,rgba(8,10,16,.98),rgba(10,13,20,.98))!important;
  border-color:rgba(245,230,66,.35)!important;
  box-shadow:0 24px 80px rgba(0,0,0,.74),0 0 54px rgba(245,230,66,.12)!important;
}
body.nova-orbit-shell.nova-theme-cyberpunk2077 .novaAiHelpPanel h3{color:var(--cp-yellow)!important;}
@keyframes novaNeonPulse{0%,100%{box-shadow:0 0 0 1px rgba(255,79,216,.08) inset,0 0 16px rgba(62,242,255,.06);}50%{box-shadow:0 0 0 1px rgba(255,79,216,.14) inset,0 0 22px rgba(62,242,255,.12);}}
body.nova-orbit-shell.nova-theme-cyberpunk2077 .sidebar.card,
body.nova-orbit-shell.nova-theme-cyberpunk2077 #orbitDrawer,
body.nova-orbit-shell.nova-theme-cyberpunk2077 #orbitRightDrawer,
body.nova-orbit-shell.nova-theme-cyberpunk2077 .composer{animation:novaNeonPulse 4.5s ease-in-out infinite;}
"""

CYBERPUNK_THEME_JS = r"""
<script>
window.NovaCyberpunkTheme = window.NovaCyberpunkTheme || {theme:'cyberpunk2077-nova-v1', patchId:'cyberpunk2077-gui-makeover-v1'};
(function(){
  function apply(){
    try{
      document.body.classList.add('nova-theme-cyberpunk2077');
      document.documentElement.style.colorScheme='dark';
      document.body.dataset.novaTheme='cyberpunk2077';
      const badge=(document.querySelector('.novaVersionBadge,.versionBadge')||document.querySelector('.topbar span,.toolbar span'));
      if(badge && !document.getElementById('novaCyberpunkBadge')){
        const tag=document.createElement('span');
        tag.id='novaCyberpunkBadge';
        tag.textContent=' CYBERPUNK ';
        tag.style.cssText='margin-left:8px;padding:2px 8px;border:1px solid rgba(245,230,66,.34);border-radius:999px;background:rgba(245,230,66,.10);color:#fff587;font-size:10px;letter-spacing:.15em;vertical-align:middle;';
        badge.parentNode.insertBefore(tag,badge.nextSibling);
      }
    }catch(e){ window.NovaCyberpunkTheme.error=String(e); }
  }
  function status(){
    const body=document.body;
    return {
      ok: !!body && body.classList.contains('nova-theme-cyberpunk2077'),
      theme: 'cyberpunk2077-nova-v1',
      patchId: window.NovaCyberpunkTheme.patchId,
      bodyClass: body ? body.className : '',
      helpDots: document.querySelectorAll('.novaAiHelpDot').length,
      drawerVisible: !!document.body.classList.contains('orbitDrawerOpen')
    };
  }
  window.novaCyberpunkThemeStatus=status;
  window.NovaCyberpunkTheme.status=status;
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply);else apply();
  setTimeout(apply,150);setTimeout(apply,800);
})();
</script>
"""


def apply_cyberpunk_theme(html: str) -> str:
    if 'cyberpunk GUI makeover v1' not in html:
        html = html.replace('</style>', CYBERPUNK_THEME_CSS + "\n</style>", 1)
    if 'NovaCyberpunkTheme' not in html:
        html = html.replace('</body>', CYBERPUNK_THEME_JS + "\n</body>", 1)
    return html
