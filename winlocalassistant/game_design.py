from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class GameDesignIntent:
    raw_text: str
    normalized_text: str
    requested_game_type: str
    explicit_game_type: bool
    genre: str
    core_objects: list[str] = field(default_factory=list)
    mechanics: list[str] = field(default_factory=list)
    required_behaviours: list[str] = field(default_factory=list)
    allowed_template_family: str = "custom_canvas_game"
    assumptions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_GAME_ALIASES: list[tuple[str, str, str, list[str], list[str]]] = [
    ("snake", "snake", "grid_survival", ["snake", "food"], ["growth", "self collision", "wall collision"]),
    ("pong", "pong", "arcade_paddle", ["paddle", "ball"], ["bounce", "opponent", "score"]),
    ("breakout", "breakout", "brick_breaker", ["paddle", "ball", "bricks"], ["brick collision", "levels", "score"]),
    ("tetris", "tetris", "falling_blocks", ["blocks", "grid"], ["rotation", "line clearing", "score"]),
    ("platformer", "platformer", "platformer", ["player", "platforms", "goal"], ["jumping", "gravity", "collision"]),
    ("space shooter", "space shooter", "shooter", ["ship", "enemies", "bullets"], ["shooting", "enemy waves", "score"]),
    ("shooter", "shooter", "shooter", ["player", "enemies", "projectiles"], ["shooting", "dodging", "score"]),
    ("maze", "maze", "maze", ["player", "maze", "exit"], ["movement", "walls", "goal"]),
    ("memory", "memory card", "card_match", ["cards", "pairs"], ["flipping", "matching", "moves"]),
    ("clicker", "clicker", "incremental", ["button", "points", "upgrades"], ["clicking", "upgrades", "progress"]),
    ("runner", "runner", "endless_runner", ["runner", "obstacles"], ["jumping", "obstacles", "distance"]),
    ("fishing", "fishing", "collection", ["hook", "fish", "water"], ["catching", "timing", "score"]),
    ("racing", "racing", "driving", ["car", "track", "obstacles"], ["steering", "laps", "timer"]),
    ("quiz", "quiz", "quiz", ["questions", "answers"], ["select answer", "score", "feedback"]),
    ("dodge", "dodge", "dodge", ["player", "obstacles"], ["dodging", "collision", "score"]),
]

_BASE_BEHAVIOURS = [
    "visible instructions",
    "player input controls",
    "state update loop or turn progression",
    "objective or win/lose condition",
    "score/progress feedback",
    "restart/reset flow",
]


def analyze_game_request(user_text: str) -> GameDesignIntent:
    raw = strip_interactive_clarification(user_text or "")
    low = _normalise(raw)
    explicit_type = ""
    genre = "custom_game"
    objects: list[str] = []
    mechanics: list[str] = []
    for needle, name, found_genre, found_objects, found_mechanics in _GAME_ALIASES:
        if needle in low:
            explicit_type = name
            genre = found_genre
            objects = list(found_objects)
            mechanics = list(found_mechanics)
            break
    if not explicit_type:
        theme = _extract_about_theme(low)
        if theme:
            explicit_type = f"{theme} game"
            genre = "custom_theme_game"
            objects = _objects_from_words(explicit_type)
            if len(objects) < 3:
                objects = ["player", theme, "hazards"]
            mechanics = _mechanics_from_text(low) or ["collecting", "dodging"]
        else:
            explicit_type = _extract_named_game(low)
        if theme:
            pass
        elif explicit_type:
            genre = "custom_named_game"
            objects = _objects_from_words(explicit_type)
            mechanics = _mechanics_from_text(low)
        elif "game" in low:
            explicit_type = "simple browser game"
            genre = "generic_browser_game"
            objects = ["player", "targets", "hazards"]
            mechanics = _mechanics_from_text(low)
        else:
            explicit_type = ""
            genre = "not_game"
    assumptions: list[str] = []
    if genre == "generic_browser_game":
        assumptions.append("The user asked for a vague game, so Nova should create a small custom browser game and state the assumed objective.")
    behaviours = list(_BASE_BEHAVIOURS)
    for mech in mechanics:
        if mech not in behaviours:
            behaviours.append(mech)
    return GameDesignIntent(raw, low, explicit_type, genre not in {"generic_browser_game", "not_game"}, genre, objects, mechanics, behaviours, "custom_canvas_game", assumptions)


def game_prompt_requirements(user_text: str) -> dict[str, Any]:
    intent = analyze_game_request(user_text)
    return {
        "game_design": intent.to_dict(),
        "prompt_rules": [
            "Build the requested game type/theme, not a fixed dodge demo unless the user asked for dodge.",
            "Use a generic game architecture that adapts objects, mechanics, scoring and instructions to the user prompt.",
            "Include controls, objective, progress/score, interaction/collision or turn logic, restart, and instructions.",
        ],
    }


def build_generic_canvas_game_project(user_text: str) -> dict[str, Any]:
    intent = analyze_game_request(user_text)
    if intent.genre == "platformer":
        return _build_platformer_game_project(user_text, intent)
    title = _title(intent.requested_game_type or "Custom Browser Game")
    slug = re.sub(r"[^a-z0-9]+", "", title.lower()) or "customgame"
    objects = intent.core_objects or ["player", "targets", "hazards"]
    mechanics = intent.mechanics or ["collect targets", "avoid hazards"]
    objective = _objective_sentence(intent)
    object_label = objects[1] if len(objects) > 1 else "targets"
    hazard_label = objects[2] if len(objects) > 2 else "hazards"
    html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>{title}</title>
  <link rel=\"stylesheet\" href=\"style.css\">
</head>
<body>
  <main class=\"game-shell\">
    <header>
      <h1>{title}</h1>
      <div class=\"scoreboard\"><span>Score: <strong id=\"score\">0</strong></span><span>Best: <strong id=\"best\">0</strong></span></div>
    </header>
    <p id=\"instructions\" class=\"instructions\">{objective} Use arrow keys or WASD. Collect {object_label}, avoid {hazard_label}, and press Start/Restart to play again.</p>
    <canvas id=\"gameCanvas\" width=\"760\" height=\"430\" aria-label=\"{title} play area\"></canvas>
    <div class=\"controls\"><button id=\"startBtn\">Start / Restart</button><button id=\"pauseBtn\">Pause</button></div>
  </main>
  <script src=\"app.js\"></script>
</body>
</html>
"""
    css = """*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:#eef4ff;color:#132033;font-family:Segoe UI,Arial,sans-serif}.game-shell{width:min(900px,96vw);display:grid;gap:12px}header{display:flex;justify-content:space-between;align-items:center;gap:16px}.scoreboard{display:flex;gap:18px;font-size:18px}.instructions{background:#fff;border-left:5px solid #2563eb;padding:12px;box-shadow:0 8px 20px #0001}canvas{width:100%;aspect-ratio:76/43;background:#111827;border:3px solid #1f2937;box-shadow:0 18px 44px #0002}.controls{display:flex;gap:10px}button{border:0;background:#2563eb;color:white;padding:12px 16px;font-weight:800;cursor:pointer;border-radius:10px}button:hover{background:#1d4ed8}
"""
    js = f"""const canvas=document.getElementById('gameCanvas');
const ctx=canvas.getContext('2d');
const scoreEl=document.getElementById('score');
const bestEl=document.getElementById('best');
const startBtn=document.getElementById('startBtn');
const pauseBtn=document.getElementById('pauseBtn');
const keys={{left:false,right:false,up:false,down:false}};
let running=false,paused=false,gameOver=false,score=0,best=Number(localStorage.getItem('{slug}Best')||0),last=0,spawnTimer=0;
bestEl.textContent=String(best);
const player={{x:360,y:210,w:28,h:28,speed:250,color:'#22c55e'}};
let targets=[],hazards=[];
function resetGame(){{running=true;paused=false;gameOver=false;score=0;spawnTimer=0;targets=[];hazards=[];player.x=360;player.y=210;scoreEl.textContent='0';last=performance.now();requestAnimationFrame(loop)}}
function rectsHit(a,b){{return a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y}}
function spawnThing(list,color,points,harmful=false){{list.push({{x:Math.random()*(canvas.width-24),y:Math.random()*(canvas.height-24),w:24,h:24,color,points,harmful,dx:(Math.random()-.5)*70,dy:(Math.random()-.5)*70}})}}
function update(dt){{if(paused||gameOver)return; if(keys.left)player.x-=player.speed*dt;if(keys.right)player.x+=player.speed*dt;if(keys.up)player.y-=player.speed*dt;if(keys.down)player.y+=player.speed*dt;player.x=Math.max(0,Math.min(canvas.width-player.w,player.x));player.y=Math.max(0,Math.min(canvas.height-player.h,player.y));spawnTimer+=dt;if(spawnTimer>0.75){{spawnTimer=0;spawnThing(targets,'#facc15',10,false);if(Math.random()<0.7)spawnThing(hazards,'#ef4444',-1,true)}}for(const item of [...targets,...hazards]){{item.x+=item.dx*dt;item.y+=item.dy*dt;if(item.x<0||item.x>canvas.width-item.w)item.dx*=-1;if(item.y<0||item.y>canvas.height-item.h)item.dy*=-1}}targets=targets.filter(t=>{{if(rectsHit(player,t)){{score+=t.points;scoreEl.textContent=String(score);return false}}return true}});for(const h of hazards){{if(rectsHit(player,h)){{gameOver=true;running=false;best=Math.max(best,score);localStorage.setItem('{slug}Best',String(best));bestEl.textContent=String(best)}}}}}};
function draw(){{ctx.clearRect(0,0,canvas.width,canvas.height);ctx.fillStyle='#111827';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.fillStyle=player.color;ctx.fillRect(player.x,player.y,player.w,player.h);for(const t of targets){{ctx.fillStyle=t.color;ctx.fillRect(t.x,t.y,t.w,t.h)}}for(const h of hazards){{ctx.fillStyle=h.color;ctx.fillRect(h.x,h.y,h.w,h.h)}}if(!running){{ctx.fillStyle='rgba(255,255,255,.92)';ctx.font='26px Segoe UI';ctx.textAlign='center';ctx.fillText(gameOver?'Game over - press Start':'{title}: press Start',canvas.width/2,canvas.height/2)}}if(paused){{ctx.fillStyle='white';ctx.font='28px Segoe UI';ctx.textAlign='center';ctx.fillText('Paused',canvas.width/2,canvas.height/2+40)}}}}
function loop(now){{const dt=Math.min(0.033,(now-last)/1000);last=now;if(running)update(dt);draw();if(running)requestAnimationFrame(loop)}}
document.addEventListener('keydown',e=>{{const k=e.key.toLowerCase();if(k==='arrowleft'||k==='a')keys.left=true;if(k==='arrowright'||k==='d')keys.right=true;if(k==='arrowup'||k==='w')keys.up=true;if(k==='arrowdown'||k==='s')keys.down=true;if(k===' '&&!running)resetGame()}});
document.addEventListener('keyup',e=>{{const k=e.key.toLowerCase();if(k==='arrowleft'||k==='a')keys.left=false;if(k==='arrowright'||k==='d')keys.right=false;if(k==='arrowup'||k==='w')keys.up=false;if(k==='arrowdown'||k==='s')keys.down=false}});
startBtn.addEventListener('click',resetGame);pauseBtn.addEventListener('click',()=>{{paused=!paused;if(running&&!paused){{last=performance.now();requestAnimationFrame(loop)}}}});draw();
"""
    readme = f"""# {title}

A dependency-free custom browser game generated for: `{user_text}`.

## Objective

{objective}

## Mechanics

- Core objects: {', '.join(objects)}
- Mechanics: {', '.join(mechanics)}
- Controls: Arrow keys or WASD
- Includes score/progress, moving objects, collision/interaction, game-over state, restart and instructions.

## Run

Open `index.html` in a browser.
"""
    return {
        "folder": re.sub(r"[^A-Za-z0-9]+", "", title) or "CustomBrowserGame",
        "main_file": "index.html",
        "run_command": "start .\\index.html",
        "verify_command": "node --check app.js",
        "manual_test_steps": ["Open index.html.", "Press Start.", "Use the listed controls.", "Confirm score/progress, end state and restart work."],
        "notes": f"Generic custom game fallback for {title}; adapts object names and objective to the user request instead of using a fixed unrelated template.",
        "human_summary": f"A custom browser game: {title}. Open index.html, press Start, use WASD/arrow keys, collect targets, avoid hazards, and restart after game over.",
        "files": {"index.html": html, "style.css": css, "app.js": js, "README.md": readme},
        "source": "generic_game_fallback",
        "fallback_reason": "local model did not produce an accepted game project",
        "game_design": intent.to_dict(),
    }


def _build_platformer_game_project(user_text: str, intent: GameDesignIntent) -> dict[str, Any]:
    title = "Platformer"
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Platformer</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <main class="game-shell">
    <header>
      <h1>Platformer</h1>
      <div class="scoreboard"><span>Coins: <strong id="score">0</strong></span><span>Status: <strong id="status">Ready</strong></span></div>
    </header>
    <p class="instructions">Run and jump across platforms, collect coins, avoid spikes, and reach the green goal. Use A/D or Left/Right to move, W/Up/Space to jump, and R to restart.</p>
    <canvas id="gameCanvas" width="860" height="480" aria-label="Platformer play area"></canvas>
    <div class="controls"><button id="startBtn">Start / Restart</button><button id="pauseBtn">Pause</button></div>
  </main>
  <script src="app.js"></script>
</body>
</html>
"""
    css = """*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:#edf6f9;color:#14213d;font-family:Segoe UI,Arial,sans-serif}.game-shell{width:min(980px,96vw);display:grid;gap:10px}header{display:flex;justify-content:space-between;align-items:center;gap:16px}.scoreboard{display:flex;gap:18px;font-size:17px}.instructions{background:#fff;border-left:5px solid #2a9d8f;padding:10px;box-shadow:0 8px 20px #0001}canvas{width:100%;aspect-ratio:43/24;background:#8ecae6;border:3px solid #1d3557;box-shadow:0 18px 44px #0002}.controls{display:flex;gap:10px}button{border:0;background:#1d3557;color:white;padding:11px 15px;font-weight:800;cursor:pointer;border-radius:8px}button:hover{background:#264a78}
"""
    js = """const canvas=document.getElementById('gameCanvas');
const ctx=canvas.getContext('2d');
const scoreEl=document.getElementById('score');
const statusEl=document.getElementById('status');
const startBtn=document.getElementById('startBtn');
const pauseBtn=document.getElementById('pauseBtn');
const keys={left:false,right:false,jump:false};
const gravity=1800;
const moveSpeed=260;
const jumpImpulse=-650;
let running=false,paused=false,last=0,score=0;
const player={x:42,y:360,w:30,h:38,vx:0,vy:0,onGround:false,color:'#ffb703'};
const start={x:42,y:360};
const platforms=[
  {x:0,y:438,w:260,h:42},{x:310,y:390,w:150,h:22},{x:510,y:335,w:150,h:22},
  {x:690,y:285,w:130,h:22},{x:170,y:300,w:120,h:22},{x:0,y:210,w:115,h:22}
];
let coins=[],hazards=[],goal={x:790,y:236,w:34,h:49};
function resetGame(){running=true;paused=false;score=0;player.x=start.x;player.y=start.y;player.vx=0;player.vy=0;player.onGround=false;coins=[{x:360,y:350,w:18,h:18},{x:560,y:295,w:18,h:18},{x:210,y:260,w:18,h:18},{x:730,y:245,w:18,h:18}];hazards=[{x:268,y:418,w:38,h:20},{x:468,y:370,w:38,h:20},{x:650,y:315,w:38,h:20}];scoreEl.textContent='0';statusEl.textContent='Playing';last=performance.now();requestAnimationFrame(loop)}
function rectsHit(a,b){return a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y}
function landOnPlatforms(prevY){player.onGround=false;for(const p of platforms){const wasAbove=prevY+player.h<=p.y;const overlaps=player.x+player.w>p.x&&player.x<p.x+p.w;if(player.vy>=0&&wasAbove&&overlaps&&player.y+player.h>=p.y&&player.y+player.h<=p.y+p.h+24){player.y=p.y-player.h;player.vy=0;player.onGround=true}}}
function fail(){running=false;statusEl.textContent='Game over - press R'}
function win(){running=false;statusEl.textContent='Goal reached'}
function update(dt){if(paused||!running)return;const prevY=player.y;player.vx=(keys.right?moveSpeed:0)-(keys.left?moveSpeed:0);if(keys.jump&&player.onGround){player.vy=jumpImpulse;player.onGround=false}player.vy+=gravity*dt;player.x+=player.vx*dt;player.y+=player.vy*dt;player.x=Math.max(0,Math.min(canvas.width-player.w,player.x));landOnPlatforms(prevY);if(player.y>canvas.height+80)fail();coins=coins.filter(c=>{if(rectsHit(player,c)){score+=1;scoreEl.textContent=String(score);return false}return true});for(const h of hazards){if(rectsHit(player,h))fail()}if(rectsHit(player,goal))win()}
function drawRect(r,color){ctx.fillStyle=color;ctx.fillRect(r.x,r.y,r.w,r.h)}
function draw(){ctx.clearRect(0,0,canvas.width,canvas.height);ctx.fillStyle='#8ecae6';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.fillStyle='#dff7ff';for(let i=0;i<5;i++)ctx.fillRect(i*190+20,60+i%2*35,80,16);for(const p of platforms)drawRect(p,'#2a9d8f');for(const c of coins){ctx.fillStyle='#ffd166';ctx.beginPath();ctx.arc(c.x+c.w/2,c.y+c.h/2,c.w/2,0,Math.PI*2);ctx.fill()}for(const h of hazards){ctx.fillStyle='#e63946';ctx.beginPath();ctx.moveTo(h.x,h.y+h.h);ctx.lineTo(h.x+h.w/2,h.y);ctx.lineTo(h.x+h.w,h.y+h.h);ctx.closePath();ctx.fill()}drawRect(goal,'#38b000');drawRect(player,player.color);if(!running){ctx.fillStyle='rgba(255,255,255,.92)';ctx.font='26px Segoe UI';ctx.textAlign='center';ctx.fillText(statusEl.textContent==='Goal reached'?'You reached the goal!':'Platformer: press Start',canvas.width/2,canvas.height/2)}if(paused){ctx.fillStyle='#14213d';ctx.font='28px Segoe UI';ctx.textAlign='center';ctx.fillText('Paused',canvas.width/2,canvas.height/2+42)}}
function loop(now){const dt=Math.min(0.033,(now-last)/1000);last=now;update(dt);draw();if(running)requestAnimationFrame(loop)}
document.addEventListener('keydown',e=>{const k=e.key.toLowerCase();if(k==='arrowleft'||k==='a')keys.left=true;if(k==='arrowright'||k==='d')keys.right=true;if(k==='arrowup'||k==='w'||k===' ')keys.jump=true;if(k==='r')resetGame()});
document.addEventListener('keyup',e=>{const k=e.key.toLowerCase();if(k==='arrowleft'||k==='a')keys.left=false;if(k==='arrowright'||k==='d')keys.right=false;if(k==='arrowup'||k==='w'||k===' ')keys.jump=false});
startBtn.addEventListener('click',resetGame);
pauseBtn.addEventListener('click',()=>{paused=!paused;statusEl.textContent=paused?'Paused':'Playing';if(running&&!paused){last=performance.now();requestAnimationFrame(loop)}});
draw();
"""
    readme = f"""# Platformer

A dependency-free canvas platformer generated for: `{user_text}`.

## Objective

Run and jump across platforms, collect coins, avoid spikes, and reach the green goal.

## Mechanics

- Gravity and vertical velocity (`vy`)
- Grounded jumps with `onGround`
- Platform collision and landing
- Coins, hazards, restart, and win/lose state

## Run

Open `index.html` in a browser.
"""
    return {
        "folder": "Platformer",
        "main_file": "index.html",
        "run_command": "start .\\index.html",
        "verify_command": "node --check app.js",
        "manual_test_steps": ["Open index.html.", "Press Start.", "Use A/D or Left/Right to move.", "Jump with W/Up/Space and confirm the player lands on platforms.", "Collect coins, touch a spike, restart, then reach the green goal."],
        "notes": "Platformer fallback with gravity, vertical velocity, grounded jumps, platforms, platform collision, hazards and a goal.",
        "human_summary": "A real browser platformer. Open index.html, press Start, move with A/D or arrows, jump with W/Up/Space, collect coins and reach the goal.",
        "files": {"index.html": html, "style.css": css, "app.js": js, "README.md": readme},
        "source": "generic_game_fallback",
        "fallback_reason": "local model did not produce an accepted platformer project",
        "game_design": intent.to_dict(),
    }


def strip_interactive_clarification(text: str) -> str:
    """Remove Nova's own interactive-run boilerplate from a user goal.

    The clarification is useful for planning, but it should not become the
    generated game's theme, folder name, acceptance terms, or visible title.
    """
    raw = str(text or "")
    raw = re.sub(r"\n\s*User clarification for this interactive run:\s*[\s\S]*$", "", raw, flags=re.I).strip()
    raw = re.sub(r"\buser clarification for this interactive run:?\b[\s\S]*$", "", raw, flags=re.I).strip()
    return raw or str(text or "")


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _extract_named_game(low: str) -> str:
    patterns = [r"(?:make|build|create|write|generate) (?:a |an )?([a-z0-9 -]+?) game\b", r"\b([a-z0-9 -]+?) game\b"]
    stop = {"make", "build", "create", "write", "generate", "a", "an", "simple", "basic", "fun", "small", "browser", "canvas", "html", "javascript", "new", "polished", "minimal"}
    for pat in patterns:
        m = re.search(pat, low)
        if m:
            words = [w for w in re.findall(r"[a-z0-9]+", m.group(1)) if w not in stop]
            if words:
                return " ".join(words[:4]) + " game"
    return ""


def _extract_about_theme(low: str) -> str:
    m = re.search(r"\b(?:about|themed around|theme(?:d)? as|based on)\s+([a-z0-9 -]{2,60})", low)
    if not m:
        return ""
    stop = {"with", "using", "that", "which", "and", "then", "in", "on", "for", "build", "polished", "minimal", "html", "css", "js", "page", "instructions", "verification", "success", "check", "project", "new"}
    words = [w for w in re.findall(r"[a-z0-9]+", m.group(1)) if w not in stop]
    return " ".join(words[:3]).strip()


def _objects_from_words(name: str) -> list[str]:
    words = [w for w in re.findall(r"[a-z0-9]+", name.lower()) if w not in {"game"}]
    if not words:
        return ["player", "targets", "hazards"]
    primary = words[0]
    return ["player", primary, "hazards"]


def _mechanics_from_text(low: str) -> list[str]:
    mechanics: list[str] = []
    for label, needles in [
        ("jumping", ["jump", "platform"]),
        ("shooting", ["shoot", "laser", "bullet"]),
        ("collecting", ["collect", "coin", "food", "fish", "resource"]),
        ("dodging", ["dodge", "avoid", "obstacle"]),
        ("racing", ["race", "lap", "car"]),
        ("puzzle solving", ["puzzle", "match", "solve"]),
        ("levels", ["level", "stage"]),
        ("timer", ["timer", "time limit"]),
    ]:
        if any(n in low for n in needles):
            mechanics.append(label)
    return mechanics


def _objective_sentence(intent: GameDesignIntent) -> str:
    theme = intent.requested_game_type or "custom game"
    if intent.genre == "quiz":
        return "Answer questions, earn points, and improve your score."
    if intent.genre == "card_match":
        return "Flip cards, find matching pairs, and finish in as few moves as possible."
    if intent.genre in {"racing", "driving"}:
        return "Steer through the course, avoid hazards, and build the highest score."
    if intent.genre == "snake":
        return "Move the snake, collect food, grow longer, and avoid collisions."
    return f"Play the {theme}, collect targets, avoid hazards, and build the highest score."


def _title(text: str) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())
    if not words:
        return "Custom Browser Game"
    return " ".join(w.capitalize() for w in words[:5])
