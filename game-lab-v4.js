/* BOOYAHJO GAME LAB v4: original Wordwall-like create → content → play flow.
   Purely presentation / navigation; all existing Game Lab scripts and APIs stay intact. */
(()=>{
 'use strict';
 const $=id=>document.getElementById(id);
 const doc=document;
 const ids=['catalog','builder','bookLab','mixer','library','cloud','studentAssignments','liveLab'];
 const choices={
  quiz:'مسابقة',fast:'سباق الوقت',pairs:'مطابقة',flash:'بطاقات الذاكرة',wheel:'عجلة الحظ',
  boxes:'صناديق مفاجآت',sort:'فرز وتصنيف',truth:'صح أم خطأ',crossword:'كلمات متقاطعة',
  wordsearch:'البحث عن الكلمات',anagram:'ترتيب الحروف',order:'رتّب الخطوات',maze:'المتاهة',
  balloons:'فرقعة البالونات',memory:'لعبة الذاكرة',hidden:'الصورة المخفية',
  cloze:'أكمل الفراغ',diagram:'تسمية الرسم',board:'لوحة النقاط',teams:'معركة الفرق',
  survey:'التصويت',exit:'بطاقة الخروج',story:'اختر المسار',bingo:'بينغو'
 };
 let template='quiz';
 const storageKey='booyahjo_game_lab_display';
 function go(id){
  const target=$(id);
  if(!target)return;
  target.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});
  doc.querySelectorAll('[data-jump]').forEach(node=>node.classList.toggle('sel',node.dataset.jump===id));
  $('rail')?.classList.remove('open');$('shade')?.classList.remove('show');
  if(history.replaceState&&ids.includes(id))history.replaceState(null,'','#'+id);
 }
 function clickable(tag,cls,label,cb){
  const b=doc.createElement(tag);b.className=cls;b.textContent=label;
  if(tag==='button')b.type='button';
  b.addEventListener('click',cb);
  return b;
 }
 function quickIcon(emoji){const el=doc.createElement('span');el.className='v4-quick-icon';el.textContent=emoji;el.setAttribute('aria-hidden','true');return el}
 function quickCard(icon,title,desc,where){
  const b=clickable('button','v4-quick-card','',()=>go(where));
  const content=doc.createElement('span');
  const strong=doc.createElement('strong');strong.textContent=title;
  const sub=doc.createElement('small');sub.textContent=desc;
  content.append(strong,sub);b.append(quickIcon(icon),content);
  return b;
 }
 function enhanceHero(){
  const mast=doc.querySelector('.mast');
  const quick=$('v4QuickStart');
  if(mast&&quick){
   quick.replaceChildren(
    quickCard('🎨','اختر لعبة جاهزة','24 قالبًا ممتعًا قابلًا للتجربة','catalog'),
    quickCard('📚','حوّل كتابك إلى نشاط','ارفع PDF أو عدّل الأسئلة بنفسك','bookLab'),
    quickCard('📡','ابدأ حصة مباشرة','رمز جلسة ومنافسة بين الطلاب','liveLab')
   );
  }
 }
 function markTemplate(mode){
  template=mode;
  const select=$('cloudMode');
  if(select&&Array.from(select.options).some(o=>o.value===mode))select.value=mode;
  const label=$('v4ChosenTemplate');
  if(label)label.textContent='القالب المحدد: '+(choices[mode]||mode)+' — عدّل أسئلتك ثم اضغط تجربة.';
  doc.querySelectorAll('#gameGrid .game').forEach(card=>card.classList.toggle('v4-selected',card.dataset.gameMode===mode));
 }
 function updateCards(){
  const cards=doc.querySelectorAll('#gameGrid .game');
  cards.forEach(card=>{
   if(card.dataset.v4Enhanced)return;
   card.dataset.v4Enhanced='1';
   // The catalog's original Play button is intentionally preserved.
   const launch=card.querySelector('button.button');
   if(!launch)return;
   const index=[...card.parentNode.children].indexOf(card);
   const label=card.querySelector('h3')?.textContent?.trim()||'قالب';
   const mode=Object.keys(choices).find(x=>choices[x]===label)
     ||(
       // The original catalog always renders in its known deterministic order
       // before the optional search/filter changes the visible subset. ID mapping
       // is resolved from the card title when possible, never from filtered index.
       ({'تحدي الاختيار':'quiz','سباق الوقت':'fast','توصيل الأزواج':'pairs','بطاقات الذاكرة':'flash',
        'عجلة الحظ':'wheel','الصناديق الغامضة':'boxes','فرز وتصنيف':'sort','صح أم خطأ؟':'truth',
        'الكلمات المتقاطعة':'crossword','البحث عن الكلمات':'wordsearch','ترتيب الحروف':'anagram',
        'الترتيب المنطقي':'order','المتاهة':'maze','فرقعة البالونات':'balloons','لعبة الذاكرة':'memory',
        'الصورة المخفية':'hidden','أكمل الفراغ':'cloze','تسمية الرسم':'diagram',
        'لوحة نقاط':'board','معركة الفرق':'teams','استطلاع':'survey',
        'بطاقة الخروج':'exit','اختر مسارك':'story','بينغو':'bingo'})[label]
      );
   if(!mode)return;
   card.dataset.gameMode=mode;
   const controls=doc.createElement('div');controls.className='buttons';
   const create=clickable('button','button v4-use-template','✏️ أنشئ بهذا القالب',()=>{
    markTemplate(mode);go('builder');$('activityTitle')?.focus({preventScroll:true});
   });
   launch.textContent='▶ جرّب';
   launch.setAttribute('aria-label','تجربة '+label);
   create.setAttribute('aria-label','إنشاء نشاط جديد بقالب '+label);
   launch.replaceWith(controls);controls.append(launch,create);
   card.querySelector('.state')?.setAttribute('title','قالب تفاعلي متاح للتجربة');
  });
  const counter=$('resultCount');
  if(counter)counter.setAttribute('aria-live','polite');
 }
 function start(){
  doc.body.classList.add('game-lab-v4');
  enhanceHero();
  const grid=$('gameGrid');
  if(grid){
   updateCards();
   const observer=new MutationObserver(()=>updateCards());
   observer.observe(grid,{childList:true});
  }
  const themeButton=$('v4ThemeToggle');
  function setTheme(theme){
   doc.body.dataset.labTheme=theme;
   if(themeButton){
    themeButton.textContent=theme==='projector'?'☀️ الوضع المريح':'◐ وضع العرض عالي التباين';
    themeButton.setAttribute('aria-pressed',String(theme==='projector'));
   }
  }
  let savedTheme='comfort';
  try{savedTheme=localStorage.getItem(storageKey)==='projector'?'projector':'comfort'}catch(_){}
  setTheme(savedTheme);
  themeButton?.addEventListener('click',()=>{
   const next=doc.body.dataset.labTheme==='projector'?'comfort':'projector';
   setTheme(next);
   try{localStorage.setItem(storageKey,next)}catch(_){}
  });
  const top=$('v4BackToTop');
  const updateTop=()=>top?.classList.toggle('shown',scrollY>950);
  addEventListener('scroll',updateTop,{passive:true});
  updateTop();
  top?.addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));
  const apply=$('applyContent');
  apply?.addEventListener('click',()=>{
   const el=$('v4ChosenTemplate');
   if(el)el.textContent='تم تجهيز المحتوى. القالب المختار: '+(choices[template]||'المسابقة')+'. يمكنك التجربة أو حفظه في مكتبتك.';
  });
  $('v4TrySelected')?.addEventListener('click',()=>{
   const card=doc.querySelector('#gameGrid .game[data-game-mode="'+template+'"]');
   if(card){card.querySelector('.button:not(.v4-use-template)')?.click();}
   else{
    $('gameSearch').value='';$('gradeFilter').value='all';
    doc.querySelector('#filterBar [data-category="all"]')?.click();
    requestAnimationFrame(()=>doc.querySelector('#gameGrid .game[data-game-mode="'+template+'"] .button:not(.v4-use-template)')?.click());
   }
  });
  $('v4SaveSelected')?.addEventListener('click',()=>{
    const select=$('cloudMode');
    if(select&&[...select.options].some(o=>o.value===template))select.value=template;
    go('cloud');
    if($('cloudSave')&&!$('cloudWorkspace')?.classList.contains('hide'))$('cloudSave').focus({preventScroll:true});
  });
  const wrap=$('gameSearch');
  if(wrap)wrap.setAttribute('aria-label','ابحث عن قالب لعبة تعليمية');
  // Link navigation buttons remain functional; the new actions are additions only.
  if(location.hash&&ids.includes(location.hash.slice(1))){
    requestAnimationFrame(()=>setTimeout(()=>$(location.hash.slice(1))?.scrollIntoView({block:'start'}),120));
  }
  // The light theme is also applied to the long-form teacher workflow. No app
  // data, login token, student records or saved activity is changed by this module.
 }
 if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();