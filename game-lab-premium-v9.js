/* TeachGame Game Lab V9 Premium Stage
 * Decorates the existing distinct 24 preview engines without rewriting
 * their answer handlers, timer loops, score or classroom persistence.
 */
(()=>{
'use strict';
const D=document,O=D.getElementById('playOverlay'),B=D.getElementById('playBody'),S=D.getElementById('playStatus');
if(!O||!B)return;
const icons={quiz:'🎯',fast:'⚡',truth:'✅',pairs:'🧩',flash:'🃏',wheel:'🎡',boxes:'🎁',sort:'🗂️',crossword:'🔠',wordsearch:'🔎',anagram:'🔤',order:'🪜',maze:'🌀',balloons:'🎈',memory:'🧠',hidden:'🖼️',cloze:'✍️',diagram:'📍',board:'🏆',teams:'⚔️',survey:'📊',exit:'🎟️',story:'🧭',bingo:'⭐'};
let lastMode='',lastStatus='',scheduled=false,burstTimer=0;
function reduce(){return window.matchMedia&&matchMedia('(prefers-reduced-motion:reduce)').matches}
function progress(mode){
 const counter=D.getElementById('playCounter')?.textContent||'';
 const m=counter.match(/(\d+)\s*\/\s*(\d+)/);
 let info=B.querySelector('.playinfo');
 if(!info&&m){
  info=D.createElement('div');info.className='playinfo v9-generated-info';
  const title=D.createElement('span');title.textContent='المستوى '+m[1]+' من '+m[2];
  info.append(title);B.prepend(info);
 }
 if(!info||!m)return;
 let bar=info.querySelector(':scope > .v9-progress');
 if(!bar){
  bar=D.createElement('div');bar.className='v9-progress';bar.setAttribute('role','progressbar');
  bar.setAttribute('aria-valuemin','0');bar.setAttribute('aria-label','تقدم اللعبة');
  const fill=D.createElement('span');bar.append(fill);info.append(bar);
 }
 const current=Math.max(0,Math.min(Number(m[1]),Number(m[2]))),total=Math.max(1,Number(m[2]));
 const pct=Math.round(current/total*100);
 if(bar.style.getPropertyValue('--v9-pct')!==pct+'%')bar.style.setProperty('--v9-pct',pct+'%');
 if(bar.getAttribute('aria-valuemax')!==String(total))bar.setAttribute('aria-valuemax',String(total));
 if(bar.getAttribute('aria-valuenow')!==String(current))bar.setAttribute('aria-valuenow',String(current));
}
function burst(){
 if(reduce())return;
 O.querySelector('.v9-burst')?.remove();
 const layer=D.createElement('div');layer.className='v9-burst';layer.setAttribute('aria-hidden','true');
 const colors=['#ffd070','#f28bab','#6ddbcb','#89baf5','#f4f2a6','#ba99fa'];
 for(let i=0;i<22;i++){
  const e=D.createElement('i'),angle=i*2.399963;
  e.style.setProperty('--color',colors[i%colors.length]);
  e.style.setProperty('--x',(50+35*Math.cos(angle))+'%');
  e.style.setProperty('--y',(40+20*Math.sin(angle))+'%');
  e.style.setProperty('--dx',((i%2?1:-1)*(15+i*2))+'px');
  layer.append(e);
 }
 O.append(layer);clearTimeout(burstTimer);burstTimer=setTimeout(()=>layer.remove(),1200);
}
function feedback(){
 if(!S)return;
 const message=S.textContent.trim();
 if(message===lastStatus)return;lastStatus=message;
 const win=/✅|🎉|ممتاز|أحسنت|صحيح|بينغو|اكتملت|فتحت جميع الصناديق/.test(message);
 const bad=/حاول|غير صحيح|لم تتطابق|الإجابة الصحيحة|الإجابة الأصلية/.test(message);
 S.classList.toggle('v9-success',win&&!bad);
 S.classList.toggle('v9-error',bad);
 if(win&&!bad&&!O.classList.contains('v7-game'))burst();
}
function decorate(){
 if(O.hidden){
  if(lastMode){lastMode='';lastStatus='';O.classList.remove('v9-stage');delete O.dataset.v9Mode;clearTimeout(burstTimer);O.querySelector('.v9-burst')?.remove()}
  return;
 }
 const mode=O.dataset.v9Mode||O.dataset.v6Mode||'';
 if(!icons[mode])return;
 if(mode!==lastMode){
  lastMode=mode;lastStatus='';O.querySelector('.v9-burst')?.remove();
  S?.classList.remove('v9-success','v9-error');
 }
 O.classList.add('v9-stage');
 // In modes with no V7 theme, make the activity name immediately recognizable.
 if(!O.classList.contains('v7-game')){
  const title=O.querySelector('.playhead h2');
  if(title&&!title.dataset.v9Title){title.dataset.v9Title='1';}
 }
 progress(mode);
 feedback();
 for(const el of B.querySelectorAll('button:not([aria-label])')){
  if(el.classList.contains('mystery'))continue;
  const label=el.textContent.trim().slice(0,150);
  if(label&&el.getAttribute('aria-label')!==label)el.setAttribute('aria-label',label);
 }
}
function start(){
 const observer=new MutationObserver(()=>{
  if(scheduled)return;
  scheduled=true;requestAnimationFrame(()=>{scheduled=false;decorate()});
 });
 observer.observe(B,{childList:true,subtree:true,characterData:true});
 if(S)observer.observe(S,{childList:true,subtree:true,characterData:true});
 observer.observe(O,{attributes:true,attributeFilter:['hidden','data-v9-mode','class']});
 decorate();
}
if(D.readyState==='loading')D.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();