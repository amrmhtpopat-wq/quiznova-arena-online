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
const tabs={overview:'نظرة عامة',teachers:'المعلمون',schools:'المدارس',audit:'سجل الإدارة'};
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
const sections=['overview','teachers','schools','audit'];
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
   +'<td><button class="action-btn '+(t.admin_disabled?'':'danger')+'" type="button" data-status="'+h(t.id)
   +'" data-disabled="'+(t.admin_disabled?'0':'1')+'">'+(t.admin_disabled?'إعادة تفعيل':'إيقاف الحساب')+'</button></td></tr>').join('');
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
  '<tr><td><strong>'+h(s.school||'غير محدد')+'</strong></td><td>'+num(s.teachers)
  +'</td><td>'+num(s.students)+'</td><td>'+num(s.sessions)+'</td></tr>').join('')
 :'<tr><td colspan="4" class="empty">لا توجد مدارس مطابقة.</td></tr>';
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
void start();
})();
