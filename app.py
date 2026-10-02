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

SETUP=r'''<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>SETUP</title><style>body{background:#050405;color:white;font:18px Arial;max-width:760px;margin:40px auto;padding:20px}button,select{font:inherit;padding:14px;margin:8px;background:#21101d;color:white;border:1px solid #ff3c9f;border-radius:12px}select{width:100%}#bar{height:18px;background:#26101e;border-radius:10px;overflow:hidden}#fill{height:100%;width:0;background:#ff3c9f}a{color:#ff70bf}</style><h1>НАСТРОЙКА МИКРОФОНА</h1><button id=a>РАЗРЕШИТЬ МИКРОФОН</button><select id=d><option>Выберите микрофон</option></select><p id=s>Не подключён</p><div id=bar><div id=fill></div></div><p><a href=/screen target=_blank>ЭКРАН ИГРЫ</a> · <a href=/control target=_blank>ПУЛЬТ</a></p><script>
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
const $=x=>document.querySelector(x);let busy=false,last=null;
async function post(u,b={},btn=null){
 if(busy)return null;busy=true;
 if(btn){btn.classList.add("pressed");btn.disabled=true}
 ack.textContent="КОМАНДА ПРИНЯТА";
 try{let r=await fetch(u,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b),cache:"no-store"});let j=await r.json();draw(j);return j}
 catch(e){ack.textContent="ОШИБКА СВЯЗИ — НАЖМИТЕ ЕЩЁ РАЗ"}
 finally{setTimeout(()=>{busy=false;if(btn){btn.disabled=false;btn.classList.remove("pressed")}ack.textContent=""},450)}
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
setInterval(async()=>{if(busy)return;try{draw(await fetch("/api/state?_="+Date.now(),{cache:"no-store"}).then(x=>x.json()))}catch(e){}},180);
</script>"""
SCREEN=r"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#020203;color:#fff;font-family:Arial,sans-serif}
.stage{height:100vh;padding:24px 34px 30px;background:radial-gradient(circle at 48% 44%,#130711 0,#060306 38%,#020203 72%);display:flex;flex-direction:column}
.hud{height:92px;display:grid;grid-template-columns:1fr auto 1fr;align-items:center;position:relative;z-index:20}
.brand{font-size:31px;font-weight:900;letter-spacing:2.8px;text-transform:uppercase}.brand span{color:#ff4fa8}
.centerHud{text-align:center}.participant{font-size:15px;color:#9f8997;font-weight:800;letter-spacing:1.6px}.targetTitle{margin-top:5px;font-size:16px;color:#d7c7d0;font-weight:800;letter-spacing:1px}.targetTitle b{color:#ff55ad;font-size:30px;margin-left:8px}
.stats{display:flex;justify-content:flex-end;gap:12px}.pill{min-width:132px;padding:11px 16px;border:1px solid #4b263c;background:#0c070b;border-radius:12px;text-align:center}.pill small{display:block;color:#9f8997;font-size:11px;font-weight:900;letter-spacing:1.5px}.pill strong{display:block;margin-top:3px;font-size:25px;color:#fff}.pill strong.pink{color:#ff55ad}
.game{position:relative;flex:1;min-height:0;border:1px solid #3b1d30;border-radius:18px;overflow:hidden;background:linear-gradient(90deg,#030203,#080407 48%,#030203)}
.vignette{position:absolute;inset:0;box-shadow:inset 0 0 100px #000;pointer-events:none;z-index:12}
.motion{position:absolute;inset:0;overflow:hidden;opacity:.72}
.motion:before,.motion:after{content:"";position:absolute;inset:-10% -60%;background:
radial-gradient(circle,#ff5caf88 0 1px,transparent 2px) 0 0/150px 95px,
linear-gradient(90deg,transparent 0 86%,#ff4fa820 87% 88%,transparent 89%) 0 0/220px 100%;
animation:bgmove 20s linear infinite}
.motion:after{opacity:.28;filter:blur(.4px);background-size:260px 155px,390px 100%;animation-duration:34s;transform:translateX(18%)}
@keyframes bgmove{to{transform:translateX(-32%)}}
.guide{position:absolute;left:0;right:116px;border-top:1px solid #7e3d6350;z-index:1}
.guide:after{content:"";position:absolute;left:0;right:0;top:-1px;border-top:1px dashed #ff55aa1f}
.noteLabel{position:absolute;right:24px;width:78px;text-align:center;transform:translateY(-50%);font-size:26px;font-weight:900;letter-spacing:1.5px;color:#ff4fa8;transition:transform .24s ease,color .24s ease,text-shadow .24s ease;z-index:9}
.noteLabel.active{color:#fff;transform:translateY(-50%) scale(1.38);text-shadow:0 0 8px #fff,0 0 24px #ff4fa8,0 0 42px #ff2e96}
.dot{position:absolute;left:17%;top:50%;width:28px;height:28px;border-radius:50%;background:#fff;border:5px solid #ff58ae;box-shadow:0 0 8px #fff,0 0 22px #ff4fa8,0 0 46px #ff2e96;transform:translate(-50%,-50%);z-index:8}
.trail{position:absolute;left:4%;width:13%;height:2px;background:linear-gradient(90deg,transparent,#ff4fa844,#ff6ab6aa);top:50%;transform:translateY(-50%);filter:blur(.2px);z-index:5}
.wallPart{position:absolute;width:52px;background:linear-gradient(90deg,#541333,#ff3f9d 48%,#7c174c);border:1px solid #ff71ba;box-shadow:0 0 14px #ff2e9688,0 0 34px #ff2e9638;z-index:7}
.wallCap{position:absolute;left:-8px;right:-8px;height:5px;background:#ff8bc7;box-shadow:0 0 14px #ff4fa8}
#wallTop .wallCap{bottom:0}#wallBottom .wallCap{top:0}
.msg{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:#030203e8;font-size:84px;font-weight:900;letter-spacing:2px;z-index:30}
.mic{position:absolute;right:18px;bottom:16px;padding:12px 16px;background:#ff3199;color:#fff;border:0;border-radius:10px;font-weight:900;z-index:40}
</style>
<main class=stage>
 <header class=hud>
  <div class=brand>ТОЧНО <span>В НОТУ</span></div>
  <div class=centerHud><div id=who class=participant></div><div class=targetTitle>НУЖНА НОТА <b id=note>DO</b></div></div>
  <div class=stats><div class=pill><small>ВРЕМЯ</small><strong id=tm>01:00</strong></div><div class=pill><small>СЧЁТ</small><strong id=sc class=pink>0</strong></div></div>
 </header>
 <section id=game class=game>
  <div class=motion></div><div id=lines></div><div id=trail class=trail></div><div id=dot class=dot></div>
  <div id=wallTop class=wallPart><i class=wallCap></i></div><div id=wallBottom class=wallPart><i class=wallCap></i></div>
  <div class=vignette></div><div id=msg class=msg>ОЖИДАНИЕ</div><button id=mic class=mic>ПОДКЛЮЧИТЬ МИКРОФОН</button>
 </section>
</main>
<script>
const NS=["DO","RE","MI","FA","SOL","LA","TI"],$=x=>document.querySelector(x);
let st,ctx,an,b,sr=48000,sm=3,targetPos=3,micOK=false,S=null,x=.84,mode="in",lt=performance.now(),hitting=false,pitchHist=[];
/* Высокие ноты сверху, низкие снизу: TI ... DO */
function ty(i){return 88-i*(76/6)}
$("#lines").innerHTML=NS.map((n,i)=>`<div class=guide style="top:${ty(i)}%"></div><div class=noteLabel id=l${i} style="top:${ty(i)}%">${n}</div>`).join("");
async function audio(){try{let id=localStorage.getItem("voiceMeterDevice");st=await navigator.mediaDevices.getUserMedia({audio:{deviceId:id?{exact:id}:undefined,echoCancellation:false,noiseSuppression:false,autoGainControl:false}});ctx=new AudioContext();sr=ctx.sampleRate;an=ctx.createAnalyser();an.fftSize=4096;an.smoothingTimeConstant=.15;b=new Float32Array(an.fftSize);ctx.createMediaStreamSource(st).connect(an);micOK=true;$("#mic").style.display="none";listen()}catch(e){$("#mic").textContent="РАЗРЕШИТЬ МИКРОФОН"}}
$("#mic").onclick=audio;
function pitch(a){let mean=0;for(let v of a)mean+=v;mean/=a.length;let rms=0;for(let v of a){let q=v-mean;rms+=q*q}rms=Math.sqrt(rms/a.length);if(rms<.007)return null;const minF=65,maxF=700,lo=Math.max(2,Math.floor(sr/maxF)),hi=Math.min(Math.floor(sr/minF),Math.floor(a.length*.48));let corr=new Float32Array(hi+1),best=0;for(let l=lo;l<=hi;l++){let xy=0,xx=0,yy=0,n=a.length-l;for(let i=0;i<n;i++){let xxv=a[i]-mean,yyv=a[i+l]-mean;xy+=xxv*yyv;xx+=xxv*xxv;yy+=yyv*yyv}let c=xy/Math.sqrt(xx*yy+1e-12);corr[l]=c;if(c>best)best=c}if(best<.55)return null;let lag=0,gate=Math.max(.58,best*.90);for(let l=lo+1;l<hi;l++)if(corr[l]>=gate&&corr[l]>=corr[l-1]&&corr[l]>=corr[l+1]){lag=l;break}if(!lag){for(let l=lo;l<=hi;l++)if(corr[l]===best){lag=l;break}}if(lag>lo&&lag<hi){let a1=corr[lag-1],a2=corr[lag],a3=corr[lag+1],d=a1-2*a2+a3;if(Math.abs(d)>1e-6)lag+=.5*(a1-a3)/d}let f=sr/lag;if(f<minF||f>maxF)return null;return 69+12*Math.log2(f/440)}
const pcs=[0,2,4,5,7,9,11];
function notePos(m){let pc=((Math.round(m)-60)%12+12)%12,best=0,bd=99;pcs.forEach((v,i)=>{let d=Math.min(Math.abs(pc-v),12-Math.abs(pc-v));if(d<bd){bd=d;best=i}});return best}
function active(i){document.querySelectorAll(".noteLabel").forEach((e,j)=>e.classList.toggle("active",j===i))}
function listen(){an.getFloatTimeDomainData(b);let m=pitch(b);if(m!=null){let p=notePos(m);pitchHist.push(p);if(pitchHist.length>5)pitchHist.shift();let z=[...pitchHist].sort((a,b)=>a-b);targetPos=z[Math.floor(z.length/2)];active(targetPos)}sm+=(targetPos-sm)*.075;let y=ty(sm);$("#dot").style.top=y+"%";$("#trail").style.top=y+"%";requestAnimationFrame(listen)}
function setWallGap(noteIndex){let y=ty(noteIndex),half=7.5;$("#wallTop").style.top="0";$("#wallTop").style.height=Math.max(0,y-half)+"%";$("#wallBottom").style.top=(y+half)+"%";$("#wallBottom").style.bottom="0";$("#wallBottom").style.height="auto"}
function resetWall(){x=.84;mode="in";hitting=false}
async function hit(){if(hitting)return;hitting=true;mode="pass";try{await fetch("/api/hit",{method:"POST",headers:{"Content-Type":"application/json"},body:"{}",cache:"no-store"})}catch(e){}}
function moveWall(){let left=x*100+"%";$("#wallTop").style.left=left;$("#wallBottom").style.left=left}
function anim(t){let dt=Math.min(.05,(t-lt)/1000);lt=t;if(S&&S.phase==="play"){let target=ty(S.note_i);setWallGap(S.note_i);if(mode==="in")x-=dt*.19;else if(mode==="out"){x+=dt*.34;if(x>=.72)mode="in"}else if(mode==="pass"){x-=dt*.24;if(x<-.08)resetWall()}let wx=x*$("#game").clientWidth,dx=.17*$("#game").clientWidth;if(mode==="in"&&wx<=dx+28){if(micOK&&Math.abs(ty(sm)-target)<=7)hit();else mode="out"}moveWall()}requestAnimationFrame(anim)}requestAnimationFrame(anim);
function draw(s){let phaseChanged=!S||S.phase!==s.phase;S=s;$("#who").textContent=s.name||"";$("#note").textContent=s.note;$("#sc").textContent=s.score;let q=Math.max(0,Math.ceil(s.remaining));$("#tm").textContent=q>=60?"01:00":"00:"+String(q).padStart(2,"0");if(s.phase==="play"){$("#msg").style.display="none";if(phaseChanged)resetWall()}else{$("#msg").style.display="flex";$("#msg").textContent=s.phase==="prep"?Math.max(1,Math.ceil(s.remaining)):s.phase==="ready"?"ГОТОВ":s.phase==="timeup"?"ВРЕМЯ!":s.phase==="finished"?"ФИНИШ":"ОЖИДАНИЕ"}}
setInterval(async()=>{try{draw(await fetch("/api/state?_="+Date.now(),{cache:"no-store"}).then(x=>x.json()))}catch(e){}},120);audio()
</script>"""
