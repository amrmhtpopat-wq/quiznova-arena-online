/* TeachGame Game Lab V9: specialized template guidance, persistent lesson images,
 * class results and secure CSV exports. QA-only; the official site is untouched.
 */
(()=>{
'use strict';
const D=document,$=id=>D.getElementById(id);
const MODE=new URL(location.href).searchParams.get('mode')||'quiz';
const PERSONAL={
 quiz:['🎯','مسابقة الاختيار','أدخل سؤالًا وإجابة واحدة صحيحة، ويمكنك كتابة 3 مشتتات بنفسك.'],
 fast:['⚡','سباق الوقت','اكتب أسئلة قصيرة بأربع خيارات، واضبط زمن الإجابة من إعدادات النشاط.'],
 truth:['✅','صح أم خطأ','اكتب سؤالًا وإجابته المرجعية؛ تُعرض العلاقة للطالب ويقرر إن كانت صحيحة.'],
 pairs:['🧩','المطابقة','اكتب المفهوم في خانة السؤال والتعريف المطابق في خانة الإجابة؛ تجنب تكرار التعريفات.'],
 memory:['🧠','ذاكرة الأزواج','كل صف يمثل زوجًا من بطاقتين. حاول أن تجعل نصوصها قصيرة وواضحة.'],
 flash:['🃏','بطاقات التقليب','الوجه الأمامي مفهوم أو سؤال؛ الوجه الخلفي شرح أو إجابة.'],
 sort:['🗂️','فرز وتصنيف','اكتب العنصر في خانة الإجابة واكتب مجموعته الصحيحة في خانة المجموعة. استخدم مجموعتين على الأقل.'],
 anagram:['🔤','ترتيب الحروف','الإجابة هي الكلمة التي سيعيد الطالب ترتيب حروفها، والسؤال هو التلميح.'],
 crossword:['🔠','الكلمات المتقاطعة','اكتب تعريفًا وإجابة قصيرة من حرفين إلى عشرة حروف لتناسب الشبكة.'],
 wordsearch:['🔎','البحث عن الكلمات','اكتب مفردات من 2 إلى 12 حرفًا؛ تظهر داخل شبكة الحروف مع قائمة الكلمات.'],
 order:['🪜','الترتيب المنطقي','اكتب الخطوات بالترتيب الصحيح من الأعلى للأسفل، ثم استخدم ↑ ↓ لتعديل ترتيبها.'],
 maze:['🌀','متاهة المعرفة','كل إجابة صحيحة تفتح محطة جديدة في الطريق حتى الوصول إلى نهاية المتاهة.'],
 balloons:['🎈','البالونات','استخدم إجابات قصيرة كي تظل النصوص مقروءة داخل البالونات المتحركة.'],
 hidden:['🖼️','كشف الصورة','اختر صورة للنشاط، ثم اكتب الأسئلة والأجوبة التي يكتشفها الطالب أثناء فتح الأجزاء.'],
 cloze:['✍️','أكمل الفراغ','اكتب الجملة مع ___ حيث تريد الفراغ، واكتب الكلمة الناقصة في الإجابة.'],
 diagram:['📍','تسمية الرسم','ارفع صورة الرسم ثم حدد لكل سؤال موضع العلامة X وY كنسبة من 0 إلى 100.'],
 board:['🏆','لوحة النقاط','اكتب أسئلة الفرق، ثم خصص أسماء المجموعات. النقاط في عرض المعلم قابلة للإضافة والخصم.'],
 teams:['⚔️','معركة الفرق','ادخل أسئلة تنافسية وأسماء الفريقين؛ سيتناوبان على الإجابة وجمع النقاط.'],
 survey:['📊','استفتاء الصف','اكتب سؤال التصويت في خانة السؤال، وكل صف يمثل خيارًا من خيارات التصويت.'],
 exit:['🎟️','بطاقة الخروج','اكتب سؤالًا تأمليًا وأضف إجابة استرشادية للمعلم؛ الإجابات النصية لا تمنح نقاطًا تلقائيًا.'],
 story:['🧭','اختر مسارك','كل صف مرحلة من القصة فيها موقف وقرار صحيح وثلاثة مسارات خاطئة اختيارية.'],
 bingo:['⭐','بينغو','أدخل مصطلحات متنوعة وإجابات قصيرة، ويفضل 9 مصطلحات مختلفة على الأقل.'],
 wheel:['🎡','عجلة الحظ','كل صف سؤال وإجابته؛ تُسحب الأسئلة دون تكرار حتى تنتهي الجولة.'],
 boxes:['🎁','الصناديق','كل صف صندوق. الضغطة الأولى تكشف السؤال والثانية تكشف الإجابة.']
};
let imageObjectUrl='',lastReport=null,lastTitle='';
const isImage=MODE==='hidden'||MODE==='diagram',isTeams=MODE==='teams'||MODE==='board';
function token(){try{return localStorage.getItem('qn9_teacher_token')||''}catch(_){return ''}}
function notice(t,error=false){const area=$('v9ImageStatus');if(area){area.textContent=t;area.classList.toggle('v9-error',error)}}
function draftMerge(obj){
 try{
  const key='tg_lab_creator_v8_'+MODE;
  const existing=JSON.parse(localStorage.getItem(key)||'{}');
  localStorage.setItem(key,JSON.stringify({...existing,...obj}));
 }catch(_){}
}
function setImageId(id,preview){
 $('v9ImageId').value=id||'';
 draftMerge({imageId:id||''});
 if(preview)showPreview(preview);
}
function showPreview(src){
 const el=$('v9ImagePreview');el.replaceChildren();
 if(imageObjectUrl){URL.revokeObjectURL(imageObjectUrl);imageObjectUrl=''}
 if(!src){el.hidden=true;return}
 const img=D.createElement('img');img.alt='معاينة صورة النشاط';img.src=src;
 el.append(img);el.hidden=false;
}
function showMode(){
 const p=PERSONAL[MODE]||PERSONAL.quiz;
 $('v9ModeIcon').textContent=p[0];$('v9ModeHeading').textContent=p[1];
 $('v9ModeSubtitle').textContent=p[2];
 const info=$('v9ModeInstructions');
 info.textContent=p[2];
 info.dataset.mode=MODE;
 $('v9ImageControls').hidden=!isImage;
 $('v9TeamsControls').hidden=!isTeams;
 $('v9Team3Field').hidden=MODE==='teams';
 if(isImage&&$('v9ImageId').value)notice('تم تحديد صورة محفوظة في حسابك. يمكن استبدالها بصورة جديدة.');
 for(const id of ['v9Team1','v9Team2','v9Team3']){
  $(id).addEventListener('input',()=>draftMerge({teamNames:[$('v9Team1').value,$('v9Team2').value,...(MODE==='board'?[$('v9Team3').value]:[])]}));
 }
}
async function jsonRequest(path,method='GET',body){
 const h={Authorization:'Bearer '+token()};
 if(body!==undefined)h['Content-Type']='application/json';
 const response=await fetch(path,{method,headers:h,body:body===undefined?undefined:JSON.stringify(body),cache:'no-store'});
 let data;try{data=await response.json()}catch(_){throw Error('تعذر قراءة استجابة الخدمة')}
 if(!response.ok||!data.ok)throw Error(data.error||'تعذر إكمال العملية');
 return data;
}
async function chooseImage(){
 const file=$('v9ImageUpload').files?.[0];if(!file)return;
 if(!['image/png','image/jpeg','image/webp'].includes(file.type)){notice('اختر PNG أو JPG أو WEBP فقط.',true);return}
 if(file.size>1500000){notice('الحد الأقصى 1.5 ميجابايت للصورة.',true);return}
 setImageId('');
 if(imageObjectUrl)URL.revokeObjectURL(imageObjectUrl);
 imageObjectUrl=URL.createObjectURL(file);
 const img=D.createElement('img');img.alt='صورة النشاط المختارة';img.src=imageObjectUrl;
 $('v9ImagePreview').replaceChildren(img);$('v9ImagePreview').hidden=false;
 notice('الصورة جاهزة للمعاينة. اضغط «رفع الصورة للحفظ الدائم» قبل النشر.');
 // Same-origin frame can use this limited-lived preview asset without exposing it publicly.
 const reader=new FileReader();
 reader.onload=()=>{
  try{sessionStorage.setItem('tg_game_lab_v9_preview_image',String(reader.result).slice(0,2100000))}catch(_){}
 };
 reader.readAsDataURL(file);
}
async function uploadImage(){
 const file=$('v9ImageUpload').files?.[0];if(!file){notice('اختر صورة أولًا.',true);return}
 if(!token()){notice('سجّل دخول المعلم من خطوة الحفظ أولًا، ثم ارجع لرفع الصورة.',true);return}
 if(file.size>1500000||!['image/png','image/jpeg','image/webp'].includes(file.type)){notice('نوع الصورة أو حجمها غير مسموح.',true);return}
 const b=$('v9UploadButton');b.disabled=true;notice('جارٍ رفع الصورة إلى المكتبة الدائمة...');
 try{
  const base64=await new Promise((resolve,reject)=>{
   const r=new FileReader();r.onload=()=>resolve(String(r.result).split(',')[1]||'');r.onerror=()=>reject(Error('تعذر قراءة الملف'));r.readAsDataURL(file);
  });
  const res=await jsonRequest('/api/game-lab/pro/media/upload','POST',{filename:file.name,mime:file.type,data:base64});
  if(!res.image?.id)throw Error('لم تعُد معرف الصورة');
  setImageId(res.image.id);notice('✓ حُفظت الصورة في مكتبة حساب المعلم.');
  await loadImages();
 }catch(e){notice('فشل رفع الصورة: '+e.message,true)}
 finally{b.disabled=false}
}
async function loadImages(){
 if(!token()){notice('سجّل دخول المعلم لفتح مكتبة الصور.',true);return}
 const target=$('v9MediaLibrary');const current=$('v9ImageId').value;
 try{
  const d=await jsonRequest('/api/game-lab/pro/media');
  target.replaceChildren(new Option('— صور حسابك المحفوظة —',''));
  for(const item of d.images||[])target.append(new Option(item.name||'صورة',item.id));
  target.value=current;
  notice('توجد '+(d.images||[]).length+' صورة في مكتبتك.');
 }catch(e){notice('تعذر فتح مكتبة الصور: '+e.message,true)}
}
async function selectStoredImage(id){
 if(!id)return;
 $('v9ImageUpload').value='';setImageId(id);
 try{
  const response=await fetch('/api/game-lab/pro/image?id='+encodeURIComponent(id),{headers:{Authorization:'Bearer '+token()},cache:'no-store'});
  if(!response.ok)throw Error('تعذر تحميل صورة الحساب');
  const b=await response.blob();
  if(imageObjectUrl)URL.revokeObjectURL(imageObjectUrl);
  imageObjectUrl=URL.createObjectURL(b);
  const img=D.createElement('img');img.alt='صورة من المكتبة';img.src=imageObjectUrl;
  $('v9ImagePreview').replaceChildren(img);$('v9ImagePreview').hidden=false;
  const reader=new FileReader();
  reader.onload=()=>{try{sessionStorage.setItem('tg_game_lab_v9_preview_image',String(reader.result))}catch(_){}};
  reader.readAsDataURL(b);
  notice('✓ اخترت الصورة المحفوظة للاستخدام في اللعبة.');
 }catch(e){notice(e.message,true)}
}
function td(row,value){
 const cell=D.createElement('td');cell.textContent=String(value??'');row.append(cell);
}
const formatDate=t=>{if(!Number(t))return '—';return new Date(Number(t)*1000).toLocaleString('ar-JO')};
function exportCSV(){
 if(!lastReport)return;
 const header=['الترتيب','اسم الطالب','الشعبة','الصحيح','الأسئلة','النسبة المئوية','النقاط','تاريخ الإنجاز'];
 const safeCsv=x=>{
  let value=String(x??'');
  // Prevent spreadsheet formula injection in student-supplied names.
  if(/^[\s]*[=+\-@]/.test(value))value="'"+value;
  return '"'+value.replace(/"/g,'""')+'"';
 };
 const ordered=[...(lastReport.results||[])].sort((a,b)=>b.score-a.score||b.correct-a.correct);
 const data=[header,...ordered.map((r,i)=>[i+1,r.name,r.className,r.correct,r.questions,
  Math.round(r.correct*100/Math.max(1,r.questions)),r.score,formatDate(r.finishedAt)])];
 const csv='\ufeff'+data.map(row=>row.map(safeCsv).join(',')).join('\r\n');
 const href=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
 const a=D.createElement('a');a.href=href;a.download='TeachGame-results-'+String(Date.now())+'.csv';
 D.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(href),2000);
}
function renderReport(data,title){
 lastReport=data;lastTitle=title;
 $('v9ReportTitle').textContent='نتائج: '+title;
 $('v9ReportSummary').textContent='المشاركات المكتملة: '+data.total+' • متوسط الإجابات الصحيحة: '+data.averagePercent+'%';
 const skills=$('v9ReportSkills');skills.replaceChildren();
 if(!(data.skillSummary||[]).length){
  const e=D.createElement('p');e.textContent='لا يوجد تحليل مهارات بعد؛ سيظهر عند إكمال الطلاب للأنشطة الجديدة.';skills.append(e);
 }
 for(const skill of data.skillSummary||[]){
  const card=D.createElement('div');card.className='v9-skill-card';
  const text=D.createElement('strong');text.textContent=skill.group+' — '+skill.percent+'%';
  const track=D.createElement('div');track.className='v9-skill-track';
  const fill=D.createElement('span');fill.style.width=skill.percent+'%';track.append(fill);
  const small=D.createElement('small');small.textContent=skill.correct+' صحيحة من '+skill.answers;
  card.append(text,track,small);skills.append(card);
 }
 const target=$('v9ReportRows');target.replaceChildren();
 const sorted=[...(data.results||[])].sort((a,b)=>b.score-a.score||b.correct-a.correct);
 if(!sorted.length){
  const tr=D.createElement('tr'),cell=D.createElement('td');cell.colSpan=7;cell.textContent='لا توجد محاولات مكتملة بعد.';tr.append(cell);target.append(tr);
 }
 sorted.forEach((r,i)=>{
  const row=D.createElement('tr');[i+1,r.name,r.className,r.correct+' / '+r.questions,
   Math.round(r.correct*100/Math.max(1,r.questions))+'%',r.score,formatDate(r.finishedAt)].forEach(v=>td(row,v));
  target.append(row);
 });
 const question=$('v9QuestionAnalysis');question.replaceChildren();
 for(const item of (data.questionStats||[]).filter(q=>q.percent<60)){
  const p=D.createElement('p');p.textContent='السؤال '+(item.index+1)+': '+item.percent+'% إجابات صحيحة — يحتاج مراجعة';question.append(p);
 }
 $('v9ReportPanel').hidden=false;$('v9ReportPanel').scrollIntoView({behavior:'smooth',block:'nearest'});
}
async function openReport(button){
 if(!token()){alert('سجّل دخول المعلم لعرض النتائج.');return}
 $('v9ReportPanel').hidden=false;$('v9ReportSummary').textContent='جارٍ تحميل النتائج...';
 try{
  const id=button.dataset.id;
  if(!/^[a-f0-9]{32}$/.test(id))throw Error('نشاط غير صالح');
  const result=await jsonRequest('/api/game-lab/teacher/reports?id='+encodeURIComponent(id));
  renderReport(result,button.dataset.title||'النشاط');
 }catch(e){$('v9ReportSummary').textContent='تعذر جلب النتائج: '+e.message}
}
function start(){
 if(!$('v9ModeOptions'))return;
 showMode();
 if(isImage){
  $('v9ImageUpload').addEventListener('change',chooseImage);
  $('v9UploadButton').addEventListener('click',uploadImage);
  $('v9LoadImages').addEventListener('click',loadImages);
  $('v9MediaLibrary').addEventListener('change',e=>selectStoredImage(e.target.value));
 }
 $('libraryItems').addEventListener('click',e=>{
  const button=e.target.closest('.v9-open-report');if(button)openReport(button);
 });
 $('v9ExportCsv').addEventListener('click',exportCSV);
 $('v9CloseReport').addEventListener('click',()=>{$('v9ReportPanel').hidden=true});
}
if(D.readyState==='loading')D.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();