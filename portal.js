(()=>{'use strict';
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const TOKEN_KEY='qn9_teacher_token';let teacher=null,mode='login',cache={dashboard:null,students:[],sessions:[]};
const esc=x=>String(x??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const token=()=>localStorage.getItem(TOKEN_KEY)||'';
function pendingStudioDestination(){
  const raw=new URLSearchParams(location.search).get('next');
  if(!raw)return '';
  try{
    const url=new URL(raw,location.origin);
    const allowed=['dashboard','generator','gamelab','builder','bank','media','library','live','play','results','settings'];
    const target=url.hash.slice(1);
    return url.origin===location.origin&&url.pathname==='/studio.html'&&allowed.includes(target)
      ?'/studio.html#'+target:'';
  }catch{return ''}
}
function resumeStudioAfterLogin(){
  const target=pendingStudioDestination();
  if(target){location.replace(target);return true}
  return false;
}
const notify=msg=>{const e=$('#notification');e.textContent=msg;e.classList.remove('hidden');clearTimeout(e._t);e._t=setTimeout(()=>e.classList.add('hidden'),3200)};
async function api(path,options={}){const headers={'Authorization':'Bearer '+token(),...(options.body?{'Content-Type':'application/json'}:{}),...(options.headers||{})};let r=await fetch(path,{...options,headers,cache:'no-store'});let d=await r.json();if(!r.ok||!d.ok)throw Error(d.error||'network');return d}
function err(e){const map={email_taken:'هذا البريد مستخدم سابقًا',invalid_email:'تأكد من البريد الإلكتروني',weak_password:'استخدم كلمة مرور لا تقل عن 10 أحرف',wrong_credentials:'البريد أو كلمة المرور غير صحيحة',login_required:'انتهت الجلسة، سجّل الدخول مجددًا',server_error:'خطأ في الخادم',too_many_students:'العدد كبير جدًا'};return map[e.message]||'تعذر إكمال العملية: '+e.message}
function toggleAuth(){mode=mode==='login'?'register':'login';$('#signupFields').classList.toggle('hidden',mode==='login');$('#authTitle').textContent=mode==='login'?'دخول المعلمين':'إنشاء حساب معلم';$('#authIntro').textContent=mode==='login'?'سجّل دخولك للوصول إلى لوحة القيادة الخاصة بك.':'حساب مستقل مع المادة والطلاب والاختبارات الخاصة بك.';$('#authSubmit').textContent=mode==='login'?'دخول إلى لوحة القيادة':'إنشاء الحساب والدخول';$('#authToggle').textContent=mode==='login'?'ليس لديك حساب؟ أنشئ حساب معلم جديد':'لديك حساب بالفعل؟ تسجيل الدخول';$('#authError').classList.add('hidden');}
$('#authToggle').onclick=toggleAuth;
$('#authForm').onsubmit=async ev=>{ev.preventDefault();$('#authError').classList.add('hidden');const btn=$('#authSubmit');btn.disabled=true;try{let d=await api('/api/auth/'+(mode==='login'?'login':'register'),{method:'POST',body:JSON.stringify({email:$('#email').value,password:$('#password').value,name:$('#fullName').value,school:$('#school').value,subject:$('#subject').value||'عام',schoolType:$('#schoolType').value})});localStorage.setItem(TOKEN_KEY,d.token);teacher=d.teacher;if(resumeStudioAfterLogin())return;showWorkspace();await loadAll()}catch(e){$('#authError').textContent=err(e);$('#authError').classList.remove('hidden')}finally{btn.disabled=false}}
function showTeacherAuth(){
  $('#studentWelcome').classList.add('hidden');
  $('#authWall').classList.remove('hidden');
  $('#workspace').classList.add('hidden');
}
function showStudentWelcome(){
  $('#studentWelcome').classList.remove('hidden');
  $('#authWall').classList.add('hidden');
  $('#workspace').classList.add('hidden');
}
function teacherEntryRequested(){
  const params=new URLSearchParams(location.search);
  return params.get('teacher')==='1'||!!params.get('next');
}
async function boot(){
  // The public domain always opens the student's gateway, even if this browser
  // previously had a teacher session. Teachers enter intentionally via ?teacher=1.
  if(!teacherEntryRequested()){showStudentWelcome();return}
  if(!token()){showTeacherAuth();return}
  let profile=null;
  // Transient 401s can happen during a deployment; do not clear the token on one bad reply.
  for(let attempt=0;attempt<3;attempt++){
    try{profile=await api('/api/auth/me');break}
    catch(e){if(attempt===2)break;await new Promise(resolve=>setTimeout(resolve,350*(attempt+1)))}
  }
  if(!profile){
    localStorage.removeItem(TOKEN_KEY);
    if(teacherEntryRequested())showTeacherAuth();else showStudentWelcome();
    notify('تحتاج إلى تسجيل الدخول مجددًا.');
    return;
  }
  teacher=profile.teacher;
  if(resumeStudioAfterLogin())return;
  showWorkspace();
  try{await loadAll()}catch(e){notify('تعذر تحديث بيانات لوحة القيادة مؤقتًا. جرّب زر التحديث.')}
}
function showWorkspace(){$('#studentWelcome').classList.add('hidden');$('#authWall').classList.add('hidden');$('#workspace').classList.remove('hidden');$('#teacherSideName').textContent=teacher.name;$('#teacherSubject').textContent=teacher.subject;$('#schoolFoot').textContent=teacher.school;$('#schoolModeEditor').value=teacher.school_type||'mixed';renderAvatarChoices();$('#welcome').textContent='أهلًا '+teacher.name+'، المادة: '+teacher.subject+' • '+teacher.school}
$('#downloadBackup').onclick=async()=>{try{const data=await api('/api/teacher/backup');const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='TeachGame_Backup_'+new Date().toISOString().slice(0,10)+'.json';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);notify('تم تنزيل نسخة البيانات. احتفظ بها في مكان آمن.')}catch(e){notify(err(e))}};
$('#logout').onclick=async()=>{try{await api('/api/auth/logout',{method:'POST',body:'{}'})}catch(e){}localStorage.removeItem(TOKEN_KEY);location.reload()};
const panels={school:['إعدادات المدرسة','إدارة صور الطلاب حسب نوع المدرسة'],home:['لوحة القيادة','نظرة شاملة على فصولك وتقدم طلابك'],classes:['حرب الشعب','منافسات مميزة بين شعب المادة'],mastery:['إتقان المهارات','تابع نتاجات التعلم بالتفصيل'],students:['الطلاب والبطاقات','إدارة الهويات الرقمية وصور الشخصيات'],history:['سجل الاختبارات','نتائج محفوظة تحت حسابك']};
function go(name){$$('.panel-view').forEach(e=>e.classList.toggle('active',e.id==='panel-'+name));$$('button.nav').forEach(e=>e.classList.toggle('active',e.dataset.panel===name));$('#pageTitle').textContent=panels[name][0];$('#pageDesc').textContent=panels[name][1];window.scrollTo({top:0,behavior:'smooth'})}$$('button.nav').forEach(b=>b.onclick=()=>go(b.dataset.panel));$$('[data-jump]').forEach(b=>b.onclick=()=>go(b.dataset.jump));$('#refresh').onclick=()=>loadAll().then(()=>notify('تم تحديث البيانات')).catch(e=>notify(err(e)));
function rateRow(c,i){let score=Number(c.rating||0);return `<div class="rank-row"><div><b>${i+1===1?'🥇':i+1===2?'🥈':i+1===3?'🥉':'◈'} ${esc(c.section)}</b><small>${esc(c.subject)} • ${c.sessions} جلسات • ${c.participants} مشارك</small></div><div class="progress"><i style="width:${score}%"></i></div><div class="score-badge">${score.toFixed(1)}/100</div></div>`}
function skillRow(s){let score=Number(s.rate||0);return `<div class="skill-row"><div><b>${esc(s.skill)}</b><small>${esc(s.section)} • ${esc(s.subject)} • ${s.total} إجابة ${s.needsReview?'• يحتاج دعم':'• متقن'}</small></div><div class="progress"><i style="width:${score}%;background:${s.needsReview?'linear-gradient(90deg,#ff7445,#ffca7d)':'linear-gradient(90deg,#0fb3ff,#59ffec)'}"></i></div><strong class="${s.needsReview?'need':''}">${score}%</strong></div>`}
function sessionRow(s){let date=new Date(s.played_at*1000).toLocaleString('ar-JO');return `<div class="history-row"><div><b>🎮 ${esc(s.quiz_title)}</b><small>${esc(s.section||'شعبة غير محددة')} • ${esc(s.subject)} • ${date}</small></div><span class="overline">${esc(s.game_mode)}</span></div>`}
function renderHome(){let d=cache.dashboard||{};$('#metSessions').textContent=d.sessions||0;$('#metStudents').textContent=d.students||0;$('#metAverage').textContent=(d.average||0)+'%';$('#metAttempts').textContent=d.attempts||0;$('#homeClasses').innerHTML=(d.classes||[]).slice(0,4).map(rateRow).join('')||'<div class="empty">لا توجد منافسات بعد.</div>';$('#homeMastery').innerHTML=(d.support||[]).filter(s=>s.needsReview).slice(0,5).map(skillRow).join('')||'<div class="empty">لا توجد مهارات تحتاج دعمًا بعد.</div>';$('#homeHistory').innerHTML=(d.recent||[]).slice(0,5).map(sessionRow).join('')||'<div class="empty">لا توجد جلسات محفوظة بعد.</div>';$('#classesBoard').innerHTML=(d.classes||[]).map(rateRow).join('')||'<div class="empty">الترتيب سيظهر بعد إنهاء جلسات شعب مختلفة.</div>';$('#masteryBoard').innerHTML=(d.mastery||[]).sort((a,b)=>a.rate-b.rate).map(skillRow).join('')||'<div class="empty">أنهِ مسابقة ذات أسئلة مصنفة حسب المهارات.</div>';$('#storageStatus').textContent=d.dbKind==='postgres'?'◉ قاعدة بيانات سحابية':'◉ تخزين محلي (ليس دائمًا على Render)';}
const booyahMascotNames={m01:'شرارة',m02:'روبوك',m03:'فوكسو',m04:'نينزو',m05:'درعو',m06:'بيكسو',m07:'زومي',m08:'زومي'};
function avatarDisplayName(id){
  if(window.booyahAvatarLabel)return window.booyahAvatarLabel(id);
  if(booyahMascotNames[id])return booyahMascotNames[id];
  if(/^n0[1-8]$/.test(id))return ['التراث الأردني','الشرطة','الهندسة','الطيران','كرة القدم','الكلية العسكرية','النينجا الأصلي','البطل التقني'][Number(id.slice(1))-1];
  return id.startsWith('b')?'بطل اللعبة':id.startsWith('g')?'بطلة اللعبة':'شخصية اللعبة';
}
function avatarPath(id){
  if(/^m0[1-8]$/.test(id))return '/assets/avatars-game/'+(id==='m08'?'m07':id)+'.svg';
  if(/^n0[1-8]$/.test(id)||/^[bg](0[1-9]|1[0-6])$/.test(id))return '/assets/avatars3d/'+id+'.webp';
  return '/assets/avatars/'+(/^\d{2}$/.test(id)?id:'01')+'.svg';
}
function avatarIds(){
  const kind=teacher?.school_type||'mixed';
  const gameAvatars=Array.from({length:7},(_,i)=>'m'+String(i+1).padStart(2,'0'));
  const jordanian=Array.from({length:8},(_,i)=>'n'+String(i+1).padStart(2,'0'));
  const classic=[...Array(16)].flatMap((_,i)=>['b','g'].filter(c=>kind==='mixed'||c===(kind==='boys'?'b':'g')).map(c=>c+String(i+1).padStart(2,'0')));
  return (kind==='girls'?[]:[...gameAvatars,...jordanian]).concat(classic);
}
function renderAvatarChoices(){
  const ids=avatarIds(),select=$('#newStudentAvatar'),current=select.value;
  select.innerHTML=ids.map(id=>`<option value="${id}">${esc(avatarDisplayName(id))}</option>`).join('');
  if(ids.includes(current))select.value=current;
  $('#schoolAvatarGallery').innerHTML=ids.map(id=>`<figure class="bo-mascot-option"><img loading="lazy" src="${avatarPath(id)}" alt="${esc(avatarDisplayName(id))}"><figcaption>${esc(avatarDisplayName(id))}</figcaption></figure>`).join('');
  updateAvatarPreview();
}
function updateAvatarPreview(){const p=$('#studentAvatarPreview');if(p)p.src=avatarPath($('#newStudentAvatar').value)}
$('#newStudentAvatar').addEventListener('change',updateAvatarPreview);
$('#saveSchoolMode').onclick=async()=>{try{const res=await api('/api/teacher/school-type',{method:'POST',body:JSON.stringify({schoolType:$('#schoolModeEditor').value})});teacher.school_type=res.schoolType;renderAvatarChoices();notify('تم حفظ نوع المدرسة. سيتم تطبيقه في الغرف الجديدة.')}catch(e){notify(err(e))}};
function renderStudents(){
  const list=cache.students;
  $('#studentCount').textContent=list.length;
  const base=location.origin+'/student.html?card=';
  const folders=[...new Set(list.map(s=>s.className||'شعبة غير محددة'))].sort((a,b)=>a.localeCompare(b,'ar'));
  $('#studentsBoard').innerHTML=folders.map((cls,i)=>{
  const group=list.filter(s=>(s.className||'شعبة غير محددة')===cls).map(student=>{
    const link=base+encodeURIComponent(student.card);
    const qr='/api/qr?text='+encodeURIComponent(link);
    const percent=Math.max(0,Math.min(100,Number(student.progress?.percent)||0));
    const level=Math.max(1,Number(student.level)||1);
    const xp=Math.max(0,Number(student.xp)||0);
    const name=esc(student.name);
    const className=esc(student.className);
    const cardCode=esc(student.cardCode||'—');
    const characterName=esc(avatarDisplayName(student.avatar));
    return `<article class="idcard bo-student-id" dir="rtl" aria-label="بطاقة الطالب ${name}">
      <header class="bo-badge-header">
        <span class="bo-badge-icon" aria-hidden="true">🎮</span>
        <div class="bo-badge-brand"><strong>TeachGame</strong><small>تيتش جيم · بطاقة الطالب الذكية</small></div>
        <span class="bo-badge-edition" title="بطاقة TeachGame الجديدة" data-card-version="BADJ-TH42">TG 2026</span>
      </header>
      <div class="bo-badge-content">
        <div class="bo-badge-avatar"><img class="avatar-pic" loading="lazy" src="${avatarPath(student.avatar)}" alt="شخصية ${characterName}"><span>${characterName}</span></div>
        <div class="bo-badge-identity">
          <span class="bo-badge-field-label">اسم الطالب</span>
          <strong class="bo-badge-student-name">${name}</strong>
          <div class="bo-badge-class"><span>الصف / الشعبة</span><b>${className}</b></div>
          <div class="bo-badge-code"><span>رمز الدخول</span><b class="bo-badge-access-id" dir="ltr">${cardCode}</b></div>
        </div>
      </div>
      <div class="bo-badge-bottom">
        <div class="bo-badge-progress">
          <div class="bo-badge-level"><span>⭐ المستوى ${level}</span><b>${esc(student.progress?.title||'مبتدئ')}</b></div>
          <div class="bo-badge-xp"><strong>${xp.toLocaleString('en-US')} XP</strong><small>تبقى ${Number(student.progress?.xpToNext)||0} XP للمستوى التالي</small></div>
          <div class="bo-badge-meter" role="progressbar" aria-valuenow="${percent}" aria-valuemin="0" aria-valuemax="100"><span style="width:${percent}%"></span></div>
        </div>
        <div class="bo-badge-qr"><img class="qr" src="${qr}" loading="lazy" alt="رمز QR لبطاقة ${name}"><small>امسح للانضمام</small></div>
      </div>
    <div class="bo-card-actions bo-no-print"><button type="button" data-edit-student="${esc(student.id)}">✏️ تعديل البطاقة</button><button type="button" class="bo-card-danger" data-remove-student="${esc(student.id)}">🗑 حذف البطاقة</button></div>
    </article>`;
  }).join('');
  return `<details class="bo-class-folder" open data-class-folder="${esc(cls)}"><summary>📁 ${esc(cls)} <span>${list.filter(s=>s.className===cls).length} بطاقات</span></summary><div class="bo-folder-toolbar bo-no-print"><button type="button" data-print-class="${esc(cls)}">🖨 طباعة بطاقات هذه الشعبة فقط</button></div><div class="bo-folder-cards">${group}</div></details>`;
  }).join('')||'<div class="empty">ابدأ بإضافة الطلاب لتوليد بطاقاتهم.</div>';
}

function editCardModal(student){
 let box=$('#boCardEditor');
 if(!box){box=document.createElement('div');box.id='boCardEditor';box.className='bo-card-dialog';document.body.appendChild(box)}
 const ids=avatarIds();
 box.innerHTML='<div class="bo-card-shade" data-close-card></div><section class="bo-card-dialog-box" role="dialog" aria-modal="true" aria-label="تعديل بطاقة الطالب">'
  +'<div class="bo-card-dialog-head"><h2>✏️ تعديل بطاقة الطالب</h2><button type="button" data-close-card aria-label="إغلاق">✕</button></div>'
  +'<form id="boCardEditForm"><label>اسم الطالب<input name="name" required maxlength="90" value="'+esc(student.name)+'"></label>'
  +'<label>الصف والشعبة<input name="className" required maxlength="65" value="'+esc(student.className)+'"></label>'
  +'<label>الشخصية / الصورة<select name="avatar">'+ids.map(id=>'<option value="'+esc(id)+'"'+(id===student.avatar?' selected':'')+'>'+esc(avatarDisplayName(id))+'</option>').join('')+'</select></label>'
  +'<div class="bo-avatar-dialog-preview"><img id="boEditAvatarImage" src="'+avatarPath(student.avatar)+'" alt="معاينة الشخصية"><span>رمز QR ورقم البطاقة سيبقيان كما هما</span></div>'
  +'<div class="bo-card-dialog-actions"><button type="button" data-close-card>إلغاء</button><button type="submit" class="primary" id="boCardSave">حفظ التعديل</button></div></form></section>';
 box.classList.add('open');
 box.querySelectorAll('[data-close-card]').forEach(b=>b.onclick=()=>box.classList.remove('open'));
 box.querySelector('select[name=avatar]').onchange=e=>$('#boEditAvatarImage').src=avatarPath(e.target.value);
 $('#boCardEditForm').onsubmit=async e=>{
  e.preventDefault();const form=new FormData(e.target),btn=$('#boCardSave');btn.disabled=true;
  try{
   await api('/api/teacher/students/edit',{method:'POST',body:JSON.stringify({
    id:student.id,name:form.get('name'),className:form.get('className'),avatar:form.get('avatar')})});
   box.classList.remove('open');await loadAll();notify('تم تعديل البطاقة دون تغيير رمز QR');
  }catch(ex){notify(err(ex))}finally{btn.disabled=false}
 };
}
$('#studentsBoard').addEventListener('click',async e=>{
 const edit=e.target.closest('[data-edit-student]');
 if(edit){
  const s=cache.students.find(x=>x.id===edit.dataset.editStudent);
  if(s)editCardModal(s);return;
 }
 const remove=e.target.closest('[data-remove-student]');
 if(remove){
  const s=cache.students.find(x=>x.id===remove.dataset.removeStudent);
  if(!s||!confirm('حذف بطاقة '+s.name+'؟ سيتوقف رمز QR ورمز الدخول عن العمل، وستبقى النتائج السابقة محفوظة.'))return;
  try{
   await api('/api/teacher/students/delete',{method:'POST',body:JSON.stringify({id:s.id,confirm:true})});
   await loadAll();notify('تم إلغاء البطاقة مع الاحتفاظ بالنتائج السابقة');
  }catch(ex){notify(err(ex))}return;
 }
 const print=e.target.closest('[data-print-class]');
 if(print){
  const folder=print.closest('.bo-class-folder');if(!folder)return;
  const all=$$('#studentsBoard .bo-class-folder');
  all.forEach(f=>f.classList.toggle('bo-print-other',f!==folder));
  folder.open=true;
  await $('#printCards').click();
  // A print-dialog can be asynchronous. Keep only this group targeted until after printing.
  setTimeout(()=>all.forEach(f=>f.classList.remove('bo-print-other')),1400);
 }
});

function renderHistory(){const sessions=cache.sessions;$('#historyBoard').innerHTML=sessions.map(s=>`<div class="history-row"><div><b>📘 ${esc(s.quiz_title)}</b><small>${esc(s.section)} • ${new Date(s.played_at*1000).toLocaleDateString('ar-JO')} • ${s.report.length} مشارك</small></div><b>${s.report.length?Math.round(s.report.reduce((a,r)=>a+r.percent,0)/s.report.length):0}%</b></div>`).join('')||'<div class="empty">لا توجد نتائج محفوظة بعد.</div>'}

// QA V12.4: owner-scoped non-destructive report view reset. Stored results and XP remain intact.
async function resetReportView(scope,restore){
 const names={recent:'أحدث الجلسات',classes:'ترتيب الشعب',support:'المهارات التي تحتاج دعمًا',history:'سجل النتائج',mastery:'خريطة إتقان المهارات'};
 if(!names[scope])return;
 if(!restore&&!confirm('تصفير عرض «'+names[scope]+'»؟ السجلات الحقيقية ونقاط الطلاب لن تُحذف، ويمكنك استعادة العرض لاحقًا.'))return;
 try{await api('/api/teacher/reset-view',{method:'POST',body:JSON.stringify({scope,restore})});await loadAll();notify((restore?'تمت استعادة عرض ':'تم تصفير عرض ')+names[scope]);}
 catch(e){notify('تعذر تحديث العرض: '+err(e))}
}
document.addEventListener('click',event=>{
 const reset=event.target.closest('[data-reset-view]');if(reset){resetReportView(reset.dataset.resetView,false);return}
 const restore=event.target.closest('[data-restore-view]');if(restore){resetReportView(restore.dataset.restoreView,true)}
});
async function loadAll(){const [d,s,h]=await Promise.all([api('/api/teacher/dashboard'),api('/api/teacher/students'),api('/api/teacher/history')]);cache={dashboard:d.dashboard,students:s.students,sessions:h.sessions};renderHome();renderStudents();renderHistory()}
async function saveStudents(students){const r=await api('/api/teacher/students',{method:'POST',body:JSON.stringify({students})});notify('تمت إضافة '+r.count+' طالب');await loadAll()}
$('#addStudentForm').onsubmit=async e=>{e.preventDefault();try{await saveStudents([{name:$('#newStudentName').value,className:$('#newStudentClass').value,avatar:$('#newStudentAvatar').value}]);$('#newStudentName').value=''}catch(ex){notify(err(ex))}};
$('#bulkImport').onclick=async()=>{let names=$('#bulkNames').value.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);let cl=$('#bulkClass').value.trim();if(!names.length||!cl)return notify('أدخل الشعبة وأسماء الطلاب أولًا');try{await saveStudents(names.map(name=>({name,className:cl,avatar:avatarIds()[Math.floor(Math.random()*avatarIds().length)]})));$('#bulkNames').value=''}catch(ex){notify(err(ex))}};
$('#shortenCards').onclick=async()=>{
  if(!cache.students.some(s=>String(s.cardCode||'').startsWith('QNA-')))return notify('كل الطلاب لديهم رموز مختصرة بالفعل.');
  if(!confirm('سيتم إصدار رموز أقصر للبطاقات القديمة. ستبقى الرموز المطبوعة ورموز QR السابقة صالحة. هل تريد المتابعة؟'))return;
  const btn=$('#shortenCards');btn.disabled=true;
  try{
    const result=await api('/api/teacher/students/shorten-codes',{method:'POST',body:'{}'});
    await loadAll();
    notify('تم إصدار رموز مختصرة لـ '+result.updated+' طالب. الرموز القديمة ما زالت تعمل.');
  }catch(e){notify(err(e))}
  finally{btn.disabled=false}
};
// Reissue all existing cards with the current TeachGame identity without deleting or changing a card code.
$('#reissueTeachGameCards').onclick=async()=>{
  if(!cache.students.length)return notify('لا توجد بطاقات لإعادة طباعتها.');
  const btn=$('#reissueTeachGameCards'),label=btn.textContent;
  btn.disabled=true;btn.textContent='جارٍ تحديث بطاقات TeachGame...';
  try{
    await loadAll();
    const cards=[...document.querySelectorAll('#studentsBoard .bo-student-id')];
    if(cards.length!==cache.students.length||cards.some(card=>!card.querySelector('.bo-badge-brand strong')?.textContent.includes('TeachGame'))){
      throw Error('card_refresh_incomplete');
    }
    notify('تم تحديث '+cards.length+' بطاقة باسم TeachGame؛ رموز الطلاب القديمة لم تتغير. افتح الطباعة لحفظ النسخة الجديدة.');
    $('#printCards').click();
  }catch(error){notify('تعذر تحديث معاينات البطاقات. يرجى تحديث الصفحة والمحاولة مجددًا.')}
  finally{btn.disabled=false;btn.textContent=label}
};
$('#printCards').onclick=async()=>{
  if(!cache.students.length)return notify('أضف الطلاب أولًا');
  const button=$('#printCards'),original=button.textContent;
  button.disabled=true;button.textContent='جارٍ تجهيز البطاقات وQR...';
  try{
    const images=[...document.querySelectorAll('#studentsBoard .bo-student-id img')];
    // Image lazy loading can leave off-screen printed QR codes blank.
    images.forEach(img=>{img.loading='eager'});
    await Promise.all(images.map(img=>{
      if(img.complete)return Promise.resolve();
      return new Promise(resolve=>{
        const done=()=>{clearTimeout(timer);resolve()};
        const timer=setTimeout(done,20000);
        img.addEventListener('load',done,{once:true});
        img.addEventListener('error',done,{once:true});
      });
    }));
    if(images.some(img=>!img.naturalWidth)){
      notify('لم يكتمل تحميل بعض الصور أو رموز QR. تأكد من اتصال الخادم ثم أعد الطباعة.');
      return;
    }
    window.print();
  }finally{button.disabled=false;button.textContent=original}
};
boot();
})();
