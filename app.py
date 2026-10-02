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
@app.post("/api/reset")
def reset():
 with lock:G.update(ps=[],i=-1,phase="idle",started=None,score=0,hit=0);return jsonify(snap())

SETUP=r'''<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>SETUP</title><style>body{background:#050405;color:white;font:18px Arial;max-width:760px;margin:40px auto;padding:20px}button,select{font:inherit;padding:14px;margin:8px;background:#21101d;color:white;border:1px solid #ff3c9f;border-radius:12px}select{width:100%}#bar{height:18px;background:#26101e;border-radius:10px;overflow:hidden}#fill{height:100%;width:0;background:#ff3c9f}a{color:#ff70bf}</style><h1>НАСТРОЙКА МИКРОФОНА</h1><button id=a>РАЗРЕШИТЬ МИКРОФОН</button><select id=d><option>Выберите микрофон</option></select><p id=s>Не подключён</p><div id=bar><div id=fill></div></div><p><a href=/screen target=_blank>ЭКРАН ИГРЫ</a> · <a href=/control target=_blank>ПУЛЬТ</a></p><script>
let st,c,an,b;const d=document.querySelector("#d"),s=document.querySelector("#s"),f=document.querySelector("#fill");
async function list(){let q=(await navigator.mediaDevices.enumerateDevices()).filter(x=>x.kind==="audioinput"),sv=localStorage.getItem("voiceMeterDevice");d.innerHTML="";q.forEach((x,i)=>{let o=document.createElement("option");o.value=x.deviceId;o.textContent=x.label||"Аудиовход "+(i+1);if(sv===x.deviceId)o.selected=true;d.appendChild(o)})}
async function go(id){try{if(st)st.getTracks().forEach(x=>x.stop());st=await navigator.mediaDevices.getUserMedia({audio:{deviceId:id?{exact:id}:undefined,echoCancellation:false,noiseSuppression:false,autoGainControl:false}});let z=st.getAudioTracks()[0].getSettings();if(z.deviceId)localStorage.setItem("voiceMeterDevice",z.deviceId);await list();d.value=z.deviceId;c=new AudioContext();an=c.createAnalyser();an.fftSize=1024;b=new Float32Array(an.fftSize);c.createMediaStreamSource(st).connect(an);s.textContent="МИКРОФОН ПОДКЛЮЧЁН";tick()}catch(e){s.textContent="РАЗРЕШИТЕ ДОСТУП К МИКРОФОНУ"}}
function tick(){if(!an)return;an.getFloatTimeDomainData(b);let q=0;for(let v of b)q+=v*v;f.style.width=Math.min(100,Math.sqrt(q/b.length)*500)+"%";requestAnimationFrame(tick)}
a.onclick=()=>go(localStorage.getItem("voiceMeterDevice")||"");d.onchange=()=>go(d.value);list()</script>'''
CONTROL=r'''<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><style>body{background:#050405;color:white;font:18px Arial;max-width:760px;margin:auto;padding:24px}.c{background:#100a0f;border:1px solid #632048;border-radius:18px;padding:20px;margin:14px 0}button,input{font:inherit;padding:14px;border-radius:12px;border:0}button{background:#ff3199;color:white;font-weight:bold}.big{font-size:64px;color:#ff55b0;font-weight:bold}.r{display:flex;justify-content:space-between;padding:10px;border-bottom:1px solid #33202c}</style><h1>ТОЧНО В НОТУ</h1><div class=c>УЧАСТНИКОВ <input id=n type=number min=1 max=10 value=4 style="width:70px"> <button onclick="post('/api/init',{count:+n.value})">НАЧАТЬ КОНКУРС</button></div><div id=g class=c>ОЖИДАНИЕ</div><script>
async function post(u,b={}){return fetch(u,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b)}).then(x=>x.json())}
function draw(s){if(!s.ps.length){g.innerHTML="ОЖИДАНИЕ";return}if(s.phase==="finished"){g.innerHTML="<h2>РЕЗУЛЬТАТЫ</h2>"+s.ranking.map((x,i)=>`<div class=r><span>${["🥇","🥈","🥉"][i]||""} ${x.name}</span><b>${x.score}</b></div>`).join("")+`<p><button onclick="post('/api/reset')">НАЧАТЬ ЗАНОВО</button>`;return}let b=s.phase==="ready"?`<button onclick="post('/api/start')">СТАРТ</button>`:s.phase==="timeup"?`<button onclick="post('/api/next')">СЛЕДУЮЩИЙ УЧАСТНИК</button>`:"";g.innerHTML=`<h2>${s.name}</h2><div>ПРОЙДЕНО СТЕН</div><div class=big>${s.score}</div><p>NOTE: <b>${s.note}</b></p>${b}`}
setInterval(async()=>{try{draw(await fetch("/api/state?_="+Date.now()).then(x=>x.json()))}catch(e){}},120)</script>'''
SCREEN=r'''<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><style>*{box-sizing:border-box}body{margin:0;background:#050405;color:white;font-family:Arial;overflow:hidden}.w{height:100vh;padding:20px 32px;display:flex;flex-direction:column}.top{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;font-size:28px;font-weight:bold}.note{font-size:52px;color:#ff52ae}.stat{text-align:right}.game{position:relative;flex:1;margin-top:14px;border:1px solid #632048;border-radius:18px;overflow:hidden;background:#0a0709}.line{position:absolute;left:0;right:0;border-top:1px dashed #392531}.lab{position:absolute;left:10px;transform:translateY(-50%);color:#856d7b}.dot{position:absolute;left:16%;top:50%;width:30px;height:30px;border-radius:50%;background:white;box-shadow:0 0 28px #ff3ca1;transform:translate(-50%,-50%)}.wall{position:absolute;top:0;bottom:0;width:55px;background:#ff3199;box-shadow:0 0 22px #a10b5d}.gap{position:absolute;left:-2px;width:59px;background:#0a0709}.msg{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:#050405dd;font-size:100px;font-weight:bold;z-index:5}.mic{position:absolute;right:15px;bottom:15px;padding:12px;background:#ff3199;color:white;border:0;border-radius:10px;font-weight:bold}.hz{position:absolute;left:15px;bottom:15px;color:#a98d9d}</style><main class=w><div class=top><div id=who></div><div>NOTE: <span id=note class=note>DO</span></div><div class=stat><span id=sc>0</span> СТЕН · <span id=tm>01:00</span></div></div><div id=game class=game><div id=lines></div><div id=wall class=wall><div id=gap class=gap></div></div><div id=dot class=dot></div><div id=msg class=msg>ОЖИДАНИЕ</div><div id=hz class=hz>—</div><button id=mic class=mic>ПОДКЛЮЧИТЬ МИКРОФОН</button></div></main><script>
const NS=["DO","RE","MI","FA","SOL","LA","TI"],MS=[60,62,64,65,67,69,71],$=x=>document.querySelector(x);let st,ctx,an,b,sr=48000,sm=64,micOK=false,S=null,x=.84,mode="in",lt=performance.now(),hitting=false;
function yp(m){return 88-(Math.max(58,Math.min(73,m))-58)/15*76}function ty(i){return yp(MS[i])}
$("#lines").innerHTML=NS.map((n,i)=>`<div class=line style="top:${ty(i)}%"></div><div class=lab style="top:${ty(i)}%">${n}</div>`).join("");
async function audio(){try{let id=localStorage.getItem("voiceMeterDevice");st=await navigator.mediaDevices.getUserMedia({audio:{deviceId:id?{exact:id}:undefined,echoCancellation:false,noiseSuppression:false,autoGainControl:false}});ctx=new AudioContext();sr=ctx.sampleRate;an=ctx.createAnalyser();an.fftSize=2048;b=new Float32Array(an.fftSize);ctx.createMediaStreamSource(st).connect(an);micOK=true;$("#mic").style.display="none";listen()}catch(e){$("#mic").textContent="РАЗРЕШИТЬ МИКРОФОН"}}
$("#mic").onclick=audio;
function pitch(a){let rms=0;for(let v of a)rms+=v*v;rms=Math.sqrt(rms/a.length);if(rms<.012)return null;let best=0,lag=0,lo=Math.floor(sr/900),hi=Math.min(Math.floor(sr/80),a.length-2);for(let l=lo;l<=hi;l++){let c=0,n=a.length-l;for(let i=0;i<n;i++)c+=a[i]*a[i+l];c/=n;if(c>best){best=c;lag=l}}if(!lag)return null;let f=sr/lag;if(f<80||f>900)return null;return [f,69+12*Math.log2(f/440)]}
function listen(){an.getFloatTimeDomainData(b);let p=pitch(b);if(p){sm=sm*.72+p[1]*.28;$("#dot").style.top=yp(sm)+"%";$("#hz").textContent=p[0].toFixed(0)+" Hz"}requestAnimationFrame(listen)}
function reset(){x=.84;mode="in";hitting=false}
async function hit(){if(hitting)return;hitting=true;await fetch("/api/hit",{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"});reset()}
function anim(t){let dt=Math.min(.05,(t-lt)/1000);lt=t;if(S&&S.phase==="play"){let target=ty(S.note_i);$("#gap").style.top=(target-8)+"%";$("#gap").style.height="16%";if(mode==="in")x-=dt*.19;else{x+=dt*.34;if(x>=.72)mode="in"}let wx=x*$("#game").clientWidth,dx=.16*$("#game").clientWidth;if(mode==="in"&&wx<=dx+28){if(micOK&&Math.abs(yp(sm)-target)<=7)hit();else mode="out"}$("#wall").style.left=x*100+"%"}requestAnimationFrame(anim)}requestAnimationFrame(anim);
function draw(s){let ch=!S||S.note!==s.note||S.phase!==s.phase;S=s;$("#who").textContent=s.name;$("#note").textContent=s.note;$("#sc").textContent=s.score;let q=Math.ceil(s.remaining);$("#tm").textContent=(q>=60?"01:00":"00:"+String(q).padStart(2,"0"));if(s.phase==="play"){$("#msg").style.display="none";if(ch)reset()}else{$("#msg").style.display="flex";$("#msg").textContent=s.phase==="prep"?Math.max(1,Math.ceil(s.remaining)):s.phase==="ready"?"ГОТОВ":s.phase==="timeup"?"ВРЕМЯ!":s.phase==="finished"?"ФИНИШ":"ОЖИДАНИЕ"}}
setInterval(async()=>{try{draw(await fetch("/api/state?_="+Date.now()).then(x=>x.json()))}catch(e){}},100);audio()</script>'''
