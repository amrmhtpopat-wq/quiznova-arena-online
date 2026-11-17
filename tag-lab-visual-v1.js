/* TAG LAB VISUAL SYSTEM V1 — shared static shell; no cross-site access. */
(()=>{'use strict';
 const d=document,h=d.documentElement,body=d.body;
 if(!body||body.classList.contains('tagv-enabled'))return;
 const currentPath=location.pathname||'/';
 const student=currentPath==='/tag-lab-student.html'||currentPath==='/tag-lab-live-student.html';
 const display=currentPath==='/tag-lab-live-display.html';
 const navData=student?[
  ['/tag-lab-student.html','🎮','ألعابي'],
  ['/tag-lab-live-student.html','📡','التحدي المباشر'],
 ]:[
  ['/tag-lab-home.html','⌂','الرئيسية'],
  ['/tag-lab-library.html','▣','أنشطتي'],
  ['/tag-lab-games.html','🎮','قوالب الألعاب'],
  ['/tag-lab-books.html','▤','كتبي'],
  ['/tag-lab-live-teacher.html','◉','التحدي المباشر'],
  ['/tag-lab-results.html','▥','النتائج'],
  ['/tag-lab-create.html','✎','صانع الأسئلة'],
  ['/tag-lab-mixer.html','⚗','الحصة التفاعلية'],
  ['/tag-lab-assign.html','▣','إسناد الألعاب'],
 ];
 const storageKey='tag_lab_visual_theme_v1';
 let saved='';
 try{saved=localStorage.getItem(storageKey)||''}catch(_){}
 const darkPref=matchMedia?.('(prefers-color-scheme:dark)').matches;
 let theme=saved==='dark'||saved==='light'?saved:(darkPref?'dark':'light');
 function themeApply(mode){
  theme=mode;h.setAttribute('data-tag-theme',mode);
  d.querySelector('meta[name="theme-color"]')?.setAttribute('content',mode==='dark'?'#10112D':'#F8F9FF');
  d.querySelectorAll('[data-tagv-theme]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.tagvTheme===mode)));
  try{localStorage.setItem(storageKey,mode)}catch(_){}
 }
 function el(tag,cls,txt){const e=d.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=txt;return e}
 const nav=el('aside','tagv-sidebar');nav.id='tagvSidebar';nav.setAttribute('aria-label','القائمة الرئيسية');
 const brand=el('a','tagv-brand');brand.href='/tag-lab-home.html';
 const brandImage=el('img');brandImage.src='/assets/brand/tag-lab-visual-v1.svg';brandImage.alt='TAG LAB — TEACH AND GAME';
 brand.append(brandImage);nav.append(brand);
 const links=el('nav','tagv-links');
 for(const [url,icon,name] of navData){
  const a=el('a');a.href=url;
  if(currentPath===url||(currentPath==='/game-lab-preview.html'&&url==='/tag-lab-games.html'))a.setAttribute('aria-current','page');
  const i=el('span','tagv-icon',icon);i.setAttribute('aria-hidden','true');a.append(i,d.createTextNode(name));links.append(a)
 }
 nav.append(links);
 const bottom=el('div','tagv-sidebar-footer');
 if(!student&&!display){
  const settings=el('a',null,'⚙  الإعدادات');settings.href='/tag-lab-account.html';bottom.append(settings);
  const account=el('a',null,'👤  حساب المعلم');account.href='/tag-lab-account.html';bottom.append(account)
 }else if(student){
  const out=el('a',null,'↩  العودة إلى ألعابي');out.href='/tag-lab-student.html';bottom.append(out)
 }
 nav.append(bottom);
 const top=el('header','tagv-topbar');
 const navButton=el('button','tagv-menu-btn','☰');navButton.type='button';navButton.setAttribute('aria-label','فتح القائمة');
 const search=el('label','tagv-search');const magnify=el('span',null,'⌕');magnify.setAttribute('aria-hidden','true');
 const input=el('input');input.placeholder=student?'ابحث في ألعابك':'ابحث عن نشاط، درس أو قالب...';input.setAttribute('aria-label','بحث في الصفحة');input.type='search';
 search.append(magnify,input);
 const right=el('div','tagv-header-actions');
 const toggle=el('div','tagv-theme');
 for(const [mode,ico,title] of [['light','☀','الوضع النهاري'],['dark','☾','الوضع الليلي']]){
  const b=el('button',null,ico);b.type='button';b.dataset.tagvTheme=mode;b.title=title;b.setAttribute('aria-label',title);
  b.addEventListener('click',()=>themeApply(mode));toggle.append(b)
 }
 right.append(toggle);
 if(!student&&!display){
  const user=el('div','tagv-user');user.id='tagvUser';
  user.append(el('span',null,'👤'),el('b',null,'حساب المعلم'));
  right.append(user);
 }
 top.append(navButton,search,right);
 const overlay=el('div','tagv-overlay');overlay.addEventListener('click',()=>body.classList.remove('tagv-nav-open'));
 navButton.addEventListener('click',()=>body.classList.toggle('tagv-nav-open'));
 nav.addEventListener('click',e=>{if(e.target.closest('a'))body.classList.remove('tagv-nav-open')});
 d.addEventListener('keydown',e=>{if(e.key==='Escape')body.classList.remove('tagv-nav-open')});
 body.classList.add('tagv-enabled');
 body.prepend(overlay,top,nav);
 themeApply(theme);
 input.addEventListener('input',()=>{
  const q=input.value.trim().toLocaleLowerCase('ar');
  const cards=d.querySelectorAll('.tag-v32-game,.card,.game-card,.tagv-result-card');
  cards.forEach(c=>{const hay=c.textContent.toLocaleLowerCase('ar');c.hidden=!!q&&!hay.includes(q)});
 });
 if(!student&&!display){
  const token=localStorage.getItem('qn9_teacher_token');
  if(token)fetch('/api/auth/me',{headers:{Authorization:'Bearer '+token},cache:'no-store'})
   .then(r=>r.ok?r.json():null).then(data=>{if(data?.ok&&data.teacher?.name){
    const label=d.getElementById('tagvUser')?.querySelector('b');if(label)label.textContent=data.teacher.name
   }}).catch(()=>{});
 }
 if(currentPath==='/tag-lab-home.html'){
  const hero=d.querySelector('section.hero');
  const art=hero?.querySelector('.visual');if(art)art.replaceChildren();
  if(art){const image=el('img');image.src='/assets/brand/tag-lab-hero-v1.svg';image.alt='ألعاب وكتب وجوائز تعليمية';art.append(image)}
  if(hero){
   const summary=el('section','tagv-summary');summary.setAttribute('aria-live','polite');
   summary.innerHTML='<div class="tagv-stat"><span>أنشطتي</span><strong id="tagvActivityCount">—</strong></div>'+
    '<div class="tagv-stat"><span>الأنشطة المنشورة</span><strong id="tagvPublishedCount">—</strong></div>'+
    '<div class="tagv-stat"><span>المسودات</span><strong id="tagvDraftCount">—</strong></div>';
   summary.style.cssText='display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px;margin:22px 0';
   hero.after(summary);
   const token=localStorage.getItem('qn9_teacher_token');
   if(token)fetch('/api/game-lab/teacher/list',{headers:{Authorization:'Bearer '+token},cache:'no-store'})
    .then(r=>r.ok?r.json():null).then(x=>{if(!x?.ok)return;
     const activities=x.activities||[];const all=activities.length,published=activities.filter(a=>a.published).length;
     const a=d.getElementById('tagvActivityCount'),p=d.getElementById('tagvPublishedCount'),f=d.getElementById('tagvDraftCount');
     if(a)a.textContent=all;if(p)p.textContent=published;if(f)f.textContent=all-published;
    }).catch(()=>{});
  }
 }
})();
