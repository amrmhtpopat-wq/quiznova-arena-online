/* TAG LAB V40 — teacher-page navigation guard; student/play links stay public. */
(()=>{'use strict';
if(!document.documentElement.dataset.tagView&&
 !/^\/tag-lab-(home|account|assign|results|live-teacher)\.html$/.test(location.pathname))return;
const key='qn9_teacher_token';
const restricted=/^\/tag-lab-(home|games|books|create|library|mixer|assign|account|results|live-teacher)\.html$/;
if(!restricted.test(location.pathname))return;
const dest='/tag-lab-login.html?next='+encodeURIComponent(location.pathname+location.search+location.hash);
const token=localStorage.getItem(key)||'';
if(!token){location.replace(dest);return}
const style=document.createElement('style');style.id='tagLabGuardWaiting';
style.textContent='html.tag-lab-auth-check body{visibility:hidden!important}';
document.head.append(style);
document.documentElement.classList.add('tag-lab-auth-check');
function show(){document.documentElement.classList.remove('tag-lab-auth-check');style.remove()}
fetch('/api/auth/me',{headers:{Authorization:'Bearer '+token},cache:'no-store'})
 .then(async response=>{
  if(response.status===401||response.status===403){
   localStorage.removeItem(key);location.replace(dest);return
  }
  if(!response.ok){show();return}
  const data=await response.json();
  if(!data.ok){localStorage.removeItem(key);location.replace(dest);return}
  show()
 }).catch(show);
})();
