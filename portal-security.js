/* QuizNova V10.3: teacher account security, email recovery and backups */
(()=>{'use strict';
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const token=()=>localStorage.getItem('qn9_teacher_token')||'';
async function call(path,body,auth=true){
 const hdr={'Content-Type':'application/json'};
 if(auth)hdr.Authorization='Bearer '+token();
 const response=await fetch(path,{method:body===undefined?'GET':'POST',headers:hdr,body:body===undefined?undefined:JSON.stringify(body),cache:'no-store'});
 const data=await response.json();if(!response.ok||!data.ok)throw Error(data.error||'server_error');return data
}
const labels={email_not_configured:'استعادة كلمة المرور بالبريد غير مفعلة بعد. يمكنك تغييرها من حسابك.',weak_password:'كلمة المرور يجب أن تتكون من 10 أحرف على الأقل.',wrong_credentials:'كلمة المرور الحالية غير صحيحة.',reset_invalid:'رابط الاستعادة غير صالح أو انتهت صلاحيته.',login_required:'يرجى تسجيل الدخول مجددًا.',server_error:'تعذّر إتمام الطلب.'};
const errorText=e=>labels[e.message]||'تعذّر إكمال العملية: '+e.message;
function notice(s){const el=$('#qnSecNotice');if(el)el.textContent=s;else alert(s)}
function modal(title,body,submit){
 const prev=$('#qnSecDialog');if(prev)prev.remove();
 const d=document.createElement('dialog');d.id='qnSecDialog';d.className='qn-modal';
 d.innerHTML='<form id="qnSecForm"><h3>'+title+'</h3>'+body+'<div class="qn-row"><button class="primary" type="submit">تأكيد</button><button id="qnCancel" class="secondary" type="button">إلغاء</button></div><p id="qnErr" role="alert"></p></form>';
 document.body.append(d);d.querySelector('#qnCancel').onclick=()=>d.close();
 d.querySelector('#qnSecForm').onsubmit=async e=>{e.preventDefault();const b=e.submitter||d.querySelector('button[type=submit]');b.disabled=true;try{await submit(new FormData(e.target));d.close()}catch(x){d.querySelector('#qnErr').textContent=errorText(x)}finally{b.disabled=false}};
 d.addEventListener('close',()=>d.remove());d.showModal();
}
const authButton=$('#authToggle');
if(authButton){
 const button=document.createElement('button');button.type='button';button.className='text-action';button.textContent='نسيت كلمة المرور؟';authButton.after(button);
 button.onclick=()=>modal('استعادة كلمة المرور','<label>البريد الإلكتروني<input name="email" type="email" autocomplete="email" required placeholder="example@school.edu.jo"></label>',async f=>{await call('/api/auth/forgot',{email:f.get('email')},false);alert('إذا كان البريد مسجلًا ستصلك رسالة استعادة. تحقق من مجلد البريد غير المرغوب فيه.')});
}
const resetCode=new URLSearchParams(location.search).get('reset');
if(resetCode){
 history.replaceState(null,'',location.pathname);
 setTimeout(()=>modal('إعادة تعيين كلمة المرور','<label>كلمة المرور الجديدة<input name="password" type="password" minlength="10" autocomplete="new-password" required></label>',async f=>{await call('/api/auth/reset',{token:resetCode,password:f.get('password')},false);alert('تم تغيير كلمة المرور. يمكنك تسجيل الدخول الآن.') }),200);
}
const nav=$('aside.sidebar nav'),main=$('main.main');
if(nav&&main){
 const button=document.createElement('button');button.type='button';button.className='nav';button.innerHTML='<span>🛡</span> حماية الحساب والنسخ';nav.append(button);
 const panel=document.createElement('section');panel.id='panel-security';panel.className='panel-view';
 panel.innerHTML='<div class="page-hero"><span class="kicker">ACCOUNT PROTECTION</span><h2>حماية الحساب والنسخ الاحتياطية</h2><p>إدارة كلمة المرور وحفظ واستعادة البيانات الخاصة بك.</p></div><div class="grid-two"><div class="pane"><h3>تغيير كلمة المرور</h3><form id="qnChangePass" class="student-form"><label>كلمة المرور الحالية<input name="old" type="password" autocomplete="current-password" required></label><label>كلمة المرور الجديدة<input name="next" type="password" minlength="10" autocomplete="new-password" required></label><button class="primary" type="submit">حفظ كلمة المرور</button></form></div><div class="pane"><h3>نسخ البيانات المحفوظة</h3><p>يُحتفظ بآخر 14 نسخة لكل معلم. النسخ التلقائي عند النشاط ولا يُغني عن النسخ الخارجية.</p><div class="qn-row"><button id="qnNewBackup" class="primary" type="button">إنشاء نسخة الآن</button><button id="qnRefreshBackup" class="secondary" type="button">تحديث القائمة</button></div><div id="qnBackups"></div></div></div><p id="qnSecNotice" role="status"></p>';
 main.append(panel);
 async function refresh(){
   const out=$('#qnBackups');out.textContent='جاري جلب النسخ...';
   try{
     const data=await call('/api/teacher/backups');out.replaceChildren();
     if(!data.backups.length){out.textContent='لا توجد نسخ محفوظة بعد.';return}
     for(const item of data.backups){
       const row=document.createElement('div');row.className='qn-backup';
       const when=document.createElement('span');when.textContent=new Date(item.created_at*1000).toLocaleString('ar-JO')+' · '+({manual:'يدوية',automatic:'تلقائية',before_restore:'قبل الاستعادة'}[item.reason]||item.reason);
       const restore=document.createElement('button');restore.type='button';restore.className='secondary';restore.textContent='استعادة';
       restore.onclick=()=>{
         if(!confirm('ستستبدل هذه النسخة بيانات معلمك الحالية، مع إنشاء نسخة إنقاذ قبل التعديل. هل توافق؟'))return;
         modal('تأكيد استعادة البيانات','<label>كلمة مرور حساب المعلم<input name="password" type="password" autocomplete="current-password" required></label>',async f=>{await call('/api/teacher/backups/restore',{backupId:item.id,password:f.get('password')});alert('تمت الاستعادة بنجاح. سيتم تحديث الصفحة.');location.reload()});
       };
       row.append(when,restore);out.append(row);
     }
   }catch(e){out.textContent=errorText(e)}
 }
 button.onclick=()=>{$$('.panel-view').forEach(e=>e.classList.toggle('active',e===panel));$$('button.nav').forEach(e=>e.classList.toggle('active',e===button));$('#pageTitle').textContent='حماية الحساب والنسخ';$('#pageDesc').textContent='إدارة كلمة المرور واستعادة بياناتك';refresh()};
 $('#qnNewBackup').onclick=async()=>{try{await call('/api/teacher/backups/create',{});await refresh();notice('تم إنشاء نسخة احتياطية')}catch(e){notice(errorText(e))}};
 $('#qnRefreshBackup').onclick=refresh;
 $('#qnChangePass').onsubmit=async e=>{
   e.preventDefault();const f=new FormData(e.target);
   try{await call('/api/auth/password',{oldPassword:f.get('old'),newPassword:f.get('next')});localStorage.removeItem('qn9_teacher_token');alert('تغيرت كلمة المرور وأُغلقت الجلسات السابقة. سجّل الدخول مجددًا.');location.assign('/')}
   catch(err){notice(errorText(err))}
 };
}
const css=document.createElement('style');
css.textContent='.qn-modal{background:linear-gradient(140deg,#073e69,#0875b6);border:1px solid #8edaff;border-radius:22px;padding:24px;width:min(440px,94vw);color:white;box-shadow:0 30px 100px #0009}.qn-modal::backdrop{background:#071b30bc}.qn-modal label{display:block;margin:14px 0}.qn-modal input{display:block;margin-top:8px;padding:13px;width:100%;border:1px solid #9fdfff;border-radius:12px;color:#052844;background:#effaff}.qn-modal #qnErr{color:#ffd0c9}.qn-row{display:flex;flex-wrap:wrap;gap:9px;margin:14px 0}.qn-backup{padding:11px;display:flex;align-items:center;justify-content:space-between;gap:12px;background:#094f8155;border:1px solid #6ecffa55;border-radius:12px;margin:8px 0}.qn-backup span{font-size:12px}.qn-backup button{flex-shrink:0}#qnSecNotice{color:#a4eeff}';
document.head.append(css);
})();