/* BOOYAHJO Control Center V1. Admin cookie is HttpOnly; CSRF from separate same-site cookie. */
(()=>{
'use strict';
const $=id=>document.getElementById(id);
const h=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num=v=>Number(v||0).toLocaleString('en-US');
let authPending=null;
let teachersPage=1,teachersTotal=0;
let allSchools=[];
let searchTimer;
const tabs={overview:'نظرة عامة',teachers:'المعلمون',students:'الطلاب',sessions:'الجلسات والاختبارات',schools:'المدارس',audit:'سجل الإدارة'};
const csrf=()=>{
 const cookie=document.cookie.split('; ').find(x=>x.startsWith('bjcsrf='));
 return cookie?decodeURIComponent(cookie.slice(7)):'';
};
async function request(path,{method='GET',data=null,auth=true}={}){
 const headers={'Accept':'application/json'};
 if(method!=='GET'){headers['Content-Type']='application/json';headers['X-BOOYAH-Admin']='1'}
 if(auth&&method!=='GET')headers['X-Admin-CSRF']=csrf();
 const response=await fetch('/api/admin/'+path,{method,credentials:'same-origin',cache:'no-store',headers,
  body:method==='GET'?undefined:JSON.stringify(data||{})});
 const output=await response.json().catch(()=>({ok:false,error:'network'}));
 if(!response.ok||!output.ok)throw Object.assign(new Error(output.error||'network'),{status:response.status});
 return output;
}
function msg(message){
 $('authMessage').textContent=message||'';
}
let toastTimer;
function toast(message,failed=false){
 const element=$('adminToast');
 element.classList.remove('hidden');
 element.style.background=failed?'#fff0f1':'#e5f8f5';
 element.style.color=failed?'#972538':'#126453';
 element.textContent=message;
 clearTimeout(toastTimer);
 toastTimer=setTimeout(()=>element.classList.add('hidden'),5000);
}
function setForm(name){
 for(const id of ['loginForm','setupForm','activateForm'])$(id).classList.toggle('hidden',id!==name);
 msg('');
}
function errorLabel(error){
 return ({
  invalid_credentials:'البريد أو كلمة المرور أو رمز المصادقة غير صحيح.',
  rate_limited:'محاولات كثيرة. جرّب لاحقًا.',
  admin_login_required:'انتهت جلسة المدير. سجّل الدخول من جديد.',
  admin_csrf_or_login_required:'جلسة الإدارة غير صالحة. أعد تسجيل الدخول.',
  invalid_setup_key:'مفتاح التأسيس غير صحيح.',
  setup_disabled:'حساب المدير موجود بالفعل. لا يمكن تأسيس حساب جديد.',
  password_min_14:'استخدم اسمًا صحيحًا وكلمة مرور من 14 حرفًا على الأقل.',
  invalid_otp:'رمز المصادقة غير صحيح. تحقق من الوقت في هاتفك.',
  admin_server_error:'حدث خطأ في الخادم. تحقق من الاتصال وحاول مرة أخرى.',
  network:'تعذر الاتصال بالخادم.'
 })[error.message]||'تعذر تنفيذ العملية. تحقق من البيانات وأعد المحاولة.';
}
function showApp(admin){
 $('authentication').classList.add('hidden');
 $('adminApp').classList.remove('hidden');
 $('adminName').textContent=admin?.name||'مدير المنصة';
 selectTab('overview');
}
function showLogin(message=''){
 $('adminApp').classList.add('hidden');
 $('authentication').classList.remove('hidden');
 setForm('loginForm');
 if(message)msg(message);
}
async function start(){
 try{
  const me=await request('me');
  showApp(me.admin);
 }catch{
  showLogin();
  try{
   const status=await request('status',{auth:false});
   if(status.setupAvailable)setForm('setupForm');
  }catch{msg('تعذر التواصل مع قاعدة البيانات. تحقق من تشغيل الخادم.')}
 }
}
$('loginForm').addEventListener('submit',async event=>{
 event.preventDefault();
 const button=event.submitter;button.disabled=true;msg('');
 try{
  const output=await request('login',{method:'POST',auth:false,data:{
   email:$('loginEmail').value,password:$('loginPassword').value,otp:$('loginOtp').value
  }});
  $('loginPassword').value='';$('loginOtp').value='';
  showApp(output.admin);
 }catch(error){msg(errorLabel(error))}
 finally{button.disabled=false}
});
$('setupForm').addEventListener('submit',async event=>{
 event.preventDefault();const button=event.submitter;button.disabled=true;msg('');
 const setupKey=$('setupKey').value.trim(),email=$('setupEmail').value.trim();
 try{
  const output=await request('setup',{method:'POST',auth:false,data:{
   setupKey,name:$('setupName').value,email,password:$('setupPassword').value
  }});
  authPending={setupKey,email};
  $('setupPassword').value='';
  $('totpSecret').textContent=output.secret;
  setForm('activateForm');
 }catch(error){msg(errorLabel(error))}
 finally{button.disabled=false}
});
$('activateForm').addEventListener('submit',async event=>{
 event.preventDefault();if(!authPending)return msg('أكمل إعداد الحساب أولًا.');
 const button=event.submitter;button.disabled=true;
 try{
  await request('activate',{method:'POST',auth:false,data:{
   ...authPending,otp:$('activateOtp').value
  }});
  $('activateOtp').value='';
  $('totpSecret').textContent='';
  authPending=null;
  showLogin('تم تفعيل المدير والمصادقة الثنائية. سجّل الدخول ببريدك وكلمة المرور ورمز التطبيق.');
 }catch(error){msg(errorLabel(error))}
 finally{button.disabled=false}
});
$('logoutBtn').addEventListener('click',async()=>{
 try{await request('logout',{method:'POST'})}finally{showLogin('تم تسجيل الخروج.')}
});
const sections=['overview','teachers','students','sessions','schools','audit'];
function selectTab(view){
 if(!sections.includes(view))view='overview';
 sections.forEach(id=>$(id+'View').classList.toggle('hidden',id!==view));
 document.querySelectorAll('[data-view]').forEach(el=>{
  const selected=el.dataset.view===view;
  el.classList.toggle('selected',selected);
  el.setAttribute('aria-current',selected?'page':'false');
 });
 $('topPage').textContent=tabs[view];
 $('sidebar').classList.remove('open');
 if(view==='overview')void loadOverview();
 if(view==='teachers')void loadTeachers();
 if(view==='schools')void loadSchools();
 if(view==='students')void loadStudents();
 if(view==='sessions')void loadSessions();
 if(view==='audit')void loadAudit();
}
document.querySelectorAll('[data-view]').forEach(item=>
 item.addEventListener('click',()=>selectTab(item.dataset.view)));
$('menuToggle').addEventListener('click',()=>$('sidebar').classList.toggle('open'));

async function loadOverview(){
 $('metricsGrid').innerHTML='<p class="loading">جارٍ تحميل المؤشرات الفعلية...</p>';
 try{
  const r=await request('summary');
  const s=r.summary||{};
  $('databaseBadge').textContent=s.database==='postgres'?'Neon PostgreSQL':'SQLite (محلي)';
  const cards=[
   {label:'المعلمون المسجلون',value:s.teachers,icon:'♙',foot:'إجمالي حسابات المعلمين'},
   {label:'الطلاب',value:s.students,icon:'♧',foot:'بطاقات طلاب مسجلة'},
   {label:'الاختبارات',value:s.quizzes,icon:'▤',foot:'اختبارات محفوظة'},
   {label:'الجلسات المكتملة',value:s.sessions,icon:'▣',foot:'سجل الجلسات في القاعدة'}
  ];
  $('metricsGrid').innerHTML=cards.map(c=>
   '<article class="metric"><div class="metric-top"><span class="metric-label">'+h(c.label)
   +'</span><span class="metric-icon">'+c.icon+'</span></div><strong>'+num(c.value)
   +'</strong><span class="metric-foot">'+h(c.foot)+'</span></article>').join('');
  const max=Math.max(1,...(s.days||[]).map(d=>Number(d.sessions)||0));
  $('activityChart').innerHTML=(s.days||[]).map(d=>
   '<div class="bar-cell" title="'+num(d.sessions)+' جلسة"><div class="bar" style="height:'
   +Math.max(4,Math.round(Number(d.sessions)/max*100))+'%"></div><small>'+h(d.day)+'</small></div>').join('');
  void loadInsights();
  $('operationsGrid').innerHTML=[
   ['المدارس المسجلة',s.schools],['محاولات الطلاب',s.attempts],
   ['الغرف النشطة المسجلة',s.liveRooms],['المعلمون النشطون خلال 7 أيام',s.activeTeachers7d]
  ].map(([name,value])=>'<div class="operation-item"><span>'+h(name)+'</span><strong>'+num(value)+'</strong></div>').join('');
 }catch(e){$('metricsGrid').innerHTML='<p class="empty">تعذر تحميل البيانات من قاعدة البيانات.</p>';toast(errorLabel(e),true)}
}
$('refreshBtn').addEventListener('click',loadOverview);

async function loadTeachers(){
 $('teachersBody').innerHTML='<tr><td colspan="6" class="empty">جارٍ تحميل المعلمين...</td></tr>';
 const search=$('teacherSearch').value.trim();
 try{
  const data=await request('teachers?'+new URLSearchParams({page:String(teachersPage),search}));
  teachersTotal=data.total;
  $('teachersCount').textContent='عدد النتائج: '+num(data.total);
  $('teachersPage').textContent=String(teachersPage);
  $('prevTeachers').disabled=teachersPage===1;
  $('nextTeachers').disabled=teachersPage*data.pageSize>=data.total;
  if(!data.rows.length){$('teachersBody').innerHTML='<tr><td colspan="6" class="empty">لا توجد حسابات مطابقة.</td></tr>';return}
  $('teachersBody').innerHTML=data.rows.map(t=>
   '<tr><td><strong>'+h(t.name)+'</strong><small>'+h(t.email)+'</small></td>'
   +'<td>'+h(t.school)+'<small>'+h(t.subject)+'</small></td>'
   +'<td>'+num(t.students)+'</td><td>'+num(t.sessions)+'</td>'
   +'<td><span class="state-tag '+(t.admin_disabled?'off':'')+'">'+(t.admin_disabled?'موقوف':'نشط')+'</span></td>'
   +'<td><button class="action-btn" type="button" data-profile="'+h(t.id)+'">التفاصيل</button> <button class="action-btn '+(t.admin_disabled?'':'danger')+'" type="button" data-status="'+h(t.id)
   +'" data-disabled="'+(t.admin_disabled?'0':'1')+'">'+(t.admin_disabled?'إعادة تفعيل':'إيقاف الحساب')+'</button></td></tr>').join('');
  $('teachersBody').querySelectorAll('[data-profile]').forEach(b=>b.addEventListener('click',()=>openTeacher(b.dataset.profile)));
  $('teachersBody').querySelectorAll('[data-status]').forEach(b=>b.addEventListener('click',()=>changeTeacher(b)));
 }catch(e){
  $('teachersBody').innerHTML='<tr><td colspan="6" class="empty">تعذر تحميل حسابات المعلمين.</td></tr>';
  if(e.status===401)showLogin(errorLabel(e));
  else toast(errorLabel(e),true);
 }
}
async function changeTeacher(button){
 const disable=button.dataset.disabled==='1';
 const verb=disable?'إيقاف':'إعادة تفعيل';
 if(!window.confirm('هل تريد '+verb+' حساب المعلم؟ ستُلغى جلساته الحالية عند إيقافه، دون حذف بياناته.'))return;
 const reason=window.prompt('اكتب سبب الإجراء (8 أحرف على الأقل) ليدخل في سجل الإدارة:');
 if(reason===null)return;
 if(reason.trim().length<8)return toast('يرجى كتابة سبب واضح لا يقل عن 8 أحرف.',true);
 button.disabled=true;
 try{
  await request('teacher/status',{method:'POST',data:{
   teacherId:button.dataset.status,disabled:disable,reason:reason.trim()
  }});
  toast('تم '+verb+' الحساب وتوثيق العملية بنجاح.');
  await loadTeachers();
 }catch(e){toast(errorLabel(e),true)}
 finally{button.disabled=false}
}
$('teacherRefresh').addEventListener('click',loadTeachers);
$('teacherSearch').addEventListener('input',()=>{
 clearTimeout(searchTimer);teachersPage=1;
 searchTimer=setTimeout(loadTeachers,350);
});
$('prevTeachers').addEventListener('click',()=>{if(teachersPage>1){teachersPage--;void loadTeachers()}});
$('nextTeachers').addEventListener('click',()=>{if(teachersPage*50<teachersTotal){teachersPage++;void loadTeachers()}});

async function loadSchools(){
 $('schoolsBody').innerHTML='<tr><td colspan="4" class="empty">جارٍ تحميل المدارس...</td></tr>';
 try{const x=await request('schools');allSchools=x.rows||[];renderSchools()}
 catch(e){$('schoolsBody').innerHTML='<tr><td colspan="4" class="empty">تعذر تحميل المدارس.</td></tr>';toast(errorLabel(e),true)}
}
function renderSchools(){
 const query=$('schoolSearch').value.trim().toLocaleLowerCase();
 const rows=allSchools.filter(s=>String(s.school||'').toLocaleLowerCase().includes(query));
 $('schoolsBody').innerHTML=rows.length?rows.map(s=>
  '<tr><td><button class="linklike" type="button" data-school="'+encodeURIComponent(s.school||'')+'">'+h(s.school||'غير محدد')+'</button></td><td>'+num(s.teachers)
  +'</td><td>'+num(s.students)+'</td><td>'+num(s.sessions)+'</td></tr>').join('')
 :'<tr><td colspan="4" class="empty">لا توجد مدارس مطابقة.</td></tr>';
 $('schoolsBody').querySelectorAll('[data-school]').forEach(b=>b.addEventListener('click',()=>openSchool(decodeURIComponent(b.dataset.school))));
}
$('schoolSearch').addEventListener('input',renderSchools);
$('schoolsRefresh').addEventListener('click',loadSchools);
async function loadAudit(){
 $('auditBody').innerHTML='<tr><td colspan="5" class="empty">جارٍ تحميل السجل...</td></tr>';
 try{
  const r=await request('audit');
  $('auditBody').innerHTML=(r.rows||[]).map(x=>
   '<tr><td>'+h(new Date(Number(x.created_at)*1000).toLocaleString('ar-JO'))+'</td>'
   +'<td>'+h(x.actor)+'</td><td>'+h(x.action)+'</td><td>'+h(x.target_type)+' '+h(x.target_id.slice(0,10))+'</td>'
   +'<td>'+h(x.note||'—')+'</td></tr>').join('')
   ||'<tr><td colspan="5" class="empty">لا توجد إجراءات إدارية مسجلة حتى الآن.</td></tr>';
 }catch(e){toast(errorLabel(e),true)}
}
$('auditRefresh').addEventListener('click',loadAudit);

const fmtDate=v=>v?new Date(Number(v)*1000).toLocaleString('ar-JO',{dateStyle:'medium',timeStyle:'short'}):'لا يوجد نشاط';
let studentsPage=1,studentsTotal=0,sessionsPage=1,sessionsTotal=0;
let studentData=[],sessionData=[],searchStudentsTimer,searchSessionsTimer;
const cleanCsv=v=>{let x=String(v??'').replace(/[\r\n]+/g,' ');if(/^[=+@-]/.test(x))x="'"+x;return '"'+x.replace(/"/g,'""')+'"';};
function csvDownload(filename,columns,rows){
 const lines=[columns.map(cleanCsv).join(','),...rows.map(r=>r.map(cleanCsv).join(','))];
 const blob=new Blob(['\ufeff'+lines.join('\r\n')],{type:'text/csv;charset=utf-8'});
 const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download=filename;link.click();
 setTimeout(()=>URL.revokeObjectURL(link.href),1000);
}
async function loadInsights(){
 try{
  const r=await request('insights');
  $('insightBanner').innerHTML='<div><small>متابعة الحسابات</small><strong>موقوفون: '+num(r.disabledTeachers)+'</strong><span>من '+num(r.summary.teachers)+' معلم</span></div>'
  +'<div><small>المدارس</small><strong>'+num(r.totalSchools)+'</strong><span>مدارس مسجلة</span></div>'
  +'<div><small>أحدث المعلمين</small><strong>'+h(r.recentTeachers[0]?.name||'—')+'</strong><span>'+h(r.recentTeachers[0]?.school||'—')+'</span></div>'
  +'<div><small>أحدث اختبار مكتمل</small><strong>'+h(r.recentSessions[0]?.quiz_title||'—')+'</strong><span>'+fmtDate(r.recentSessions[0]?.played_at)+'</span></div>';
 }catch(e){$('insightBanner').textContent='تعذر تحميل مؤشرات الحسابات الإضافية.'}
}
async function loadStudents(){
 $('studentsBody').innerHTML='<tr><td colspan="5" class="empty">جارٍ تحميل حسابات الطلاب...</td></tr>';
 try{
  const r=await request('students?'+new URLSearchParams({page:String(studentsPage),search:$('studentSearch').value.trim()}));
  studentData=r.rows;studentsTotal=r.total;
  $('studentsPage').textContent=String(studentsPage);
  $('studentsCount').textContent='عدد النتائج: '+num(r.total);
  $('prevStudents').disabled=studentsPage===1;
  $('nextStudents').disabled=studentsPage*50>=r.total;
  $('studentsBody').innerHTML=r.rows.map(x=>'<tr><td><strong>'+h(x.name)+'</strong><small>'+h(x.class_name||'غير محدد')+'</small></td>'
   +'<td>'+h(x.teacher_name)+'<small>'+h(x.school)+'</small></td><td>'+num(x.attempts)+'</td>'
   +'<td>'+num(x.xp)+'</td><td>'+h(fmtDate(x.last_attempt))+'</td></tr>').join('')
   ||'<tr><td colspan="5" class="empty">لا توجد حسابات مطابقة.</td></tr>';
 }catch(e){$('studentsBody').innerHTML='<tr><td colspan="5" class="empty">تعذر تحميل الحسابات.</td></tr>';toast(errorLabel(e),true)}
}
async function loadSessions(){
 $('sessionsBody').innerHTML='<tr><td colspan="5" class="empty">جارٍ تحميل الجلسات...</td></tr>';
 try{
  const r=await request('sessions?'+new URLSearchParams({page:String(sessionsPage),search:$('sessionSearch').value.trim()}));
  sessionData=r.rows;sessionsTotal=r.total;
  $('sessionsPage').textContent=String(sessionsPage);
  $('sessionsCount').textContent='عدد النتائج: '+num(r.total);
  $('prevSessions').disabled=sessionsPage===1;
  $('nextSessions').disabled=sessionsPage*50>=r.total;
  $('sessionsBody').innerHTML=r.rows.map(x=>'<tr><td><strong>'+h(x.quiz_title||'اختبار بدون عنوان')+'</strong><small>'+h(x.subject||'')+'</small></td>'
   +'<td>'+h(x.teacher_name)+'<small>'+h(x.school||'')+'</small></td><td>'+h(x.section||'—')+' / '+h(x.game_mode||'—')+'</td>'
   +'<td>'+num(x.attempts)+'</td><td>'+h(fmtDate(x.played_at))+'</td></tr>').join('')
   ||'<tr><td colspan="5" class="empty">لا توجد جلسات مطابقة.</td></tr>';
 }catch(e){$('sessionsBody').innerHTML='<tr><td colspan="5" class="empty">تعذر تحميل الجلسات.</td></tr>';toast(errorLabel(e),true)}
}
$('studentRefresh').addEventListener('click',loadStudents);
$('sessionRefresh').addEventListener('click',loadSessions);
$('studentSearch').addEventListener('input',()=>{studentsPage=1;clearTimeout(searchStudentsTimer);searchStudentsTimer=setTimeout(loadStudents,350)});
$('sessionSearch').addEventListener('input',()=>{sessionsPage=1;clearTimeout(searchSessionsTimer);searchSessionsTimer=setTimeout(loadSessions,350)});
$('prevStudents').addEventListener('click',()=>{if(studentsPage>1){studentsPage--;void loadStudents()}});
$('nextStudents').addEventListener('click',()=>{if(studentsPage*50<studentsTotal){studentsPage++;void loadStudents()}});
$('prevSessions').addEventListener('click',()=>{if(sessionsPage>1){sessionsPage--;void loadSessions()}});
$('nextSessions').addEventListener('click',()=>{if(sessionsPage*50<sessionsTotal){sessionsPage++;void loadSessions()}});
$('studentsExport').addEventListener('click',()=>csvDownload('booyahjo-students-page-'+studentsPage+'.csv',
 ['الطالب','الشعبة','المعلم','المدرسة','المحاولات','XP','آخر مشاركة'],
 studentData.map(x=>[x.name,x.class_name,x.teacher_name,x.school,x.attempts,x.xp,fmtDate(x.last_attempt)])));
$('sessionsExport').addEventListener('click',()=>csvDownload('booyahjo-sessions-page-'+sessionsPage+'.csv',
 ['الاختبار','المعلم','المدرسة','الشعبة','النمط','المشاركات','التاريخ'],
 sessionData.map(x=>[x.quiz_title,x.teacher_name,x.school,x.section,x.game_mode,x.attempts,fmtDate(x.played_at)])));
function openDrawer(title,html){
 $('detailTitle').textContent=title;
 $('detailContent').innerHTML=html;
 $('detailBackdrop').classList.remove('hidden');
 $('detailDrawer').classList.remove('hidden');
 $('detailClose').focus();
}
function closeDrawer(){
 $('detailBackdrop').classList.add('hidden');
 $('detailDrawer').classList.add('hidden');
 $('detailContent').replaceChildren();
}
$('detailClose').addEventListener('click',closeDrawer);
$('detailBackdrop').addEventListener('click',closeDrawer);
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeDrawer()});
const detailStat=(label,value)=>'<div class="detail-stat"><small>'+h(label)+'</small><strong>'+h(String(value??0))+'</strong></div>';
async function openTeacher(id){
 openDrawer('تفاصيل حساب المعلم','<p class="empty">جارٍ تحميل بيانات المعلم من Neon...</p>');
 try{
  const r=await request('teacher/detail?'+new URLSearchParams({id})),t=r.teacher;
  const classes=(t.classes||[]).map(x=>'<li>'+h(x.class_name||'بدون شعبة')+' — '+num(x.students)+' طالب</li>').join('');
  const sessions=(t.recentSessions||[]).map(x=>'<tr><td>'+h(x.quiz_title||'اختبار')+'</td><td>'+h(x.section||'—')+'</td><td>'+h(fmtDate(x.played_at))+'</td></tr>').join('');
  const html='<div class="identity"><div class="avatar-circle">'+h((t.name||'م').slice(0,1))+'</div><div><h3>'+h(t.name)+'</h3><p dir="ltr">'+h(t.email)+'</p><span class="state-tag '+(t.admin_disabled?'off':'')+'">'+(t.admin_disabled?'موقوف':'نشط')+'</span></div></div>'
   +'<p class="detail-meta"><b>المدرسة:</b> '+h(t.school||'—')+'<br><b>المادة:</b> '+h(t.subject||'—')+'<br><b>نوع المدرسة:</b> '+h(t.school_type||'—')
   +'<br><b>تاريخ التسجيل:</b> '+h(fmtDate(t.created_at))+'<br><b>آخر جلسة:</b> '+h(fmtDate(t.last_session))+'</p>'
   +'<div class="detail-stats">'+detailStat('الطلاب',num(t.students))+detailStat('الاختبارات',num(t.quizzes))
   +detailStat('الجلسات المكتملة',num(t.sessions))+detailStat('محاولات الطلاب',num(t.attempts))
   +detailStat('متوسط النتائج',t.averagePercent+'%')+detailStat('نتائج 80% فأعلى',num(t.highScores))+'</div>'
   +'<h3 class="detail-h">الشعب المسجلة</h3><ul class="detail-list">'+(classes||'<li>لا توجد شعب</li>')+'</ul>'
   +'<h3 class="detail-h">آخر الجلسات</h3><div class="table-scroll"><table><thead><tr><th>الاختبار</th><th>الشعبة</th><th>التاريخ</th></tr></thead><tbody>'
   +(sessions||'<tr><td colspan="3">لا توجد جلسات</td></tr>')+'</tbody></table></div>';
  openDrawer('ملف المعلم — '+t.name,html);
 }catch(e){openDrawer('تعذر تحميل الحساب','<p class="empty">'+h(errorLabel(e))+'</p>')}
}
async function openSchool(name){
 openDrawer('تفاصيل المدرسة','<p class="empty">جارٍ تحميل بيانات المدرسة...</p>');
 try{
  const r=await request('school/detail?'+new URLSearchParams({name})),s=r.school;
  const teachers=(s.teachersList||[]).map(t=>'<tr><td><button class="linklike" data-profile="'+h(t.id)+'">'+h(t.name)+'</button><small>'+h(t.subject||'')+'</small></td><td>'+num(t.students)+'</td><td>'+num(t.sessions)+'</td><td>'+ (t.admin_disabled?'موقوف':'نشط')+'</td></tr>').join('');
  openDrawer('المدرسة — '+s.school,'<div class="detail-stats">'+detailStat('المعلمون',num(s.teachers))+detailStat('الطلاب',num(s.students))+detailStat('الجلسات',num(s.sessions))+'</div>'
   +'<h3 class="detail-h">حسابات المعلمين في المدرسة</h3><div class="table-scroll"><table><thead><tr><th>المعلم</th><th>الطلاب</th><th>الجلسات</th><th>الحالة</th></tr></thead><tbody>'+teachers+'</tbody></table></div>');
  $('detailContent').querySelectorAll('[data-profile]').forEach(b=>b.addEventListener('click',()=>openTeacher(b.dataset.profile)));
 }catch(e){openDrawer('تعذر تحميل المدرسة','<p class="empty">'+h(errorLabel(e))+'</p>')}
}

void start();
})();
