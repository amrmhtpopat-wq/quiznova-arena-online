/* TAG LAB Simple V31 — physical page routes over one backwards-compatible game engine. */
(()=>{'use strict';
const html=document.documentElement, view=html.dataset.tagView;
if(!view)return;
const pages=[
 {id:'home',url:'/tag-lab-home.html',icon:'🏠',label:'الرئيسية'},
 {id:'books',url:'/tag-lab-books.html',icon:'📚',label:'الكتب والذكاء'},
 {id:'create',url:'/tag-lab-create.html',icon:'✍️',label:'صانع الألعاب'},
 {id:'games',url:'/tag-lab-games.html',icon:'🎮',label:'الألعاب'},
 {id:'library',url:'/tag-lab-library.html',icon:'🗂️',label:'مكتبتي'},
 {id:'mixer',url:'/tag-lab-mixer.html',icon:'🧪',label:'الحصة التفاعلية'},
 {id:'assign',url:'/tag-lab-assign.html',icon:'🪪',label:'إسناد الألعاب'},
 {id:'account',url:'/tag-lab-account.html',icon:'👤',label:'حسابي'}
];
const labels={
 books:{title:'الكتب وTAG AI',description:'ارفع كتابك وحوّل صفحاته إلى أسئلة.'},
 create:{title:'صانع الألعاب',description:'أضف الأسئلة واختر القالب المناسب.'},
 games:{title:'قوالب الألعاب',description:'اختر القالب الذي يناسب درسك.'},
 library:{title:'مكتبتي',description:'أنشطتك المحفوظة في مكان واحد.'},
 mixer:{title:'الحصة التفاعلية',description:'استخدم عدة ألعاب ضمن حصة واحدة.'}
};
const linkBySection={catalog:'games',builder:'create',bookLab:'books',mixer:'mixer',library:'library',cloud:'library',roadmap:'home'};
const $=id=>document.getElementById(id);
const make=(tag,cls,text)=>{const node=document.createElement(tag);if(cls)node.className=cls;if(text!==undefined)node.textContent=text;return node};
const nav=make('header','tag-simple-nav');
const inside=make('div','inside');
const logo=make('a','tag-simple-logo');logo.href='/tag-lab-home.html';logo.setAttribute('aria-label','العودة إلى الرئيسية');
const mark=document.createElement('img');mark.src='/assets/brand/tag-logo-dark-v21.png';mark.alt='شعار TAG';
const brand=make('span');brand.append(make('strong','', 'TAG LAB'),make('span','', 'تعلّم • العب • تفوّق'));
logo.append(mark,brand);
const menu=make('nav','tag-simple-links');menu.setAttribute('aria-label','الصفحات الرئيسية');
for(const p of pages){const a=make('a','',p.icon+' '+p.label);a.href=p.url;if(p.id===view)a.setAttribute('aria-current','page');menu.append(a)}
inside.append(logo,menu);nav.append(inside);
document.body.prepend(nav);
const main=document.querySelector('.main');
if(!main)return;
const copy=labels[view]||labels.books;
const intro=make('div','tag-simple-intro');
const info=make('div');
info.append(make('h1','',copy.title),make('p','',copy.description));
intro.append(info);
const heroArt=make('img','tagv-intro-art');
heroArt.src='/assets/brand/tag-lab-hero-v1.svg';
heroArt.alt='ألعاب تعليمية وكتب وكأس البطولة';
intro.append(heroArt);
const introActions=make('div','tag-simple-actions');
const back=make('a','tag-simple-back','↩ الرئيسية');back.href='/tag-lab-home.html';introActions.append(back);intro.append(introActions);
main.prepend(intro);
const auth=make('div','tag-simple-auth');auth.id='tagSimpleAuth';
if(view!=='library'){
 const login=$('cloudLogin');
 if(login){auth.append(login);intro.after(auth)}
}
function logged(){return Boolean($('cloudWorkspace')&&!$('cloudWorkspace').classList.contains('hide'))}
function authView(){const ok=logged();if(view!=='library')auth.dataset.logged=ok?'yes':'no'}
authView();
const workspace=$('cloudWorkspace');if(workspace)new MutationObserver(authView).observe(workspace,{attributes:true,attributeFilter:['class']});
document.addEventListener('gamelab:library',authView);
const toast=make('div','tag-simple-toast');toast.hidden=true;toast.setAttribute('role','status');
function show(text,error=false){toast.textContent=text;toast.hidden=false;toast.classList.toggle('error',error);toast.scrollIntoView({block:'nearest',behavior:'smooth'})}
const goto=(id)=>{const dest=pages.find(x=>x.id===id);if(dest)location.href=dest.url};
const draftKey='tag_lab_question_draft_v31';
function stash(){
 const rows=window.TG_QUESTION_BANK_ROWS;
 if(!Array.isArray(rows)||!rows.length)return false;
 const payload={ts:Date.now(),title:$('activityTitle').value,subject:$('subject').value,
  grade:$('grade').value,bookId:window.BOOYAH_LAB_BOOK_ID||'',
  rows:rows.map(x=>({...x}))};
 try{sessionStorage.setItem(draftKey,JSON.stringify(payload));return true}
 catch(_){show('يتعذر نقل الأسئلة بسبب مساحة المتصفح. حاول إزالة ملفات قديمة أو افتح صانع الألعاب واكتب أسئلتك.',true);return false}
}
function importStash(){
 const raw=sessionStorage.getItem(draftKey);
 if(!raw)return;
 try{
  const data=JSON.parse(raw);
  if(Date.now()-Number(data.ts)>2*3600*1000||!Array.isArray(data.rows)||!data.rows.length){
   sessionStorage.removeItem(draftKey);return
  }
  if($('activityTitle'))$('activityTitle').value=data.title||'ألعاب الدرس';
  if($('subject')&&[...$('subject').options].some(o=>o.value===data.subject))$('subject').value=data.subject;
  if($('grade')&&[...$('grade').options].some(o=>o.value===data.grade))$('grade').value=data.grade;
  if($('activityData'))$('activityData').value=data.rows.map(x=>x.q+' | '+x.a+' | '+(x.g||'عام')+(x.sourcePage?' | '+x.sourcePage:'')).join('\n');
  window.TG_QUESTION_BANK_ROWS=data.rows.map(x=>({...x}));
  window.TG_CREATOR_PREVIEW_ROWS=data.rows.map(x=>({...x}));
  window.BOOYAH_LAB_BOOK_ID=data.bookId||'';
  const apply=$('applyContent');if(apply)apply.click();
  show('✓ تم نقل '+data.rows.length+' سؤالًا مع الخيارات والصعوبة من صفحة الكتاب. راجع المحتوى ثم احفظ النشاط.');
  sessionStorage.removeItem(draftKey)
 }catch(_){sessionStorage.removeItem(draftKey);show('تعذر فتح مسودة الصفحات؛ افتح كتابك وأنشئ أسئلة جديدة.',true)}
}
if(view==='books'){
 const area=$('bookLab');
 const after=make('div','tag-simple-savebar');after.id='tagBookNext';after.hidden=true;
 const title=make('strong','', 'انتهيت من مراجعة الأسئلة؟');
 const actions=make('div','tag-simple-actions');
 const next=make('button','tag-simple-btn','التالي: صانع الألعاب ←');next.type='button';next.disabled=true;
 next.onclick=()=>{if(stash())goto('create')};
 const libraryLink=make('a','tag-simple-btn alt','مكتبتي الخاصة');libraryLink.href='/tag-lab-library.html';
 actions.append(next,libraryLink);after.append(title,actions);
 if(area)area.append(after);
 document.addEventListener('gamelab:book-bank-accepted',()=>{next.disabled=false;after.hidden=false;show('✓ الأسئلة المعتمدة جاهزة. اضغط «التالي: صانع الألعاب» لتكمل.');});
 const oldSave=$('labBookSaveCloud');if(oldSave)oldSave.style.display='none';
 after.prepend(toast)
}else if(view==='create'){
 const section=$('builder');
 const savebar=make('div','tag-simple-savebar');
 const buttons=make('div','tag-simple-actions');
 const save=make('button','tag-simple-btn','💾 حفظ في مكتبتي');save.type='button';
 save.onclick=()=>{
  if(!logged()){show('سجّل الدخول إلى حساب TAG LAB قبل الحفظ.',true);location.href='/tag-lab-account.html';return}
  const native=$('cloudSave');if(!native){show('تعذر العثور على زر الحفظ.',true);return}
  native.click()
 };
 const goLib=make('a','tag-simple-btn alt','🗂️ عرض مكتبتي');goLib.href='/tag-lab-library.html';
 const goGames=make('a','tag-simple-btn alt','🎮 تصفح الألعاب');goGames.href='/tag-lab-games.html';
 buttons.append(save,goLib,goGames);savebar.append(buttons,toast);
 if(section)section.after(savebar);
 const nativeMessage=$('cloudMessage');
 if(nativeMessage)new MutationObserver(()=>{const text=nativeMessage.textContent||'';if(text&&text.trim())show(text,/تعذر|خطأ|يجب|يرجى/.test(text))}).observe(nativeMessage,{childList:true,characterData:true,subtree:true});
 importStash();
 const selected=sessionStorage.getItem('tag_lab_selected_game');
 if(selected&&$('cloudMode')){
  const mode=$('cloudMode');if([...mode.options].some(x=>x.value===selected)){mode.value=selected;mode.dispatchEvent(new Event('change'))}
  sessionStorage.removeItem('tag_lab_selected_game')
 }
}else if(view==='games'){
 // The V32 template-first gallery owns this route; legacy 24-card controls stay in the engine but are not shown.
}else if(view==='library'){
 const cloud=$('cloud');
 if(cloud){
  const quick=make('div','tag-simple-actions');
  const create=make('a','tag-simple-btn','✍️ إنشاء نشاط جديد');create.href='/tag-lab-create.html';
  const books=make('a','tag-simple-btn alt','📚 من كتابي');books.href='/tag-lab-books.html';
  quick.append(create,books);cloud.prepend(quick)
 }
 document.addEventListener('gamelab:edit-structured-bank',()=>{
  const area=$('bookLab');if(!area)return;
  area.classList.add('tag-visible-section');
  document.body.classList.add('tag-simple-editing');
  if(!$('tagEditExistingBar')){
   const bar=make('div','tag-simple-savebar');bar.id='tagEditExistingBar';
   bar.append(make('strong','', '✏️ تعديل أسئلة النشاط المحفوظ'));
   const buttons=make('div','tag-simple-actions');
   const save=make('button','tag-simple-btn','💾 حفظ التعديلات على النشاط نفسه');save.type='button';
   save.onclick=()=>{if($('labBookApprove').disabled){show('لم تُحمّل الأسئلة بعد.',true);return}
     if(window.TG_BOOK_EDITOR_REUSE){show('اضغط «اعتماد المختار» أولًا، ثم احفظ التعديلات.',true);return}
     $('cloudSave')?.click()
   };
   const cancel=make('button','tag-simple-btn alt','↩ العودة إلى مكتبتي');cancel.type='button';
   cancel.onclick=()=>{area.classList.remove('tag-visible-section');document.body.classList.remove('tag-simple-editing');cloud?.scrollIntoView({behavior:'smooth'})};
   buttons.append(save,cancel);bar.append(buttons);area.append(bar)
  }
  requestAnimationFrame(()=>area.scrollIntoView({block:'start',behavior:'smooth'}));
 });
 document.addEventListener('gamelab:book-bank-accepted',event=>{
  if(event.detail?.editingExisting)show('✓ راجعت الأسئلة الجديدة. اضغط «حفظ التعديلات على النشاط نفسه».')
 });
}else if(view==='mixer'){
 const section=$('mixer');
 if(section){
  const quick=make('div','tag-simple-actions');
  const create=make('a','tag-simple-btn alt','🗂️ افتح مكتبتي أولًا');create.href='/tag-lab-library.html';quick.append(create);
  section.prepend(quick)
 }
}
document.addEventListener('click',e=>{
 const nav=e.target.closest('[data-scroll],[data-jump]');const target=nav?.dataset?.scroll||nav?.dataset?.jump;
 if(target&&linkBySection[target]&&linkBySection[target]!==view){e.preventDefault();e.stopImmediatePropagation();goto(linkBySection[target]);return}
 const gameButton=e.target.closest('#gameGrid .game button');
 if(gameButton&&/أنشئ|إنشاء|صمّم/.test(gameButton.textContent)&&view==='games'){
  e.preventDefault();e.stopImmediatePropagation();
  const mode=gameButton.closest('.game')?.dataset.gameMode;
  if(mode)sessionStorage.setItem('tag_lab_selected_game',mode);
  goto('create')
 }
},true);
})();
