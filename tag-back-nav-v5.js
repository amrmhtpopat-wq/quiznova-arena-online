/* TAG BACK NAV V5. Accessible, history-aware and fallback-safe.
   Does not mutate quiz/game state, routes or authentication handlers. */
(()=>{'use strict';
 if(window.TAGGoBack)return;
 const loc=()=>location.pathname.split('/').pop().toLowerCase();
 const paths={
  'studio.html':'/?teacher=1','champion.html':'/?teacher=1','champion-board.html':'/champion.html',
  'admin.html':'/','student.html':'/','stage.html':'/studio.html#live',
  'game-lab-preview.html':'/tag-lab-home.html',
  'tag-lab-home.html':'/?teacher=1',
  'app.html':'/','about.html':'/','for-teachers.html':'/'
 };
 const fallback=()=>loc().startsWith('tag-lab-')?'/tag-lab-home.html':(loc().startsWith('game-lab-')?'/game-lab-preview.html':(paths[loc()]||'/'));
 const go=()=>{
  let previous=null;
  try{previous=document.referrer?new URL(document.referrer):null}catch(e){}
  // Do not navigate backwards off-site, into a login provider or back into
  // this same route. Direct links always land at a meaningful local page.
  if(previous&&previous.origin===location.origin&&
     (previous.pathname!==location.pathname||previous.search!==location.search||
      previous.hash!==location.hash)&&history.length>1){
   history.back();return;
  }
  location.assign(fallback());
 };
 window.TAGGoBack=go;
 const esc='<svg aria-hidden="true" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/><path d="M9 12h11"/></svg>';
 function make(){
  const b=document.createElement('button');b.type='button';
  b.className='tag-back-nav';b.setAttribute('aria-label','العودة إلى الصفحة السابقة');
  b.setAttribute('title','رجوع');b.innerHTML=esc+'<span>رجوع</span>';
  b.addEventListener('click',go);return b;
 }
 function install(){
  if(document.querySelector('.tag-back-nav'))return;
  // The root public page is the natural navigation origin; avoid a redundant
  // button overlay on its three student entry points.
  const file=loc(),portalRoot=file===''||file==='index.html';
  if(portalRoot)return;
  const b=make();let dest=null;
  if(file==='champion.html'||file==='champion-board.html')dest=document.querySelector('header.top .head-actions');
  else if(file==='studio.html')dest=document.querySelector('#app header.topbar .topbar-actions,#app header.topbar');
  else if(file==='student.html')dest=document.querySelector('.student-brand');
  else if(file==='app.html')dest=document.querySelector('header.top');
  else if(file==='about.html')dest=document.querySelector('header nav');
  else if(file==='for-teachers.html')dest=document.querySelector('header.site-header .nav-wrap');
  // TAG LAB/game pages have responsive sliding menu rails. A header child
  // can end up translated outside the viewport; keep back fixed in the safe area.
  else if(file.startsWith('tag-lab-')||file.startsWith('game-lab-'))dest=null;
  else if(file==='tag-spatial-home-v3.html')dest=document.querySelector('header.header .header-actions');
  else if(file==='admin.html')dest=null; // login-visible back control, retained after authentication
  // An app can render a toolbar inside a hidden authenticated panel.
  // In that case keep the back control visible on its public sign-in screen.
  if(dest&&!dest.getClientRects().length)dest=null;
  if(dest){
   b.classList.add('tag-back-nav--inline');dest.appendChild(b);
  }else{
   b.classList.add('tag-back-nav--floating');document.body.appendChild(b);
  }
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});
 else install();
})();
