/* CHAMPION TAG: RTL, multi-teacher persistent knockout tournaments and live-match host. */
(function(){
"use strict";
const $=id=>document.getElementById(id);
const safe=window.TAGChampionBracket.escape;
const BR=window.TAGChampionBracket;
const VISUAL=window.TAGChampionTheme;
const draftAppearance={theme:'gold',background:'daylight'};
const currentAppearance={theme:'gold',background:'daylight'};
function syncLegacyOption(context,background){
 const grid=$(context+'BackgroundGrid');if(!grid)return;
 const existing=grid.querySelector('[data-ct-legacy="true"]');
 const legacy=!!(VISUAL.backgrounds[background]&&!VISUAL.visibleBackgrounds.includes(background));
 if(!legacy){existing?.remove();return}
 const card=existing||document.createElement('button');
 if(!existing){card.type='button';card.className='ct-background-card ct-legacy-card';card.dataset.ctLegacy='true';card.dataset.ctContext=context;grid.append(card)}
 card.dataset.ctBg=background;
 card.setAttribute('aria-label','خلفية محفوظة من إصدار سابق');
 card.replaceChildren();
 const preview=document.createElement('span');preview.className='ct-background-preview ct-bg-'+background;preview.setAttribute('aria-hidden','true');
 const label=document.createElement('span');label.textContent='محفوظة سابقًا: '+VISUAL.backgrounds[background];
 card.append(preview,label);
}
function updatePreview(context){
 const state=context==='create'?draftAppearance:currentAppearance;
 VISUAL.apply(state.theme,state.background);
 VISUAL.syncButtons($(context+'ThemeGrid'),'data-ct-theme',state.theme);
 VISUAL.syncButtons($(context+'BackgroundGrid'),'data-ct-bg',state.background);
}
function chooseAppearance(context,kind,value){
 const state=context==='create'?draftAppearance:currentAppearance;
 if(kind==='theme'&&VISUAL.themes[value]){
  state.theme=value;
  state.background=VISUAL.themes[value].defaultBackground;
 }else if(kind==='background'&&VISUAL.backgrounds[value]){
  state.background=value;
 }else{return}
 updatePreview(context);
 if(context==='active'){
  const msg=$('championThemeMessage');
  if(msg)msg.textContent='هذه معاينة لم تُحفظ بعد. اضغط «حفظ التصميم» لتحديث بطولة التصفيات وشاشة العرض.';
 }
}
const token=()=>localStorage.getItem('qn9_teacher_token')||'';
const errors={
login_required:'يلزم تسجيل الدخول بحساب المعلم.',tournament_not_found:'لم يُعثر على هذه البطولة في حسابك.',
participants_2_to_32:'أدخل بين مشاركَين و32 مشاركًا.',invalid_participants:'تحقق من الأسماء (55 حرفًا لكل اسم كحد أقصى).',
duplicate_participants:'توجد أسماء مكررة؛ يجب أن يكون لكل مشارك اسم مختلف.',
invalid_tournament_type:'اختر نوع المشاركين وطريقة التصفيات.',quiz_not_found:'الاختبار المحدد غير موجود أو لا يحتوي على أسئلة. احفظ اختبارًا في الاستوديو أولًا.',
invalid_appearance:'التصميم أو الخلفية غير متاحين. اختر أحد الأنماط الرسمية.',quiz_too_large:'الاختبار المختار أكبر من الحجم المسموح.',manual_pairings_required:'حدّد جميع مواجهات الدور الأول.',
invalid_pairings:'يجب توزيع كل مشارك مرة واحدة بالضبط، دون تكرار أو نسيان.',
empty_fixture:'لا يمكن ترك مواجهة فارغة من الطرفين.',tournament_limit:'وصلت إلى الحد الأقصى للبطولات المحفوظة.',
match_not_found:'تعذر العثور على هذه المواجهة.',match_not_ready:'هذه المواجهة ليست جاهزة بعد أو بدأ تشغيلها بالفعل.',
match_not_started:'لم تبدأ هذه المواجهة بعد.',room_not_finished:'لا يمكن اعتماد النتيجة قبل انتهاء الأسئلة وإغلاق الجولة.',
both_teams_required:'يجب انضمام مشارك واحد على الأقل إلى كل طرف قبل بدء التحدي.',
tie_requires_decision:'تعادل الطرفان؛ اختر المتأهل يدويًا لفك التعادل.',
forfeit_not_allowed:'لا يمكن اعتماد انسحاب بعد بدء المواجهة أو انتهائها.',
room_not_found:'انتهت صلاحية هذه الغرفة؛ لا يمكن استعادتها حاليًا.',
not_in_lobby:'لا يمكن نقل الطالب بين الفرق بعد بدء الأسئلة.',
team_missing:'عيّن كل طالب للفريق الذي ينتمي إليه قبل بدء التحدي.',
unauthorized:'ليس لديك صلاحية لتنفيذ هذا الإجراء.'};
const label=e=>errors[e]||('تعذر إكمال العملية: '+String(e||'خطأ في الاتصال'));
let teacher=null,quizzes=[],tournaments=[],active=null,selectedId='',live=null,polling=null,loading=false,tiePending=false,roomViewSig='';
function toast(text,bad=false){
 const t=$('championToast');t.textContent=text;t.style.borderColor=bad?'#f38b9e':'#7cebdd';t.hidden=false;
 clearTimeout(toast.timer);toast.timer=setTimeout(()=>t.hidden=true,4500);
}
async function request(path,method='GET',payload=null,privateRequest=true){
 const headers={};
 if(privateRequest)headers.Authorization='Bearer '+token();
 if(payload!==null)headers['Content-Type']='application/json';
 const r=await fetch(path,{method,headers,body:payload===null?undefined:JSON.stringify(payload),cache:'no-store'});
 let data;try{data=await r.json()}catch{throw new Error('network_error')}
 if(!r.ok||!data.ok){const e=new Error(data.error||'server_error');e.status=r.status;throw e}
 return data;
}
function getEntrants(){return $('championParticipants').value.split(/\r?\n/).map(n=>n.trim()).filter(Boolean)}
function seedSlots(names){
 let size=2;while(size<names.length)size*=2;
 let seeds=[1,2];while(seeds.length<size){const n=2*seeds.length+1;seeds=seeds.flatMap(k=>[k,n-k])}
 return seeds.map(i=>names[i-1]||'');
}
function drawPairs(){
 const manual=$('championSeeding').value==='manual';
 $('manualFixtures').hidden=!manual;
 const names=getEntrants();
 $('entrantsCount').textContent=names.length+' مشارك/مشاركين • '+(manual?'اختر المتنافسين في كل مواجهة؛ يمكن أن يتأهل طرف تلقائيًا.':'سيُجري النظام قرعة عشوائية متوازنة ويمنح بطاقات التأهل التلقائي عند الحاجة.');
 if(!manual)return;
 if(names.length<2||names.length>32){$('manualFixtures').innerHTML='<p class="hint">أدخل أسماء المشاركين أولًا (من 2 إلى 32).</p>';return}
 const seats=seedSlots(names);
 const options=(picked)=>'<option value="">— تأهل تلقائي —</option>'+names.map(n=>'<option value="'+safe(n)+'"'+(n===picked?' selected':'')+'>'+safe(n)+'</option>').join('');
 $('manualFixtures').innerHTML='<h3>تحديد مواجهات الدور الأول</h3><p class="hint">اختر طرفَي كل مواجهة كما تريد. يجب استخدام كل اسم مرة واحدة. اترك الطرف الثاني فارغًا إذا كان متأهلًا تلقائيًا.</p><div class="pair-grid">'+
 Array.from({length:seats.length/2},(_,i)=>'<div class="pair-box"><b>المواجهة '+(i+1)+'</b><select class="pair-slot" aria-label="الطرف الأول للمواجهة '+(i+1)+'">'+options(seats[2*i])+'</select><select class="pair-slot" aria-label="الطرف الثاني للمواجهة '+(i+1)+'">'+options(seats[2*i+1])+'</select></div>').join('')+'</div>';
}
function manualPairs(){
 const selects=[...document.querySelectorAll('#manualFixtures .pair-slot')];
 const pairs=[];for(let i=0;i<selects.length;i+=2)pairs.push([selects[i].value,selects[i+1].value]);
 return pairs;
}
function currentUrl(){return location.origin+'/champion-board.html?id='+encodeURIComponent(active.id)}
function selectTab(tab){
 const screens={create:'createScreen',archive:'archiveScreen',bracket:'bracketScreen'};
 for(const [key,value] of Object.entries(screens)){
  $(value).hidden=key!==tab;
  $('tab'+key.charAt(0).toUpperCase()+key.slice(1)).classList.toggle('active',key===tab);
 }
 if(tab==='bracket'&&!active){toast('أنشئ بطولة أو اختر بطولة محفوظة أولًا.',true);selectTab('archive');return}
 updatePreview(tab==='create'||!active?'create':'active');
}
function renderArchive(){
 $('championArchive').innerHTML=tournaments.length?tournaments.map(t=>
  '<button type="button" class="library-item'+(active?.id===t.id?' active':'')+'" data-tournament="'+safe(t.id)+'">'+
  '<strong>🏆 '+safe(t.title)+'</strong><span class="meta">'+safe(t.kind==='students'?'طلاب':t.kind==='classes'?'شعب':'فرق')+' • '+safe(t.quizTitle)+'</span>'+
  '<span class="badge '+(t.champion?'gold':'')+'">'+(t.champion?'👑 البطل: '+safe(t.champion):'بطولة جارية أو بانتظار الانطلاق')+'</span>'+
  '<span class="meta">'+new Date(t.createdAt*1000).toLocaleDateString('ar-JO')+'</span></button>').join('')
  :'<p class="muted">لا توجد بطولات محفوظة بعد. ابدأ بإنشاء بطولة جديدة.</p>';
}
async function refreshList(){
 const data=await request('/api/champion');tournaments=data.tournaments||[];renderArchive();
}
async function openTournament(id){
 clearInterval(polling);polling=null;live=null;selectedId='';roomViewSig='';tiePending=false;
 const d=await request('/api/champion?id='+encodeURIComponent(id));
 active=d.tournament;
 window.TAGChampionCeremony?.update(active,{autoplay:false});
 currentAppearance.theme=VISUAL.themes[active.theme]?active.theme:'gold';
 currentAppearance.background=VISUAL.backgrounds[active.background]?active.background:VISUAL.themes[currentAppearance.theme].defaultBackground;
 updatePreview('active');
 renderBracket();renderArchive();selectTab('bracket');
 try{localStorage.setItem('tag_champion_last_'+teacher.id,id)}catch{}
 const liveMatch=active.rounds.flatMap(r=>r.matches).find(m=>m.status==='live');
 if(liveMatch)chooseMatch(liveMatch.id);
}
function renderBracket(){
 if(!active)return;
 const allMatches=active.rounds.flatMap(round=>round.matches);
 const firstRound=active.rounds[0]?.matches||[];
 const entrants=firstRound.flatMap(match=>[match.a,match.b]).filter(Boolean).length;
 const finished=allMatches.filter(match=>match.status==='finished'||match.status==='bye').length;
 $('wcParticipants').textContent=String(entrants);
 $('wcFixtures').textContent=String(allMatches.length);
 $('wcProgress').textContent=finished+' / '+allMatches.length;
 $('wcChampion').textContent=active.champion||'بانتظار البطل';
 $('currentTournamentTitle').textContent=active.title;

 const kind=active.kind==='students'?'الطلاب':active.kind==='classes'?'الشعب':'الفرق';
 $('currentTournamentMeta').textContent=kind+' • '+entrants+' مشارك • '+active.quizTitle+(active.champion?' • البطل: '+active.champion:'');
 $('bracketCanvas').innerHTML=BR.render(active,true);
 BR.afterRender($('bracketCanvas'));
 if(selectedId){
  for(const card of $('bracketCanvas').querySelectorAll('[data-match]'))card.classList.toggle('active',card.dataset.match===selectedId);
 }
}
function button(id,title,extra=''){return '<button type="button" class="btn '+extra+'" data-action="'+id+'">'+title+'</button>'}
function chooseMatch(matchId){
 const m=BR.find(active,matchId);if(!m)return;
 if(selectedId!==matchId){clearInterval(polling);polling=null;live=null;roomViewSig='';tiePending=false}
 selectedId=matchId;renderBracket();renderMatchDetails(m);
 if(m.status==='live'){
  void refreshRoom();
  polling=setInterval(()=>void refreshRoom(),1700);
 }
}
function renderMatchDetails(m){
 const note={ready:'المواجهة جاهزة لإنشاء غرفة التحدي.',live:'المواجهة جارية — استخدم لوحة التحكم لمتابعة الطلاب.',finished:'انتهت المواجهة وتأهل الفائز إلى الدور التالي.',bye:'تأهل تلقائي دون مواجهة.',pending:'بانتظار نتائج الدور السابق.'};
 const action=m.status==='ready'
  ?button('launch','▶ إنشاء التحدي المباشر','primary')+'<p class="hint">أسئلة الاختبار المختار ستُعرض على الطلاب عبر رمز الجلسة أو QR.</p>'
  +(active.kind==='students'||active.kind==='classes'||active.kind==='teams'?'<p class="hint">في حال غياب أحد الطرفين يمكن اعتماد انسحابه: </p>'+button('forfeitA','تأهل '+safe(m.a),'')+button('forfeitB','تأهل '+safe(m.b),''):'')
  :m.status==='live'?'<span class="badge">المواجهة مرتبطة بغرفة مباشرة. اضغط على المواجهة للمتابعة.</span>'
  :m.status==='finished'?'<p class="success">👑 الفائز: <strong>'+safe(m.winner)+'</strong></p>'
  :m.status==='bye'?'<p class="success">✓ تأهل تلقائيًا: <strong>'+safe(m.winner)+'</strong></p>':'';
 $('championMatchDetails').innerHTML='<h3>⚔️ '+safe(m.a||'بانتظار المتأهل')+' ضد '+safe(m.b||'بانتظار المتأهل')+'</h3>'+
  '<div class="face-off"><span>'+safe(m.a||'—')+'</span><span class="versus">VS</span><span>'+safe(m.b||'—')+'</span></div>'+
  '<p class="muted">'+safe(note[m.status]||'')+'</p><div class="row-actions">'+action+'</div>';
 if(m.status!=='live'){
  $('championLiveHost').innerHTML='<h3>ساحة التحدي المباشر</h3><p class="muted">'+(m.status==='finished'?'تم احتساب النتيجة وانتقال الفائز في شجرة التصفيات.':'تظهر هنا أسئلة التحدي المباشر ونتائج الطرفين بعد إنشاء الغرفة.')+'</p>';
 }
}
function accessRoom(match){
 const base=location.hostname==='quiznova-arena-online.onrender.com'?'https://teachgame.onrender.com/play/':location.origin+'/student.html';
 return base+'?code='+encodeURIComponent(match.code);
}
function renderRoom(room){
 const m=BR.find(active,selectedId);if(!m||m.status!=='live')return;
 const sig=JSON.stringify([room.status,room.index,room.players,room.teams,room.question,room.stats,room.startedAt,tiePending]);
 if(sig===roomViewSig)return;roomViewSig=sig;
 const statusNames={lobby:'بانتظار دخول المشاركين',question:'السؤال '+(room.index+1)+' من '+room.total,results:'نتائج السؤال '+(room.index+1),finished:'انتهت المواجهة'};
 const teams=(room.teams||[]);const getScore=name=>teams.find(z=>z.name===name)||{score:0,correct:0,members:0};
 const scoreMarkup=[m.a,m.b].map(name=>{
  const s=getScore(name);return '<div class="score-team"><strong>'+safe(name)+'</strong><div class="points">'+(s.members?(s.score/s.members).toFixed(1):'0.0')+'</div><small>متوسط النقاط • '+s.members+' مشارك • '+s.correct+' إجابة صحيحة</small></div>';
 }).join('');
 const roster=(room.players||[]).map(p=>{
  const edit=room.status==='lobby'&&active.kind!=='students';
  const teamSelect=edit?'<select aria-label="فريق '+safe(p.name)+'" data-member="'+safe(p.id)+'"><option value="">— اختر الطرف —</option>'+[m.a,m.b].map(name=>'<option value="'+safe(name)+'"'+(name===p.team?' selected':'')+'>'+safe(name)+'</option>').join('')+'</select>':'<span class="hint">'+safe(p.team||'لم يُحدّد الفريق')+' • '+p.score+' نقطة</span>';
  return '<div class="member"><strong>👤 '+safe(p.name)+'</strong>'+teamSelect+'</div>';
 }).join('')||'<p class="muted">بانتظار انضمام أول مشارك...</p>';
 const control=room.status==='lobby'?button('start','▶ ابدأ أول سؤال','primary')
 :room.status==='question'?button('reveal','◉ إظهار الإجابة والنتائج')+button('skip','⏭ تخطي السؤال')
 :room.status==='results'?button('next','⏭ السؤال التالي','primary'):'';
 const finish=room.status==='lobby'||room.status==='question'||room.status==='results'?button('end','⏹ إنهاء المواجهة','danger'):'';
 const qrURL='/api/qr?format=png&text='+encodeURIComponent(accessRoom(m));
 const stageURL='/stage.html?code='+encodeURIComponent(m.code)+'&stage='+encodeURIComponent(m.stageToken);
 const question=room.question?.text||room.question_text||'بانتظار بدء الأسئلة';
 const kpi=room.stats||{};
 $('championLiveHost').innerHTML=
  '<div class="bracket-head"><div><h3>🎮 غرفة المواجهة</h3><span class="badge">'+safe(statusNames[room.status]||room.status)+'</span></div><span class="clock">رمز الجلسة</span></div>'+
  '<div class="join-grid"><img class="qr" src="'+qrURL+'" alt="QR انضمام الطلاب للمواجهة"><div><div class="room-code">'+safe(m.code)+'</div><p class="hint">امسح QR أو أدخل الرمز من بوابة الطالب</p>'+
  '<div class="row-actions">'+button('copyJoin','نسخ رابط الانضمام')+
  '<a class="btn" target="_blank" rel="noopener" href="'+stageURL+'">📺 شاشة عرض اللعبة</a></div></div></div>'+
  '<div class="scoreboard">'+scoreMarkup+'</div>'+
  '<div class="row-actions">'+(room.status==='finished'?'<span class="badge gold">جاري اعتماد النتيجة...</span>':control+finish)+'</div>'+
  '<div class="panel" style="margin:15px 0"><div class="eyebrow">LIVE QUESTION</div><p class="q-line"><b>'+safe(question)+'</b></p>'+
  '<span class="badge">أجاب '+(kpi.answered||0)+' من '+(room.players||[]).length+'</span> '+
  '<span class="badge">صحيحة: '+(kpi.correct||0)+'</span></div>'+
  '<h3>المشاركون في هذه المواجهة</h3><div class="live-roster">'+roster+'</div>'+
  (active.kind==='students'?'<p class="hint">يدخل الطالب باسمه المسجل في البطولة ويُسند تلقائيًا إلى طرفه.</p>':'<p class="hint">عيّن الطلاب إلى الشعب/الفرق قبل بدء الجولة. عند استخدام بطاقة الطالب تُحدَّد الشعبة تلقائيًا إن طابقت الاسم.</p>');
}
async function refreshRoom(){
 if(loading||!active||!selectedId)return;
 const m=BR.find(active,selectedId);if(!m||m.status!=='live')return;
 loading=true;
 try{
  const d=await request('/api/room/state?code='+encodeURIComponent(m.code)+'&host='+encodeURIComponent(m.hostToken),'GET',null,false);
  live=d.room;renderRoom(live);
  if(live.status==='finished'&&!tiePending){
   await settleMatch();
  }
 }catch(e){
  if(String(e.message)==='room_not_found'){
   clearInterval(polling);polling=null;
   $('championLiveHost').insertAdjacentHTML('beforeend','<p class="error">تعذّر استعادة غرفة هذه المباراة. سجلات التصفيات محفوظة؛ راجع الدعم الفني قبل إعادة مواجهتها.</p>');
  }else{console.warn('CHAMPION TAG polling:',e)}
 }finally{loading=false}
}
async function settleMatch(tieWinner=''){
 if(!active||!selectedId)return;
 const matchId=selectedId,tournamentId=active.id;
 try{
  const d=await request('/api/champion/match/complete','POST',{tournamentId,matchId,tieWinner});
  clearInterval(polling);polling=null;roomViewSig='';tiePending=false;
  active=d.tournament;await refreshList();renderBracket();
  window.TAGChampionCeremony?.update(active,{autoplay:true});
  const m=BR.find(active,matchId);renderMatchDetails(m);toast('تم اعتماد النتيجة وتأهل '+m.winner+' إلى الدور التالي');
  if(active.champion)toast('🏆 بطل البطولة: '+active.champion);
 }catch(e){
  if(e.message==='tie_requires_decision'){
   tiePending=true;showTie();
  }else{
   toast(label(e.message),true);
  }
 }
}
function showTie(){
 const m=BR.find(active,selectedId);if(!m)return;
 $('championLiveHost').insertAdjacentHTML('beforeend','<div class="panel" style="margin-top:15px"><h3>⚖️ تعادل الطرفين</h3><p>تساوى متوسط النقاط والإجابات الصحيحة. اختر المتأهل وفق قاعدة كسر التعادل التي تعلنها للطلاب.</p><div class="row-actions">'+button('tieA','تأهيل '+safe(m.a),'gold')+button('tieB','تأهيل '+safe(m.b),'gold')+'</div></div>');
}
async function launchMatch(){
 const match=BR.find(active,selectedId);if(!match||match.status!=='ready')return;
 $('championLiveHost').innerHTML='<h3>جارٍ إنشاء غرفة التحدي...</h3>';
 try{
  const d=await request('/api/champion/match/start','POST',{tournamentId:active.id,matchId:match.id,background:'cine-arena'});
  const latest=await request('/api/champion?id='+encodeURIComponent(active.id));active=latest.tournament;
  roomViewSig='';renderBracket();renderMatchDetails(BR.find(active,selectedId));toast('تم إنشاء غرفة التحدي برمز '+d.code);
  void refreshRoom();polling=setInterval(()=>void refreshRoom(),1700);
 }catch(e){toast(label(e.message),true);renderMatchDetails(match)}
}
async function performControl(action){
 const m=BR.find(active,selectedId);if(!m||!m.code)return;
 if(action==='end'&&!confirm('إنهاء المواجهة الآن واحتساب نتائجها الحالية؟'))return;
 try{
  await request('/api/room/control','POST',{code:m.code,hostToken:m.hostToken,action});
  roomViewSig='';void refreshRoom();
 }catch(e){toast(label(e.message),true)}
}
async function assignMember(playerId,team){
 if(!team)return;
 const m=BR.find(active,selectedId);if(!m||!m.code)return;
 try{await request('/api/room/team','POST',{code:m.code,hostToken:m.hostToken,playerId,team});roomViewSig='';void refreshRoom()}
 catch(e){toast(label(e.message),true)}
}
async function forfeit(which){
 const m=BR.find(active,selectedId);if(!m||m.status!=='ready')return;
 const winner=which==='forfeitA'?m.a:m.b;
 if(!confirm('هل تؤكد انسحاب الطرف المقابل وتأهل «'+winner+'» دون لعب؟'))return;
 try{
  const d=await request('/api/champion/match/forfeit','POST',{tournamentId:active.id,matchId:selectedId,winner});
  active=d.tournament;await refreshList();renderBracket();renderMatchDetails(BR.find(active,selectedId));
  window.TAGChampionCeremony?.update(active,{autoplay:true});toast('تم التأهل دون لعب');
 }catch(e){toast(label(e.message),true)}
}
async function saveAppearance(){
 if(!active){toast('اختر بطولة أولًا.',true);return}
 const button=$('saveChampionAppearance');
 button.disabled=true;
 try{
  const d=await request('/api/champion/appearance','POST',{
   tournamentId:active.id,theme:currentAppearance.theme,background:currentAppearance.background
  });
  active=d.tournament;
  await refreshList();
  renderBracket();
  const msg=$('championThemeMessage');
  if(msg)msg.textContent='✓ تم حفظ النمط والخلفية لهذه البطولة. شاشة العرض تستخدم الاختيار المحفوظ.';
  toast('✓ تم حفظ تصميم البطولة وخلفيتها بنجاح');
 }catch(e){toast(label(e.message),true)}
 finally{button.disabled=false}
}
function bind(){
 for(const tab of ['Create','Archive','Bracket'])$('tab'+tab).addEventListener('click',()=>selectTab(tab.toLowerCase()));
 for(const btn of document.querySelectorAll('[data-champion-jump]')){
  btn.addEventListener('click',()=>{
   const target=btn.dataset.championJump;
   selectTab(target);
   document.querySelector('.wc-tabbar')?.scrollIntoView({block:'start',behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
  });
 }
 for(const context of ['create','active']){
  const prefix=context;
  $(prefix+'ThemeGrid').addEventListener('click',ev=>{
   const button=ev.target.closest('[data-ct-theme]');
   if(button)chooseAppearance(context,'theme',button.dataset.ctTheme);
  });
  $(prefix+'BackgroundGrid').addEventListener('click',ev=>{
   const button=ev.target.closest('[data-ct-bg]');
   if(button)chooseAppearance(context,'background',button.dataset.ctBg);
  });
 }
 $('saveChampionAppearance').addEventListener('click',()=>void saveAppearance());
 $('championParticipants').addEventListener('input',drawPairs);
 $('championSeeding').addEventListener('change',drawPairs);
 $('championCreateForm').addEventListener('submit',async ev=>{
  ev.preventDefault();$('championCreateError').hidden=true;
  const names=getEntrants();if(names.length<2||names.length>32){toast(errors.participants_2_to_32,true);return}
  const payload={title:$('championTitle').value.trim(),kind:$('championKind').value,
    seedMode:$('championSeeding').value,participants:names,quizId:$('championQuiz').value,
    theme:draftAppearance.theme,background:draftAppearance.background};
  if(payload.seedMode==='manual')payload.manualPairs=manualPairs();
  $('createTournamentButton').disabled=true;
  try{
   const d=await request('/api/champion','POST',payload);
   await refreshList();await openTournament(d.tournament.id);toast('تم إنشاء البطولة وحفظ جدول التصفيات بنجاح');
  }catch(e){$('championCreateError').hidden=false;$('championCreateError').textContent=label(e.message)}
  finally{$('createTournamentButton').disabled=false}
 });
 $('championArchive').addEventListener('click',ev=>{
  const b=ev.target.closest('[data-tournament]');if(b)void openTournament(b.dataset.tournament).catch(e=>toast(label(e.message),true));
 });
 $('bracketCanvas').addEventListener('click',ev=>{const e=ev.target.closest('[data-match]');if(e)chooseMatch(e.dataset.match)});
 $('bracketCanvas').addEventListener('keydown',ev=>{const e=ev.target.closest('[data-match]');if(e&&(ev.key==='Enter'||ev.key===' ')){ev.preventDefault();chooseMatch(e.dataset.match)}});
 $('championMatchDetails').addEventListener('click',ev=>{
  const b=ev.target.closest('[data-action]');if(!b)return;
  if(b.dataset.action==='launch')void launchMatch();
  if(b.dataset.action==='forfeitA'||b.dataset.action==='forfeitB')void forfeit(b.dataset.action);
 });
 $('championLiveHost').addEventListener('change',ev=>{const sel=ev.target.closest('[data-member]');if(sel)void assignMember(sel.dataset.member,sel.value)});
 $('championLiveHost').addEventListener('click',ev=>{
  const b=ev.target.closest('[data-action]');if(!b)return;const action=b.dataset.action;
  if(['start','next','reveal','skip','end'].includes(action))void performControl(action);
  if(action==='copyJoin'){const m=BR.find(active,selectedId);if(m)void navigator.clipboard.writeText(accessRoom(m)).then(()=>toast('تم نسخ رابط انضمام الطلاب')).catch(()=>toast('تعذر النسخ، استخدم رمز QR'))}
  if(action==='tieA'||action==='tieB'){const m=BR.find(active,selectedId);if(m)void settleMatch(action==='tieA'?m.a:m.b)}
 });
 $('openPublicBoard').addEventListener('click',()=>{if(active)window.open(currentUrl(),'_blank','noopener')});
 $('copyPublicBoard').addEventListener('click',()=>{if(active)void navigator.clipboard.writeText(currentUrl()).then(()=>toast('تم نسخ رابط لوحة التصفيات')).catch(()=>toast('تعذر نسخ الرابط',true))});
 $('refreshTournaments').addEventListener('click',()=>void refreshList().then(()=>toast('تم تحديث البطولات')).catch(e=>toast(label(e.message),true)));
 window.addEventListener('pagehide',()=>clearInterval(polling));
}
async function init(){
 bind();drawPairs();updatePreview('create');
 if(!token()){location.replace('/?next='+encodeURIComponent('/champion.html'));return}
 try{
  const [auth,snapshot,champions]=await Promise.all([request('/api/auth/me'),request('/api/teacher/snapshot'),request('/api/champion')]);
  teacher=auth.teacher;quizzes=Array.isArray(snapshot.data?.quizzes)?snapshot.data.quizzes.filter(q=>q?.id&&Array.isArray(q.questions)&&q.questions.length):[];
  $('championQuiz').innerHTML=quizzes.length?quizzes.map(q=>'<option value="'+safe(q.id)+'">'+safe(q.title||'اختبار دون عنوان')+' — '+q.questions.length+' سؤال</option>').join(''):'<option value="">لا توجد اختبارات محفوظة؛ أنشئ اختبارًا في الاستوديو</option>';
  tournaments=champions.tournaments||[];
  $('championLoading').hidden=true;$('championApp').hidden=false;
  renderArchive();selectTab('create');
  let last='';try{last=localStorage.getItem('tag_champion_last_'+teacher.id)||''}catch{}
  if(last&&tournaments.some(t=>t.id===last))await openTournament(last);
  else if(!quizzes.length)toast('أنشئ اختبارًا واحفظه في استوديو TAG قبل بدء البطولة.');
 }catch(e){
  if(e.status===401){location.replace('/?next='+encodeURIComponent('/champion.html'));return}
  $('championLoading').innerHTML='<h2>تعذر تحميل البطولات</h2><p>'+safe(label(e.message))+'</p><button class="btn primary" onclick="location.reload()">إعادة المحاولة</button>';
 }
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>void init());else void init();
})();
