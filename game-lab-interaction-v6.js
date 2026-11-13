/* TeachGame / BOOYAHJO Game Lab — Interaction Redesign V6
 * Visually enrich the six QA teacher-preview games. Preserve the original
 * game logic, scoring, timers, text and API flows; only decorate rendered nodes.
 */
(()=>{
'use strict';
const doc=document;
const $=id=>doc.getElementById(id);
const supported=new Set(['quiz','fast','truth','pairs','wheel','boxes']);
const answerLetters=['أ','ب','ج','د'];
let lastFeedback='', lastBody=null;
function gameMode(){
 const title=($('playTitle')?.textContent||'').trim();
 if(title.includes('سباق الوقت'))return 'fast';
 if(title.includes('تحدي الاختيار'))return 'quiz';
 if(title.includes('صح أم خطأ'))return 'truth';
 if(title.includes('توصيل الأزواج'))return 'pairs';
 if(title.includes('عجلة الحظ'))return 'wheel';
 if(title.includes('الصناديق الغامضة'))return 'boxes';
 return '';
}
function getProgress(){
 const counter=$('playCounter')?.textContent||'';
 const match=counter.match(/(\d+)\s*\/\s*(\d+)/);
 if(match)return {current:Number(match[1]),total:Number(match[2])};
 const info=$('playBody')?.querySelector('.playinfo > span:first-child')?.textContent||'';
 const m=info.match(/(\d+)\s*من\s*(\d+)/);
 return m?{current:Number(m[1]),total:Number(m[2])}:null;
}
function progressBar(parent,key,current,total){
 if(!parent||!total)return;
 let bar=parent.querySelector('.v6-progress[data-v6-key="'+key+'"]');
 if(!bar){
  bar=doc.createElement('div');bar.className='v6-progress';bar.dataset.v6Key=key;
  bar.setAttribute('role','progressbar');bar.setAttribute('aria-valuemin','0');bar.setAttribute('aria-valuemax',String(total));
  bar.setAttribute('aria-label','تقدم اللعبة');
  const inner=doc.createElement('span');bar.append(inner);parent.append(bar);
 }
 const done=Math.max(0,Math.min(total,current));
 const pct=Math.round(done*100/total);
 const old=bar.style.getPropertyValue('--v6-pct');
 if(old!==pct+'%')bar.style.setProperty('--v6-pct',pct+'%');
 if(bar.getAttribute('aria-valuenow')!==String(done))bar.setAttribute('aria-valuenow',String(done));
}
function decorateInfo(mode){
 const info=$('playBody')?.querySelector('.playinfo');
 if(!info)return;
 const p=getProgress();
 if(p)progressBar(info,'round',mode==='pairs'?p.current:Math.min(p.total,p.current),p.total);
 if(mode==='fast'){
  let dial=info.querySelector('.v6-timer');
  if(!dial){
   dial=doc.createElement('div');dial.className='v6-timer';
   dial.setAttribute('role','timer');dial.setAttribute('aria-label','الوقت المتبقي');
   const inner=doc.createElement('span');dial.append(inner);info.append(dial);
  }
  const original=$('roundTime'),total=Math.max(1,Number(original?.value)||25);
  const text=$('clockChip')?.textContent||'';
  const m=text.match(/(\d+)/),remaining=m?Math.max(0,Number(m[1])):total;
  const ratio=Math.max(0,Math.min(100,Math.round(remaining*100/total)));
  dial.style.setProperty('--v6-time',ratio+'%');
  if(dial.firstElementChild.textContent!==String(remaining))dial.firstElementChild.textContent=String(remaining);
  dial.classList.toggle('v6-critical',remaining<=5);
 }else{
  info.querySelector('.v6-timer')?.remove();
 }
}
function decorateQuestion(mode){
 const card=$('playBody')?.querySelector('.playcard');
 if(!card||card.querySelector('.v6-question-label'))return;
 if(!card.querySelector('h3'))return;
 const label=doc.createElement('span');label.className='v6-question-label';
 const title={
  quiz:'🎯 اختر الإجابة الصحيحة',fast:'⚡ تحدي السرعة',truth:'🧠 صح أم خطأ',
  wheel:'🎡 عجلة الأسئلة',boxes:'🎁 اكشف المفاجأة',pairs:'🧩 مطابقة الأزواج'
 };
 label.textContent=title[mode]||'سؤال';
 card.prepend(label);
}
function decorateChoices(mode){
 const answers=$('playBody')?.querySelector(mode==='truth'?'#truthActions':'#answers');
 if(!answers)return;
 answers.querySelectorAll('button.choice').forEach((button,i)=>{
  if(button.dataset.v6Choice)return;
  const text=button.textContent;
  const letter=doc.createElement('span');letter.className='v6-choice-index';letter.setAttribute('aria-hidden','true');
  letter.textContent=mode==='truth'?(i===0?'✓':'✕'):answerLetters[i]||String(i+1);
  const label=doc.createElement('span');label.className='v6-choice-label';label.textContent=text;
  button.replaceChildren(letter,label);button.dataset.v6Choice='1';
  button.setAttribute('aria-label',(mode==='truth'?'':'الخيار '+letter.textContent+': ')+text);
 });
}
function decoratePairs(){
 const grid=$('playBody')?.querySelector('.matchgrid');if(!grid)return;
 for(const [id,label] of [['matchLeft','📚 الأسئلة'],['matchRight','🔗 الإجابات']]){
  const col=$(id);if(!col||col.querySelector('.v6-column-heading'))continue;
  const h=doc.createElement('div');h.className='v6-column-heading';h.textContent=label;col.prepend(h);
 }
 // The original pair game re-renders button lists after each selection.
 // We do not replace buttons or alter their click handlers.
}
function decorateWheel(){
 const wheel=$('spinWheel'),revealed=$('wheelReveal');
 if(!wheel)return;
 if(!wheel.dataset.v6Disc){
  wheel.dataset.v6Disc='1';wheel.setAttribute('aria-label','عجلة حظ ملونة لاختيار السؤال');
 }
 if(revealed?.querySelector('h3')&&!revealed.querySelector('.v6-question-label')){
  const label=doc.createElement('span');label.className='v6-question-label';
  label.textContent='✨ سؤال الحظ';revealed.prepend(label);
 }
}
function decorateBoxes(){
 const grid=$('boxesGrid');if(!grid)return;
 grid.querySelectorAll('button.mystery').forEach((button,i)=>{
  if(!button.dataset.v6Box){button.dataset.v6Box='1';button.setAttribute('aria-label','افتح الصندوق '+(i+1))}
  const solved=button.textContent.trim().startsWith('✅');
  if(button.classList.contains('v6-solved')!==solved)button.classList.toggle('v6-solved',solved);
 });
 // Track boxes opened on the real game's existing status counter.
 const p=getProgress();if(p){
  let head=grid.previousElementSibling;
  if(head&&!head.classList.contains('v6-box-progress')){
   const parent=doc.createElement('div');parent.className='v6-box-progress';
   grid.before(parent);head=parent;
  }
  if(head?.classList.contains('v6-box-progress'))progressBar(head,'boxes',p.current,p.total);
 }
}
function flashFeedback(){
 if(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches)return;
 const overlay=$('playOverlay');if(!overlay||overlay.hidden)return;
 overlay.querySelector('.v6-confetti')?.remove();
 const group=doc.createElement('div');group.className='v6-confetti';group.setAttribute('aria-hidden','true');
 const colors=['#ec5e97','#f2bb52','#5ed4bb','#7e7aeb','#66c8f0','#dd79c5'];
 for(let i=0;i<18;i++){
  const particle=doc.createElement('i');
  particle.style.setProperty('--v6-left',(4+i*5.2)+'%');
  particle.style.setProperty('--v6-color',colors[i%colors.length]);
  particle.style.setProperty('--v6-delay',(i%5)*35+'ms');
  group.append(particle);
 }
 overlay.append(group);
 setTimeout(()=>{if(group.isConnected)group.remove()},1700);
}
function reflectFeedback(){
 const overlay=$('playOverlay'),status=$('playStatus');
 if(!overlay?.classList.contains('v6-game')||!status)return;
 const text=status.textContent.trim();
 let type='';
 if(/✅|صحيح|أحسنت|فتحت جميع الصناديق/.test(text))type='correct';
 else if(/💡|جرّب مرة|خاطئ|الإجابة الصحيحة|الإجابة الأصلية/.test(text))type='wrong';
 else if(/^الإجابة\s*:/.test(text))type='reveal';
 if(status.dataset.v6Result!==type)status.dataset.v6Result=type;
 if(text!==lastFeedback){
  lastFeedback=text;
  if(type==='correct')flashFeedback();
  if(type==='wrong'&&overlay.dataset.v6Mode==='truth'){
   const selected=doc.querySelector('#truthActions .choice[data-v6-selected="1"]');
   if(selected)selected.classList.add('wrong');
  }
 }
}
function decorate(){
 const overlay=$('playOverlay'),body=$('playBody');if(!overlay||!body)return;
 if(overlay.hidden)return;
 const mode=gameMode();
 if(!supported.has(mode)){
  overlay.classList.remove('v6-game');delete overlay.dataset.v6Mode;return;
 }
 if(!overlay.classList.contains('v6-game'))overlay.classList.add('v6-game');
 if(overlay.dataset.v6Mode!==mode){
  overlay.dataset.v6Mode=mode;lastFeedback='';
 }
 if(body!==lastBody){lastBody=body;lastFeedback=''}
 decorateInfo(mode);
 decorateQuestion(mode);
 if(mode==='quiz'||mode==='fast'||mode==='truth')decorateChoices(mode);
 if(mode==='pairs')decoratePairs();
 if(mode==='wheel')decorateWheel();
 if(mode==='boxes')decorateBoxes();
 reflectFeedback();
}
function start(){
 const overlay=$('playOverlay'),body=$('playBody'),status=$('playStatus');
 if(!overlay||!body)return;
 let queued=false;
 function schedule(){
  if(queued)return;queued=true;
  queueMicrotask(()=>{queued=false;decorate()});
 }
 const observer=new MutationObserver(schedule);
 observer.observe(body,{childList:true,subtree:true,characterData:true});
 if(status)observer.observe(status,{childList:true,subtree:true,characterData:true});
 observer.observe(overlay,{attributes:true,attributeFilter:['hidden']});
 // If the user guesses an answer in the true/false game, remember its selected tile
 // for the later visual correctness highlight only; the original handler scores it.
 overlay.addEventListener('click',e=>{
  const b=e.target.closest('#truthActions button.choice');
  if(!b)return;
  overlay.querySelectorAll('#truthActions .choice').forEach(x=>delete x.dataset.v6Selected);
  b.dataset.v6Selected='1';
  schedule();
 },true);
 doc.addEventListener('keydown',e=>{if(e.key==='Escape'&&overlay.hidden){overlay.classList.remove('v6-game');delete overlay.dataset.v6Mode}});
 schedule();
}
if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
