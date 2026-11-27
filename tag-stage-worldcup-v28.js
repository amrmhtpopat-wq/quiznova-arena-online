/* TAG World Cup Finale V28 — premium read-only final awards ceremony.
   The server's final ranked report is the ONLY source of names, scores, avatars and places.
   No student or teacher secrets are read, stored or transmitted by this presentation. */
(()=>{'use strict';
 const tokens={sequence:0,timers:[],audio:null,open:false};
 const safe=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
 const points=value=>Math.max(0,Math.round(Number(value)||0)).toLocaleString('en-US');
 const reduced=()=>window.matchMedia?.('(prefers-reduced-motion: reduce)').matches===true;
 const schedule=(fn,ms)=>{const timer=setTimeout(fn,ms);tokens.timers.push(timer)};
 const stop=()=>{tokens.sequence++;tokens.timers.forEach(clearTimeout);tokens.timers=[]};
 const avatarOf=(p,room,parts)=>{
  const roster=room.players||[];
  const actual=roster.find(x=>p.id&&x.id&&String(x.id)===String(p.id)) ||
   roster.find(x=>String(x.name||'').trim()===String(p.name||'').trim()) || {};
  const avatar=String(actual.avatar||p.avatar||'01');
  return parts.avatarPath(avatar);
 };
 function figure(participant,room,parts){
  // Display ONLY the complete original avatar chosen by this student.
  // No generated torso, limbs, altered face, cropped circle or stitched figure.
  const img=safe(avatarOf(participant,room,parts));
  const name=safe(participant.name||'مشارك');
  return '<div class="tag28-person" role="group" aria-label="صورة '+name+'">'+
   '<div class="tag28-person-aura" aria-hidden="true"></div>'+
   '<img class="tag28-avatar-original" src="'+img+'" alt="الصورة التي اختارها '+name+'" loading="eager" decoding="async"></div>';
 }
 function award(p,index,room,parts){
  const place=index+1,colors=['ذهبي','فضي','برونزي'];
  return '<article class="tag28-winner tag27-podium-card tag27-place-'+place+' tag28-place-'+place+'" data-place="'+place+'" aria-label="المركز '+place+'، '+safe(p.name)+'" aria-hidden="true">'+
   '<span class="tag28-place-medal" aria-hidden="true">'+place+'</span>'+
   figure(p,room,parts)+
   '<div class="tag28-nameplate"><span>المركز '+(place===1?'الأول':place===2?'الثاني':'الثالث')+'</span><strong class="tag27-podium-name">'+safe(p.name||'مشارك')+'</strong>'+
   '<b>'+points(p.score)+' <small>نقطة</small></b></div>'+
   '<div class="tag28-stand"><div class="tag28-stand-top"></div><div class="tag28-stand-front"><span class="tag28-shield">'+place+'</span><strong>'+colors[index]+'</strong></div></div></article>';
 }
 function stat(icon,label,value){return '<div class="tag28-stat"><span class="tag28-stat-icon" aria-hidden="true">'+icon+'</span><span>'+label+'</span><strong>'+safe(value)+'</strong></div>'}
 function row(p,index){
  return '<li class="tag28-all-row"><span class="tag28-all-rank">'+(index+1)+'</span><span class="tag28-all-name">'+safe(p.name||'مشارك')+'</span><strong>'+points(p.score)+' نقطة</strong></li>';
 }
 function chime(){
  if(!tokens.audio)return;
  try{
   const ctx=tokens.audio;
   if(ctx.state==='suspended')void ctx.resume();
   const now=ctx.currentTime;
   [392,523.25,659.25,783.99].forEach((pitch,i)=>{
    const osc=ctx.createOscillator(),gain=ctx.createGain();
    osc.type='sine';osc.frequency.value=pitch;
    gain.gain.setValueAtTime(.0001,now+i*.14);
    gain.gain.exponentialRampToValueAtTime(.048,now+i*.14+.03);
    gain.gain.exponentialRampToValueAtTime(.0001,now+i*.14+.6);
    osc.connect(gain);gain.connect(ctx.destination);
    osc.start(now+i*.14);osc.stop(now+i*.14+.65);
   });
  }catch(_e){}
 }
 function confetti(root){
  const box=root.querySelector('.tag28-confetti');if(!box)return;
  box.replaceChildren();if(reduced())return;
  for(let i=0;i<76;i++){
   const el=document.createElement('i');
   el.style.setProperty('--x',((i*71.43)%100)+'%');
   el.style.setProperty('--wait',((i*13)%21)/10+'s');
   el.style.setProperty('--speed',(3+(i%9)*.32)+'s');
   el.style.setProperty('--h',i%3===0?'45':i%3===1?'195':'280');
   el.style.setProperty('--r',((i*29)%240-120)+'deg');
   box.append(el);
  }
 }
 function flourish(root){
  const zone=root.querySelector('.tag28-fireworks');if(!zone||reduced())return;
  zone.replaceChildren();
  const spots=[[24,25],[74,15],[13,45],[86,38],[49,13]];
  spots.forEach(([x,y],n)=>{
   const ring=document.createElement('div');ring.className='tag28-burst';
   ring.style.setProperty('--x',x+'%');ring.style.setProperty('--y',y+'%');
   ring.style.setProperty('--delay',n*.17+'s');
   for(let i=0;i<18;i++){
    const dot=document.createElement('i');dot.style.setProperty('--rot',(i*20)+'deg');ring.append(dot);
   }
   zone.append(ring);
  });
  confetti(root);
 }
 function finale(room,parts){
  const mount=document.getElementById('stage');if(!mount)return false;
  stop();tokens.open=false;
  const teams=room.playType==='teams';
  const ranked=(teams?room.teams:room.report)||[];
  const players=room.players||[];
  const podium=[2,1,0].filter(i=>ranked[i]).map(i=>{
   const item=ranked[i];
   const avatarItem=teams?(players.find(p=>p.team===item.name)||{}):item;
   return award({...avatarItem,...item},i,room,parts);
  }).join('');
  const c4=ranked[3],c5=ranked[4];
  const sideCard=(participant,label)=>participant?'<div class="tag28-sidecard"><img class="tag28-side-avatar" src="'+safe(avatarOf(participant,room,parts))+'" alt="" loading="eager">'+
   '<span>المركز '+label+'</span><strong>'+safe(participant.name)+'</strong><b>🏆 '+points(participant.score)+' نقطة</b></div>':'';
  const winner=ranked[0];
  const fullRows=ranked.map(row).join('');
  mount.innerHTML='<div class="stage-wrap tag28-wrap">'+parts.head+
   '<section class="tag28-finale" aria-label="حفل نهائي تحدي TAG">'+
   '<div class="tag28-stadium" aria-hidden="true"></div><div class="tag28-lightbeams" aria-hidden="true"></div><div class="tag28-fireworks" aria-hidden="true"></div><div class="tag28-confetti" aria-hidden="true"></div>'+
   '<div class="tag28-banners" aria-hidden="true"><div class="tag28-banner">★ <b>TAG</b><small>TEACH AND GAME</small></div><div class="tag28-banner">★ <b>TAG</b><small>TEACH AND GAME</small></div></div>'+
   '<header class="tag28-hero"><div class="tag28-finale-kicker">✦ انتهى التحدي ✦ <span>TAG WORLD CLASS FINAL</span></div>'+
   '<div class="tag28-heading"><span aria-hidden="true">❯</span><h1>لحظة التتويج</h1><span aria-hidden="true">❮</span></div>'+
   '<p id="tag28Announcement" class="tag27-announcement" aria-live="polite">استعدوا لصعود الأبطال إلى منصة المجد</p></header>'+
   '<section class="tag28-main-grid">'+
   '<aside class="tag28-side tag28-left" aria-label="المركزان الرابع والخامس">'+
   sideCard(c4,'الرابع')+
   sideCard(c5,'الخامس')+
   '</aside>'+
   '<div class="tag28-arena"><div class="tag28-orbit" aria-hidden="true"></div><div class="tag28-podium">'+podium+'</div><div class="tag28-stage-lip" aria-hidden="true"><span>★ TAG • THE GRAND FINALE ★</span></div></div>'+
   '<aside class="tag28-side tag28-right" aria-label="إحصاءات التحدي">'+
   stat('♟','عدد المشاركين',points(teams?players.length:ranked.length))+
   stat('☑','عدد الأسئلة',points(room.total))+
   stat('🏆','أعلى نتيجة',winner?points(winner.score):'0')+'</aside>'+
   '</section>'+
   '<footer class="tag28-footer">'+
   '<div class="tag28-reveal-progress" aria-label="تسلسل إعلان المراكز"><span>الثالث</span><i></i><span>الثاني</span><i></i><span>الأول</span></div>'+
   '<nav class="tag28-actions" aria-label="التحكم بحفل التتويج">'+
   '<button id="tag28Back" type="button" aria-label="الرجوع إلى الصفحة السابقة">↩ <span>رجوع</span></button>'+
   '<button id="tag28All" type="button">☷ <span>جميع النتائج</span></button>'+
   '<button id="tag27Replay" type="button">↻ <span>إعادة العرض</span></button>'+
   '<button id="tag28Skip" type="button">⏭ <span>تخطي الاحتفال</span></button>'+
   '<button id="tag28Sound" type="button" aria-pressed="false" title="تشغيل المؤثر الصوتي">♪ <span>الصوت</span></button>'+
   '</nav></footer>'+
   '<div id="tag28AllPanel" class="tag28-dialog" role="dialog" aria-modal="true" aria-label="جميع النتائج" hidden><div class="tag28-dialog-card">'+
   '<div class="tag28-dialog-head"><h2>🏅 الترتيب النهائي</h2><button id="tag28Close" type="button" aria-label="إغلاق النتائج">✕</button></div>'+
   '<ol class="tag28-all-list">'+(fullRows||'<li>لم تسجل نتائج بعد</li>')+'</ol></div></div>'+
   '</section></div>';
  const root=mount.querySelector('.tag28-finale');
  const announcer=root.querySelector('#tag28Announcement');
  const originalFocus=document.activeElement;
  const play=()=>{
   stop();const id=tokens.sequence;
   root.querySelectorAll('.tag28-winner').forEach(el=>{el.classList.remove('tag28-visible','tag27-entered','tag28-crowned');el.setAttribute('aria-hidden','true')});
   const marks=root.querySelectorAll('.tag28-reveal-progress span');marks.forEach(el=>el.classList.remove('tag28-active'));
   root.querySelector('.tag28-fireworks')?.replaceChildren();root.querySelector('.tag28-confetti')?.replaceChildren();
   announcer.textContent='استعدوا لصعود الأبطال إلى منصة المجد';
   const places=[3,2,1].filter(p=>root.querySelector('.tag28-place-'+p));
   places.forEach((place,i)=>schedule(()=>{
    if(id!==tokens.sequence||!root.isConnected)return;
    const card=root.querySelector('.tag28-place-'+place);card.classList.add('tag28-visible','tag27-entered');card.setAttribute('aria-hidden','false');
    const name=card.querySelector('.tag27-podium-name')?.textContent||'المشارك';
    announcer.textContent=place===1?'🏆 '+name+'… بطل TAG!':place===2?'🥈 '+name+'… وصيف التحدي!':'🥉 '+name+'… المركز الثالث!';
    marks[2-i]?.classList.add('tag28-active');
    if(place===1){card.classList.add('tag28-crowned');flourish(root);chime()}
   },reduced()?i*30:550+i*2200));
  };
  const skip=()=>{
   stop();root.querySelectorAll('.tag28-winner').forEach(el=>{el.classList.add('tag28-visible','tag27-entered');el.setAttribute('aria-hidden','false')});
   root.querySelectorAll('.tag28-reveal-progress span').forEach(el=>el.classList.add('tag28-active'));
   announcer.textContent=winner?'🏆 '+winner.name+'… بطل TAG!':'شكرًا لجميع المشاركين';
  };
  const panel=root.querySelector('#tag28AllPanel');
  const openPanel=()=>{panel.hidden=false;tokens.open=true;root.querySelector('#tag28Close').focus()};
  const closePanel=()=>{panel.hidden=true;tokens.open=false;root.querySelector('#tag28All').focus()};
  root.querySelector('#tag27Replay').addEventListener('click',play);
  root.querySelector('#tag28Skip').addEventListener('click',skip);
  root.querySelector('#tag28All').addEventListener('click',openPanel);
  root.querySelector('#tag28Close').addEventListener('click',closePanel);
  panel.addEventListener('click',e=>{if(e.target===panel)closePanel()});
  root.addEventListener('keydown',e=>{if(e.key==='Escape'&&tokens.open){e.preventDefault();closePanel()}if(e.key==='Tab'&&tokens.open){const buttons=panel.querySelectorAll('button');if(buttons.length===1){e.preventDefault();buttons[0].focus()}}});
  root.querySelector('#tag28Back').addEventListener('click',()=>{
   // Return to the actual previous page when this projector view was navigated in-place.
   if(window.history.length>1){window.history.back();return}
   // A projector often opens in a new tab (no back entry): use its referring page.
   let previous=null;
   try{previous=document.referrer?new URL(document.referrer):null}catch(_e){}
   const platformHosts=['teachgame.onrender.com','quiznova-arena-online.onrender.com'];
   if(previous&&previous.href!==window.location.href&&
      (previous.origin===window.location.origin||
       (previous.protocol==='https:'&&platformHosts.includes(previous.hostname)))){
    window.location.assign(previous.href);return;
   }
   // Direct URL, bookmark or QR with no previous page: return to the teacher workspace.
   window.location.assign('/studio.html');
  });
  root.querySelector('#tag28Sound').addEventListener('click',e=>{
   const btn=e.currentTarget;
   if(tokens.audio){try{void tokens.audio.close()}catch(_e){}tokens.audio=null;btn.setAttribute('aria-pressed','false');btn.classList.remove('tag28-sound-on');return}
   const API=window.AudioContext||window.webkitAudioContext;
   if(!API){btn.title='هذا المتصفح لا يدعم تشغيل المؤثرات';return}
   try{tokens.audio=new API();btn.setAttribute('aria-pressed','true');btn.classList.add('tag28-sound-on');chime()}catch(_e){tokens.audio=null}
  });
  play();return true;
 }
 // Preserve the V27 question view, top-five live leaderboard, privacy checks and room polling.
 const previous=window.TAGStageCinema||{};
 window.TAGStageCinema={...previous,finale,reset(){stop();try{previous.reset?.()}catch(_e){}}};
 window.TAGStageWorldCup={finale};
})();