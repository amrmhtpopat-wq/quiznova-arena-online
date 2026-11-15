/* TeachGame Game Lab V10.1 — original 2.5D cartoon mascot, theme toggle,
 * game-scene badges and readable overlay. Deliberately lightweight for school PCs.
 */
(()=>{
'use strict';
const D=document,overlay=D.getElementById('playOverlay'),body=D.getElementById('playBody');
if(!overlay||!body)return;
const tokens={
 quiz:'🏆',fast:'⚡',truth:'✅',pairs:'🧩',wheel:'🎡',boxes:'🎁',
 flash:'🃏',memory:'🧠',sort:'🗂️',crossword:'🔠',wordsearch:'🔎',anagram:'🔤',
 order:'🪜',maze:'🌀',balloons:'🎈',hidden:'🖼️',cloze:'✍️',
 diagram:'📍',board:'🏆',teams:'⚔️',survey:'📊',exit:'🎟️',story:'🧭',bingo:'⭐'
};
const STORE='teachgame_game_lab_theme';
let saved='light',lastMode='',pending=false;
try{const x=localStorage.getItem(STORE);if(x==='dark'||x==='light')saved=x}catch(_){}
function svgMascot(){
 const node=D.createElement('span');node.className='v101-buddy';node.setAttribute('aria-hidden','true');
 // Original SVG robot, shaded with layered gradients for a friendly 2.5D look.
 node.innerHTML='<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" role="presentation">'+
 '<defs><linearGradient id="tg101face" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#ffffff"/><stop offset=".5" stop-color="#dbf7ff"/><stop offset="1" stop-color="#91b9fb"/></linearGradient>'+
 '<linearGradient id="tg101body" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#c5a7ff"/><stop offset=".55" stop-color="#7a64dc"/><stop offset="1" stop-color="#444596"/></linearGradient>'+
 '<radialGradient id="tg101eye"><stop stop-color="#252b6c"/><stop offset="1" stop-color="#121b50"/></radialGradient></defs>'+
 '<ellipse cx="60" cy="110" rx="36" ry="8" fill="#263567" opacity=".28"/>'+
 '<path d="M60 25V12" stroke="#6464b2" stroke-width="6" stroke-linecap="round"/><circle cx="60" cy="11" r="8" fill="#ffc969" stroke="#fff3cd" stroke-width="3"/>'+
 '<path d="M34 81Q60 61 86 81L90 103Q60 117 30 103Z" fill="url(#tg101body)" stroke="#5b4fad" stroke-width="3"/>'+
 '<path d="M31 89Q15 91 13 106M89 89Q105 91 107 106" fill="none" stroke="#987adb" stroke-width="11" stroke-linecap="round"/>'+
 '<rect x="19" y="24" width="82" height="64" rx="28" fill="url(#tg101face)" stroke="#e6edff" stroke-width="5"/>'+
 '<rect x="27" y="32" width="66" height="45" rx="18" fill="#bbdff5" opacity=".66"/>'+
 '<ellipse cx="43" cy="54" rx="7" ry="10" fill="url(#tg101eye)"/><ellipse cx="76" cy="54" rx="7" ry="10" fill="url(#tg101eye)"/>'+
 '<circle cx="45" cy="51" r="2.5" fill="#fff"/><circle cx="78" cy="51" r="2.5" fill="#fff"/>'+
 '<path d="M47 69Q60 79 73 69" fill="none" stroke="#a3528e" stroke-width="4" stroke-linecap="round"/>'+
 '<circle cx="29" cy="67" r="5" fill="#ffc9d8" opacity=".8"/><circle cx="91" cy="67" r="5" fill="#ffc9d8" opacity=".8"/>'+
 '<path d="M44 92H77" stroke="#f4e6ff" stroke-width="5" stroke-linecap="round" opacity=".8"/>'+
 '<path d="M52 103L48 113M70 103L74 113" stroke="#5955a5" stroke-width="8" stroke-linecap="round"/>'+
 '</svg>';
 return node;
}
function theme(mode){
 if(!tokens[mode])return;
 overlay.dataset.v101Theme=saved;
 let button=D.getElementById('v101ThemeButton');
 if(!button){
  button=D.createElement('button');button.id='v101ThemeButton';button.type='button';
  button.className='button alt small v101-theme-switch';
  button.setAttribute('aria-label','تبديل الوضع النهاري والليلي');
  button.addEventListener('click',()=>{
   saved=saved==='dark'?'light':'dark';
   overlay.dataset.v101Theme=saved;
   button.textContent=saved==='dark'?'☀️ نهاري':'🌙 ليلي';
   button.setAttribute('aria-pressed',String(saved==='dark'));
   try{localStorage.setItem(STORE,saved)}catch(_){}
  });
  overlay.querySelector('.playhead .buttons')?.prepend(button);
 }
 button.textContent=saved==='dark'?'☀️ نهاري':'🌙 ليلي';
 button.setAttribute('aria-pressed',String(saved==='dark'));
 if(!overlay.querySelector('.v101-buddy')){
  overlay.querySelector('.playhead')?.prepend(svgMascot());
 }
}
function render(){
 if(overlay.hidden){
  lastMode='';return;
 }
 const mode=overlay.dataset.v9Mode||overlay.dataset.v6Mode||'';
 if(!tokens[mode])return;
 if(mode!==lastMode){
  lastMode=mode;
  overlay.dataset.v101Scene=mode;
  theme(mode);
 }
 const existing=body.querySelector('.v101-scene-token');
 if(existing){
  if(existing.dataset.mode!==mode){existing.textContent=tokens[mode];existing.dataset.mode=mode}
 }else{
  const art=D.createElement('span');art.className='v101-scene-token';art.setAttribute('aria-hidden','true');
  art.dataset.mode=mode;art.textContent=tokens[mode];body.append(art);
 }
}
function start(){
 const observer=new MutationObserver(()=>{
  if(pending)return;pending=true;
  requestAnimationFrame(()=>{pending=false;render()});
 });
 observer.observe(body,{childList:true,subtree:true});
 observer.observe(overlay,{attributes:true,attributeFilter:['hidden','data-v9-mode']});
 render();
}
if(D.readyState==='loading')D.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();