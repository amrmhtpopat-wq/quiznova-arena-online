/* TAG LAB V38 — prevent activity actions from being clipped below the viewport. */
(()=>{
'use strict';
const overlay=document.getElementById('playOverlay');
const body=document.getElementById('playBody');
if(!overlay||!body||!document.documentElement.dataset.tagView)return;
const dock=document.createElement('div');
dock.id='tagPlayActionDock';
dock.className='tag-play-action-dock';
dock.setAttribute('role','group');
dock.setAttribute('aria-label','أزرار متابعة النشاط');
dock.hidden=true;
overlay.append(dock);
let root=null,pending=false,previousScale=1;
const questionModes=new Set(['quiz','fast','truth','sort']);
const visible=()=>!overlay.hidden&&overlay.classList.contains('v101-overhaul');
function measuredOverflow(){
 const rect=body.getBoundingClientRect();
 let bottom=0,top=0;
 for(const el of body.children){
  const r=el.getBoundingClientRect();
  bottom=Math.max(bottom,r.bottom-rect.top);
  top=Math.min(top,r.top-rect.top)
 }
 return Math.max(body.scrollHeight,bottom-top)-body.clientHeight;
}
function fit(){
 body.style.removeProperty('transform');
 overlay.dataset.tagFit='normal';
 if(!visible())return;
 let excess=measuredOverflow();
 if(excess>5){
  overlay.dataset.tagFit='tight';
  excess=measuredOverflow()
 }
 if(excess>4){
  const needed=Math.max(1,body.clientHeight+excess);
  const scale=Math.max(.57,Math.min(1,(body.clientHeight-3)/needed));
  if(scale<.995)body.style.transform='scale('+scale.toFixed(3)+')';
  previousScale=scale
 }else previousScale=1
}
function update(){
 if(!visible()){
  root=null;dock.replaceChildren();dock.hidden=true;
  body.style.removeProperty('transform');delete overlay.dataset.tagFit;
  return
 }
 const first=body.firstElementChild;
 if(root!==first){
  root=first;
  dock.replaceChildren();
  dock.hidden=true;
  body.scrollTop=0;
 }
 // The games place their Next/Finish controls as the final direct child.
 // Moving this exact node keeps the original button event handlers working.
 const finalChild=body.lastElementChild;
 if(finalChild&&finalChild.classList.contains('buttons')&&finalChild!==body.firstElementChild){
  if(finalChild.parentElement===body){
   dock.replaceChildren(finalChild);
   dock.hidden=false
  }
 }
 if(!dock.children.length){
  dock.hidden=!questionModes.has(overlay.dataset.v9Mode)
 }else dock.hidden=false;
 fit()
}
function schedule(){
 if(pending)return;pending=true;
 requestAnimationFrame(()=>{pending=false;update()})
}
new MutationObserver(schedule).observe(body,{subtree:true,childList:true,characterData:true});
new MutationObserver(schedule).observe(dock,{subtree:true,childList:true,characterData:true});
new MutationObserver(schedule).observe(overlay,{attributes:true,attributeFilter:['hidden','class','data-v9-mode']});
window.addEventListener('resize',schedule,{passive:true});
window.addEventListener('orientationchange',schedule,{passive:true});
document.addEventListener('fullscreenchange',schedule);
if(window.visualViewport)visualViewport.addEventListener('resize',schedule,{passive:true});
schedule()
})();
