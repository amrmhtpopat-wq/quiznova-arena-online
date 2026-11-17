/* TeachGame Game Lab V9 student scene feedback.
 * All real answers, progress, grades and retries remain server-authoritative.
 */
(()=>{
'use strict';
const D=document,answer=D.getElementById('answerMessage'),question=D.getElementById('questionPanel'),finish=D.getElementById('finishPanel');
if(!answer||!question||!finish)return;
let prev='',finishShown=false,timeout=0;
const reduce=()=>Boolean(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches);
function celebrate(){
 if(reduce())return;
 const prior=D.querySelector('.v9-student-burst');if(prior)prior.remove();
 const layer=D.createElement('div');layer.className='v9-student-burst';layer.setAttribute('aria-hidden','true');
 const palette=['#ffe187','#f2a2bd','#79e1ed','#aff1bd','#aa9af4'];
 for(let i=0;i<24;i++){
  const piece=D.createElement('i'),theta=i*2.3999632;
  piece.style.setProperty('--x',(50+37*Math.sin(theta))+'%');
  piece.style.setProperty('--y',(36+25*Math.cos(theta))+'%');
  piece.style.setProperty('--dx',((i%2?1:-1)*(25+3*i))+'px');
  piece.style.setProperty('--color',palette[i%palette.length]);layer.append(piece);
 }
 D.body.append(layer);clearTimeout(timeout);timeout=setTimeout(()=>layer.remove(),1400);
}
function render(){
 const msg=answer.textContent.trim();
 if(msg!==prev){
  const correct=/✅|أحسنت|صحيحة/.test(msg),wrong=/الإجابة الصحيحة|خطأ|خاطئة|💡/.test(msg)&&!correct;
  answer.classList.toggle('v9-good',correct&&!wrong);
  answer.classList.toggle('v9-bad',wrong);
  if(correct&&msg&&!question.classList.contains('hide'))celebrate();
  prev=msg;
 }
 const ended=!finish.classList.contains('hide');
 if(ended&&!finishShown)celebrate();
 finishShown=ended;
}
function start(){
 let scheduled=false;
 const observer=new MutationObserver(()=>{
  if(scheduled)return;scheduled=true;
  requestAnimationFrame(()=>{scheduled=false;render()});
 });
 observer.observe(answer,{subtree:true,childList:true,characterData:true});
 observer.observe(finish,{attributes:true,attributeFilter:['class']});
 observer.observe(question,{attributes:true,attributeFilter:['class']});
 render();
}
if(D.readyState==='loading')D.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();