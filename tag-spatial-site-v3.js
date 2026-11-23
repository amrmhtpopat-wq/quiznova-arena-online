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
 if(!page||page.querySelector('iframe.tag-spatial-host'))return;
 const iframe=document.createElement('iframe');
 iframe.className='tag-spatial-host';
 iframe.title='مساحة عمل المعلم ثلاثية الأبعاد — TAG Spatial';
 iframe.loading='lazy';
 iframe.referrerPolicy='same-origin';
 iframe.setAttribute('allow','fullscreen');
 iframe.setAttribute('scrolling','no');
 iframe.dataset.src='/tag-spatial-home-v3.html';
 iframe.style.height='1250px';
 page.insertBefore(iframe,page.firstChild);
 page.classList.add('tag-spatial-embedded');
 let lastHeight=1250;
 function visible(){
  const parent=iframe.closest('#workspace');
  return (!parent||!parent.classList.contains('hidden'))&&page.classList.contains('active')
    &&document.visibilityState==='visible';
 }
 function sync(){
  const isVisible=visible();
  if(isVisible&&!iframe.src.includes('tag-spatial-home-v3.html'))iframe.src=iframe.dataset.src;
  if(iframe.contentWindow&&iframe.src!=='about:blank'){
   iframe.contentWindow.postMessage({type:'tag-spatial-v3-visibility',visible:isVisible},location.origin);
  }
 }
 iframe.addEventListener('load',sync);
 const onSize=e=>{
  if(e.origin!==location.origin||e.source!==iframe.contentWindow)return;
  if(!e.data||e.data.type!=='tag-spatial-v3-size')return;
  const height=Number(e.data.height);
  if(!Number.isFinite(height)||height<400||height>9000)return;
  const next=Math.ceil(height+4);
  if(Math.abs(next-lastHeight)<4)return;
  lastHeight=next;
  iframe.style.height=next+'px';
 };
 window.addEventListener('message',onSize);
 if(window.MutationObserver){
  new MutationObserver(sync).observe(page,{attributes:true,attributeFilter:['class']});
  const parent=iframe.closest('#workspace');
  if(parent)new MutationObserver(sync).observe(parent,{attributes:true,attributeFilter:['class']});
 }
 document.addEventListener('visibilitychange',sync);
 const navButtons=[...document.querySelectorAll('[data-view],[data-panel]')];
 navButtons.forEach(b=>b.addEventListener('click',()=>requestAnimationFrame(sync)));
 sync();
}
function enrichSurface(){
 const targets=document.querySelectorAll('.panel,.pane,.metric,.stat-card,.insight-card,.quiz-card');
 targets.forEach(el=>{
  if(el.closest('.tag-spatial-embedded')||el.closest('.tag-spatial-host'))return;
  el.classList.add('tag-spatial-surface');
 });
}
function start(){
 installIdentity();
 mountHub();
 enrichSurface();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});
else start();
})();