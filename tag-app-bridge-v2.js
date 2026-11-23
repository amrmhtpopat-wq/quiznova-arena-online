/* TAG V26: all first-party pages, including TAG LAB, stay in the installed app.
 * No forced _blank, external browser handoff or full-screen blocker.
 * The default same-origin /tag-lab-*.html route preserves authentication,
 * PWA scope, browser history and student card session. */
(()=>{'use strict';
 const isLabPath=path=>/^\/(?:tag-lab-[a-z0-9-]+|game-lab-[a-z0-9-]+)\.html$/i.test(path);
 const firstPartyLab=href=>{try{const target=new URL(href,location.href);return target.origin===location.origin&&isLabPath(target.pathname)}catch{return false}};
 function normalize(anchor){
  if(!anchor||!firstPartyLab(anchor.getAttribute('href')))return;
  // Do not let PWA route this page to an external tab/window.
  anchor.removeAttribute('target');
  anchor.removeAttribute('data-tag-external-browser');
  anchor.setAttribute('rel','');
  if(anchor.getAttribute('data-tag-lab-entry')==='external')anchor.setAttribute('data-tag-lab-entry','internal');
  let desc=anchor.querySelector('.desc');
  if(desc)desc.textContent=desc.textContent.replace(/يفتح في المتصفح الخارجي|يفتح في المتصفح|·\s*يفتح في المتصفح/g,'يفتح داخل تطبيق TAG');
  const label=anchor.getAttribute('aria-label');
  if(label)anchor.setAttribute('aria-label',label.replace(' — يفتح في المتصفح',''));
 }
 function init(){
  document.querySelectorAll('a[href]').forEach(normalize);
  // Navigation cards are dynamically inserted by the teacher spatial dashboard.
  document.addEventListener('click',e=>{
   const a=e.target.closest?.('a[href]');
   if(a)normalize(a);
  },true);
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
