/* TAG Studio Navigation V6 — accessible group navigation and reliable mobile drawer.
 * The application retains its 10 original view IDs and normal go() handler.
 * Only visual organization / focus / responsive controls live here.
 */
(function(){
'use strict';
function setup(){
 const sidebar=document.getElementById('sidebar');
 const opener=document.getElementById('menuBtn');
 const closer=document.getElementById('mobileCloseNav');
 const backdrop=document.getElementById('tagStudioNavBackdrop');
 const nav=sidebar&&sidebar.querySelector('.tag-studio-nav-v6');
 if(!sidebar||!opener||!closer||!backdrop||!nav)return;
 const mq=window.matchMedia('(max-width:1024px)');
 const groups=Array.from(nav.querySelectorAll('.tag-studio-nav-group'));
 function activeGroup(){
  const selected=nav.querySelector('.nav-item.active[data-view]');
  const group=selected&&selected.closest('.tag-studio-nav-group');
  return group||groups[0]||null;
 }
 function groupState(group,expanded){
  group.classList.toggle('is-expanded',expanded);
  const button=group.querySelector('.tag-studio-group-toggle');
  if(button)button.setAttribute('aria-expanded',String(expanded));
 }
 function syncGroups(){
  const active=activeGroup();
  groups.forEach(group=>groupState(group,!mq.matches||group===active));
 }
 function setOpen(requested,returnFocus){
  const next=Boolean(requested&&mq.matches);
  sidebar.classList.toggle('open',next);
  document.body.classList.toggle('tag-studio-nav-open',next);
  document.documentElement.classList.toggle('tag-studio-html-lock',next);
  backdrop.hidden=!next;
  opener.setAttribute('aria-expanded',String(next));
  opener.setAttribute('aria-label',next?'إغلاق قائمة أقسام استوديو TAG':'فتح قائمة أقسام استوديو TAG');
  // Inert prevents tabbing or screen-reader access to a closed off-screen drawer.
  sidebar.inert=Boolean(mq.matches&&!next);
  if(next){
   syncGroups();
   closer.focus({preventScroll:true});
  }else if(returnFocus&&mq.matches){
   opener.focus({preventScroll:true});
  }
 }
 // Replace the old bare class toggle with a complete drawer state transition.
 opener.onclick=function(){setOpen(!sidebar.classList.contains('open'),false)};
 closer.onclick=function(){setOpen(false,true)};
 backdrop.addEventListener('click',function(){setOpen(false,true)});
 groups.forEach(group=>{
  const toggle=group.querySelector('.tag-studio-group-toggle');
  if(!toggle)return;
  toggle.addEventListener('click',function(){
   if(!mq.matches)return;
   const wasExpanded=group.classList.contains('is-expanded');
   groups.forEach(g=>groupState(g,false));
   groupState(group,!wasExpanded);
  });
 });
 nav.addEventListener('click',function(event){
  const selected=event.target.closest('.nav-item[data-view],.tag-studio-external-link');
  if(!selected)return;
  if(selected.matches('.nav-item[data-view]')){
   const group=selected.closest('.tag-studio-nav-group');
   if(group)groups.forEach(g=>groupState(g,!mq.matches||g===group));
  }
  if(mq.matches)setOpen(false,true);
 });
 document.addEventListener('keydown',function(event){
  if(!mq.matches||!sidebar.classList.contains('open'))return;
  if(event.key==='Escape'){
   event.preventDefault();setOpen(false,true);return;
  }
  if(event.key!=='Tab')return;
  const focusable=Array.from(sidebar.querySelectorAll('a[href],button:not([disabled])'))
   .filter(el=>el.getClientRects().length>0&&getComputedStyle(el).visibility!=='hidden');
  if(!focusable.length)return;
  const first=focusable[0],last=focusable[focusable.length-1];
  if(event.shiftKey&&(document.activeElement===first||!sidebar.contains(document.activeElement))){
   event.preventDefault();last.focus({preventScroll:true});
  }else if(!event.shiftKey&&(document.activeElement===last||!sidebar.contains(document.activeElement))){
   event.preventDefault();first.focus({preventScroll:true});
  }
 });
 function refreshForBreakpoint(){
  setOpen(false,false);
  syncGroups();
 }
 if(typeof mq.addEventListener==='function')mq.addEventListener('change',refreshForBreakpoint);
 else if(typeof mq.addListener==='function')mq.addListener(refreshForBreakpoint);
 // An authenticated deep-link should select its corresponding page group.
 window.addEventListener('hashchange',function(){if(!sidebar.classList.contains('open'))syncGroups()});
 refreshForBreakpoint();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',setup,{once:true});
else setup();
})();
