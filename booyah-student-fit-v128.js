/* BOOYAHJO V12.8: no-page-scroll student questions on both live and solo play. */
(()=>{
'use strict';
const live=document.getElementById('gameView');
const solo=document.getElementById('soloPlayArea');
if(!live||!solo)return;
let scheduled=0;
function fitFont(element,ideal,minimum){
 if(!element||!element.isConnected||!element.clientHeight)return;
 const original=element.style.getPropertyValue('font-size');
 const priority=element.style.getPropertyPriority('font-size');
 // Old versions set inline sizes with important; re-evaluate for each screen.
 let value=ideal;
 for(;value>=minimum;value--){
  element.style.setProperty('font-size',value+'px','important');
  if(element.scrollHeight<=element.clientHeight+2&&
     element.scrollWidth<=element.clientWidth+2)break;
 }
 if(value<minimum)element.style.setProperty('font-size',minimum+'px','important');
 // Let CSS restore defaults only when the UI is no longer a question.
}
function fitCard(card,kind){
 if(!card||!card.isConnected)return;
 const options=kind==='live'?[...card.querySelectorAll('.answers .answer')]:
                           [...card.querySelectorAll('.bo-solo-options .bo-solo-choice')];
 const grid=kind==='live'?card.querySelector('.answers'):card.querySelector('.bo-solo-options');
 if(grid&&options.length)grid.style.setProperty('--bo-answer-rows',String(Math.ceil(options.length/2)));
 const mobile=window.innerWidth<=600;
 const title=card.querySelector('h2');
 if(title)fitFont(title,mobile?Math.min(28,Math.max(19,Math.round(innerWidth*.055))):Math.min(42,Math.max(26,Math.round(innerWidth*.027))),mobile?15:18);
 const viewportHeight=window.visualViewport?.height||window.innerHeight;
 const ideal=mobile?Math.min(20,Math.max(15,Math.round(innerWidth*.039))):Math.min(27,Math.max(19,Math.round(innerWidth*.019)));
 // Fit the answer labels individually without shrinking short choices unnecessarily.
 for(const option of options){
  fitFont(option,viewportHeight<600?Math.min(ideal,18):ideal,12);
 }
}
function apply(){
 scheduled=0;
 const liveCard=live.querySelector('.question-card');
 const soloCard=solo.querySelector('.bo-solo-question');
 const active=liveCard?'live':soloCard?'solo':'';
 if(document.body.dataset.boQuestion!==active){
  document.body.dataset.boQuestion=active;
 }
 if(!active)return;
 const card=active==='live'?liveCard:soloCard;
 fitCard(card,active);
 // Layout may settle after webfont/image load or a new question arrives.
 if(card.querySelector('img')){
  const image=card.querySelector('img');
  if(!image.complete)image.addEventListener('load',schedule,{once:true});
 }
}
function schedule(){
 if(scheduled)cancelAnimationFrame(scheduled);
 scheduled=requestAnimationFrame(apply);
}
new MutationObserver(schedule).observe(live,{childList:true});
new MutationObserver(schedule).observe(solo,{childList:true});
window.addEventListener('resize',schedule,{passive:true});
window.addEventListener('orientationchange',schedule,{passive:true});
window.visualViewport?.addEventListener('resize',schedule,{passive:true});
document.fonts?.ready?.then(schedule).catch(()=>{});
schedule();
})();