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
 // Keep the navigation header uncluttered: no injected mascot.
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
 // Decorative icons must not cover a question or create an extra overlay.
 body.querySelector('.v101-scene-token')?.remove();
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