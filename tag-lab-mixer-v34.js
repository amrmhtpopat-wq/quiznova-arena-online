/* TAG LAB Game Mixer V34: choose an existing owned activity and run three sequential classroom games. */
(()=>{'use strict';
if(document.documentElement.dataset.tagView!=='mixer')return;
const $=id=>document.getElementById(id);
const outer=$('mixer');if(!outer)return;
const box=document.createElement('section');box.id='tagMixerLibrary';
const head=document.createElement('h2');head.textContent='1. اختر درسًا محفوظًا من مكتبتك';
const help=document.createElement('p');help.textContent='اختر نشاطًا واحدًا؛ سنستخدم أسئلته في ثلاث ألعاب متتالية، دون تعديل النشاط أو إعادة التوليد.';
const select=document.createElement('select');select.id='tagMixerActivity';select.setAttribute('aria-label','اختر نشاطًا محفوظًا');
const opt=document.createElement('option');opt.value='';opt.textContent='سجّل الدخول ثم اختر النشاط';select.append(opt);
const status=document.createElement('p');status.id='tagMixerStatus';status.setAttribute('role','status');status.textContent='بانتظار تسجيل دخول المعلم وتحميل مكتبة الأنشطة.';
const actions=document.createElement('div');actions.className='tag-simple-actions';
const library=document.createElement('a');library.href='/tag-lab-library.html';library.className='tag-simple-btn alt';library.textContent='🗂️ افتح مكتبتي';
const reload=document.createElement('button');reload.type='button';reload.className='tag-simple-btn alt';reload.textContent='↻ تحديث القائمة';
actions.append(reload,library);box.append(head,help,select,actions,status);outer.prepend(box);
let items=[];
const start=$('mixerStart');start.disabled=true;
function selectRows(item){
 if(!item||!item.activity?.rows?.length){
  $('activityData').value='';start.disabled=true;status.textContent='اختر نشاطًا يحتوي على أربعة أسئلة على الأقل.';return
 }
 const p=item.activity;
 if(p.rows.length<4){start.disabled=true;status.textContent='النشاط المحدد لا يضم أربعة أسئلة صالحة.';return}
 const q=new Set(p.rows.map(r=>String(r.q||'').trim()).filter(Boolean));
 if(q.size<4){start.disabled=true;status.textContent='النشاط المحدد يحتاج إلى أربعة أسئلة مختلفة على الأقل.';return}
 $('activityData').value=p.rows.map(r=>r.q+' | '+r.a+' | '+(r.g||'عام')+(r.sourcePage?' | '+r.sourcePage:'')).join('\n');
 window.TG_QUESTION_BANK_ROWS=p.rows.map(x=>({...x}));
 window.TG_CREATOR_PREVIEW_ROWS=p.rows.map(x=>({...x}));
 $('activityTitle').value=p.title;
 if([...$('subject').options].some(o=>o.value===p.subject))$('subject').value=p.subject;
 if([...$('grade').options].some(o=>o.value===p.grade))$('grade').value=p.grade;
 $('applyContent')?.click();
 start.disabled=false;
 status.textContent='✓ جاهز: «'+p.title+'» • '+p.rows.length+' سؤالًا. اختر الألعاب الثلاث واضغط «تشغيل الحصة التفاعلية».';
}
function render(){
 const current=select.value;
 select.replaceChildren();
 const empty=document.createElement('option');empty.value='';empty.textContent=items.length?'اختر النشاط الذي تريد تحويله إلى حصة':'لا توجد أنشطة محفوظة بعد';
 select.append(empty);
 for(const item of items){
  if(!item.activity?.rows?.length)continue;
  const o=document.createElement('option');o.value=item.id;
  o.textContent=(item.title||'نشاط')+' • '+item.questionCount+' أسئلة • '+(item.published?'منشور':'مسودة');
  select.append(o)
 }
 if(current&&items.some(x=>x.id===current))select.value=current;
 if(select.value)selectRows(items.find(x=>x.id===select.value));
 else{start.disabled=true;status.textContent=items.length?'اختر درسًا من القائمة، ثم حدّد الألعاب الثلاث.':'أنشئ نشاطًا واحفظه في مكتبتك أولًا.'}
}
document.addEventListener('gamelab:library',e=>{
 items=Array.isArray(e.detail?.items)?e.detail.items:[];
 render()
});
select.onchange=()=>selectRows(items.find(x=>x.id===select.value));
reload.onclick=()=>{$('cloudRefresh')?.click();status.textContent='جارٍ تحديث الأنشطة...'};
start.addEventListener('click',e=>{
 if(!select.value||!items.find(x=>x.id===select.value)){
  e.preventDefault();e.stopImmediatePropagation();start.disabled=true;status.textContent='اختر نشاطًا محفوظًا أولًا.'
 }
},true);
const sectionHeading=outer.querySelector('.section-head h2');
if(sectionHeading)sectionHeading.textContent='2. اختر ثلاثة ألعاب لرحلة الحصة';
const actionsBar=outer.querySelector('.buttons');
if(actionsBar){
 const note=document.createElement('p');note.style.cssText='font-size:.83rem;color:#496b82;margin:10px 0';
 note.textContent='اللعبة الأولى للتمهيد، الثانية للتفاعل، والثالثة للتقويم الختامي. الحصة تعمل على شاشة المعلم؛ التحدي المتزامن له صفحة منفصلة.';
 actionsBar.after(note)
}
})();
