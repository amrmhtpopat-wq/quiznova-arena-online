/* TAG Mobile V2 — keep TAG LAB in the regular browser when TAG is installed.
   Never redirect unauthenticated users or alter protected student session data.
   Browsers decide whether an external target opens Safari, Chrome or another tab. */
(function(){
 'use strict';
 const standalone=()=>window.matchMedia('(display-mode: standalone)').matches
   ||window.navigator.standalone===true;
 const labPath=p=>/^\/(?:tag-lab-[a-z0-9-]+|game-lab-[a-z0-9-]+)\.html$/i.test(p);
 function labURL(href){
  try{const u=new URL(href,location.href);return u.origin===location.origin&&labPath(u.pathname)?u:null}
  catch(_){return null}
 }
 function decorateLinks(){
  if(!standalone())return;
  document.querySelectorAll('a[href]').forEach(a=>{
   const url=labURL(a.getAttribute('href'));
   if(!url)return;
   a.target='_blank';
   a.rel='noopener noreferrer external';
   a.setAttribute('aria-label',(a.getAttribute('aria-label')||a.textContent.trim())+' — يفتح في المتصفح');
   a.setAttribute('data-tag-external-browser','true');
  });
  document.querySelectorAll('[data-tag-external-browser]').forEach(a=>{
    const text=a.querySelector('.desc');
    if(text&&!text.textContent.includes('يفتح في المتصفح'))text.textContent+=' · يفتح في المتصفح';
  });
 }
 // Mobile browsers allow new-window opening only when the user taps.
 // Capture allows dynamically inserted teacher/LAB links to use the same handoff.
 document.addEventListener('click',event=>{
  if(!standalone())return;
  const anchor=event.target.closest?.('a[href]');
  if(!anchor)return;
  if(labURL(anchor.getAttribute('href'))){
   anchor.target='_blank';
   anchor.rel='noopener noreferrer external';
   anchor.setAttribute('data-tag-external-browser','true');
  }
 },true);
 function directEntryFallback(){
  if(!standalone()||!labPath(location.pathname))return;
  const existing=document.getElementById('tag-lab-browser-handoff');
  if(existing)return;
  const container=document.createElement('section');
  container.id='tag-lab-browser-handoff';
  container.setAttribute('role','dialog');
  container.setAttribute('aria-modal','true');
  container.setAttribute('aria-label','فتح TAG LAB في المتصفح');
  container.style.cssText='position:fixed;inset:0;z-index:2147483000;background:#051931f4;color:white;display:grid;place-items:center;overflow:auto;padding:18px;text-align:center;direction:rtl;font-family:Tahoma,Arial,sans-serif';
  const box=document.createElement('div');
  box.style.cssText='width:min(100%,430px);padding:27px 21px;background:#104367;border:1px solid #78d9c7;border-radius:23px;box-shadow:0 20px 55px #0008;line-height:1.8';
  const img=document.createElement('img');img.src='/assets/pwa/tag-192.png';img.width=82;img.height=82;img.alt='TAG';img.style.cssText='margin:0 auto 12px;display:block;max-width:100%';
  const title=document.createElement('h1');title.textContent='افتح TAG LAB في المتصفح';title.style.cssText='font-size:22px;margin:0 0 9px;color:#eaffd4';
  const desc=document.createElement('p');desc.textContent='مختبر الألعاب يعمل بواجهة أفضل في Chrome أو Safari خارج تطبيق TAG. اضغط الزر لفتح الصفحة في المتصفح.';desc.style.cssText='font-size:14px;margin:0 0 19px;color:#d8edfa';
  const link=document.createElement('a');link.textContent='🌐 فتح المختبر في المتصفح';
  link.href=location.href;link.target='_blank';link.rel='noopener noreferrer external';
  link.style.cssText='display:block;background:#80e457;color:#12371d;font-weight:900;border-radius:13px;text-decoration:none;padding:13px;margin-bottom:10px';
  const copy=document.createElement('button');copy.type='button';copy.textContent='📋 نسخ رابط المختبر';
  copy.style.cssText='display:block;width:100%;background:#ffffff14;color:white;border:1px solid #ffffff66;border-radius:13px;padding:12px;font:inherit;margin-bottom:10px';
  const back=document.createElement('a');back.textContent='العودة إلى تطبيق TAG';back.href='/app.html';
  back.style.cssText='display:block;color:#d1eefa;padding:9px;font-weight:800';
  copy.onclick=async()=>{
   try{await navigator.clipboard.writeText(location.href);copy.textContent='✓ تم نسخ الرابط — افتحه في المتصفح'}
   catch(_){copy.textContent='انسخ الرابط من شريط العنوان أو افتحه من مشاركة التطبيق'}
  };
  box.append(img,title,desc,link,copy,back);container.appendChild(box);
  document.body.prepend(container);
  link.focus();
 }
 function init(){decorateLinks();directEntryFallback()}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});
 else init();
})();
