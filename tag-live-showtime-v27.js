/* TAG LIVE SHOWTIME V27
 * Presentation only. All points, ranks and winners come from the authoritative
 * /api/room/state response; never change scoring, attendance, room permissions,
 * PINs or exam feedback policy.
 */
(()=>{
'use strict';
const state={stage:{question:null,scores:new Map()},host:{question:null,scores:new Map()}};
const ceremonyRuns=new WeakMap();
const prefersReduced=()=>!!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
const escapeText=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const avatarPath=id=>/^m0[1-8]$/.test(id)?'/assets/avatars-game/'+(id==='m08'?'m07':id)+'.svg':/^n0[1-8]$/.test(id)?'/assets/avatars3d/'+id+'.webp':/^[bg](0[1-9]|1[0-6])$/.test(id)?'/assets/avatars3d/'+id+'.webp':'/assets/avatars/'+(/^\d{2}$/.test(id)?id:'01')+'.svg';
const points=n=>Math.max(0,Math.round(Number(n)||0));
const key=(p,teams)=>teams?'team:'+String(p.name||''):'student:'+String(p.name||'')+':'+String(p.avatar||'');
const contenders=room=>room.playType==='teams'?(room.teams||[]):(room.leaders||[]);
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));

function remember(room,where='stage'){
 const m=state[where]||state.stage;
 if(room.status!=='question'||room.examMode||!room.showFeedback)return;
 const question=String(room.code||'')+':'+String(room.index);
 if(m.question===question)return; // Never overwrite pre-round scores as students answer.
 m.question=question;
 m.scores=new Map(contenders(room).map(p=>[key(p,room.playType==='teams'),points(p.score)]));
}
function reorder(list,root){
 const all=Array.from(list);
 const before=new Map(all.map(el=>[el,el.getBoundingClientRect()]));
 all.sort((a,b)=>{
  const ar=a.dataset.revealed==='1',br=b.dataset.revealed==='1';
  if(ar!==br)return ar?-1:1;
  if(!ar)return Number(a.dataset.seed)-Number(b.dataset.seed);
  return Number(b.dataset.score)-Number(a.dataset.score)||Number(a.dataset.finalRank)-Number(b.dataset.finalRank);
 });
 root.replaceChildren(...all);
 all.forEach((el,i)=>{
  const tag=el.querySelector('.tag-v27-rank');
  if(tag&&el.dataset.revealed==='1')tag.textContent=String(i+1);
  if(prefersReduced()||!el.animate)return;
  const old=before.get(el),now=el.getBoundingClientRect();
  if(!old||!now)return;
  const dx=old.left-now.left,dy=old.top-now.top;
  if(Math.abs(dx)+Math.abs(dy)>3)el.animate(
   [{transform:'translate('+dx+'px,'+dy+'px)'},{transform:'translate(0,0)'}],
   {duration:540,easing:'cubic-bezier(.2,.8,.2,1)'});
 });
}
function round(room,mount,where='stage',onComplete){
 if(!mount||room.status!=='results'||room.examMode||!room.showFeedback)return false;
 const isTeams=room.playType==='teams',all=contenders(room).slice(0,5);
 const m=state[where]||state.stage;
 const signature=JSON.stringify([room.code,room.index,isTeams,all.map(p=>[p.name,p.avatar,p.score])]);
 if(mount.dataset.showtimeKey===signature)return true;
 mount.dataset.showtimeKey=signature;
 mount.setAttribute('role','region');
 mount.setAttribute('aria-label',isTeams?'كشف ترتيب الفرق':'كشف أول خمسة طلاب');
 const head=document.createElement('div');
 head.className='tag-v27-round-head';
 head.innerHTML='<span class="tag-v27-spark">✦</span><div><strong>لحظة الحسم!</strong><small>الاسم أولًا… ثم النقاط… ثم صعود المركز</small></div><span class="tag-v27-status" aria-live="polite">استعدّوا!</span>';
 const list=document.createElement('div');list.className='tag-v27-list';
 mount.replaceChildren(head,list);
 if(!all.length){list.innerHTML='<p class="tag-v27-empty">لا توجد نقاط بعد.</p>';if(onComplete)onComplete();return true}
 const havePrior=m.question===String(room.code||'')+':'+room.index;
 const rows=all.map((p,i)=>{
  const k=key(p,isTeams),start=havePrior?(m.scores.get(k)||0):0;
  const row=document.createElement('div');row.className='tag-v27-row';
  row.dataset.finalRank=String(i+1);row.dataset.score=String(start);
  row.dataset.seed=String(i);row.dataset.revealed='0';
  row.dataset.target=String(points(p.score));row.dataset.start=String(start);
  const avatar=isTeams?'<span class="tag-v27-team-emblem">⚔️</span>':'<img src="'+avatarPath(p.avatar)+'" alt="" loading="eager">';
  row.innerHTML='<span class="tag-v27-rank">؟</span><span class="tag-v27-person">'+avatar+
    '</span><div class="tag-v27-name"><strong class="tag-v27-realname">منافس ينتظر دوره…</strong>'+
    '<small class="tag-v27-gain">الجولة لا تزال مليئة بالمفاجآت</small></div>'+
    '<strong class="tag-v27-score">—</strong>';
  row._playerName=escapeText(p.name);
  list.appendChild(row);return row;
 });
 if(prefersReduced()){
  rows.forEach(row=>{
   row.dataset.revealed='1';row.dataset.score=row.dataset.target;
   row.querySelector('.tag-v27-realname').innerHTML=row._playerName;
   row.querySelector('.tag-v27-score').textContent=row.dataset.target+' ★';
   row.querySelector('.tag-v27-gain').textContent='تم احتساب النقاط';
   row.classList.add('tag-v27-visible');
  });
  reorder(rows,list);
  head.querySelector('.tag-v27-status').textContent='الترتيب النهائي للجولة';
  onComplete?.();
  return true;
 }
 const status=head.querySelector('.tag-v27-status');
 let completed=false;
 (async()=>{
  // Reveal 5 → 1, then let each participant's points move them upward.
  for(let index=all.length-1;index>=0;index--){
   if(!mount.isConnected||mount.dataset.showtimeKey!==signature)return;
   const row=rows[index],start=Number(row.dataset.start),target=Number(row.dataset.target);
   status.textContent='المركز '+(index+1)+'…';
   await wait(290);
   if(!mount.isConnected||mount.dataset.showtimeKey!==signature)return;
   row.dataset.revealed='1';row.classList.add('tag-v27-visible');
   row.querySelector('.tag-v27-realname').innerHTML=row._playerName;
   row.querySelector('.tag-v27-gain').textContent=target>start?'+'+(target-start)+' نقطة في الجولة':'النقاط ثابتة — المنافسة مستمرة';
   row.querySelector('.tag-v27-score').textContent=start+' ★';
   reorder(rows,list);
   await wait(250);
   const startTime=performance.now(),duration=710;
   await new Promise(resolve=>{
    const tick=now=>{
     if(!mount.isConnected||mount.dataset.showtimeKey!==signature){resolve();return}
     const t=Math.min(1,(now-startTime)/duration);
     const ease=1-Math.pow(1-t,3);
     const current=Math.round(start+(target-start)*ease);
     row.dataset.score=String(current);
     row.querySelector('.tag-v27-score').textContent=current+' ★';
     if(t<1)requestAnimationFrame(tick);else resolve();
    };
    requestAnimationFrame(tick);
   });
   if(!mount.isConnected||mount.dataset.showtimeKey!==signature)return;
   row.dataset.score=String(target);
   reorder(rows,list);
   row.classList.add('tag-v27-settled');
   await wait(225);
  }
  if(!mount.isConnected||mount.dataset.showtimeKey!==signature)return;
  status.textContent='🏆 الترتيب بعد السؤال';
  completed=true;onComplete?.();
 })().catch(err=>{console.warn('TAG round reveal:',err);if(!completed)onComplete?.()});
 return true;
}
function podiumMarkup(top,{host=false,isTeams=false}={}){
 const medals=['🥇','🥈','🥉'];
 return top.slice(0,3).map((p,i)=>{
  const safeName=escapeText(p.name),place=i+1;
  const score=points(p.score);
  const head=isTeams?'<span class="tag-v27-face-team">⚔️</span>':'<img src="'+avatarPath(p.avatar)+'" alt="" loading="eager">';
  return '<div class="'+(host?'v104-podium-card':'v104-stage-pod')+' place-'+place+' tag-v27-pod" data-tag-place="'+place+'">'+
    '<div class="tag-v27-medal">'+medals[i]+'</div>'+
    '<div class="tag-v27-character" aria-label="'+(isTeams?'فريق ':'شخصية الطالب ')+safeName+'">'+
      '<div class="tag-v27-head">'+head+'</div>'+
      '<div class="tag-v27-arms"><i></i><i></i></div>'+
      '<div class="tag-v27-torso"><span>TAG</span></div>'+
      '<div class="tag-v27-legs"><i></i><i></i></div>'+
    '</div>'+
    '<span class="tag-v27-place">'+(place===1?'المركز الأول':place===2?'المركز الثاني':'المركز الثالث')+'</span>'+
    '<h3 class="tag-v27-student">'+safeName+'</h3>'+
    '<strong class="tag-v27-points">'+score+' نقطة</strong>'+
    (p.percent!=null?'<small>'+Math.max(0,Math.min(100,Number(p.percent)||0))+'% دقة</small>':'')+
   '</div>';
 }).join('');
}
async function celebrate(root,options={}){
 if(!root)return;
 const serial=(ceremonyRuns.get(root)||0)+1;
 ceremonyRuns.set(root,serial);
 const cards=[3,2,1].map(n=>root.querySelector('.tag-v27-pod[data-tag-place="'+n+'"]')).filter(Boolean);
 for(const card of cards)card.classList.remove('tag-v27-revealed','tag-v27-crowned');
 const message=root.querySelector('.tag-v27-winner-announcement');
 if(message)message.textContent='المنصة تستعد لاستقبال الأبطال…';
 for(const card of cards){
  if(!prefersReduced())await wait(card.dataset.tagPlace==='1'?1300:900);
  if(!root.isConnected||ceremonyRuns.get(root)!==serial)return;
  card.classList.add('tag-v27-revealed');
  if(card.dataset.tagPlace==='1'){
   card.classList.add('tag-v27-crowned');
   if(message)message.textContent='👑 بطل التحدي: '+card.querySelector('.tag-v27-student')?.textContent+'!';
   if(typeof options.onChampion==='function')options.onChampion();
  }
 }
}
window.TagLiveShow={remember,round,podiumMarkup,celebrate,replayPodium:celebrate};
})();
