/* TeachGame Game Lab Visual Emotion V7 — QA only.
   Additive presentation for Quiz, Fast and True/False; original game engine owns scoring. */
(()=>{
'use strict';
const D=document, O=D.getElementById('playOverlay'), B=D.getElementById('playBody');
if(!O||!B)return;
const $=id=>D.getElementById(id);
const supported=new Set(['quiz','fast','truth']);
let mode='',streak=0,lastAward='',lastText='',winTimer=0,confettiTimer=0;
const robot='<svg viewBox="0 0 170 180" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'+
'<defs><linearGradient id="tg7body" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#a5f3ff"/><stop offset=".48" stop-color="#6b98f6"/><stop offset="1" stop-color="#8756df"/></linearGradient>'+
'<linearGradient id="tg7face" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#304b88"/><stop offset="1" stop-color="#1c2655"/></linearGradient></defs>'+
'<ellipse cx="85" cy="164" rx="67" ry="13" fill="#7380d8" opacity=".28"/>'+
'<circle cx="85" cy="82" r="72" fill="#b4e4ff" opacity=".28"/>'+
'<path class="v7-star" d="M84 11l4-10 5 11 12 1-10 8 3 12-11-7-11 6 4-12-10-8z" fill="#ffd66e" stroke="#fff0b5" stroke-width="3"/>'+
'<path d="M20 91c-18-15-15-40 0-47l11 14-1 26zm132-2c17-16 13-40-2-47l-11 15 1 25z" fill="#86b3ff" stroke="#e5eeff" stroke-width="4"/>'+
'<path d="M43 117l-10 19q-4 10 5 14l10-1 15-21M125 117l11 19q4 10-5 14l-10-1-14-22" fill="#7967d7" stroke="#e7d9ff" stroke-width="4"/>'+
'<rect x="35" y="47" width="106" height="88" rx="34" fill="url(#tg7body)" stroke="#fff" stroke-width="6"/>'+
'<rect x="47" y="62" width="82" height="50" rx="23" fill="url(#tg7face)" stroke="#b0eeff" stroke-width="3"/>'+
'<ellipse class="v7-eye" cx="73" cy="87" rx="8" ry="12" fill="#7ef9ed"/><ellipse class="v7-eye" cx="104" cy="87" rx="8" ry="12" fill="#7ef9ed"/>'+
'<circle cx="70" cy="83" r="2.8" fill="#fff"/><circle cx="101" cy="83" r="2.8" fill="#fff"/>'+
'<path d="M78 102q10 9 20 0" stroke="#8cf9e4" stroke-width="4" fill="none" stroke-linecap="round"/>'+
'<path d="M54 45L83 25l34 19-7 7H61z" fill="#704ed2" stroke="#ded0ff" stroke-width="4"/>'+
'<path d="M83 27l-2-8" stroke="#ffe5a2" stroke-width="4" stroke-linecap="round"/><circle cx="82" cy="17" r="5" fill="#ffdf78"/>'+
'<rect x="76" y="118" width="24" height="9" rx="4.5" fill="#e4ffff" opacity=".9"/>'+
'<path d="M58 134l-3 18M114 134l3 18" stroke="#8171cc" stroke-width="8" stroke-linecap="round"/>'+
'<path d="M52 154h18M105 154h18" stroke="#e9e0ff" stroke-width="10" stroke-linecap="round"/>'+
'<g stroke="#fff1a7" stroke-width="3" stroke-linecap="round"><path d="M16 17v13m-7-7h14M148 26v12m-6-6h12"/></g></svg>';
const reduce=()=>!!(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches);
function detect(){
 const prev=O.dataset.v6Mode;
 if(supported.has(prev))return prev;
 const t=$('playTitle')?.textContent||'';
 return t.includes('سباق الوقت')?'fast':t.includes('تحدي الاختيار')?'quiz':t.includes('صح أم خطأ')?'truth':'';
}
function hideWin(){
 clearTimeout(winTimer);
 const w=O.querySelector('.v7-victory');if(w)w.hidden=true;
}
function setup(){
 if(!O.querySelector('.v7-ambience')){
  const a=D.createElement('div');a.className='v7-ambience';a.setAttribute('aria-hidden','true');
  for(let i=0;i<6;i++)a.append(D.createElement('i'));O.prepend(a);
 }
 const eyebrow=O.querySelector('.playhead .eyebrow');
 if(eyebrow&&!eyebrow.querySelector('.v7-logo')){
  const logo=D.createElement('span');logo.className='v7-logo';logo.textContent='TG';logo.setAttribute('aria-hidden','true');eyebrow.append(logo);
 }
 if(!O.querySelector('.v7-victory')){
  const w=D.createElement('div');w.className='v7-victory';w.hidden=true;w.setAttribute('aria-hidden','true');
  w.innerHTML='<div class="v7-victory-card">🌟 أحسنت! <span>إجابة رائعة • +100 نقطة</span></div>';O.append(w);
 }
}
function change(next){
 if(mode===next)return;
 mode=next;streak=0;lastAward='';lastText='';
 O.classList.toggle('v7-game',Boolean(mode));O.classList.remove('v7-urgent','v7-finished');
 if(mode){O.dataset.v7Mode=mode;setup()}else delete O.dataset.v7Mode;
 hideWin();
}
function hero(){
 const card=B.querySelector('.playcard');
 const finished=Boolean(B.querySelector('#endButtons,#mixerFinishButtons'));
 O.classList.toggle('v7-finished',finished);
 if(!card||finished||!card.querySelector('h3'))return;
 let main=card.querySelector(':scope > .v7-question-content');
 if(!main){
  main=D.createElement('div');main.className='v7-question-content';
  for(const child of [...card.children])if(!child.matches('.v6-question-label,.v7-mascot'))main.append(child);
  card.append(main);
 }
 if(!card.querySelector(':scope > .v7-mascot')){
  const m=D.createElement('div');m.className='v7-mascot';m.setAttribute('aria-hidden','true');m.innerHTML=robot;card.append(m);
 }
}
function answers(){
 const area=B.querySelector(mode==='truth'?'#truthActions':'#answers');if(!area)return;
 area.querySelectorAll('button.choice').forEach((button,i)=>{
  if(button.dataset.v7Choice)return;
  if(!button.querySelector('.v6-choice-index'))return; // allow V6 to run first
  const star=D.createElement('span');star.className='v7-choice-spark';star.textContent='✦';star.setAttribute('aria-hidden','true');
  button.append(star);button.dataset.v7Choice='1';
  if(mode==='truth'){
   const label=button.querySelector('.v6-choice-label');if(label)label.textContent=i===0?'صح':'خطأ';
  }
 });
}
function hud(){
 const info=B.querySelector('.playinfo');if(!info)return;
 const score=info.querySelector(':scope > b');if(score&&!score.dataset.v7Score)score.dataset.v7Score='1';
 let combo=info.querySelector('.v7-momentum');
 if(!combo){combo=D.createElement('div');combo.className='v7-momentum';combo.setAttribute('aria-label','الإجابات الصحيحة المتتالية');combo.hidden=true;info.append(combo);}
 const value=streak>=2?'🔥 '+streak+' متتالية':'';
 if(combo.textContent!==value)combo.textContent=value;
 combo.hidden=streak<2;
 const dial=info.querySelector('.v6-timer');
 const rem=Number(dial?.firstElementChild?.textContent);
 O.classList.toggle('v7-urgent',mode==='fast'&&!!dial&&Number.isFinite(rem)&&rem<=5&&rem>0);
}
function burst(){
 if(reduce())return;
 O.querySelector('.v7-burst')?.remove();
 const group=D.createElement('div');group.className='v7-burst';group.setAttribute('aria-hidden','true');
 const palette=['#ffcc56','#70eaf0','#ff7fae','#a9a0ff','#99ffc9','#fff6c1'];
 for(let i=0;i<26;i++){
  const p=D.createElement('i'),a=i*2.39996;
  p.style.setProperty('--v7-left',(47+36*Math.cos(a))+'%');
  p.style.setProperty('--v7-top',(48+35*Math.sin(a))+'%');
  p.style.setProperty('--v7-color',palette[i%palette.length]);
  p.style.setProperty('--v7-delay',(i%5*25)+'ms');
  p.style.setProperty('--v7-rotate',(i*29%180)+'deg');
  p.style.setProperty('--v7-dx',((i%2?1:-1)*(40+i*4))+'px');
  p.style.setProperty('--v7-dy',((i%3?1:-1)*(85+i*5))+'px');
  group.append(p);
 }
 O.append(group);clearTimeout(confettiTimer);confettiTimer=setTimeout(()=>group.remove(),1300);
}
function celebrate(){
 const w=O.querySelector('.v7-victory');if(!w||reduce())return;
 const text=w.querySelector('.v7-victory-card>span');if(text)text.textContent=streak>=3?'🔥 '+streak+' إجابات صحيحة متتالية!':'إجابة رائعة • +100 نقطة';
 w.hidden=false;
 const card=w.firstElementChild;card.style.animation='none';void card.offsetHeight;card.style.animation='';
 burst();
 clearTimeout(winTimer);winTimer=setTimeout(()=>{w.hidden=true},1100);
 const score=B.querySelector('.playinfo>b');if(score){score.classList.remove('v7-score-pulse');void score.offsetHeight;score.classList.add('v7-score-pulse');}
}
function feedback(){
 const label=$('playStatus');if(!label)return;
 const text=label.textContent.trim();
 if(!text){lastText='';return;}
 if(text===lastText)return;lastText=text;
 const correct=/✅\s*إجابة صحيحة/.test(text),wrong=/💡|الإجابة الأصلية/.test(text);
 const question=B.querySelector('.playcard h3')?.textContent||'';
 const key=mode+'|'+($('playCounter')?.textContent||'')+'|'+question;
 if(!(correct||wrong)||lastAward===key)return;
 lastAward=key;
 if(correct){
  // The original teacher-preview engine updates its internal score immediately
  // but reprints the HUD on the next round. Mirror the awarded 100 points now.
  const score=B.querySelector('.playinfo > b');
  if(score){
   const initial=Number((score.textContent.match(/[0-9]+/)||['0'])[0]);
   score.textContent='⭐ '+(initial+100)+' نقطة';
  }
  streak++;celebrate();
 }else{streak=0;hideWin();}
 if(mode==='truth'){
  const selected=B.querySelector('#truthActions .choice[data-v6-selected="1"]');
  const other=B.querySelector('#truthActions .choice:not([data-v6-selected="1"])');
  if(selected){selected.classList.add(correct?'correct':'wrong');if(!correct&&other)other.classList.add('correct');}
 }
}
function render(){
 if(O.hidden){if(mode)change('');return;}
 change(detect());if(!mode)return;
 hud();hero();answers();feedback();
}
function start(){
 let pending=false;
 function schedule(){if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;render()});}
 const observer=new MutationObserver(schedule);
 observer.observe(B,{childList:true,subtree:true,characterData:true});
 const title=$('playTitle'),status=$('playStatus');
 if(title)observer.observe(title,{childList:true,characterData:true});
 if(status)observer.observe(status,{childList:true,subtree:true,characterData:true});
 observer.observe(O,{attributes:true,attributeFilter:['hidden','data-v6-mode']});
 O.addEventListener('click',e=>{if(e.target.closest('#closePlay'))change('')},true);
 schedule();
}
if(D.readyState==='loading')D.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();