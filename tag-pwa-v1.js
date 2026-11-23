/* TAG PWA V1 — opt-in installation UI, no auth data or exam storage. */
(function(){
 'use strict';
 let installPrompt=null;
 const $=id=>document.getElementById(id);
 const isStandalone=()=>window.matchMedia('(display-mode: standalone)').matches||window.navigator.standalone===true;
 const isIOS=()=>/iPad|iPhone|iPod/.test(navigator.userAgent)||(/Macintosh/.test(navigator.userAgent)&&navigator.maxTouchPoints>1);
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

/* TAG V26 canonical navigation. The public homepage is a static landing;
   the existing teacher dashboard therefore lives at /portal.html. Applied
   ONLY on teachgame.onrender.com so printed QR and old-domain links remain usable.
   Uses href changes only: does not touch auth, API, localStorage or student PIN. */
(function(){
 'use strict';
 if(location.hostname!=='teachgame.onrender.com')return;
 const oldHost='quiznova-arena-online.onrender.com';
 const origin=location.origin;
 function clean(raw){
  if(!raw||raw[0]==='#'||/^(?:javascript:|mailto:|tel:|data:)/i.test(raw))return null;
  let url;
  try{url=new URL(raw,location.href)}catch{return null}
  if(url.hostname===oldHost&&url.protocol==='https:'){
   url.hostname='teachgame.onrender.com';
  }else if(url.origin!==origin)return null;
  if(url.pathname==='/'||url.pathname==='/index.html'){
   url.pathname='/portal.html';
   if(!url.searchParams.has('teacher'))url.searchParams.set('teacher','1');
  }
  if(url.origin!==origin)return null;
  return url.pathname+url.search+url.hash;
 }
 function fix(a){
  if(!a?.getAttribute)return;
  const raw=a.getAttribute('href');
  const dest=clean(raw);
  if(dest&&dest!==raw)a.setAttribute('href',dest);
 }
 function go(){
  document.querySelectorAll('a[href]').forEach(fix);
  document.addEventListener('click',e=>{const link=e.target.closest?.('a[href]');if(link)fix(link)},true);
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',go,{once:true});else go();
})();
