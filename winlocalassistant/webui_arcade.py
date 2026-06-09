from __future__ import annotations

"""Local-only Nova Arcade GUI runtime.

The arcade is component-style: a registry describes games, and the browser
runtime launches the selected game in an isolated overlay. It does not execute
model output as code and does not write project files.
"""

ARCADE_CSS = r"""
/* v55.3.164 Nova Arcade v1: local-only cyberpunk mini-game shelf. */
#novaArcadeOverlay{position:fixed!important;inset:0!important;z-index:9800!important;display:none;align-items:center;justify-content:center;background:rgba(0,0,0,.68)!important;backdrop-filter:blur(8px)!important;padding:18px!important;}
#novaArcadePanel{width:min(980px,calc(100vw - 36px))!important;max-height:90vh!important;overflow:auto!important;background:linear-gradient(180deg,rgba(7,9,15,.98),rgba(9,11,18,.98))!important;color:#eaffff!important;border:1px solid rgba(245,230,66,.32)!important;border-radius:22px!important;box-shadow:0 30px 120px rgba(0,0,0,.78),0 0 70px rgba(245,230,66,.10)!important;padding:16px!important;}
.novaArcadeHeader{display:flex!important;gap:12px!important;align-items:center!important;justify-content:space-between!important;border-bottom:1px solid rgba(245,230,66,.22)!important;padding-bottom:10px!important;margin-bottom:12px!important;}
.novaArcadeHeader h2{margin:0!important;color:#fff45f!important;letter-spacing:.09em!important;text-transform:uppercase!important;}
.novaArcadeGrid{display:grid!important;grid-template-columns:260px minmax(320px,1fr)!important;gap:14px!important;}
.novaArcadeGameCard{border:1px solid rgba(62,242,255,.24)!important;border-radius:16px!important;padding:12px!important;background:rgba(62,242,255,.05)!important;}
#novaSystemRunnerCanvas{width:100%!important;max-width:640px!important;aspect-ratio:16/10!important;background:#03050a!important;border:1px solid rgba(62,242,255,.32)!important;border-radius:16px!important;box-shadow:0 0 42px rgba(62,242,255,.10)!important;display:block!important;}
.novaArcadeHud{display:flex!important;gap:8px!important;flex-wrap:wrap!important;margin:8px 0!important;}
.novaArcadeHud span{border:1px solid rgba(245,230,66,.26)!important;border-radius:999px!important;padding:4px 8px!important;background:rgba(245,230,66,.08)!important;color:#fff8a2!important;font-size:12px!important;}
@media(max-width:900px){.novaArcadeGrid{grid-template-columns:1fr!important;}#novaSystemRunnerCanvas{max-width:100%!important;}}
"""

ARCADE_JS = r"""
<script>
window.NovaArcade = window.NovaArcade || {version:'v55.3.164-arcade-v1', games:[]};
(function(){
  const registry=[{game_id:'system-runner',name:'Nova: System Runner',description:'Steer the Nova core, dodge bugs/corruption, collect upgrade shards, save a local high score.',icon:'◈',status:'playable-local',component:'systemRunner'}];
  let runner=null;
  function esc(s){return String(s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
  function ensureOverlay(){let ov=document.getElementById('novaArcadeOverlay');if(ov)return ov;ov=document.createElement('div');ov.id='novaArcadeOverlay';document.body.appendChild(ov);return ov;}
  function open(){const ov=ensureOverlay();ov.style.display='flex';ov.innerHTML='<div id="novaArcadePanel"><div class="novaArcadeHeader"><h2>Nova Arcade</h2><div class="row wrap"><button type="button" onclick="NovaArcade.launch(\'system-runner\')">Launch System Runner</button><button type="button" onclick="NovaArcade.close()">Close</button></div></div><div class="novaArcadeGrid"><div class="novaArcadeGameCard"><h3>◈ Nova: System Runner</h3><p>Cyberpunk runner. Avoid magenta bugs, collect yellow upgrades, protect the Nova core.</p><p><b>Controls:</b> Arrow keys or WASD. P pauses.</p><p><b>Status:</b> playable-local. High score stays in browser localStorage.</p><button type="button" onclick="NovaArcade.launch(\'system-runner\')">Play</button></div><div><canvas id="novaSystemRunnerCanvas" width="800" height="500" aria-label="Nova System Runner game canvas"></canvas><div class="novaArcadeHud"><span id="novaRunnerScore">Score 0</span><span id="novaRunnerHigh">High 0</span><span id="novaRunnerState">Ready</span></div><div class="small">Start with Play. Move the core with arrow keys/WASD. Collect upgrade shards and dodge corruption.</div></div></div></div>';}
  function close(){if(runner){runner.stop();runner=null;}const ov=document.getElementById('novaArcadeOverlay');if(ov)ov.style.display='none';}
  function launch(id){open(); if(id!=='system-runner')return; setTimeout(startSystemRunner,30);}
  function startSystemRunner(){const canvas=document.getElementById('novaSystemRunnerCanvas'); if(!canvas)return; if(runner)runner.stop(); const ctx=canvas.getContext('2d'); const keys={}; let raf=0,last=performance.now(),spawn=0,score=0,high=Number(localStorage.getItem('novaArcade.systemRunner.highScore')||0),state='running'; const player={x:80,y:250,r:14,vy:0}; let bugs=[],ups=[]; const scoreEl=document.getElementById('novaRunnerScore'), highEl=document.getElementById('novaRunnerHigh'), stateEl=document.getElementById('novaRunnerState'); function hud(){scoreEl.textContent='Score '+Math.floor(score);highEl.textContent='High '+Math.floor(high);stateEl.textContent=state==='running'?'Running':state;} function onKey(e){const k=e.key.toLowerCase(); if(['arrowup','arrowdown','w','s','p'].includes(k)){e.preventDefault();} if(k==='p'){state=state==='paused'?'running':'paused';hud(); if(state==='running')loop(performance.now()); return;} keys[k]=e.type==='keydown';}
    window.addEventListener('keydown',onKey); window.addEventListener('keyup',onKey); function stop(){cancelAnimationFrame(raf);window.removeEventListener('keydown',onKey);window.removeEventListener('keyup',onKey);} function reset(){bugs=[];ups=[];score=0;player.x=80;player.y=250;state='running';hud();}
    function collide(a,b){const dx=a.x-b.x,dy=a.y-b.y;return Math.hypot(dx,dy)<(a.r+(b.r||14));}
    function drawGrid(){ctx.fillStyle='#03050a';ctx.fillRect(0,0,800,500);ctx.strokeStyle='rgba(62,242,255,.11)';ctx.lineWidth=1;for(let x=0;x<800;x+=32){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,500);ctx.stroke();}for(let y=0;y<500;y+=32){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(800,y);ctx.stroke();}}
    function loop(now){const dt=Math.min(.04,(now-last)/1000);last=now;if(state!=='running'){drawGrid();ctx.fillStyle='#fff45f';ctx.font='bold 30px monospace';ctx.fillText(state==='game over'?'SYSTEM CORRUPTED':'PAUSED',260,240);return;} score+=dt*18; spawn+=dt; if(keys.arrowup||keys.w)player.y-=260*dt;if(keys.arrowdown||keys.s)player.y+=260*dt;player.y=Math.max(24,Math.min(476,player.y)); if(spawn>.72){spawn=0;bugs.push({x:830,y:30+Math.random()*440,r:13+Math.random()*12,s:160+Math.random()*120}); if(Math.random()<.55)ups.push({x:860,y:30+Math.random()*440,r:9,s:135+Math.random()*80});} bugs.forEach(b=>b.x-=b.s*dt); ups.forEach(u=>u.x-=u.s*dt); bugs=bugs.filter(b=>b.x>-40); ups=ups.filter(u=>u.x>-40); ups=ups.filter(u=>{if(collide(player,u)){score+=80;return false;}return true;}); if(bugs.some(b=>collide(player,b))){state='game over'; high=Math.max(high,score); localStorage.setItem('novaArcade.systemRunner.highScore',String(Math.floor(high))); hud(); drawGrid();ctx.fillStyle='#ff4fd8';ctx.font='bold 26px monospace';ctx.fillText('CORRUPTION HIT — PRESS PLAY TO RESTART',105,248);return;} high=Math.max(high,score); hud(); drawGrid();ctx.fillStyle='#f5e642';ctx.shadowColor='#f5e642';ctx.shadowBlur=16;ctx.beginPath();ctx.arc(player.x,player.y,player.r,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;bugs.forEach(b=>{ctx.fillStyle='#ff4fd8';ctx.strokeStyle='#ff7be4';ctx.fillRect(b.x-b.r,b.y-b.r,b.r*2,b.r*2);ctx.strokeRect(b.x-b.r,b.y-b.r,b.r*2,b.r*2);});ups.forEach(u=>{ctx.fillStyle='#3ef2ff';ctx.beginPath();ctx.moveTo(u.x,u.y-u.r);ctx.lineTo(u.x+u.r,u.y);ctx.lineTo(u.x,u.y+u.r);ctx.lineTo(u.x-u.r,u.y);ctx.closePath();ctx.fill();});ctx.fillStyle='rgba(245,230,66,.9)';ctx.font='12px monospace';ctx.fillText('NOVA CORE // SYSTEM RUNNER',18,24);raf=requestAnimationFrame(loop);} runner={stop,reset}; reset(); loop(performance.now());}
  function status(){return {ok:true,version:window.NovaArcade.version,games:registry,overlay:!!document.getElementById('novaArcadeOverlay')};}
  function ensureButton(){if(document.getElementById('novaArcadeHeaderBtn'))return;const holder=document.querySelector('.orbitHeaderActions,.topbar .row,.topbar')||document.body;const b=document.createElement('button');b.id='novaArcadeHeaderBtn';b.textContent='arcade';b.type='button';b.onclick=open;holder.appendChild(b);}
  window.NovaArcade={version:'v55.3.164-arcade-v1',games:registry,open,close,launch,status};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ensureButton);else ensureButton();setTimeout(ensureButton,500);setTimeout(ensureButton,1600);
})();
</script>
"""


def apply_arcade(html: str) -> str:
    if "Nova Arcade v1" not in html:
        html = html.replace("</style>", ARCADE_CSS + "\n</style>", 1)
    if "window.NovaArcade" not in html:
        html = html.replace("</body>", ARCADE_JS + "\n</body>", 1)
    return html
