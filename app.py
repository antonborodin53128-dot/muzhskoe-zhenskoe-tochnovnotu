from flask import Flask,request,jsonify,render_template_string,redirect
import time,random,threading
app=Flask(__name__); lock=threading.RLock(); NOTES=["DO","RE","MI","FA","SOL","LA","TI"]; ROUND=60; PREP=3
G={"ps":[],"i":-1,"phase":"idle","started":None,"score":0,"note_i":0,"note":"DO","hit":0}
def pick():
 x=random.randrange(7)
 if x==G["note_i"]: x=(x+random.randrange(1,7))%7
 G["note_i"]=x;G["note"]=NOTES[x]
def upd():
 if G["phase"]=="prep" and time.time()-G["started"]>=PREP:G.update(phase="play",started=time.time())
 if G["phase"]=="play" and time.time()-G["started"]>=ROUND:
  G["ps"][G["i"]].update(score=G["score"],done=True);G["phase"]="timeup"
def snap():
 upd();r=0
 if G["phase"]=="prep":r=max(0,PREP-time.time()+G["started"])
 if G["phase"]=="play":r=max(0,ROUND-time.time()+G["started"])
 rank=sorted([x.copy() for x in G["ps"] if x["done"]],key=lambda x:-x["score"])
 name=G["ps"][G["i"]]["name"] if 0<=G["i"]<len(G["ps"]) else ""
 return {**G,"remaining":r,"name":name,"ranking":rank}
@app.get("/")
def home():return redirect("/setup")
@app.get("/setup")
def setup():return render_template_string(SETUP)
@app.get("/control")
def control():return render_template_string(CONTROL)
@app.get("/screen")
def screen():return render_template_string(SCREEN)
@app.get("/api/state")
def state():
 with lock:return jsonify(snap())
@app.post("/api/init")
def init():
 d=request.get_json(silent=True) or {};n=max(1,min(10,int(d.get("count",4))))
 with lock:G.update(ps=[{"name":f"УЧАСТНИК {i+1}","score":0,"done":False} for i in range(n)],i=0,phase="ready",started=None,score=0,hit=0);pick();return jsonify(snap())
@app.post("/api/start")
def start():
 with lock:
  if G["phase"]=="ready":G.update(phase="prep",started=time.time(),score=0);pick()
  return jsonify(snap())
@app.post("/api/hit")
def hit():
 with lock:
  upd()
  if G["phase"]=="play":G["score"]+=1;G["hit"]+=1;pick()
  return jsonify(snap())
@app.post("/api/next")
def nxt():
 with lock:
  if G["phase"]=="timeup":
   if G["i"]+1<len(G["ps"]):G.update(i=G["i"]+1,phase="ready",started=None,score=0);pick()
   else:G.update(i=len(G["ps"]),phase="finished",started=None)
  return jsonify(snap())
@app.post("/api/finish")
def finish():
 with lock:
  if G["ps"] and 0<=G["i"]<len(G["ps"]) and G["phase"] in ("ready","prep","play","timeup"):
   G["ps"][G["i"]].update(score=G["score"],done=True)
  G.update(phase="finished",started=None)
  return jsonify(snap())
@app.post("/api/reset")
def reset():
 with lock:G.update(ps=[],i=-1,phase="idle",started=None,score=0,hit=0);return jsonify(snap())

SETUP=r'''<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>SETUP</title><style>body{background:#050405;color:white;font:18px Arial;max-width:760px;margin:40px auto;padding:20px}button,select{font:inherit;padding:14px;margin:8px;background:#21101d;color:white;border:1px solid #ff3c9f;border-radius:12px}select{width:100%}#bar{height:18px;background:#26101e;border-radius:10px;overflow:hidden}#fill{height:100%;width:0;background:#ff3c9f}a{color:#ff70bf}
/* ===== FRESH VISUAL V12 ===== */
.stage{background:#08090d;padding:22px 28px 28px}
.hud{height:96px;grid-template-columns:1.15fr 1fr 1.15fr}
.brand{position:relative!important;display:inline-flex!important;align-items:center!important;padding:13px 19px!important;border:1px solid #393b46!important;border-radius:10px!important;background:linear-gradient(180deg,#171820,#0e0f15)!important;font-family:Arial,sans-serif!important;font-size:34px!important;font-style:normal!important;font-weight:950!important;letter-spacing:1.5px!important;color:#fff!important;box-shadow:0 8px 28px #0008,inset 0 1px #ffffff0d!important;text-shadow:none!important}
.brand:before{content:""!important;position:absolute!important;left:-1px!important;top:14px!important;bottom:14px!important;width:4px!important;height:auto!important;background:#ff3f9d!important;box-shadow:0 0 14px #ff3f9d!important}
.brand:after{display:none!important}
.brand span{margin-left:9px!important;color:#ff4fa8!important;text-shadow:0 0 15px #ff3f9d55!important}
.game{background:linear-gradient(180deg,#11131a,#090a0f)!important;border:1px solid #2c2e38!important;border-radius:16px!important;box-shadow:inset 0 0 70px #0008,0 18px 50px #0006!important}
.motion{background:
linear-gradient(115deg,transparent 0 42%,#ff3f9d08 43% 43.5%,transparent 44% 100%),
linear-gradient(65deg,transparent 0 67%,#ffffff06 68% 68.5%,transparent 69% 100%)!important;opacity:1!important}
.motion:before,.motion:after{display:none!important}
#stars{display:none!important}
.game:before,.game:after{display:none!important}
.vignette{box-shadow:inset 0 0 85px #0009!important;z-index:3!important}

/* Seven note lanes are explicit foreground game geometry. */
#lines{position:absolute!important;inset:0!important;z-index:10!important;pointer-events:none!important}
.guide{position:absolute!important;left:0!important;right:0!important;width:100%!important;height:1px!important;border:0!important;background:linear-gradient(90deg,#ff4fa812 0%,#ff4fa83d 12%,#ff4fa83d 86%,#ff4fa81a 100%)!important;box-shadow:0 1px 0 #ffffff08!important;opacity:1!important}
.guide:after{content:""!important;position:absolute!important;left:0!important;right:0!important;top:0!important;border-top:1px dashed #ffffff18!important}
.noteLabel{right:22px!important;width:72px!important;padding:5px 0!important;border-radius:6px!important;background:#0b0c12e8!important;border:1px solid #393b46!important;font-size:20px!important;color:#ff5aad!important;z-index:18!important;box-shadow:0 5px 14px #0008!important}
.noteLabel.active{color:#fff!important;background:#ff3f9d!important;border-color:#ff9dce!important;transform:translateY(-50%) scale(1.5)!important;text-shadow:0 0 8px #fff!important;box-shadow:0 0 14px #ff4fa8,0 0 35px #ff2e9675!important}

/* Player marker: clean luminous puck with directional notch. */
.dot{width:32px!important;height:32px!important;background:radial-gradient(circle at 38% 34%,#fff 0 14%,#ff9dcc 20%,#ff3f9d 54%,#7d174e 100%)!important;border:2px solid #ffd1e8!important;box-shadow:0 0 10px #fff8,0 0 24px #ff3f9d!important;z-index:16!important;animation:none!important}
.dot:before{inset:-7px!important;border:1px solid #ff6bb44f!important}
.dot:after{display:none!important}

/* Three clean parallel fading traces attached to the puck. */
.trail{z-index:15!important;height:60px!important}
.trail .main{stroke-width:2.1!important}
.trail .sub,.trail .pulse{stroke-width:1!important;opacity:.38!important}

/* Gate becomes a clean equalizer / audio rack obstacle. */
.wallPart{width:58px!important;background:repeating-linear-gradient(180deg,#252733 0 8px,#15161e 8px 11px)!important;border:1px solid #515461!important;border-left:3px solid #ff3f9d!important;border-right:3px solid #ff3f9d!important;box-shadow:0 0 22px #000b,inset 0 0 12px #ff3f9d1c!important;z-index:14!important}
.wallPart:after{content:""!important;position:absolute!important;inset:8px 9px!important;border-left:1px solid #ffffff16!important;border-right:1px solid #ffffff16!important}
.wallCap{left:-7px!important;right:-7px!important;height:6px!important;background:#ff3f9d!important;border:0!important;box-shadow:0 0 14px #ff3f9d!important}

/* Countdown: minimal rhythmic pulse, no old techno ring. */
.msg{background:#090a0fdd!important;backdrop-filter:blur(3px)!important}
.msg .countHud{width:190px!important;height:190px!important;border-radius:18px!important;border:1px solid #3a3c47!important;background:#11131af2!important;box-shadow:0 20px 60px #000c,inset 0 0 30px #ff3f9d0e!important}
.msg .countHud:before{inset:-1px!important;border-radius:18px!important;border:0!important;border-left:5px solid #ff3f9d!important;animation:none!important}
.msg .countHud:after{display:none!important}
.countNum{font-size:100px!important;color:#fff!important;text-shadow:0 0 22px #ff3f9d88!important;animation:freshCount .72s cubic-bezier(.2,.85,.25,1)!important}
.countLabel{bottom:24px!important;color:#ff5aad!important;letter-spacing:3px!important}
.countSide{display:none!important}
@keyframes freshCount{0%{transform:translateY(18px) scale(.72);opacity:0}30%{transform:translateY(0) scale(1.08);opacity:1}65%{transform:scale(1);opacity:1}100%{transform:translateY(-12px) scale(.92);opacity:.1}}

</style><h1>НАСТРОЙКА МИКРОФОНА</h1><button id=a>РАЗРЕШИТЬ МИКРОФОН</button><select id=d><option>Выберите микрофон</option></select><p id=s>Не подключён</p><div id=bar><div id=fill></div></div><p><a href=/screen target=_blank>ЭКРАН ИГРЫ</a> · <a href=/control target=_blank>ПУЛЬТ</a></p><script>
let st,c,an,b;const d=document.querySelector("#d"),s=document.querySelector("#s"),f=document.querySelector("#fill");
async function list(){let q=(await navigator.mediaDevices.enumerateDevices()).filter(x=>x.kind==="audioinput"),sv=localStorage.getItem("voiceMeterDevice");d.innerHTML="";q.forEach((x,i)=>{let o=document.createElement("option");o.value=x.deviceId;o.textContent=x.label||"Аудиовход "+(i+1);if(sv===x.deviceId)o.selected=true;d.appendChild(o)})}
async function go(id){try{if(st)st.getTracks().forEach(x=>x.stop());st=await navigator.mediaDevices.getUserMedia({audio:{deviceId:id?{exact:id}:undefined,echoCancellation:false,noiseSuppression:false,autoGainControl:false}});let z=st.getAudioTracks()[0].getSettings();if(z.deviceId)localStorage.setItem("voiceMeterDevice",z.deviceId);await list();d.value=z.deviceId;c=new AudioContext();an=c.createAnalyser();an.fftSize=1024;b=new Float32Array(an.fftSize);c.createMediaStreamSource(st).connect(an);s.textContent="МИКРОФОН ПОДКЛЮЧЁН";tick()}catch(e){s.textContent="РАЗРЕШИТЕ ДОСТУП К МИКРОФОНУ"}}
function tick(){if(!an)return;an.getFloatTimeDomainData(b);let q=0;for(let v of b)q+=v*v;f.style.width=Math.min(100,Math.sqrt(q/b.length)*500)+"%";requestAnimationFrame(tick)}
a.onclick=()=>go(localStorage.getItem("voiceMeterDevice")||"");d.onchange=()=>go(d.value);list()</script>'''
CONTROL=r"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}body{background:#050405;color:white;font:18px Arial;max-width:760px;margin:auto;padding:24px}
h1{font-size:34px;letter-spacing:2px}.c{background:#100a0f;border:1px solid #632048;border-radius:18px;padding:20px;margin:14px 0}
button,input{font:inherit;padding:14px;border-radius:12px;border:0}button{background:#ff3199;color:white;font-weight:800;cursor:pointer;transition:transform .08s,filter .12s,box-shadow .12s}
button:active,.pressed{transform:scale(.96);filter:brightness(1.35);box-shadow:0 0 22px #ff319988}button:disabled{opacity:.55;cursor:default}
.big{font-size:64px;color:#ff55b0;font-weight:bold}.r{display:flex;justify-content:space-between;padding:11px 4px;border-bottom:1px solid #33202c}
.muted{color:#a98d9d}.danger{display:block;margin:34px 0 4px;background:#24131e;color:#ff9bca;border:1px solid #6a294c}
#ack{min-height:24px;color:#ff8ac7;font-weight:bold;margin-top:10px}.results{margin-top:34px}
</style>
<h1>ТОЧНО В НОТУ</h1>
<div class=c>УЧАСТНИКОВ <input id=n type=number min=1 max=10 value=4 style="width:70px"> <button id=init>НАЧАТЬ КОНКУРС</button><div id=ack></div></div>
<div id=g class=c>ОЖИДАНИЕ</div>
<div id=res class="c results"><h2>РЕЗУЛЬТАТЫ</h2><div class=muted>Пока нет завершённых участников</div></div>
<button id=finish class=danger style="display:none">ЗАВЕРШИТЬ ИГРУ</button>
<script>
const $=x=>document.querySelector(x);let pending=0,last=null;
async function post(u,b={},btn=null){
 const token=++pending;
 if(btn){btn.classList.add("pressed");btn.disabled=true}
 ack.textContent="ОТПРАВЛЯЮ…";
 try{
   let r=await fetch(u+"?_="+Date.now(),{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b),cache:"no-store"});
   if(!r.ok)throw new Error("HTTP "+r.status);
   let j=await r.json(); draw(j); ack.textContent="ГОТОВО";
   return j;
 }catch(e){ack.textContent="ОШИБКА СВЯЗИ — ПОВТОРИТЕ"}
 finally{setTimeout(()=>{if(token===pending)ack.textContent="";if(btn){btn.disabled=false;btn.classList.remove("pressed")}},700)}
}
function rows(a){return a.length?a.map((x,i)=>`<div class=r><span>${["🥇","🥈","🥉"][i]||""} ${x.name}</span><b>${x.score}</b></div>`).join(""):`<div class=muted>Пока нет завершённых участников</div>`}
function draw(s){
 last=s;res.innerHTML="<h2>РЕЗУЛЬТАТЫ</h2>"+rows(s.ranking||[]);
 finish.style.display=s.ps&&s.ps.length&&s.phase!=="finished"?"block":"none";
 if(!s.ps.length){g.innerHTML="ОЖИДАНИЕ";return}
 if(s.phase==="finished"){g.innerHTML="<h2>ИГРА ЗАВЕРШЕНА</h2>"+rows(s.ranking)+`<p><button id=reset>НАЧАТЬ ЗАНОВО</button>`;$("#reset").onclick=e=>post("/api/reset",{},e.currentTarget);return}
 let b=s.phase==="ready"?`<button id=start>СТАРТ</button>`:s.phase==="timeup"?`<button id=next>СЛЕДУЮЩИЙ УЧАСТНИК</button>`:"";
 g.innerHTML=`<h2>${s.name}</h2><div>ПРОЙДЕНО СТЕН</div><div class=big>${s.score}</div><p>НОТА: <b>${s.note}</b></p>${b}`;
 let st=$("#start"),nx=$("#next");if(st)st.onclick=e=>post("/api/start",{},e.currentTarget);if(nx)nx.onclick=e=>post("/api/next",{},e.currentTarget)
}
init.onclick=e=>post("/api/init",{count:+n.value},e.currentTarget);
finish.onclick=e=>post("/api/finish",{},e.currentTarget);
setInterval(async()=>{try{let r=await fetch("/api/state?_="+Date.now(),{cache:"no-store"});if(r.ok)draw(await r.json())}catch(e){}},180);
</script>"""
SCREEN=r"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#020203;color:#fff;font-family:Arial,sans-serif}
.stage{height:100vh;padding:24px 34px 30px;background:radial-gradient(circle at 48% 44%,#130711 0,#060306 38%,#020203 72%);display:flex;flex-direction:column}
.hud{height:92px;display:grid;grid-template-columns:1fr auto 1fr;align-items:center;position:relative;z-index:20}
.brand{position:relative;display:inline-flex;align-items:center;width:max-content;padding:12px 20px 11px;border:1px solid #ff5aad;background:linear-gradient(180deg,#160914cc,#08050acc);font-family:"Arial Black",Arial,sans-serif;font-size:36px;font-weight:900;letter-spacing:2.5px;line-height:1;text-transform:uppercase;color:#fff;box-shadow:inset 0 0 22px #ff3c9915,0 0 18px #ff3c9925}.brand:before,.brand:after{content:"";position:absolute;width:18px;height:5px;background:#ff5aad;box-shadow:0 0 10px #ff5aad}.brand:before{left:-1px;top:-3px}.brand:after{right:-1px;bottom:-3px}.brand span{color:#ff62b2;margin-left:10px;text-shadow:0 0 10px #ff58ae,0 0 24px #ff2e9670}
.centerHud{text-align:center}.participant{font-size:15px;color:#9f8997;font-weight:800;letter-spacing:1.6px}.targetTitle{margin-top:5px;font-size:16px;color:#d7c7d0;font-weight:800;letter-spacing:1px}.targetTitle b{color:#ff55ad;font-size:30px;margin-left:8px}
.stats{display:flex;justify-content:flex-end;gap:12px}.pill{min-width:132px;padding:11px 16px;border:1px solid #4b263c;background:#0c070b;border-radius:12px;text-align:center}.pill small{display:block;color:#9f8997;font-size:11px;font-weight:900;letter-spacing:1.5px}.pill strong{display:block;margin-top:3px;font-size:25px;color:#fff}.pill strong.pink{color:#ff55ad}
.game{position:relative;flex:1;min-height:0;border:1px solid #3b1d30;border-radius:14px;overflow:hidden;background:
radial-gradient(ellipse at 70% 28%,#8a18533d 0,transparent 26%),
radial-gradient(ellipse at 48% 72%,#d32b7b24 0,transparent 30%),
radial-gradient(ellipse at 25% 42%,#50134732 0,transparent 24%),
linear-gradient(90deg,#010106,#07030b 48%,#010106)}
}#stars{position:absolute;inset:0;width:100%;height:100%;z-index:2;opacity:.92;pointer-events:none}.vignette{position:absolute;inset:0;box-shadow:inset 0 0 100px #000;pointer-events:none;z-index:12}
.motion{position:absolute;inset:0;overflow:hidden;background:#010106}
.motion:before{content:"";position:absolute;left:0;top:0;width:200%;height:100%;will-change:transform;animation:spaceLoop 46s linear infinite;background:
radial-gradient(circle at 4% 17%,#fff 0 1px,#fff0 2px),
radial-gradient(circle at 13% 68%,#fff 0 1.5px,#fff0 2.8px),
radial-gradient(circle at 23% 31%,#ffd8ef 0 1px,#fff0 2px),
radial-gradient(circle at 31% 82%,#fff 0 2px,#fff0 3.5px),
radial-gradient(circle at 43% 12%,#fff 0 1px,#fff0 2px),
radial-gradient(circle at 56% 57%,#ffb6dc 0 1.4px,#fff0 2.7px),
radial-gradient(circle at 67% 24%,#fff 0 1.8px,#fff0 3px),
radial-gradient(circle at 79% 75%,#fff 0 1px,#fff0 2px),
radial-gradient(circle at 91% 39%,#ffd4eb 0 1.5px,#fff0 2.8px),
radial-gradient(ellipse at 18% 44%,#ff3e9a50 0 5%,#8e1d6840 13%,transparent 29%),
radial-gradient(ellipse at 31% 57%,#d62d8050 0 7%,#6f185238 18%,transparent 33%),
radial-gradient(ellipse at 67% 34%,#ff4ca557 0 5%,#91226438 16%,transparent 31%),
radial-gradient(ellipse at 82% 63%,#ba26714d 0 8%,#54134235 20%,transparent 35%)}
.motion:after{content:"";position:absolute;left:0;top:-12%;width:200%;height:124%;will-change:transform;animation:spaceLoop 72s linear infinite;filter:blur(24px);opacity:.82;background:
radial-gradient(ellipse at 12% 48%,#ff4fa87a 0 6%,#b42a7460 14%,transparent 30%),
radial-gradient(ellipse at 27% 38%,#7b246f72 0 8%,#d02c7a4f 18%,transparent 34%),
radial-gradient(ellipse at 54% 68%,#ff398f70 0 7%,#8d1e6650 18%,transparent 32%),
radial-gradient(ellipse at 74% 31%,#c62c8268 0 8%,#6f1d6650 19%,transparent 35%),
radial-gradient(ellipse at 91% 61%,#ff4b9e66 0 7%,#841c5b4d 17%,transparent 31%)}
@keyframes spaceLoop{from{transform:translateX(0)}to{transform:translateX(-50%)}}to{transform:translateX(-50%)}}to{transform:translateX(-50%)}}
.guide{position:absolute;left:0;right:0;border-top:1px solid #ff78bc45;z-index:4;pointer-events:none;box-shadow:0 -1px 0 #ffffff08}
.guide:after{content:"";position:absolute;left:0;right:0;top:-1px;border-top:1px dashed #ffffff12}
.noteLabel{position:absolute;right:24px;width:78px;text-align:center;transform:translateY(-50%);font-size:26px;font-weight:900;letter-spacing:1.5px;color:#ff4fa8;transition:transform .24s ease,color .24s ease,text-shadow .24s ease;z-index:14}
.noteLabel.active{color:#fff;transform:translateY(-50%) scale(1.72);text-shadow:0 0 8px #fff,0 0 18px #fff,0 0 34px #ff5aad,0 0 65px #ff2e96;z-index:15}
.dot{position:absolute;left:17%;top:50%;width:34px;height:34px;border-radius:50%;transform:translate(-50%,-50%);z-index:9;background:radial-gradient(circle at 38% 32%,#fff 0 12%,#ffd4eb 13% 25%,#ff5aad 40%,#b51f6c 72%,#430b2b 100%);border:1px solid #ff9dce;box-shadow:0 0 8px #fff,0 0 20px #ff5aad,0 0 45px #ff2e9675;animation:orbPulse 1.1s ease-in-out infinite alternate}.dot:before{content:"";position:absolute;inset:-7px;border-radius:50%;border:1px solid #ff79bd55}.dot:after{content:"";position:absolute;inset:-13px;border-radius:50%;border:1px solid #ff4fa825}@keyframes orbPulse{to{filter:brightness(1.18);box-shadow:0 0 10px #fff,0 0 25px #ff5aad,0 0 55px #ff2e9685}}}
.trail{position:absolute;left:2%;width:15%;height:76px;top:50%;transform:translateY(-50%);z-index:8;overflow:visible;pointer-events:none}.trail path{fill:none;stroke-linecap:round}.trail .main{stroke-width:2.3}.trail .sub{stroke-width:1.2;opacity:.58}.trail .pulse{stroke-width:.9;opacity:.34}
.wallPart{position:absolute;width:68px;background:repeating-linear-gradient(0deg,#140912 0 22px,#26101e 23px 25px);border-left:2px solid #ff4fa8;border-right:2px solid #ff4fa8;box-shadow:inset 0 0 20px #ff3c9924,0 0 16px #ff2e9655;z-index:7}.wallPart:after{content:"";position:absolute;inset:8px 11px;border-left:1px solid #ff67b044;border-right:1px solid #ff67b044}.wallCap{position:absolute;left:-10px;right:-10px;height:8px;background:#120910;border:2px solid #ff75bb;box-shadow:0 0 12px #ff4fa8,0 0 28px #ff2e9660}
#wallTop .wallCap{bottom:0}#wallBottom .wallCap{top:0}
.msg{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:radial-gradient(circle at center,#10061088 0,#02020722 28%,transparent 58%);z-index:30;pointer-events:none}
.msg .countHud{position:relative;width:220px;height:220px;display:flex;align-items:center;justify-content:center;border-radius:50%;border:1px solid #ff6ab655;box-shadow:0 0 35px #ff2e9625,inset 0 0 30px #ff2e9614}
.msg .countHud:before{content:"";position:absolute;inset:14px;border-radius:50%;border:3px dashed #ff63b2aa;animation:ringSpin 3.4s linear infinite}
.msg .countHud:after{content:"";position:absolute;inset:-15px;border-radius:50%;border-top:2px solid #fff;border-right:2px solid #ff4fa8;border-bottom:2px solid transparent;border-left:2px solid transparent;filter:drop-shadow(0 0 7px #ff4fa8);animation:ringSpin 1.9s linear infinite reverse}
.countNum{font-family:"Arial Black",Arial,sans-serif;font-size:104px;font-weight:900;line-height:1;color:#fff;text-shadow:0 0 9px #fff,0 0 24px #ff5aad,0 0 52px #ff2e9685;animation:numEnter .72s cubic-bezier(.16,.84,.22,1)}
.countLabel{position:absolute;bottom:45px;font-size:10px;font-weight:900;letter-spacing:4px;color:#ff8bc7}
.countSide{position:absolute;left:50%;top:50%;width:300px;height:1px;transform:translate(-50%,-50%);background:linear-gradient(90deg,transparent,#ff4fa855 18%,transparent 38%,transparent 62%,#ff4fa855 82%,transparent)}
.countSide:before,.countSide:after{content:"";position:absolute;top:-3px;width:7px;height:7px;background:#ff67b4;box-shadow:0 0 10px #ff4fa8;transform:rotate(45deg)}.countSide:before{left:36px}.countSide:after{right:36px}
@keyframes ringSpin{to{transform:rotate(360deg)}}@keyframes numEnter{0%{transform:scale(.25);opacity:0;filter:blur(14px)}28%{transform:scale(1.16);opacity:1;filter:blur(0)}62%{transform:scale(1)}100%{transform:scale(.82);opacity:.25;filter:blur(4px)}}
@keyframes startFlash{0%{transform:scale(.55);opacity:0}30%{transform:scale(1.08);opacity:1}100%{transform:scale(1);opacity:1}}25%{transform:scale(1);opacity:1}75%{transform:scale(1);opacity:1}100%{transform:scale(.72);opacity:.15}}
.mic{position:absolute;right:18px;bottom:16px;padding:12px 16px;background:#ff3199;color:#fff;border:0;border-radius:10px;font-weight:900;z-index:40}
</style>
<style>#noteLabels{position:absolute;inset:0;z-index:17;pointer-events:none}</style><main class=stage>
 <header class=hud>
  <div class=brand>ТОЧНО <span>В НОТУ</span></div>
  <div class=centerHud><div id=who class=participant></div><div class=targetTitle>НУЖНА НОТА <b id=note>DO</b></div></div>
  <div class=stats><div class=pill><small>ВРЕМЯ</small><strong id=tm>01:00</strong></div><div class=pill><small>СЧЁТ</small><strong id=sc class=pink>0</strong></div></div>
 </header>
 <section id=game class=game>
  <div class=motion></div><canvas id=stars></canvas><div id=lines>
<div class=guide style="top:12%"></div><div class=guide style="top:24.6667%"></div><div class=guide style="top:37.3333%"></div><div class=guide style="top:50%"></div><div class=guide style="top:62.6667%"></div><div class=guide style="top:75.3333%"></div><div class=guide style="top:88%"></div>
</div><div id=noteLabels></div><svg id=trail class=trail viewBox="0 0 300 72" preserveAspectRatio="none" aria-hidden="true">
<defs>
<linearGradient id="fadeTrail" x1="0" x2="1"><stop offset="0" stop-color="#ff4fa8" stop-opacity="0"/><stop offset=".34" stop-color="#ff4fa8" stop-opacity=".12"/><stop offset=".72" stop-color="#ff5aad" stop-opacity=".58"/><stop offset="1" stop-color="#ffd1e8" stop-opacity=".95"/></linearGradient>
<linearGradient id="fadeTrail2" x1="0" x2="1"><stop offset="0" stop-color="#ff4fa8" stop-opacity="0"/><stop offset=".48" stop-color="#ff4fa8" stop-opacity=".08"/><stop offset="1" stop-color="#ff5aad" stop-opacity=".55"/></linearGradient>
</defs>
<path id=waveSub class=sub stroke="url(#fadeTrail2)" d=""></path><path id=wave class=main stroke="url(#fadeTrail)" d=""></path><path id=wavePulse class=pulse stroke="url(#fadeTrail2)" d=""></path></svg><div id=dot class=dot></div>
  <div id=wallTop class=wallPart><i class=wallCap></i></div><div id=wallBottom class=wallPart><i class=wallCap></i></div>
  <div class=vignette></div><div id=msg class=msg></div><button id=mic class=mic>ПОДКЛЮЧИТЬ МИКРОФОН</button>
 </section>
</main>
<script>
const starCanvas=document.getElementById("stars"),sx=starCanvas.getContext("2d");
let starPts=[],starOff=0;
function initStars(){
 let d=devicePixelRatio||1,w=starCanvas.clientWidth,h=starCanvas.clientHeight;
 starCanvas.width=w*d;starCanvas.height=h*d;sx.setTransform(d,0,0,d,0,0);
 starPts=[];let seed=92731;
 const rnd=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296};
 for(let i=0;i<155;i++)starPts.push({x:rnd()*w,y:rnd()*h,r:.35+rnd()*1.45,a:.28+rnd()*.72,t:rnd()*6.28});
}
function drawStars(t){
 let w=starCanvas.clientWidth,h=starCanvas.clientHeight;starOff=(t*.004)%w;
 sx.clearRect(0,0,w,h);
 for(let q of starPts){
   let x=(q.x-starOff+w)%w,tw=.72+.28*Math.sin(t*.0018+q.t);
   sx.globalAlpha=q.a*tw;sx.fillStyle="#fff";sx.beginPath();sx.arc(x,q.y,q.r,0,Math.PI*2);sx.fill();
   if(q.r>1.35){sx.globalAlpha=q.a*.45*tw;sx.strokeStyle="#ffd9ee";sx.lineWidth=.55;sx.beginPath();sx.moveTo(x-4*q.r,q.y);sx.lineTo(x+4*q.r,q.y);sx.moveTo(x,q.y-4*q.r);sx.lineTo(x,q.y+4*q.r);sx.stroke()}
 }
 requestAnimationFrame(drawStars)
}
addEventListener("resize",initStars);initStars();requestAnimationFrame(drawStars);
const NS=["DO","RE","MI","FA","SOL","LA","TI"],$=x=>document.querySelector(x);
let st,ctx,an,b,sr=48000,sm=3,targetPos=3,micOK=false,S=null,x=.84,mode="in",lt=performance.now(),hitting=false,pitchHist=[],wallNote=0,wavePhase=0,lastVoice=0;
/* Высокие ноты сверху, низкие снизу: TI ... DO */
function ty(i){return 88-i*(76/6)}
$("#noteLabels").innerHTML=NS.map((n,i)=>`<div class=noteLabel id=l${i} style="top:${ty(i)}%">${n}</div>`).join("");
async function audio(){try{let id=localStorage.getItem("voiceMeterDevice");st=await navigator.mediaDevices.getUserMedia({audio:{deviceId:id?{exact:id}:undefined,echoCancellation:false,noiseSuppression:false,autoGainControl:false}});ctx=new AudioContext();sr=ctx.sampleRate;an=ctx.createAnalyser();an.fftSize=4096;an.smoothingTimeConstant=.15;b=new Float32Array(an.fftSize);ctx.createMediaStreamSource(st).connect(an);micOK=true;$("#mic").style.display="none";listen()}catch(e){$("#mic").textContent="РАЗРЕШИТЬ МИКРОФОН"}}
$("#mic").onclick=audio;
function pitch(a){let mean=0;for(let v of a)mean+=v;mean/=a.length;let rms=0;for(let v of a){let q=v-mean;rms+=q*q}rms=Math.sqrt(rms/a.length);if(rms<.007)return null;const minF=65,maxF=700,lo=Math.max(2,Math.floor(sr/maxF)),hi=Math.min(Math.floor(sr/minF),Math.floor(a.length*.48));let corr=new Float32Array(hi+1),best=0;for(let l=lo;l<=hi;l++){let xy=0,xx=0,yy=0,n=a.length-l;for(let i=0;i<n;i++){let xxv=a[i]-mean,yyv=a[i+l]-mean;xy+=xxv*yyv;xx+=xxv*xxv;yy+=yyv*yyv}let c=xy/Math.sqrt(xx*yy+1e-12);corr[l]=c;if(c>best)best=c}if(best<.55)return null;let lag=0,gate=Math.max(.58,best*.90);for(let l=lo+1;l<hi;l++)if(corr[l]>=gate&&corr[l]>=corr[l-1]&&corr[l]>=corr[l+1]){lag=l;break}if(!lag){for(let l=lo;l<=hi;l++)if(corr[l]===best){lag=l;break}}if(lag>lo&&lag<hi){let a1=corr[lag-1],a2=corr[lag],a3=corr[lag+1],d=a1-2*a2+a3;if(Math.abs(d)>1e-6)lag+=.5*(a1-a3)/d}let f=sr/lag;if(f<minF||f>maxF)return null;return 69+12*Math.log2(f/440)}
const pcs=[0,2,4,5,7,9,11];
function notePos(m){let pc=((m-60)%12+12)%12,best=0,bd=99;pcs.forEach((v,i)=>{let d=Math.min(Math.abs(pc-v),12-Math.abs(pc-v));if(d<bd){bd=d;best=i}});/* TI/B sits next to the octave boundary; give its upper half a stable capture zone */if(pc>=10.35&&pc<=11.85)best=6;return best}
function active(i){document.querySelectorAll(".noteLabel").forEach((e,j)=>e.classList.toggle("active",j===i))}
function listen(){an.getFloatTimeDomainData(b);let m=pitch(b);if(m!=null){lastVoice=performance.now();let p=notePos(m);pitchHist.push(p);if(pitchHist.length>5)pitchHist.shift();let z=[...pitchHist].sort((a,b)=>a-b);targetPos=z[Math.floor(z.length/2)];active(targetPos)}if(performance.now()-lastVoice>260){
  /* no confirmed voice: move away from the wall gap so silence can never coast through */
  let avoid=(S&&S.phase==="play")?S.note_i:3;
  targetPos=avoid>=3?0:6;
  active(-1);
}
sm+=(targetPos-sm)*.075;let y=ty(sm);$("#dot").style.top=y+"%";$("#trail").style.top=y+"%";requestAnimationFrame(listen)}
function setWallGap(noteIndex){let y=ty(noteIndex),half=7.5;$("#wallTop").style.top="0";$("#wallTop").style.height=Math.max(0,y-half)+"%";$("#wallBottom").style.top=(y+half)+"%";$("#wallBottom").style.bottom="0";$("#wallBottom").style.height="auto"}
function resetWall(){x=.84;mode="in";hitting=false;wallNote=S?S.note_i:0;setWallGap(wallNote)}
async function hit(){if(hitting)return;hitting=true;mode="pass";try{await fetch("/api/hit",{method:"POST",headers:{"Content-Type":"application/json"},body:"{}",cache:"no-store"})}catch(e){}}
function moveWall(){let left=x*100+"%";$("#wallTop").style.left=left;$("#wallBottom").style.left=left}
function drawWave(dt){
 wavePhase+=dt*2.15;let a="",b="",c="";
 for(let px=0;px<=300;px+=4){
   let t=px/300,amp=5.8*(.35+.65*t);
   let base=Math.sin(px*.022-wavePhase)*amp;
   /* outer tracks gently converge into the orb */
   let spread=10*(1-t);
   let y=38+base,y2=38-spread+base,y3=38+spread+base;
   a+=(px?" L":"M")+px+" "+y.toFixed(1);
   b+=(px?" L":"M")+px+" "+y2.toFixed(1);
   c+=(px?" L":"M")+px+" "+y3.toFixed(1);
 }
 $("#wave").setAttribute("d",a);$("#waveSub").setAttribute("d",b);$("#wavePulse").setAttribute("d",c);
}
function anim(t){let dt=Math.min(.05,(t-lt)/1000);lt=t;drawWave(dt);if(S&&S.phase==="play"){let target=ty(wallNote);if(mode==="in")x-=dt*.19;else if(mode==="out"){x+=dt*.34;if(x>=.72)mode="in"}else if(mode==="pass"){x-=dt*.24;if(x<-.10)resetWall()}let wx=x*$("#game").clientWidth,dx=.17*$("#game").clientWidth;if(mode==="in"&&wx<=dx+28){if(micOK&&(performance.now()-lastVoice)<260&&Math.abs(ty(sm)-target)<=7)hit();else mode="out"}moveWall()}requestAnimationFrame(anim)}requestAnimationFrame(anim);
let lastCount="";function draw(s){let phaseChanged=!S||S.phase!==s.phase;S=s;$("#who").textContent=s.name||"";$("#note").textContent=s.note;$("#sc").textContent=s.score;let q=Math.max(0,Math.ceil(s.remaining));$("#tm").textContent=q>=60?"01:00":"00:"+String(q).padStart(2,"0");if(s.phase==="play"){$("#msg").style.display="none";if(phaseChanged)resetWall()}else{$("#msg").style.display="flex";let txt=s.phase==="prep"?String(Math.max(1,Math.ceil(s.remaining))):s.phase==="ready"?"ГОТОВ":s.phase==="timeup"?"ВРЕМЯ!":s.phase==="finished"?"ФИНИШ":"ОЖИДАНИЕ";
if(s.phase==="prep"){
 if(txt!==lastCount){
   $("#msg").innerHTML='<div class="countSide"></div><div class="countHud"><div class="countNum">'+txt+'</div><div class="countLabel">SYSTEM // READY</div></div>';
   lastCount=txt;
 }
}else{
 $("#msg").innerHTML='<div class="countHud"><div class="countNum" style="font-size:'+(txt.length>3?'35px':'70px')+';animation:startFlash .45s ease-out">'+txt+'</div><div class="countLabel">ТОЧНО В НОТУ</div></div>';
}}}
setInterval(async()=>{try{draw(await fetch("/api/state?_="+Date.now(),{cache:"no-store"}).then(x=>x.json()))}catch(e){}},120);audio()
</script>"""
