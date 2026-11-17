/* TAG LAB V32 — game-first visual discovery, real playable previews, non-destructive template switching. */
(()=>{'use strict';
const view=document.documentElement.dataset.tagView;
if(view!=='games'&&view!=='create')return;
const $=id=>document.getElementById(id);
const C=[
 ['quiz','اختبار تفاعلي','أربع إجابات ملوّنة لكل سؤال','🔘','quiz','اختيار من متعدد'],
 ['wheel','عجلة الحظ','تدور العجلة وتكشف السؤال','🎡','wheel','حماس وتشويق'],
 ['pairs','المطابقة','اربط السؤال بالإجابة الصحيحة','🧩','pairs','تثبيت المفاهيم'],
 ['boxes','الصناديق الغامضة','افتح صندوقًا واكتشف التحدي','🎁','boxes','نشاط جماعي'],
 ['truth','صح أم خطأ','اختر الإجابة الصحيحة بسرعة','✅','truth','مراجعة سريعة'],
 ['fast','سباق الوقت','جاوب قبل انتهاء المؤقت','⏱️','fast','تحدي السرعة'],
 ['flash','بطاقات الذاكرة','تعلّم واقلب البطاقات','🃏','flash','تعلم فردي'],
 ['sort','فرز وتصنيف','ضع كل معلومة في مجموعتها','🗂️','sort','تصنيف'],
 ['memory','لعبة الذاكرة','اختبر قوة تذكرك','🧠','memory','تركيز'],
 ['anagram','ترتيب الحروف','رتّب حروف الإجابة','🔤','anagram','لغويات'],
 ['crossword','كلمات متقاطعة','اكتشف الكلمات المطلوبة','🔠','crossword','مفردات'],
 ['wordsearch','البحث عن الكلمات','ابحث عن المصطلحات في الشبكة','🔎','wordsearch','مفردات'],
 ['order','الترتيب المنطقي','رتب أحداث الدرس بالتسلسل','🔢','order','ترتيب'],
 ['maze','متاهة المعرفة','تقدم في المتاهة بالإجابة','🏰','maze','مغامرة'],
 ['balloons','فرقعة البالونات','اختَر البالون الصحيح','🎈','balloons','مرح'],
 ['hidden','الصورة المخفية','اكشف المحتوى تدريجيًا','🖼️','hidden','استكشاف'],
 ['cloze','أكمل الفراغ','اكتب ما يكمل الجملة','✏️','cloze','استرجاع'],
 ['diagram','تسمية الرسم','ضع التسمية على الرسم','📍','diagram','صور ومخططات'],
 ['board','لوحة نقاط','نشاط مفتوح للصف','🏅','board','تعاون'],
 ['teams','معركة الفرق','تحديات مجموعات متنافسة','⚔️','teams','تنافس'],
 ['survey','تصويت الصف','استطلاع رأي طلابك','📊','survey','مشاركة'],
 ['exit','بطاقة الخروج','ماذا تعلمت من الحصة؟','🎫','exit','تأمل'],
 ['story','اختر مسارك','اختر قرارًا في قصة تعليمية','🧭','story','تفكير'],
 ['bingo','بينغو المصطلحات','تحدي شبكة المصطلحات','🔲','bingo','تفاعل']
];
const byId=new Map(C.map(([id,name,desc,icon,art,tag])=>[id,{id,name,desc,icon,art,tag}]));
const featured=['quiz','wheel','pairs','boxes','truth','fast'];
const make=(tag,className,text)=>{const e=document.createElement(tag);if(className)e.className=className;if(text!==undefined)e.textContent=text;return e};
const selectedKey='tag_lab_selected_game';
let choice=$('cloudMode')?.value||sessionStorage.getItem(selectedKey)||'quiz';
if(!byId.has(choice))choice='quiz';
function choose(id,go=false){
 if(!byId.has(id))return;
 const previous=choice;
 if(previous!==id)document.dispatchEvent(new CustomEvent('taglab:before-template-switch',{detail:{from:previous,to:id}}));
 choice=id;sessionStorage.setItem(selectedKey,id);
 const select=$('cloudMode');
 if(select&&[...select.options].some(x=>x.value===id)){select.value=id;select.dispatchEvent(new Event('change',{bubbles:true}))}
 document.querySelectorAll('.tag-v32-mini,.tag-v32-option,.tag-v32-game').forEach(node=>{
  const active=node.dataset.mode===id;
  if(node.classList.contains('tag-v32-game'))node.setAttribute('aria-selected',String(active));
  else node.setAttribute('aria-pressed',String(active))
 });
 document.querySelectorAll('[data-v32-current]').forEach(e=>e.textContent=byId.get(id).icon+' '+byId.get(id).name);
 document.querySelectorAll('[data-v32-subtitle]').forEach(e=>e.textContent=byId.get(id).desc);
 document.dispatchEvent(new CustomEvent('taglab:template-selected',{detail:{from:previous,to:id}}));
 if(go)location.href='/tag-lab-create.html';
}
function demo(id,forceDemo){
 // A preview is not a commitment: only the Choose button changes the selected game.
 if(typeof window.TAG_LAB_V32_PREVIEW!=='function')return;
 const ok=window.TAG_LAB_V32_PREVIEW(id,forceDemo||(view==='create'&&id!==choice));
 if(!ok)return;
 const overlay=$('playOverlay');if(!overlay)return;
 let notice=$('tagV32SampleNotice');
 if(!notice){notice=make('div','tag-v32-demo-caption');notice.id='tagV32SampleNotice';notice.setAttribute('role','status');overlay.querySelector('.playhead')?.after(notice)}
 notice.hidden=!window.TAG_LAB_V32_DEMO_ACTIVE;
 notice.textContent='🎮 هذه معاينة تفاعلية بأسئلة تجريبية. يمكنك إغلاقها ثم اختيار القالب، ولن تتغير أسئلتك.';
}
function art(p){
 const art=make('div','tag-v32-art');art.dataset.art=p.art;
 if(p.art==='wheel'){const wheel=make('div','tag-v32-wheel');wheel.append(make('b','','؟'));art.append(wheel)}
 else if(p.art==='quiz'){const board=make('div','tag-v32-artboard');board.append(make('span','qline'),make('span','qline short'));
  const opts=make('div','opt');for(let i=0;i<4;i++)opts.append(document.createElement('i'));board.append(opts);art.append(board)}
 else if(p.art==='pairs'){const grid=make('div','tag-v32-pairs');for(const icon of ['🧮','🐱','🐱','🌍','🌍','🧮','📖','📖'])grid.append(make('span','',icon));art.append(grid)}
 else if(p.art==='boxes'){const grid=make('div','tag-v32-boxes');for(const icon of ['🎁','❔','🎁','🎁','🎁','🎁'])grid.append(make('span','',icon));art.append(grid)}
 else if(p.art==='truth'){const flex=make('div','tag-v32-truth');flex.append(make('span','','✓'),make('span','','✕'));art.append(flex)}
 else if(p.art==='fast'){const clock=make('div','tag-v32-fast');clock.append(make('strong','','00:15'),make('div','bar'));art.append(clock)}
 else art.append(make('div','tag-v32-art-generic',p.icon));
 return art
}
function gameCard(p){
 const card=make('article','tag-v32-game');card.dataset.mode=p.id;card.setAttribute('aria-selected',String(p.id===choice));card.append(art(p));
 const body=make('div','tag-v32-body');body.append(make('h3','',p.icon+' '+p.name),make('p','',p.desc));
 const tags=make('div','tag-v32-tags');tags.append(make('span','goodfit',p.tag),make('span','','يمكن تغيير القالب لاحقًا'));body.append(tags);
 const buttons=make('div','tag-v32-buttons');
 const preview=make('button','','▶ معاينة');preview.type='button';preview.setAttribute('aria-label','معاينة لعبة '+p.name+' بأسئلة تجريبية');preview.onclick=()=>demo(p.id,true);
 const pick=make('button','pick','✏️ اكتب أسئلة هذا القالب');pick.type='button';pick.onclick=()=>choose(p.id,true);
 buttons.append(preview,pick);body.append(buttons);card.append(body);return card
}
function option(p,chooser=()=>choose(p.id,false)){
 const b=make('button','tag-v32-option');b.type='button';b.dataset.mode=p.id;b.setAttribute('aria-pressed',String(p.id===choice));
 b.append(make('span','emoji',p.icon));
 const text=make('span');text.append(make('b','',p.name),make('span','tiny',p.tag));b.append(text);
 b.onclick=()=>chooser(p.id);return b
}
function modal(){
 let pending=choice;
 const dlg=document.createElement('dialog');dlg.className='tag-v32-dialog';dlg.id='tagV32AllModes';
 const inner=make('div','tag-v32-dialog-inner');
 const head=make('div','tag-v32-dialog-head');
 const text=make('div');text.append(make('h2','','كل القوالب الـ24'),make('p','','لكل قالب أسئلته الخاصة؛ اكتبها أو عدّلها دون التأثير على القوالب الأخرى.'));head.append(text);
 const close=make('button','tag-v32-close','×');close.type='button';close.setAttribute('aria-label','إغلاق نافذة القوالب');close.onclick=()=>dlg.close();head.append(close);
 inner.append(head);
 const all=make('div','tag-v32-all');for(const p of byId.values())all.append(option(p,()=>{
  pending=p.id;
  all.querySelectorAll('.tag-v32-option').forEach(x=>x.setAttribute('aria-pressed',String(x.dataset.mode===pending)));
  const b=$('tagV32ModalPick');if(b)b.textContent='اختيار '+p.name
 }));
 inner.append(all);
 const actions=make('div','tag-v32-dialog-actions');
 const preview=make('button','alt','▶ معاينة القالب');preview.type='button';preview.onclick=()=>{dlg.close();demo(pending,view==='games')};
 const pick=make('button','','✏️ تحرير أسئلة القالب المختار');pick.id='tagV32ModalPick';pick.type='button';pick.onclick=()=>{dlg.close();choose(pending,view==='games')};
 actions.append(preview,pick);inner.append(actions);
 dlg.append(inner);document.body.append(dlg);
 dlg.addEventListener('close',()=>{pending=choice;all.querySelectorAll('.tag-v32-option').forEach(x=>x.setAttribute('aria-pressed',String(x.dataset.mode===choice)))});
 return dlg
}
const dialog=modal();
function openDialog(){dialog.showModal();dialog.querySelector('.tag-v32-option[aria-pressed="true"]')?.focus()}
const progress=(labels)=>{
 const e=make('div','tag-v32-progress');
 labels.forEach(([label,active])=>{const node=make('span',active?'active':'',label);e.append(node)});
 return e
};
if(view==='games'){
 const catalog=$('catalog');
 if(catalog){
  const hub=make('div','tag-v32-gallery');
  hub.append(progress([['1 • اختر القالب',true],['2 • أضف الأسئلة',false],['3 • جرّب واحفظ',false]]));
  const head=make('div','tag-v32-head');const title=make('div');title.append(make('h2','','اختر اللعبة التي تحبها أولًا'),make('p','','اضغط «معاينة» لتجربة اللعبة الحقيقية؛ بعدها أضف أسئلتك بسهولة.'));
  head.append(title,make('span','tag-v32-status','6 ألعاب أساسية • 24 قالبًا متاحًا'));hub.append(head);
  const grid=make('div','tag-v32-grid');for(const id of featured)grid.append(gameCard(byId.get(id)));hub.append(grid);
  const more=make('div','tag-v32-more');const label=make('div');label.append(make('strong','','تريد لعبة أخرى؟'),make('p','','استكشف جميع القوالب بما فيها البطاقات والترتيب والكلمات والمتاهة.'));
  const button=make('button','tag-simple-btn alt','عرض جميع القوالب الـ24');button.type='button';button.onclick=openDialog;
  more.append(label,button);hub.append(more);
  const quick=make('div','tag-v32-head');const text=make('div');text.append(make('h2','','عندك أسئلة جاهزة؟'),make('p','','يمكنك تجاوز خطوة اختيار القالب وإضافتها مباشرة، ثم تغيير اللعبة في أي وقت.'));quick.append(text);
  const skip=make('a','tag-simple-btn','✍️ أدخل أسئلتي لقالب أختاره لاحقًا');skip.href='/tag-lab-create.html';quick.append(skip);hub.append(quick);
  catalog.prepend(hub)
 }
}else{
 const builder=$('builder');
 if(builder){
  const panel=make('div','tag-v32-create-panel');
  panel.append(progress([['1 • اختر قالبًا',false],['2 • أضف الأسئلة',true],['3 • جرّب واحفظ',false]]));
  panel.append(make('h2','','عدّل أسئلة القالب المختار فقط'));
  panel.append(make('p','','كل قالب له مسودته المستقلة؛ عند تغيير اللعبة لا تتغير أسئلتها ولا تُنسخ تلقائيًا.'));
  const current=make('div','tag-v32-current');
  current.append(make('span','icon',byId.get(choice).icon));
  const currentText=make('div','grow');currentText.append(make('b','',byId.get(choice).name));
  currentText.querySelector('b').setAttribute('data-v32-current','');
  currentText.append(make('small','',byId.get(choice).desc));currentText.querySelector('small').setAttribute('data-v32-subtitle','');
  current.append(currentText,make('span','tag-v32-status','يمكن تغييره في أي وقت'));panel.append(current);
  const mini=make('div','tag-v32-quick');for(const id of featured){
    const p=byId.get(id),b=make('button','tag-v32-mini');b.type='button';b.dataset.mode=id;b.setAttribute('aria-pressed',String(id===choice));
    b.append(make('span','symbol',p.icon),make('span','',p.name));b.onclick=()=>choose(id,false);mini.append(b)}
  panel.append(mini);
  const under=make('div','tag-v32-under');under.append(make('span','subnote','يمكنك العودة إلى هذا القالب لاحقًا لتعديل أسئلته الخاصة.'));
  const all=make('button','','🧩 اختر من 24 قالبًا');all.type='button';all.onclick=openDialog;under.append(all);panel.append(under);
  const shortcuts=make('div','tag-simple-actions');
  const book=make('a','tag-simple-btn alt','📚 إنشاء أسئلة من كتاب');book.href='/tag-lab-books.html';
  const saved=make('a','tag-simple-btn alt','🗂️ استخدام نشاط محفوظ');saved.href='/tag-lab-library.html';
  shortcuts.append(book,saved);panel.append(shortcuts);
  builder.prepend(panel);
  const modebar=make('div','tag-v32-modebar');
  const message=make('div');message.append(make('b','','لديك أسئلة؟ جرّبها بلعبة '+byId.get(choice).name));
  message.querySelector('b').setAttribute('data-v32-bar','');modebar.append(message);
  const buttons=make('div','btns');
  const play=make('button','','▶ تجربة أسئلة هذا القالب');play.type='button';play.onclick=()=>demo(choice,false);
  const change=make('button','secondary','🔁 فتح قالب آخر');change.type='button';change.onclick=openDialog;
  buttons.append(play,change);modebar.append(buttons);
  const after=builder.nextElementSibling;builder.after(modebar);
  const select=$('cloudMode');if(select)select.addEventListener('change',()=>{if(byId.has(select.value)){choice=select.value;
    document.querySelectorAll('[data-v32-bar]').forEach(e=>e.textContent='لديك أسئلة؟ جرّبها بلعبة '+byId.get(choice).name)}});
 }
}
choose(choice,false);
})();
