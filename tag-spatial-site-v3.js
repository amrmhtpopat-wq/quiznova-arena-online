/* TAG Spatial V3 — additive integration only. No login, API, student PIN, DB,
 * quiz, grading, game or printing functions are replaced.
 * Does not load on TAG LAB or CHAMPION TAG.
 */
(()=>{'use strict';
const excluded=/^(champion|tag-lab|game-lab|tag-independent)/i;
const here=(location.pathname.split('/').pop()||'index.html').toLowerCase();
if(excluded.test(here)||!document.body.classList.contains('tag-spatial-global'))return;
const ART='/assets/brand/tag-spatial-identity-v3.webp';
function installIdentity(){
 const current=[...document.querySelectorAll('img.tag-official-logo,.auth-brand img,.sidebar-brand img,.brand-logo img,header .brand img,.tag-brand-logo img')];
 if(!current.length)return;
 const test=new Image();
 test.onload=()=>{
  for(const img of current){
   if(!img.isConnected||img.classList.contains('tag-spatial-identity'))continue;
   img.dataset.tagOldLogo=img.getAttribute('src')||'';
   img.src=ART;
   img.removeAttribute('srcset');
   img.classList.add('tag-spatial-identity');
   img.style.objectFit='contain';
  }
 };
 test.onerror=()=>{document.documentElement.classList.add('tag-spatial-logo-fallback');};
 test.src=ART;
}
function mountHub(){
 const page=document.getElementById('panel-home')||document.getElementById('view-dashboard');
 if(!page)return;
 // Only construct a browsing context when the teacher actually opens the
 // dashboard. Eager insertion creates transient about:blank frames and breaks
 // storage-secure contexts (including real browser/teacher tests).
 let iframe=null,lastHeight=1250;
 const studio=page.id==='view-dashboard';
 const workspace=page.closest('#workspace');
 function visible(){
  if(!page.classList.contains('active')||document.visibilityState==='hidden')return false;
  if(workspace&&workspace.classList.contains('hidden'))return false;
  // The editor's HTML briefly marks dashboard active before deep-link routing.
  if(studio&&location.hash&&location.hash!=='#dashboard'&&location.hash!=='#home')return false;
  return true;
 }
 function sendVisibility(){
  if(!iframe||!iframe.contentWindow||iframe.src==='about:blank')return;
  iframe.contentWindow.postMessage({type:'tag-spatial-v3-visibility',visible:visible()},location.origin);
 }
 function sync(){
  if(!visible()){sendVisibility();return;}
  if(!iframe){
   iframe=document.createElement('iframe');
   iframe.className='tag-spatial-host';
   iframe.title='مساحة عمل المعلم ثلاثية الأبعاد — TAG Spatial';
   iframe.loading='lazy';
   iframe.referrerPolicy='same-origin';
   iframe.setAttribute('allow','fullscreen');
   iframe.setAttribute('scrolling','no');
   iframe.style.height=lastHeight+'px';
   iframe.addEventListener('load',sendVisibility);
   iframe.src='/tag-spatial-home-v3.html';
   page.insertBefore(iframe,page.firstChild);
   page.classList.add('tag-spatial-embedded');
  }
  sendVisibility();
 }
 window.addEventListener('message',e=>{
  if(!iframe||e.origin!==location.origin||e.source!==iframe.contentWindow)return;
  if(!e.data||e.data.type!=='tag-spatial-v3-size')return;
  const height=Number(e.data.height);
  if(!Number.isFinite(height)||height<400||height>9000)return;
  const next=Math.ceil(height+4);
  if(Math.abs(next-lastHeight)<4)return;
  lastHeight=next;
  iframe.style.height=next+'px';
 });
 if(window.MutationObserver){
  new MutationObserver(sync).observe(page,{attributes:true,attributeFilter:['class']});
  if(workspace)new MutationObserver(sync).observe(workspace,{attributes:true,attributeFilter:['class']});
 }
 document.addEventListener('visibilitychange',sync);
 window.addEventListener('hashchange',sync);
 document.querySelectorAll('[data-view],[data-panel]').forEach(b=>
  b.addEventListener('click',()=>requestAnimationFrame(sync)));
 // Initial check is intentionally postponed until the original app initialized its route.
 requestAnimationFrame(sync);
}
function enrichSurface(){
 const targets=document.querySelectorAll('.panel,.pane,.metric,.stat-card,.insight-card,.quiz-card');
 targets.forEach(el=>{
  if(el.closest('.tag-spatial-embedded')||el.closest('.tag-spatial-host'))return;
  el.classList.add('tag-spatial-surface');
 });
}
function spatialHeadings(){
 const names={
  dashboard:['00 / WORKSPACE','مساحة المعلم'],generator:['01 / INTELLIGENCE','TAG AI'],
  builder:['02 / DESIGN STUDIO','صناعة الاختبار'],bank:['03 / QUESTION VAULT','بنك الأسئلة'],
  library:['04 / KNOWLEDGE INDEX','المكتبة'],media:['05 / MEDIA','الوسائط'],
  live:['06 / CLASSROOM ON AIR','الصف المباشر'],play:['07 / SOLO MODE','التحدي الفردي'],
  results:['08 / LEARNING SIGNALS','النتائج والتحليل'],settings:['09 / PERSONAL SPACE','إعدادات المعلم'],
  classes:['CLASS WARS','الشعب'],mastery:['SKILL ATLAS','المهارات'],
  students:['SMART STUDENT ID','بطاقات الطلاب'],history:['ACTIVITY LOG','السجل'],
  school:['SCHOOL SETTINGS','إعدادات المدرسة']
 };
 document.querySelectorAll('.view[id^="view-"],.panel-view[id^="panel-"]').forEach(panel=>{
  const key=panel.id.replace(/^(view|panel)-/,'');
  if(key==='dashboard'||key==='home')return;
  const detail=names[key];if(!detail||panel.querySelector(':scope > .tag-spatial-titleline'))return;
  const el=document.createElement('div');
  el.className='tag-spatial-titleline';el.setAttribute('aria-hidden','true');
  el.innerHTML='<span class="tag-spatial-titleline-code"></span><span class="tag-spatial-titleline-rule"></span><span class="tag-spatial-titleline-label"></span>';
  el.querySelector('.tag-spatial-titleline-code').textContent='TAG / '+detail[0];
  el.querySelector('.tag-spatial-titleline-label').textContent=detail[1];
  panel.prepend(el);
 });
}
function start(){
 installIdentity();
 mountHub();
 enrichSurface();
 spatialHeadings();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});
else start();
})();