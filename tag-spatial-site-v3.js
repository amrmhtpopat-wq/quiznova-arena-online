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
 const current=[...document.querySelectorAll('img.tag-official-logo,.auth-brand img,.sidebar-brand img,.brand-logo img,.tag-brand-logo img')];
 if(!current.length)return;
 const test=new Image();
 test.onload=()=>{
  for(const img of current){
   if(!img.isConnected||img.classList.contains('tag-spatial-identity'))continue;
   // Product-install PWA icons are deliberately not interchangeable with a wordmark.
   if(/\/assets\/pwa\//i.test(img.getAttribute('src')||''))continue;
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
 // Render interactive 3D elements in the SAME document; never create an iframe,
 // extra storage context or replacement of the teacher app's handlers.
 const page=document.getElementById('panel-home');
 if(!page)return;
 const workspace=page.closest('#workspace');
 let host=null,loading=false,loaded=false;
 function visible(){
  return page.classList.contains('active')&&!document.hidden&&
    (!workspace||!workspace.classList.contains('hidden'));
 }
 function sync(){
  if(host)host.classList.toggle('tag-spatial-v3-paused',!visible());
  if(!visible()||loaded||loading)return;
  loading=true;
  fetch('/tag-spatial-native-v3.fragment.html?v=3',{credentials:'same-origin'})
   .then(res=>{if(!res.ok)throw Error('Workspace HTTP '+res.status);return res.text()})
   .then(markup=>{
    if(loaded||!page.isConnected)return;
    if(typeof window.TAGSpatialNativeInit!=='function')throw Error('Workspace initializer not loaded');
    host=document.createElement('div');host.className='tag-spatial-native-host';
    host.setAttribute('aria-label','مساحة المعلم التفاعلية TAG Spatial');
    const shadow=host.attachShadow({mode:'open'});
    const sheet=document.createElement('link');sheet.rel='stylesheet';
    sheet.href='/tag-spatial-native-v3.css?v=3';shadow.appendChild(sheet);
    const stage=document.createElement('div');stage.className='tag-spatial-native-stage';
    stage.dir='rtl';stage.innerHTML=markup;shadow.appendChild(stage);
    function arrange(){
     const quick=page.querySelector(':scope > .tag-v5-shortcuts');
     if(matchMedia('(max-width:650px)').matches&&quick) quick.after(host);
     else page.insertBefore(host,page.firstChild);
    }
    arrange();window.addEventListener('resize',arrange,{passive:true});
    page.classList.add('tag-spatial-native-active');
    try{window.TAGSpatialNativeInit(shadow,host);loaded=true;
      host.classList.toggle('tag-spatial-v3-paused',!visible());
    }catch(err){host.remove();host=null;page.classList.remove('tag-spatial-native-active');throw err}
   }).catch(err=>console.warn('[TAG Spatial] Safe legacy dashboard fallback:',err.message))
    .finally(()=>{loading=false});
 }
 if(window.MutationObserver){
  new MutationObserver(sync).observe(page,{attributes:true,attributeFilter:['class']});
  if(workspace)new MutationObserver(sync).observe(workspace,{attributes:true,attributeFilter:['class']});
 }
 document.addEventListener('visibilitychange',sync);
 document.querySelectorAll('[data-panel]').forEach(btn=>btn.addEventListener('click',()=>requestAnimationFrame(sync)));
 requestAnimationFrame(sync);
}
function enrichSurface(){
 const targets=document.querySelectorAll('.panel,.pane,.metric,.stat-card,.insight-card,.quiz-card');
 targets.forEach(el=>{
  if(el.closest('.tag-spatial-native-active')||el.closest('.tag-spatial-native-host'))return;
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