/* TAG LAB V40 — independent teacher login & registration using existing auth APIs. */
(()=>{'use strict';
const view=document.documentElement.dataset.tagAuth;
if(view!=='login'&&view!=='register')return;
const $=id=>document.getElementById(id);
const tokenKey='qn9_teacher_token';
const loginPath='/tag-lab-login.html',registerPath='/tag-lab-register.html';
const errors={
 email_taken:'هذا البريد الإلكتروني مسجل مسبقًا. استخدم تسجيل الدخول.',
 weak_password:'كلمة المرور يجب أن تتكوّن من 10 أحرف على الأقل.',
 invalid_email:'أدخل بريدًا إلكترونيًا صالحًا.',
 wrong_credentials:'البريد الإلكتروني أو كلمة المرور غير صحيحين.',
 invalid_credentials:'البريد الإلكتروني أو كلمة المرور غير صحيحين.',
 name_required:'أدخل اسم المعلم.',
 school_required:'أدخل اسم المدرسة.',
 subject_required:'أدخل اسم المبحث.',
 rate_limited:'تم تنفيذ محاولات كثيرة. حاول مجددًا بعد قليل.',
 login_required:'سجّل الدخول للمتابعة.',
 server_error:'تعذر إكمال الطلب حاليًا؛ حاول مجددًا.'
};
const params=new URLSearchParams(location.search);
function target(){
 const raw=params.get('next')||'/tag-lab-home.html';
 try{
  const url=new URL(raw,location.origin);
  if(url.origin!==location.origin)return '/tag-lab-home.html';
  if(!/^\/tag-lab-(home|games|books|create|library|mixer|assign|account|results|live-teacher|preview)\.html$/.test(url.pathname))
   return '/tag-lab-home.html';
  return url.pathname+url.search+url.hash
 }catch(_){return '/tag-lab-home.html'}
}
const next=target(),query=next!='/tag-lab-home.html'?'?next='+encodeURIComponent(next):'';
const link=$(view==='login'?'registerLink':'loginLink');
if(link)link.href=(view==='login'?registerPath:loginPath)+query;
for(const a of document.querySelectorAll('a[href="'+loginPath+'"],a[href="'+registerPath+'"]')){
 if(!a.id&&query)a.href=a.getAttribute('href')+query
}
function message(text,bad=false){
 const node=$('authStatus');
 node.textContent=text||'';
 node.className='auth-status'+(text?(bad?' error':' success'):'');
}
function busy(value){
 const btn=$('authSubmit');
 btn.disabled=value;
 btn.textContent=value?(view==='login'?'جارٍ تسجيل الدخول...':'جارٍ إنشاء الحساب...'):
                      (view==='login'?'دخول إلى TAG LAB':'إنشاء حساب TAG LAB')
}
function field(id){return $(id)?.value.trim()||''}
function showError(err){
 const name=String(err?.message||err||'server_error');
 message(errors[name]||'تعذر إكمال العملية الآن. تحقق من البيانات وحاول مجددًا.',true)
}
async function post(path,data){
 const res=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify(data),cache:'no-store'});
 const body=await res.json().catch(()=>({}));
 if(!res.ok||body.ok===false)throw Error(body.error||'server_error');
 if(!body.token||typeof body.token!=='string')throw Error('server_error');
 return body
}
async function checkExisting(){
 const token=localStorage.getItem(tokenKey)||'';
 if(!token)return;
 try{
  const res=await fetch('/api/auth/me',{headers:{Authorization:'Bearer '+token},cache:'no-store'});
  if(res.ok){const json=await res.json().catch(()=>({}));
   if(json.ok){location.replace(next);return}
  }
  if(res.status===401||res.status===403)localStorage.removeItem(tokenKey)
 }catch(_){/* A network outage never deletes the saved teacher session. */}
}
document.querySelectorAll('[data-toggle]').forEach(btn=>btn.addEventListener('click',()=>{
 const input=$(btn.dataset.toggle);
 if(!input)return;
 const reveal=input.type==='password';
 input.type=reveal?'text':'password';
 btn.textContent=reveal?'إخفاء':'إظهار';
 btn.setAttribute('aria-pressed',String(reveal));
 btn.setAttribute('aria-label',reveal?'إخفاء كلمة المرور':'إظهار كلمة المرور')
}));
$('authForm').addEventListener('submit',async e=>{
 e.preventDefault();
 if(!$('authForm').checkValidity())return $('authForm').reportValidity();
 message('');
 let payload;
 if(view==='register'){
  const password=$('password').value;
  if(password!==$('confirmPassword').value){
   message('تأكيد كلمة المرور غير مطابق.',true);
   $('confirmPassword').focus();return
  }
  payload={name:field('name'),school:field('school'),subject:field('subject'),
   email:field('email'),password};
 }else{
  payload={email:field('email'),password:$('password').value}
 }
 busy(true);
 try{
  const result=await post(view==='login'?'/api/auth/login':'/api/auth/register',payload);
  localStorage.setItem(tokenKey,result.token);
  $('password').value='';
  if(view==='register')$('confirmPassword').value='';
  message(view==='login'?'تم تسجيل الدخول. جارٍ فتح لوحة TAG LAB...':
   'تم إنشاء حسابك. جارٍ فتح لوحة TAG LAB...');
  location.replace(next)
 }catch(error){showError(error);busy(false)}
});
checkExisting()
})();
