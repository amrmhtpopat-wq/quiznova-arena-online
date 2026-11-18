/* TAG PWA V1 — opt-in installation UI, no auth data or exam storage. */
(function(){
 'use strict';
 let installPrompt=null;
 const $=id=>document.getElementById(id);
 const isStandalone=()=>window.matchMedia('(display-mode: standalone)').matches||window.navigator.standalone===true;
 const isIOS=/iPad|iPhone|iPod/.test(navigator.userAgent)||(/Macintosh/.test(navigator.userAgent)&&navigator.maxTouchPoints>1);
 function info(){
  const note=$('tagInstallStatus');
  if(!note)return;
  if(isStandalone()){note.textContent='تطبيق TAG مثبت ويعمل بوضع التطبيق.';return;}
  if(isIOS()){note.textContent='على الآيفون: افتح الرابط في Safari ثم اضغط مشاركة ← إضافة إلى الشاشة الرئيسية ← إضافة.';return;}
  if(installPrompt){note.textContent='التطبيق جاهز للتثبيت. اضغط تثبيت TAG.';return;}
  note.textContent='على أندرويد: افتح الرابط في Chrome، ثم القائمة ⋮ ← تثبيت التطبيق أو إضافة إلى الشاشة الرئيسية.';
 }
 function update(){
  document.querySelectorAll('[data-tag-install]').forEach(b=>{
   b.hidden=isStandalone();
   b.textContent=installPrompt?'⬇ تثبيت TAG على الجهاز':'📲 طريقة تثبيت TAG';
  });
  const guide=$('tagInstallGuide');
  if(guide)guide.hidden=isStandalone();
  info();
 }
 window.addEventListener('beforeinstallprompt',event=>{
  event.preventDefault();installPrompt=event;update();
 });
 window.addEventListener('appinstalled',()=>{
  installPrompt=null;update();
  const note=$('tagInstallStatus');if(note)note.textContent='تم تثبيت TAG بنجاح.';
 });
 async function install(){
  if(installPrompt){
   const prompt=installPrompt;installPrompt=null;
   try{await prompt.prompt();await prompt.userChoice;}catch(_){}
   update();return;
  }
  const guide=$('tagInstallGuide');
  if(guide){guide.hidden=false;guide.scrollIntoView({behavior:'smooth',block:'nearest'});}
  info();
 }
 function init(){
  document.querySelectorAll('[data-tag-install]').forEach(b=>b.addEventListener('click',install));
  update();
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
 if('serviceWorker' in navigator&&window.isSecureContext){
  window.addEventListener('load',()=>{
   navigator.serviceWorker.register('/sw.js',{scope:'/',updateViaCache:'none'})
     .catch(()=>{/* Do not block login or classroom quizzes if SW is unsupported. */});
  },{once:true});
 }
})();
