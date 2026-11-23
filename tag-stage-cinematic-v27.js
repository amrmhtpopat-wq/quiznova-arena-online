/* TAG V27 — live leaderboard reveal & third→second→first cinematic podium.
 * Read-only visual effects. The server remains the only source of scores,
 * positions, answers, student avatars and the winner.
 */
(()=>{'use strict';
 const state={seq:0,timers:[],liveSig:'',lastLive:[],finishSig:'',resultsSig:'',liveBusyUntil:0,pendingLive:null};
 const delay=(fn,ms)=>{const id=setTimeout(fn,ms);state.timers.push(id);return id};
 const clear=()=>{state.seq++;state.timers.forEach(clearTimeout);state.timers=[]};
 const reduced=()=>window.matchMedia?.('(prefers-reduced-motion: reduce)').matches===true;
 const safe=(v)=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const numeric=v=>Math.max(0,Math.round(Number(v)||0));
 const top=r=>((r.playType==='teams'?r.teams:r.leaders)||[]).slice(0,5);
 const marker=i=>['🥇','🥈','🥉','4','5'][i]||String(i+1);
 function animateScore(node,next,previous,token,done){
  if(!node)return;
  const to=numeric(next),from=Math.min(to,numeric(previous));
  if(reduced()||from===to){node.textContent=to.toLocaleString('ar-JO');done?.();return}
  const start=performance.now(),duration=550;
  const run=now=>{
   if(token!==state.seq||!node.isConnected)return;
   const step=Math.min(1,(now-start)/duration);
   node.textContent=Math.round(from+(to-from)*(1-(1-step)**3)).toLocaleString('ar-JO');
   if(step<1)requestAnimationFrame(run);else done?.();
  };
  requestAnimationFrame(run);
 }
 function progress(rows,container,opts={}){
  if(!container)return;
  const token=state.seq;
  const ordered=rows.slice(0,5);
  container.replaceChildren();
  if(!ordered.length){container.innerHTML='<p class="tag27-empty">بانتظار إجابات الطلاب والنقاط…</p>';return}
  const previous=new Map((opts.before||[]).map(p=>[String(p.name),numeric(p.score)]));
  const spacing=reduced()?0:opts.spacing??820;
  ordered.forEach((p,i)=>{
   delay(()=>{
    if(token!==state.seq||!container.isConnected)return;
    const row=document.createElement('div');row.className='tag27-rank-row';
    row.style.setProperty('--i',String(i));
    row.innerHTML='<div class="tag27-position">'+marker(i)+'</div>'+
      '<div class="tag27-player"><b>'+safe(p.name)+'</b><small>'+(i===0?'المتصدر الآن':i===1?'المنافس الأقرب':i===2?'على منصة التتويج':'ضمن الخمسة الأوائل')+'</small></div>'+
      '<div class="tag27-score"><strong>0</strong><span>نقطة</span></div>';
    container.appendChild(row);
    row.classList.add('tag27-visible');
    const number=row.querySelector('.tag27-score strong');
    animateScore(number,p.score,previous.get(String(p.name))||0,token);
    if(i===ordered.length-1)delay(()=>{
      if(token===state.seq&&container.isConnected)container.classList.add('tag27-complete');
    },spacing*0.6);
   },(reduced()?0:i*spacing));
  });
 }
 function updateLive(room){
  const root=document.getElementById('tagLiveLeaders');
  if(!root)return;
  if(room.examMode||room.showFeedback===false){root.textContent='🛡️ الترتيب مخفي خلال التحدي';return}
  const list=top(room),sig=JSON.stringify(list.map(p=>[p.name,p.score]));
  if(sig===state.liveSig&&root.querySelector('.tag27-live-list'))return;
  // Keep every reveal readable even when the server publishes score changes
  // every 700ms. Coalesce incoming updates and animate the freshest standings
  // after the current five names have been shown.
  if(!reduced()&&Date.now()<state.liveBusyUntil){
    state.pendingLive=room;
    return;
  }
  const before=state.lastLive;
  state.lastLive=list.map(p=>({name:p.name,score:p.score}));
  state.liveSig=sig;
  clear();
  root.innerHTML='<div class="tag27-live-head"><span>⚡ تحديث مباشر للمراكز الخمسة</span><small>النقاط والترتيب يتجددان بالتتابع</small></div><div class="tag27-live-list" aria-label="ترتيب الخمسة الأوائل"></div>';
  progress(list,root.querySelector('.tag27-live-list'),{before,spacing:500});
  state.liveBusyUntil=Date.now()+(reduced()?0:Math.max(1,list.length)*500+800);
  delay(()=>{
    if(!state.pendingLive)return;
    const latest=state.pendingLive;
    state.pendingLive=null;state.liveBusyUntil=0;
    updateLive(latest);
  },reduced()?0:Math.max(1,list.length)*500+820);
 }
 function results(room,parts){
  const dest=document.getElementById('stage');if(!dest)return false;
  const list=top(room),stats=room.stats||{};
  clear();state.liveSig='';state.liveBusyUntil=0;state.pendingLive=null;
  dest.innerHTML='<div class="stage-wrap tag27-round-wrap">'+parts.head+
   '<div class="round-stage tag27-results"><div class="tag27-intro"><span>TAG LIVE • ROUND '+(numeric(room.index)+1)+'</span>'+
   '<h1>⚡ لحظة تغيير الترتيب!</h1><p>تابعوا المراكز وهي تظهر واحدًا بعد الآخر…</p></div>'+
   '<section class="tag27-rank-panel"><div class="tag27-rank-heading"><strong>'+
   (room.playType==='teams'?'🏆 ترتيب المجموعات':'🏅 أفضل خمسة طلاب')+'</strong>'+
   '<span>'+numeric(stats.accuracy)+'% دقة • '+numeric(stats.correct)+' إجابة صحيحة</span></div>'+
   '<div id="tag27RoundList" class="tag27-round-list" aria-label="أفضل خمسة بعد الجولة"></div></section>'+
   (room.explanation?'<p class="bo-stage-explanation">💡 '+safe(room.explanation)+'</p>':'')+
   parts.next+'</div></div>';
  progress(list,document.getElementById('tag27RoundList'),{before:state.lastLive,spacing:900});
  state.lastLive=list.map(p=>({name:p.name,score:p.score}));
  return true;
 }
 function fullFigure(p,parts){
  const path=parts.avatarPath(p.avatar||'01');
  const name=safe(p.name);
  return '<div class="tag27-figure" role="img" aria-label="الشخصية الكاملة للمشارك '+name+'">'+
   '<span class="tag27-figure-glow"></span><div class="tag27-head"><img loading="eager" src="'+safe(path)+'" alt="الصورة الشخصية لـ '+name+'"></div>'+
   '<div class="tag27-body"><i class="tag27-arm tag27-arm-left"></i><i class="tag27-arm tag27-arm-right"></i>'+
   '<span class="tag27-body-logo">TAG</span><i class="tag27-leg tag27-leg-left"></i><i class="tag27-leg tag27-leg-right"></i></div></div>';
 }
 function finale(room,parts){
  const dest=document.getElementById('stage');if(!dest)return false;
  clear();state.liveSig='';state.liveBusyUntil=0;state.pendingLive=null;
  const teams=room.playType==='teams',ranked=(teams?room.teams:room.report)||[],players=room.players||[];
  const winner=ranked[0];
  const podium=[2,1,0].filter(i=>ranked[i]).map(i=>{
   const item=ranked[i],place=i+1;
   const avatarItem=teams?(players.find(p=>p.team===item.name)||{}):item;
   return '<article class="tag27-podium-card tag27-place-'+place+'" data-place="'+place+'" aria-label="المركز '+place+'، '+safe(item.name)+'">'+
    '<div class="tag27-medal">'+marker(i)+'</div>'+
    fullFigure({...avatarItem,name:item.name},parts)+
    '<div class="tag27-podium-name">'+safe(item.name)+'</div>'+
    '<div class="tag27-points">'+numeric(item.score).toLocaleString('ar-JO')+' نقطة</div>'+
    '<div class="tag27-stand">'+(place===1?'البطل':place===2?'الوصيف':'المركز الثالث')+'</div></article>';
  }).join('');
  dest.innerHTML='<div class="stage-wrap tag27-final-wrap">'+parts.head+
   '<div class="v104-confetti" id="v104VictoryParticles"></div>'+
   '<section class="tag27-final" aria-label="حفل تتويج أفضل ثلاثة">'+
   '<div class="tag27-final-head"><span>🏆 TAG CHAMPIONS • GRAND FINALE</span><h1>لحظة التتويج الكبرى</h1>'+
   '<p id="tag27Announcement" aria-live="polite">استعدوا لصعود أبطال التحدي!</p></div>'+
   '<div class="tag27-podium" id="tag27Podium">'+podium+'</div>'+
   '<div class="tag27-final-footer"><small>👥 '+(teams?players.length:ranked.length)+' مشارك • 🎯 '+numeric(room.total)+' سؤال</small>'+
   '<button id="tag27Replay" type="button">🎉 إعادة التتويج</button></div></section></div>';
  const play=()=>{
    clear();const token=state.seq;
    dest.querySelectorAll('.tag27-podium-card').forEach(x=>x.classList.remove('tag27-entered'));
    const notice=dest.querySelector('#tag27Announcement');
    const entrants=[3,2,1].filter(n=>dest.querySelector('.tag27-place-'+n));
    entrants.forEach((place,i)=>{
      delay(()=>{
        if(token!==state.seq)return;
        const el=dest.querySelector('.tag27-place-'+place);if(!el)return;
        el.classList.add('tag27-entered');
        notice.textContent=place===1?'🥇 '+(winner?winner.name:'بطل التحدي')+'… بطل TAG!':
         place===2?'🥈 الوصيف يعتلي المنصة!':'🥉 المركز الثالث يعتلي المنصة!';
        if(place===1){parts.replay?.();el.classList.add('tag27-champion');}
      },reduced()?i*10:650+i*2100);
    });
  };
  dest.querySelector('#tag27Replay')?.addEventListener('click',play);
  play();return true;
 }
 function reset(){
  clear();state.liveSig='';state.lastLive=[];state.liveBusyUntil=0;state.pendingLive=null;
 }
 window.TAGStageCinema={results,finale,updateLive,reset};
})();
