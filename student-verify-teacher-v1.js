/* TAG Student Verify V1 — teacher-only issuance and activation.
 * PIN secrets appear only in a one-time authenticated POST response. Never write
 * them to localStorage, URLs, QR codes, analytics or application logs.
 */
(()=>{
'use strict';
const el=id=>document.getElementById(id);
if(!el('studentVerifyPanel'))return;
const token=()=>localStorage.getItem('qn9_teacher_token')||'';
const state={enabled:false,students:0,issued:0,busy:false,rows:[]};
let directory=null;
const codeRx=/^[A-Z0-9_-]{5,25}$/;
async function api(path,options={}){
 const t=token();if(!t)throw new Error('login_required');
 const res=await fetch(path,{
  ...options,cache:'no-store',
  headers:{'Authorization':'Bearer '+t,...(options.body?{'Content-Type':'application/json'}:{}),...(options.headers||{})}
 });
 const data=await res.json().catch(()=>({}));
 if(!res.ok||!data.ok)throw new Error(data.error||'network');
 return data;
}
function notify(msg,isError=false){
 const out=el('verifyStatus');out.textContent=msg;out.classList.toggle('error',isError);
}
function render(showSummary=false){
 const label=el('verifyEnabledLabel');label.classList.toggle('is-on',state.enabled);
 label.textContent=state.enabled?'مفعّل — PIN مطلوب':'غير مفعّل';
 const toggle=el('verifyToggle');
 toggle.textContent=state.enabled?'تعطيل الحماية':'🛡️ تفعيل الحماية';
 toggle.disabled=state.busy||(!state.enabled&&(state.students===0||state.issued!==state.students));
 for(const id of ['verifyIssueMissing','verifyRotate','verifyUnlock'])el(id).disabled=state.busy;
 if(showSummary&&!state.busy)notify('البطاقات: '+state.students+' • PIN صادر: '+state.issued+' • '+(state.enabled?'الحماية تعمل عند بدء كل اختبار.':'يجب إصدار وتسليم الرموز قبل التفعيل.'));
}
function hideSecrets(){
 state.rows=[];
 el('verifyPinList').textContent='';
 el('verifyReveal').hidden=true;
}
function reveal(rows){
 hideSecrets();
 state.rows=rows.map(x=>({id:x.id,name:x.name,className:x.className,cardCode:x.cardCode,pin:x.pin}));
 if(!state.rows.length){notify('جميع بطاقات الطلاب الموجودة لديها PIN بالفعل؛ لن يُعاد إصداره إلا بطلب صريح.');return}
 const lines=['الشعبة\tرمز الدخول\tاسم الطالب\tPIN'];
 state.rows.forEach(r=>lines.push([r.className,r.cardCode,r.name,r.pin].join('\t')));
 el('verifyPinList').textContent=lines.join('\n');
 el('verifyReveal').hidden=false;
 notify('تم إصدار '+rows.length+' رمزًا سريًا. احفظ الكشف بشكل خاص الآن؛ لن يمكن عرضه مرة ثانية.');
}
function message(e){
 const map={login_required:'تحتاج إلى تسجيل الدخول بحساب المعلم.',
 pin_not_ready:'يجب إصدار PIN لكل الطلاب قبل التفعيل.',
 student_not_found:'لا توجد بطاقة نشطة بهذا الرمز في حسابك.',
 student_required_for_rotation:'حدد الطالب لتغيير رمزه.',
 invalid_student:'رقم الطالب غير صالح.',
 active_attempt:'لديه محاولة نشطة بالفعل.',
 network:'تعذر الاتصال بخدمة TAG'};
 return map[e.message]||'تعذّر تنفيذ العملية: '+e.message;
}
async function refresh(){
 if(!token())return;
 try{
  const r=await api('/api/teacher/student-verify');
  state.enabled=Boolean(r.enabled);state.students=Number(r.students)||0;state.issued=Number(r.issued)||0;
  render(true);
 }catch(e){notify(message(e),true)}
}
async function busy(action){
 if(state.busy)return;
 state.busy=true;render();
 try{await action()}catch(e){notify(message(e),true)}
 finally{state.busy=false;render()}
}
async function identify(){
 const raw=el('verifyTargetCode').value.trim().toUpperCase();
 if(!codeRx.test(raw))throw new Error('أدخل رمز بطاقة صحيحًا مثل G9A-001.');
 if(!directory){
  const r=await api('/api/teacher/students');
  directory=Array.isArray(r.students)?r.students:[];
 }
 const student=directory.find(x=>String(x.cardCode||'').toUpperCase()===raw);
 if(!student)throw new Error('student_not_found');
 return student;
}
el('verifyIssueMissing').onclick=()=>busy(async()=>{
 if(!confirm('إصدار رموز PIN شخصية عشوائية للبطاقات التي لا تملكها فقط؟\nسيظهر الكشف مرة واحدة ويجب توزيعه للطلاب على انفراد.'))return;
 const r=await api('/api/teacher/student-verify/issue',{method:'POST',body:JSON.stringify({})});
 state.enabled=Boolean(r.status.enabled);state.students=r.status.students;state.issued=r.status.issued;
 reveal(r.pins||[]);
});
el('verifyToggle').onclick=()=>busy(async()=>{
 const enable=!state.enabled;
 if(!confirm(enable?'تفعيل PIN الآن لجميع الطلاب في حسابك؟ لن يبدأ أي طالب الاختبار دون رمزه، ولا تحتاج موافقة يدوية.':'تعطيل طلب PIN للطلاب؟ سيُسمح بالدخول دون التحقق الشخصي.'))return;
 const r=await api('/api/teacher/student-verify/toggle',{method:'POST',body:JSON.stringify({enabled:enable})});
 state.enabled=Boolean(r.enabled);state.students=r.students;state.issued=r.issued;
});
el('verifyRotate').onclick=()=>busy(async()=>{
 const student=await identify();
 if(!confirm('إلغاء PIN السابق للطالب '+student.name+' وإصدار رمز جديد؟'))return;
 const r=await api('/api/teacher/student-verify/issue',{method:'POST',body:JSON.stringify({studentId:student.id,rotate:true})});
 reveal(r.pins||[]);
 state.enabled=Boolean(r.status.enabled);state.students=r.status.students;state.issued=r.status.issued;
});
el('verifyUnlock').onclick=()=>busy(async()=>{
 const student=await identify();
 if(!confirm('إلغاء محاولة الاختبار غير المكتملة للطالب '+student.name+'؟ يمكنه البدء من جديد بعد إدخال PIN.'))return;
 const r=await api('/api/teacher/student-verify/unlock',{method:'POST',body:JSON.stringify({studentId:student.id})});
 notify('تم تحرير '+Number(r.revoked||0)+' محاولة غير مكتملة. سجلات النتائج المكتملة لم تتغير.');
});
el('verifyHide').onclick=hideSecrets;
el('verifyCopy').onclick=async()=>{
 if(!state.rows.length)return;
 try{await navigator.clipboard.writeText(el('verifyPinList').textContent);notify('تم نسخ كشف PIN. تجنب مشاركته في مجموعة الطلاب.')}
 catch{notify('تعذر النسخ؛ يمكنك تحديد الكشف ونسخه يدويًا.',true)}
};
el('verifyExport').onclick=()=>{
 if(!state.rows.length)return;
 const lines=[['الشعبة','رمز البطاقة','اسم الطالب','PIN'].join(',')];
 for(const s of state.rows){
  const values=[s.className,s.cardCode,s.name,s.pin].map(v=>'"'+String(v).replace(/"/g,'""')+'"');
  lines.push(values.join(','));
 }
 const blob=new Blob(['\uFEFF'+lines.join('\r\n')],{type:'text/csv;charset=utf-8'});
 const url=URL.createObjectURL(blob);const link=document.createElement('a');
 link.href=url;link.download='TAG_Student_PINs_SECRET_'+new Date().toISOString().slice(0,10)+'.csv';
 document.body.appendChild(link);link.click();link.remove();URL.revokeObjectURL(url);
 notify('تم تنزيل كشف PIN الشخصي. احتفظ به بعيدًا عن الطلاب الآخرين.');
};
document.querySelectorAll('[data-panel="students"]').forEach(button=>button.addEventListener('click',()=>{directory=null;void refresh()}));
window.addEventListener('pagehide',hideSecrets);
})();
