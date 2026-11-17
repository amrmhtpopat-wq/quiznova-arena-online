/* CHAMPION TAG V4 — final-win ceremony and original Web Audio fanfare */
(function(){
"use strict";
let champion=null,overlay=null,context=null,ready=false,audioOn=true,closeTimer=0,lastFocus=null;
const celebrated=new Set();
try{audioOn=localStorage.getItem('tag_champion_audio')!=='off'}catch(e){}
const soundBtns=()=>[document.getElementById('championSound'),document.getElementById('boardSound')].filter(Boolean);
const replayBtns=()=>[document.getElementById('championCelebrate'),document.getElementById('boardCelebrate')].filter(Boolean);
function label(){
 soundBtns().forEach(b=>{
  b.textContent=audioOn?(ready?'🔊 موسيقى التتويج جاهزة':'🔊 تفعيل موسيقى التتويج'):'🔇 موسيقى التتويج مغلقة';
  b.setAttribute('aria-pressed',String(audioOn));
 });
}
async function unlock(){
 if(!audioOn)return false;
 try{
  const AudioContextType=window.AudioContext||window.webkitAudioContext;
  if(!AudioContextType)return false;
  if(!context)context=new AudioContextType();
  if(context.state==='suspended')await context.resume();
  ready=context.state==='running';label();return ready;
 }catch(e){ready=false;label();return false}
}
async function fanfare(){
 if(!audioOn||!(await unlock()))return;
 const t=context.currentTime+.04;
 // A short original victory melody, generated locally with no licensed recording.
 const notes=[[392,0,.21],[523.25,.24,.21],[659.25,.48,.22],[783.99,.73,.41],
  [659.25,1.23,.21],[783.99,1.48,.22],[1046.5,1.75,.63],[783.99,2.49,.24],[1046.5,2.79,.83]];
 notes.forEach(([frequency,offset,duration],i)=>{
  const osc=context.createOscillator(),gain=context.createGain();
  osc.type=i===6||i===8?'triangle':'sine';
  osc.frequency.setValueAtTime(frequency,t+offset);
  gain.gain.setValueAtTime(.0001,t+offset);
  gain.gain.exponentialRampToValueAtTime(.07,t+offset+.05);
  gain.gain.exponentialRampToValueAtTime(.0001,t+offset+duration);
  osc.connect(gain);gain.connect(context.destination);
  osc.start(t+offset);osc.stop(t+offset+duration+.02);
 });
}
function ensure(){
 if(overlay)return overlay;
 overlay=document.createElement('div');overlay.hidden=true;
 overlay.id='tagChampionCeremony';overlay.className='ct-ceremony';overlay.tabIndex=-1;
 overlay.setAttribute('role','dialog');overlay.setAttribute('aria-modal','true');
 overlay.setAttribute('aria-label','مراسم تتويج بطل البطولة');
 overlay.innerHTML='<div class="ct-confetti" aria-hidden="true"></div>'+
 '<section class="ct-ceremony-stage"><div class="ct-ceremony-kicker">CHAMPION TAG • GRAND FINALE</div>'+
 '<img class="ct-ceremony-trophy" src="/assets/champion/trophy.svg" alt="">'+
 '<h2>🏆 بطل البطولة 🏆</h2><div class="ct-ceremony-winner" id="ctCeremonyWinner"></div>'+
 '<p class="ct-ceremony-subtitle" id="ctCeremonyTitle"></p>'+
 '<div class="ct-ceremony-actions"><button type="button" class="ct-primary" data-ct-ceremony="close">العودة للتصفيات</button>'+
 '<button type="button" data-ct-ceremony="again">↻ إعادة التتويج</button>'+
 '<button type="button" data-ct-ceremony="sound">🔊 تشغيل الموسيقى</button></div></section>';
 const colors=['#ffdc75','#fff','#65d7ff','#a8ffcb','#ffc4e9'];
 const rain=overlay.querySelector('.ct-confetti');
 for(let i=0;i<55;i++){
  const part=document.createElement('i');
  part.style.left=((i*41.9)%100)+'%';
  part.style.setProperty('--color',colors[i%colors.length]);
  part.style.setProperty('--duration',(3+(i%8)*.35)+'s');
  part.style.setProperty('--delay',(-((i%11)*.37))+'s');
  part.style.setProperty('--drift',(((i*23)%150)-75)+'px');
  rain.append(part);
 }
 overlay.addEventListener('click',event=>{
  if(event.target===overlay){close();return}
  const el=event.target.closest('[data-ct-ceremony]');
  if(!el)return;
  if(el.dataset.ctCeremony==='close')close();
  if(el.dataset.ctCeremony==='again')void fanfare();
  if(el.dataset.ctCeremony==='sound'){
   audioOn=true;try{localStorage.setItem('tag_champion_audio','on')}catch(e){}
   void fanfare();label();
  }
 });
 document.body.append(overlay);return overlay;
}
function close(){
 clearTimeout(closeTimer);
 if(!overlay||overlay.hidden)return;
 overlay.hidden=true;document.body.classList.remove('ct-award-active');
 if(lastFocus&&lastFocus.isConnected)lastFocus.focus();
 lastFocus=null;
}
function show(){
 if(!champion||!champion.champion)return;
 const modal=ensure();lastFocus=document.activeElement;
 modal.querySelector('#ctCeremonyWinner').textContent=champion.champion;
 modal.querySelector('#ctCeremonyTitle').textContent=champion.title+' • لحظة المجد';
 modal.hidden=false;document.body.classList.add('ct-award-active');
 modal.focus();void fanfare();clearTimeout(closeTimer);
 closeTimer=setTimeout(close,20000);
}
function update(t,options){
 if(!t)return;
 champion={id:String(t.id||''),champion:String(t.champion||''),title:String(t.title||'بطولة TAG')};
 replayBtns().forEach(btn=>{btn.hidden=!champion.champion});
 const key=champion.id+':'+champion.champion;
 if(options&&options.autoplay&&champion.champion&&!celebrated.has(key)){
  celebrated.add(key);show();
 }
}
document.addEventListener('click',event=>{
 if(event.target.closest('#championCelebrate,#boardCelebrate'))show();
 if(event.target.closest('#championSound,#boardSound')){
  if(audioOn&&ready){audioOn=false;ready=false}
  else{audioOn=true;void unlock()}
  try{localStorage.setItem('tag_champion_audio',audioOn?'on':'off')}catch(e){}
  label();if(audioOn&&overlay&&!overlay.hidden)void fanfare();
 }
});
document.addEventListener('pointerdown',event=>{if(event.target.closest('#championSound,#boardSound'))return;if(audioOn)void unlock()},{once:true});
document.addEventListener('keydown',event=>{
 if(event.key==='Escape'&&overlay&&!overlay.hidden)close();
 if(event.key==='Tab'&&overlay&&!overlay.hidden){
  const controls=Array.from(overlay.querySelectorAll('button'));
  if(!controls.length)return;
  const first=controls[0],last=controls[controls.length-1];
  if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus()}
  else if(!event.shiftKey&&(document.activeElement===last||document.activeElement===overlay)){event.preventDefault();first.focus()}
 }
});
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',label,{once:true});else label();
window.TAGChampionCeremony={update,show,close};
})();