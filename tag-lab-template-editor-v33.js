/* TAG LAB V33 — template-owned question editor.
 * Distinct same-tab drafts and single-mode cloud saves; changing templates cannot
 * silently reuse or overwrite another game's questions.
 */
(()=>{
'use strict';
if(document.documentElement.dataset.tagView!=='create')return;
const $=id=>document.getElementById(id),mk=(tag,cl,txt)=>{
 const e=document.createElement(tag);if(cl)e.className=cl;if(txt!==undefined)e.textContent=txt;return e
};
const defs={
 quiz:{label:'الاختبار التفاعلي',icon:'🔘',type:'mcq',q:'نص السؤال',a:'الإجابة الصحيحة',help:'اكتب السؤال ثم الإجابة الصحيحة، ويمكنك إضافة ثلاث إجابات خاطئة من تصميمك.'},
 fast:{label:'سباق الوقت',icon:'⏱️',type:'mcq',q:'السؤال السريع',a:'الإجابة الصحيحة',help:'أسئلة قصيرة وإجابات مختصرة. اكتب ثلاثة بدائل لتظهر الخيارات الأربعة.'},
 wheel:{label:'عجلة الحظ',icon:'🎡',type:'short',q:'السؤال الذي يظهر بعد دوران العجلة',a:'إجابته الصحيحة',help:'كل سؤال تضيفه يصبح تحديًا داخل عجلة الحظ.'},
 pairs:{label:'المطابقة',icon:'🧩',type:'short',q:'الطرف الأول (مصطلح أو سؤال)',a:'الطرف الثاني المطابق',help:'اكتب كل زوج متطابق: مصطلح وتعريفه، أو سؤال وإجابته.'},
 boxes:{label:'الصناديق الغامضة',icon:'🎁',type:'short',q:'سؤال داخل الصندوق',a:'الإجابة الصحيحة',help:'كل صندوق يخفي سؤالًا من الأسئلة التي تكتبها هنا.'},
 truth:{label:'صح أم خطأ',icon:'✅',type:'true_false',q:'العبارة المطلوب الحكم عليها',a:'هل العبارة صحيحة؟',help:'اكتب جملة خبرية وحدد هل هي صح أم خطأ.'},
 flash:{label:'بطاقات الذاكرة',icon:'🃏',type:'short',q:'الوجه الأمامي',a:'الوجه الخلفي',help:'اكتب سؤالًا أو مفهومًا في الوجه الأمامي، وإجابته أو تفسيره في الخلفي.'}
};
const extras={
 sort:'فرز وتصنيف',memory:'لعبة الذاكرة',anagram:'ترتيب الحروف',crossword:'كلمات متقاطعة',wordsearch:'البحث عن الكلمات',
 order:'الترتيب المنطقي',maze:'متاهة المعرفة',balloons:'فرقعة البالونات',hidden:'الصورة المخفية',
 cloze:'أكمل الفراغ',diagram:'تسمية الرسم',board:'لوحة نقاط',teams:'معركة الفرق',
 survey:'تصويت الصف',exit:'بطاقة الخروج',story:'اختر مسارك',bingo:'بينغو'
};
const schema=id=>defs[id]||{label:extras[id]||id,icon:'🎮',type:'short',q:'السؤال أو العنصر',a:'الإجابة أو العنصر المقابل',
 help:'حرّر أسئلة هذا القالب فقط. لبعض الألعاب خيارات متقدمة في النسخة الكاملة.'};
const ID='tag_lab_v33_template_drafts';
let drafts={};
try{const parsed=JSON.parse(sessionStorage.getItem(ID)||'{}');if(parsed&&typeof parsed==='object')drafts=parsed}catch(_){}
let mode=$('cloudMode')?.value||'quiz';
const isBookImport=Array.isArray(window.TG_QUESTION_BANK_ROWS)&&window.TG_QUESTION_BANK_ROWS.length>=4;
const parent=$('builder');
if(!parent)return;
const editor=mk('section','tag-v33-editor');editor.id='tagV33Editor';
const top=mk('div','tag-v33-head'),headtext=mk('div');
const chip=mk('span','tag-v33-chip','✏️ تعديل هذا القالب فقط');
const title=mk('h2','','أسئلة '+schema(mode).label);
title.id='tagV33Heading';headtext.append(chip,title);
const help=mk('p','',schema(mode).help);help.id='tagV33Help';headtext.append(help);
const count=mk('span','tag-v33-count','0 سؤال');count.id='tagV33Count';
top.append(headtext,count);editor.append(top);
const info=mk('div','tag-v33-info','🔒 لكل قالب مسودة مستقلة. عند فتح قالب آخر لن تُنقل إليه هذه الأسئلة تلقائيًا.');
editor.append(info);
const list=mk('div','tag-v33-list');list.id='tagV33List';editor.append(list);
const actions=mk('div','tag-v33-actions');
const add=mk('button','tag-v33-primary','＋ إضافة سؤال');add.type='button';add.id='tagV33Add';
const preview=mk('button','tag-v33-secondary','▶ جرّب هذا القالب');preview.type='button';preview.id='tagV33Preview';
const status=mk('p','tag-v33-status','ابدأ بالسؤال الأول؛ تحتاج إلى 4 أسئلة مختلفة على الأقل لحفظ اللعبة.');
status.id='tagV33Message';status.setAttribute('role','status');
actions.append(add,preview);editor.append(actions,status);
const panel=parent.querySelector('.tag-v32-create-panel');
if(panel)panel.after(editor);else parent.prepend(editor);
let rows=[];
const normalize=v=>String(v||'').replace(/\s+/g,' ').replace(/\|/g,' / ').trim();
const cleanedRow=(r,id)=>{
 const x={...r,q:normalize(r.q).slice(0,200),a:normalize(r.a).slice(0,100),g:normalize(r.g).slice(0,60)||'عام'};
 const d=schema(id);
 if(id==='truth'){
  x.questionType='true_false';x.a=(x.a==='خطأ')?'خطأ':'صح';x.choices=['صح','خطأ']
 }else if(id==='quiz'||id==='fast'){
  const other=(Array.isArray(r.choices)?r.choices:[]).filter(y=>normalize(y)!==normalize(r.a)).map(v=>normalize(v)).slice(0,3);
  // A complete teacher-authored set must contain exactly one correct answer.
  if(other.length===3&&other.every(Boolean)&&new Set([x.a,...other].map(v=>v.toLocaleLowerCase('ar'))).size===4){
   x.questionType='mcq';x.choices=[x.a,...other]
  }else{
   delete x.choices;
   if(x.questionType==='mcq')delete x.questionType; // fall back to existing legacy option generation
  }
 }else{
  delete x.choices;
  if(x.questionType==='mcq'||x.questionType==='true_false')delete x.questionType
 }
 return x
};
function persist(){try{sessionStorage.setItem(ID,JSON.stringify(drafts))}catch(_){}}
function fullRows(){return rows.filter(r=>normalize(r.q)&&normalize(r.a)).map(r=>cleanedRow(r,mode))}
function updateLegacy(){
 const complete=fullRows();
 const raw=$('activityData');
 raw.value=complete.map(r=>[r.q,r.a,r.g,...(r.sourcePage?[r.sourcePage]:[])].join(' | ')).join('\n');
 window.TG_QUESTION_BANK_ROWS=complete.map(x=>({...x}));
 window.TG_CREATOR_PREVIEW_ROWS=complete.map(x=>({...x}));
 raw.dispatchEvent(new Event('input',{bubbles:true}));
 count.textContent=complete.length+' / '+rows.length+' مكتمل';
}
function capture(){
 drafts[mode]={rows:rows.map(x=>({...x})),title:$('activityTitle')?.value||'',
  subject:$('subject')?.value||'عام',grade:$('grade')?.value||'عام',
  time:$('roundTime')?.value||'25',bookId:window.BOOYAH_LAB_BOOK_ID||'',
  imageId:window.BOOYAH_LAB_IMAGE_ID||'',sourceGroup:window.BOOYAH_LAB_SOURCE_GROUP||''};
 persist()
}
function notice(text,isError=false){
 status.textContent=text;status.classList.toggle('error',isError);
 if(isError)status.scrollIntoView({block:'nearest',behavior:'smooth'})
}
function field(label,value,maxLen,callback,opts={}){
 const wrap=mk('label','tag-v33-field');wrap.append(mk('span','',label));
 let input;
 if(opts.options){
  input=mk('select','tag-v33-input');
  for(const [v,t] of opts.options){const o=mk('option','',t);o.value=v;input.append(o)}
  input.value=value||opts.options[0][0];
  input.addEventListener('change',()=>callback(input.value))
 }else{
  input=opts.multiline?mk('textarea','tag-v33-input'):mk('input','tag-v33-input');
  if(!opts.multiline)input.type='text';
  input.maxLength=maxLen;input.value=value||'';
  input.placeholder=opts.placeholder||'';
  input.dir='auto';
  input.addEventListener('input',()=>callback(input.value))
 }
 wrap.append(input);return wrap
}
function paint(){
 const d=schema(mode);list.replaceChildren();
 title.textContent=d.icon+' أسئلة قالب '+d.label;
 help.textContent=d.help;
 rows.forEach((r,index)=>{
  const card=mk('article','tag-v33-card');card.dataset.index=String(index);
  const h=mk('header','tag-v33-card-head');h.append(mk('strong','',((mode==='pairs')?'الزوج ':'السؤال ')+(index+1)));
  const remove=mk('button','tag-v33-remove','حذف');remove.type='button';remove.setAttribute('aria-label','حذف السؤال '+(index+1));
  remove.onclick=()=>{if(rows.length===1){rows=[{q:'',a:mode==='truth'?'صح':'',g:'عام'}]}else rows.splice(index,1);paint();updateLegacy();capture()};
  h.append(remove);card.append(h);
  const fields=mk('div','tag-v33-fields');
  fields.append(field(d.q,r.q,200,value=>{r.q=value;change()} ,{multiline:true,placeholder:'اكتب السؤال هنا...'}));
  if(mode==='truth')fields.append(field(d.a,r.a||'صح',100,value=>{r.a=value;change()},{options:[['صح','✅ صح'],['خطأ','❌ خطأ']]}));
  else fields.append(field(d.a,r.a,100,value=>{r.a=value;change()},{placeholder:'اكتب الإجابة الصحيحة...'}));
  card.append(fields);
  if(mode==='quiz'||mode==='fast'){
   const opts=mk('div','tag-v33-alternatives');opts.append(mk('strong','','الخيارات الخاطئة الثلاثة (اختيارية إن أردت خيارات تلقائية)'));
   const alternatives=(Array.isArray(r.choices)?r.choices:[]).filter(x=>normalize(x)!==normalize(r.a)).slice(0,3);
   const altFields=mk('div','tag-v33-three');
   for(let k=0;k<3;k++){
    altFields.append(field('خيار خاطئ '+(k+1),alternatives[k]||'',100,value=>{
      const answer=normalize(r.a);
      const all=(Array.isArray(r.choices)?r.choices:[]).filter(x=>normalize(x)!==answer).slice(0,3);
      while(all.length<3)all.push('');
      all[k]=value;r.choices=[answer,...all];change()
    },{placeholder:'أدخل خيارًا مختلفًا'}))
   }
   opts.append(altFields);card.append(opts)
  }
  const extra=document.createElement('details');extra.className='tag-v33-extra';extra.append(mk('summary','','إعدادات اختيارية: المجموعة والتفسير'));
  const other=mk('div','tag-v33-extra-fields');
  other.append(field('المجموعة أو موضوع السؤال',r.g||'عام',60,value=>{r.g=value;change()},{placeholder:'عام'}));
  other.append(field('تفسير الإجابة للطالب',r.explanation||'',240,value=>{r.explanation=value;change()},{multiline:true,placeholder:'اختياري'}));
  extra.append(other);card.append(extra);
  list.append(card)
 });
 updateLegacy()
}
function change(){updateLegacy();capture();notice('✓ تم تعديل أسئلة '+schema(mode).label+' فقط. احفظ النشاط في مكتبتك عند الانتهاء.')}
function check(){
 const complete=fullRows();
 if(complete.length<4){notice('يحتاج قالب '+schema(mode).label+' إلى 4 أسئلة مكتملة على الأقل.',true);return false}
 if(complete.length>80){notice('الحد الأقصى 80 سؤالًا.',true);return false}
 const keys=new Set();
 for(const r of complete){
  const key=(r.q+'|'+r.a).toLocaleLowerCase('ar');
  if(keys.has(key)){notice('يوجد سؤال مكرر؛ عدّل السؤال أو احذف النسخة المكررة.',true);return false}
  keys.add(key);
 }
 if(mode==='quiz'||mode==='fast')for(let i=0;i<rows.length;i++){
  const r=rows[i];if(!normalize(r.q)||!normalize(r.a))continue;
  const others=(Array.isArray(r.choices)?r.choices:[]).filter(x=>normalize(x)!==normalize(r.a)).slice(0,3).map(normalize);
  if(others.some(Boolean)&&(!others.every(Boolean)||others.length!==3||new Set([normalize(r.a),...others].map(x=>x.toLocaleLowerCase('ar'))).size!==4)){
   notice('السؤال '+(i+1)+': اكتب 3 خيارات خاطئة مختلفة، أو اتركها جميعًا فارغة ليولدها النظام تلقائيًا.',true);return false
  }
 }
 updateLegacy();capture();notice('✓ '+complete.length+' أسئلة خاصة بقالب '+schema(mode).label+' جاهزة.');
 return true
}
function activate(id,opts={}){
 if(!id||!$('cloudMode')||![...$('cloudMode').options].some(x=>x.value===id))return;
 mode=id;
 const b=drafts[id];
 if(b){
  rows=Array.isArray(b.rows)&&b.rows.length?b.rows.map(r=>({...r})): [{q:'',a:id==='truth'?'صح':'',g:'عام'}];
  $('activityTitle').value=b.title||'';$('subject').value=b.subject||'عام';
  $('grade').value=b.grade||'عام';$('roundTime').value=b.time||'25';
  window.BOOYAH_LAB_BOOK_ID=b.bookId||'';
  window.BOOYAH_LAB_IMAGE_ID=b.imageId||'';
  window.BOOYAH_LAB_SOURCE_GROUP=b.sourceGroup||'';
 }else{
  rows=[{q:'',a:id==='truth'?'صح':'',g:'عام'}];
  $('activityTitle').value='';$('subject').value='عام';$('grade').value='عام';$('roundTime').value='25';
  window.BOOYAH_LAB_BOOK_ID='';window.BOOYAH_LAB_IMAGE_ID='';window.BOOYAH_LAB_SOURCE_GROUP='';
 }
 paint();
 if(!opts.silent)notice(b?'↩ تم فتح مسودة '+schema(id).label+' الخاصة، دون تغيير أي قالب آخر.':'ابدأ بكتابة الأسئلة الخاصة بقالب '+schema(id).label+'.');
}
function importRows(modeId,data,owned){
 const copy={...data,rows:(data.rows||[]).map(x=>({...x}))};
 if(!owned)delete copy.activityId;
 drafts[modeId]=copy;persist();
 if(mode===modeId){activate(modeId,{silent:true});notice('✓ فُتحت أسئلة '+schema(mode).label+' لتعديلها داخل قالبها فقط.')}
}
add.onclick=()=>{
 if(rows.length>=80){notice('الحد الأعلى 80 سؤالًا.',true);return}
 rows.push({q:'',a:mode==='truth'?'صح':'',g:'عام'});paint();capture();
 list.lastElementChild?.querySelector('textarea')?.focus({preventScroll:true});
 list.lastElementChild?.scrollIntoView({block:'nearest',behavior:'smooth'})
};
preview.onclick=()=>{if(check())window.TAG_LAB_V32_PREVIEW?.(mode,false)};
document.addEventListener('taglab:before-template-switch',e=>{if(e.detail?.from===mode&&e.detail.to!==mode)capture()});
document.addEventListener('taglab:template-selected',e=>{
 if(e.detail?.to&&e.detail.to!==mode){
  window.TAG_LAB_V33_CLEAR_SAVED?.();
  activate(e.detail.to)
 }
});
document.addEventListener('gamelab:book-bank-accepted',e=>{
 if(e.detail?.editingExisting)return;
 const saved=window.TG_QUESTION_BANK_ROWS;
 if(Array.isArray(saved)&&saved.length){
  importRows(mode,{rows:saved,title:$('activityTitle')?.value||'',subject:$('subject')?.value||'عام',
   grade:$('grade')?.value||'عام',time:$('roundTime')?.value||'25',bookId:window.BOOYAH_LAB_BOOK_ID||''})
 }
});
document.addEventListener('taglab:saved-activity-opened',e=>{
 const p=e.detail?.activity;
 if(!p||!Array.isArray(p.rows))return;
 const dest=p.mode||'quiz';
 if(dest!==mode){
  window.TAG_LAB_V33_SELECT?.(dest);
  mode=dest;
 }
 importRows(dest,{rows:p.rows,title:p.title||'',subject:p.subject||'عام',
  grade:p.grade||'عام',time:String(p.time||25),bookId:p.bookId||'',
  imageId:p.imageId||'',sourceGroup:p.sourceGroup||''},true);
});
document.addEventListener('taglab:activity-saved',e=>{
 if(e.detail?.id){capture();drafts[mode].activityId=e.detail.id;persist()}
});
for(const id of ['activityTitle','subject','grade','roundTime'])$(id)?.addEventListener('change',capture);
$('activityTitle')?.addEventListener('input',capture);
document.addEventListener('click',e=>{
 const button=e.target.closest('button');
 if(!button)return;
 if(button.id==='cloudSave'||button.id==='v33Preview'||button.textContent.includes('حفظ في مكتبتي')){
  if(!check()){e.preventDefault();e.stopImmediatePropagation();editor.scrollIntoView({block:'start',behavior:'smooth'})}
 }
},true);
window.TAG_LAB_V33_CHECK=check;
window.TAG_LAB_V33_IMPORT=importRows;
window.TAG_LAB_V33_MODE=()=>mode;
window.TAG_LAB_V33_SELECT=id=>{
 if(!id||id===mode)return;
 if(typeof window.TAG_LAB_V32_CHOOSE==='function'){window.TAG_LAB_V32_CHOOSE(id);return}
 const t=$('cloudMode');if(!t)return;
 document.dispatchEvent(new CustomEvent('taglab:before-template-switch',{detail:{from:mode,to:id}}));
 t.value=id;t.dispatchEvent(new Event('change',{bubbles:true}));
 document.dispatchEvent(new CustomEvent('taglab:template-selected',{detail:{from:mode,to:id}}))
};
if(isBookImport){
 importRows(mode,{rows:window.TG_QUESTION_BANK_ROWS.map(x=>({...x})),
  title:$('activityTitle')?.value||'',subject:$('subject')?.value||'عام',
  grade:$('grade')?.value||'عام',time:$('roundTime')?.value||'25',bookId:window.BOOYAH_LAB_BOOK_ID||''})
}else activate(mode,{silent:true});
})();
