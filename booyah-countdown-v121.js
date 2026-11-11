/* Shared synchronized classroom launch: 3 • 2 • 1 • READY • GO.
   Rendered once per room on teacher, stage and student views. */
(function(){
 'use strict';
 const seen=new Set();
 let active=null,frame=0;
 const frames=[
  [0,'3','bo-number'],[620,'2','bo-number'],[1240,'1','bo-number'],
  [1860,'READY','bo-ready'],[2560,'GO!','bo-go']
 ];
 const DURATION=3450;
 function cleanup(){
  cancelAnimationFrame(frame);
  if(active){active.remove();active=null}
 }
 function maybe(room,code){
  if(!room||room.status!=='question'||Number(room.index)!==0)return;
  const key=String(code||room.code||'room')+':'+String(room.startedAt||0);
  const elapsed=Date.now()-Number(room.startedAt||0);
  if(seen.has(key)||!Number.isFinite(elapsed)||elapsed< -500||elapsed>=DURATION)return;
  seen.add(key);cleanup();
  const el=document.createElement('div');
  el.className='bo-launch-countdown';
  el.setAttribute('role','status');el.setAttribute('aria-live','polite');
  el.innerHTML='<small>TeachGame • استعد للانطلاق</small><strong>3</strong>';
  document.body.appendChild(el);active=el;
  let last='';
  const tick=()=>{
   if(active!==el)return;
   const t=Date.now()-Number(room.startedAt||0);
   if(t>=DURATION||t< -500){cleanup();return}
   let current=frames[0];
   for(const item of frames){if(t>=item[0])current=item}
   if(current[1]!==last){
    last=current[1];el.className='bo-launch-countdown '+current[2];
    el.querySelector('strong').textContent=current[1];
   }
   frame=requestAnimationFrame(tick);
  };
  tick();
 }
 window.booyahLaunchCountdown=maybe;
 window.booyahClearCountdown=cleanup;
})();
