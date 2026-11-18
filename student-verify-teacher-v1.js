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
 toggle.disabled=state.busy||(!state.enabled&&(state.students===0||state.issued!==state.students||!el('verifyDelivered').checked));
 for(const id of ['verifyIssueMissing','verifyRotate','verifyUnlock'])el(id).disabled=state.busy;
 el('verifyReissueAll').disabled=state.busy||state.enabled||state.students===0;
 if(showSummary&&!state.busy)notify('البطاقات: '+state.students+' • PIN صادر: '+state.issued+' • '+(state.enabled?'الحماية تعمل عند بدء كل اختبار.':'يجب إصدار وتسليم الرموز قبل التفعيل.'));
}
function hideSecrets(){
 document.getElementById('tagPinReceipt')?.remove();
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
 pin_protection_must_be_disabled:'يجب تعطيل الحماية أولًا، قبل استبدال رموز جميع الطلاب.',
 invalid_expected_students:'عدد الطلاب غير صالح.',
 pin_rotation_confirmation_required:'تأكيد الاستبدال غير مطابق؛ لم تتغير الرموز.',
 student_count_changed:'تغير عدد الطلاب أثناء العملية. حدّث لوحة الطلاب ثم حاول مرة ثانية.',
 pin_rotation_incomplete:'لم يكتمل تأكيد استلام الكشف. لا تغادر الصفحة قبل مراجعة عدد الرموز.',
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
el('verifyDelivered').addEventListener('change',()=>render());
el('verifyIssueMissing').onclick=()=>busy(async()=>{
 if(!confirm('إصدار رموز PIN شخصية عشوائية للبطاقات التي لا تملكها فقط؟\nسيظهر الكشف مرة واحدة ويجب توزيعه للطلاب على انفراد.'))return;
 const r=await api('/api/teacher/student-verify/issue',{method:'POST',body:JSON.stringify({})});
 state.enabled=Boolean(r.status.enabled);state.students=r.status.students;state.issued=r.status.issued;
 el('verifyDelivered').checked=false;
 reveal(r.pins||[]);
});
el('verifyReissueAll').onclick=()=>busy(async()=>{
 if(state.enabled){notify('عطّل الحماية قبل استبدال جميع رموز PIN.',true);return}
 if(!state.students){notify('لا توجد بطاقات نشطة لإصدار رموز جديدة.',true);return}
 const count=state.students;
 if(!confirm('تحذير: سيُلغى PIN القديم لجميع الطلاب ('+count+') ويُصدر رمز جديد لكل طالب.\nلن تتغير رموز الدخول أو QR أو نتائج الاختبارات، ولن تُفعّل الحماية.\nهل تريد المتابعة؟'))return;
 const expected='REISSUE '+count;
 const confirmation=prompt('تأكيد أخير لحماية بطاقات الطلاب: اكتب النص التالي تمامًا ثم اضغط موافق:\n'+expected,'');
 if(confirmation!==expected){
  notify('لم يتم تغيير أي PIN لأن تأكيد إعادة الإصدار غير مطابق.',true);
  return;
 }
 notify('جارٍ إصدار رموز PIN بديلة للطلاب '+count+'، لا تغلق الصفحة.');
 const r=await api('/api/teacher/student-verify/reissue-all',{
  method:'POST',body:JSON.stringify({expectedStudents:count,confirmation})
 });
 if(!Array.isArray(r.pins)||r.pins.length!==count)
  throw new Error('pin_rotation_incomplete');
 state.enabled=Boolean(r.status.enabled);
 state.students=Number(r.status.students)||0;
 state.issued=Number(r.status.issued)||0;
 el('verifyDelivered').checked=false;
 reveal(r.pins);
 openPinReceipt();
 notify('تم استبدال '+count+' رمز PIN بنجاح. ظهرت صفحة الرموز كاملة؛ احفظ نسخة خاصة باستخدام زر تنزيل الكشف أو طباعة / حفظ PDF. الرموز القديمة لم تعد صالحة.');
});
el('verifyToggle').onclick=()=>busy(async()=>{
 const enable=!state.enabled;
 if(!confirm(enable?'تفعيل PIN الآن لجميع الطلاب في حسابك؟ لن يبدأ أي طالب الاختبار دون رمزه، ولا تحتاج موافقة يدوية.':'تعطيل طلب PIN للطلاب؟ سيُسمح بالدخول دون التحقق الشخصي.'))return;
 const r=await api('/api/teacher/student-verify/toggle',{method:'POST',body:JSON.stringify({enabled:enable,deliveredConfirmed:enable&&el('verifyDelivered').checked})});
 state.enabled=Boolean(r.enabled);state.students=r.students;state.issued=r.issued;
 notify(enable?'تم تفعيل PIN: لن يبدأ الطالب اختبارًا دون رمزه الشخصي.':'تم تعطيل التحقق للمعلم الحالي فقط.');
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
  const values=[s.className,s.cardCode,s.name,s.pin].map(v=>{
   const safe=String(v).replace(/^[=+@\-\t\r]/,"'$&");
   return '"'+safe.replace(/"/g,'""')+'"';
  });
  lines.push(values.join(','));
 }
 const blob=new Blob(['\uFEFF'+lines.join('\r\n')],{type:'text/csv;charset=utf-8'});
 const url=URL.createObjectURL(blob);const link=document.createElement('a');
 link.href=url;link.download='TAG_Student_PINs_SECRET_'+new Date().toISOString().slice(0,10)+'.csv';
 document.body.appendChild(link);link.click();link.remove();URL.revokeObjectURL(url);
 notify('تم تنزيل كشف PIN الشخصي. احتفظ به بعيدًا عن الطلاب الآخرين.');
};
function escapeSlip(value){
 return String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}
el('verifyOne').onclick=async()=>{
 const code=el('verifyTargetCode').value.trim().toUpperCase();
 const row=state.rows.find(x=>String(x.cardCode||'').toUpperCase()===code);
 if(!row){notify('أدخل رمز بطاقة الطالب في خانة الإدارة لاختيار رسالة هذا الطالب فقط.',true);el('verifyTargetCode').focus();return}
 const message='مرحبًا '+row.name+'، رمز التحقق الشخصي الخاص بك في منصة TAG هو: '+row.pin+
  '. رقم بطاقتك: '+row.cardCode+'. احتفظ بهذا الرمز لنفسك ولا ترسله إلى أحد.';
 try{await navigator.clipboard.writeText(message);notify('تم نسخ رسالة '+row.name+' فقط. أرسلها إلى الطالب بصورة خاصة، لا إلى مجموعة الصف.')}
 catch{notify('تعذر نسخ الرسالة. استخدم القصاصات السرية أو الكشف الخاص.',true)}
};

function openPinReceipt(){
 if(!state.rows.length){notify('لا توجد رموز PIN ظاهرة في هذه الجلسة. لا يمكن استرجاع الأرقام القديمة بعد إغلاق الصفحة.',true);return}
 document.getElementById('tagPinReceipt')?.remove();
 const sections=[...new Set(state.rows.map(s=>String(s.className||'غير محدد')))];
 const tables=sections.map(section=>{
  const students=state.rows.filter(s=>String(s.className||'غير محدد')===section)
      .slice().sort((a,b)=>String(a.cardCode).localeCompare(String(b.cardCode)));
  const rows=students.map((r,i)=>'<tr><td>'+String(i+1)+'</td><td>'+escapeSlip(r.name)+'</td><td dir="ltr">'+escapeSlip(r.cardCode)+'</td><td class="pin-value" dir="ltr">'+escapeSlip(r.pin)+'</td></tr>').join('');
  return '<section class="tag-pin-sheet"><h3>الشعبة: '+escapeSlip(section)+' <small>('+students.length+' طالب)</small></h3>'+
  '<table><thead><tr><th>م</th><th>اسم الطالب</th><th>رمز البطاقة</th><th>PIN الشخصي</th></tr></thead><tbody>'+rows+'</tbody></table></section>';
 }).join('');
 const modal=document.createElement('div');
 modal.id='tagPinReceipt';modal.className='tag-pin-receipt';modal.setAttribute('role','dialog');
 modal.setAttribute('aria-modal','true');modal.setAttribute('aria-label','صفحة رموز الطلاب السرية');
 modal.innerHTML='<div class="tag-pin-receipt-inner">'+
  '<header class="tag-pin-receipt-head"><div><h2>🔐 صفحة رموز PIN للطلاب</h2>'+
  '<p>الكشف الخاص بالمعلم — '+state.rows.length+' رمزًا موزعًا على '+sections.length+' شعب. لا تشارك هذه الصفحة أو الملف في مجموعة الصف.</p></div>'+
  '<nav class="tag-pin-receipt-controls" aria-label="إجراءات الكشف">'+
  '<button type="button" id="verifyReceiptDownload">⬇️ تنزيل الكشف Excel / CSV</button>'+
  '<button type="button" id="verifyReceiptPrint">🖨️ طباعة / حفظ PDF</button>'+
  '<button type="button" id="verifyReceiptSlips">✉️ قصاصات لكل طالب</button>'+
  '<button type="button" id="verifyReceiptClose">إغلاق الصفحة</button></nav></header>'+
  '<main class="tag-pin-receipt-content">'+tables+'</main>'+
  '<footer class="tag-pin-receipt-footer">⚠️ الرموز تظهر في هذه الجلسة فقط ولا يمكن استرجاعها من قاعدة البيانات بعد إغلاق الصفحة. احفظ نسخة خاصة.</footer>'+
  '</div>';
 document.body.appendChild(modal);
 modal.querySelector('#verifyReceiptClose').onclick=()=>modal.remove();
 modal.querySelector('#verifyReceiptDownload').onclick=()=>el('verifyExport').click();
 modal.querySelector('#verifyReceiptSlips').onclick=()=>el('verifySlips').click();
 modal.querySelector('#verifyReceiptPrint').onclick=()=>window.print();
 modal.addEventListener('keydown',event=>{if(event.key==='Escape'){modal.remove();event.preventDefault()}});
 modal.querySelector('#verifyReceiptDownload').focus();
}

el('verifyReceiptPage').onclick=openPinReceipt;
el('verifySlips').onclick=()=>{
 if(!state.rows.length){notify('لا توجد رموز ظاهرة لإعداد القصاصات.',true);return}
 const pages=[];
 for(let i=0;i<state.rows.length;i+=8){
  const cards=state.rows.slice(i,i+8).map(row=>
   '<article class="slip"><div class="brand">🔐 TAG Student Verify</div>'+
   '<div class="label">رمز دخول شخصي • سرّي للطالب فقط</div>'+
   '<div class="name">'+escapeSlip(row.name)+'</div>'+
   '<div class="section">'+escapeSlip(row.className)+'</div>'+
   '<div class="access">البطاقة: <b dir="ltr">'+escapeSlip(row.cardCode)+'</b></div>'+
   '<div class="pin" dir="ltr">'+escapeSlip(row.pin)+'</div>'+
   '<div class="footer">لا تُظهر هذا الرمز لزملائك. احتفظ به بعيدًا عن بطاقة QR.</div></article>'
  ).join('');
  pages.push('<section class="page">'+cards+'</section>');
 }
 const documentHtml='<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+
 '<title>TAG • قصاصات PIN السرية</title><style>'+
 '*{box-sizing:border-box}body{font-family:Tahoma,Arial,sans-serif;color:#102c48;background:#f2f6fa;margin:0}'+
 '.page{width:210mm;height:297mm;margin:0 auto;display:grid;grid-template-columns:repeat(2,1fr);grid-template-rows:repeat(4,1fr);gap:3mm;padding:10mm;break-after:page;background:white}'+
 '.slip{border:1px dashed #6486a4;border-radius:9px;display:flex;flex-direction:column;align-items:center;justify-content:space-evenly;padding:6mm;text-align:center;min-height:0;overflow:hidden}'+
 '.brand{font-size:15px;font-weight:900;color:#16749a}.label{font-size:11px;color:#8c3d38;font-weight:800}'+
 '.name{font-size:15px;font-weight:900}.section{font-size:12px}.access{font-size:12px}'+
 '.pin{letter-spacing:5px;font-family:Arial,sans-serif;font-size:26px;font-weight:900;background:#e4f8f1;border-radius:6px;padding:6px 18px}'+
 '.footer{font-size:10px;color:#4a647b;line-height:1.5}'+
 '@page{size:A4;margin:0}@media print{body{background:white}.page{margin:0;break-after:page}}'+
 '</style></head><body>'+pages.join('')+'</body></html>';
 const blob=new Blob([documentHtml],{type:'text/html;charset=utf-8'});
 const url=URL.createObjectURL(blob),a=document.createElement('a');
 a.href=url;a.download='TAG_PIN_Private_Slips_'+new Date().toISOString().slice(0,10)+'.html';
 document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
 notify('تم إنشاء قصاصات PIN منفصلة لكل طالب. اطبعها على انفراد، وقصّها، وسلّم كل ورقة لصاحبها فقط.');
};
document.querySelectorAll('[data-panel="students"]').forEach(button=>button.addEventListener('click',()=>{directory=null;void refresh()}));
document.querySelectorAll('button.nav[data-panel]').forEach(button=>button.addEventListener('click',()=>{
 if(button.dataset.panel!=='students')hideSecrets();
}));
window.addEventListener('pagehide',hideSecrets);
})();
