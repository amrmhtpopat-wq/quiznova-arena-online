/* TeachGame Game Lab V8 | QA teacher creator, 24 templates */
(()=>{
'use strict';
const D=document,$=id=>D.getElementById(id),KEY='tg_lab_creator_v8_',PREVIEW='tg_game_lab_creator_preview_v8',TOKEN='qn9_teacher_token';
const MODES=[
 ['quiz','تحدي الاختيار','🎯','اختر الإجابة الصحيحة'],
 ['fast','سباق الوقت','⚡','أجب قبل انتهاء الوقت'],
 ['pairs','توصيل الأزواج','🧩','طابق الأسئلة بالإجابات'],
 ['flash','بطاقات الذاكرة','🃏','اقلب البطاقات'],
 ['wheel','عجلة الحظ','🎡','أدر العجلة للكشف عن السؤال'],
 ['boxes','الصناديق الغامضة','🎁','افتح الصناديق المفاجئة'],
 ['sort','فرز وتصنيف','🗂️','صنّف الإجابات إلى مجموعات'],
 ['truth','صح أم خطأ','✅','تحقق من العلاقة بين السؤال والإجابة'],
 ['crossword','الكلمات المتقاطعة','🔠','أكمل شبكة المفردات'],
 ['wordsearch','البحث عن الكلمات','🔎','اكتشف الكلمات داخل الشبكة'],
 ['anagram','ترتيب الحروف','🔤','ركّب الحروف لتكوين الإجابة'],
 ['order','الترتيب المنطقي','🪜','رتّب الخطوات والمعلومات'],
 ['maze','متاهة المعرفة','🌀','اعبر المتاهة بالمعلومات الصحيحة'],
 ['balloons','فرقعة البالونات','🎈','اصطد الإجابة في بالون'],
 ['memory','لعبة الذاكرة','🧠','اكتشف أزواج البطاقات'],
 ['hidden','الصورة المخفية','🖼️','اكشف الصورة المخفية'],
 ['cloze','أكمل الفراغ','✍️','اكتب الكلمة الناقصة'],
 ['diagram','تسمية الرسم','📍','تعرّف على أجزاء الرسم'],
 ['board','لوحة النقاط','🏆','تنافس في جمع النقاط'],
 ['teams','معركة الفرق','⚔️','نافِس ضمن فريقك'],
 ['survey','تصويت الصف','📊','اجمع آراء الطلاب'],
 ['exit','بطاقة الخروج','🎟️','اختبر فهم الطلاب في النهاية'],
 ['story','اختر مسارك','🧭','اعبر مسارات القصة'],
 ['bingo','بينغو','⭐','أكمل شبكة بينغو']
];
const modes=new Map(MODES.map(a=>[a[0],a])),choiceModes=new Set(['quiz','fast','maze','balloons','bingo','story','board','teams','hidden']);
const params=new URL(location.href).searchParams;
let mode=modes.has(params.get('mode'))?params.get('mode'):'quiz',rows=[],cloudId='',token='',activeStep=2,toastTimer=0;
const sample=[
 {q:'ما الجزء الذي ينفذ التعليمات؟',a:'CPU',g:'مكونات الحاسوب',wrongs:['RAM','SSD','الشاشة']},
 {q:'أين تُخزن البيانات مؤقتًا أثناء التشغيل؟',a:'RAM',g:'مكونات الحاسوب',wrongs:['CPU','SSD','لوحة المفاتيح']},
 {q:'ما أداة إدخال النصوص؟',a:'لوحة المفاتيح',g:'إدخال',wrongs:['الفأرة','الشاشة','السماعات']},
 {q:'ما وحدة تخزين الملفات الدائمة؟',a:'SSD',g:'تخزين',wrongs:['RAM','CPU','الكاميرا']},
 {q:'ما الجهاز الذي يعرض الصور؟',a:'الشاشة',g:'إخراج',wrongs:['المايكروفون','الفأرة','المعالج']},
 {q:'ما وظيفة اللوحة الأم؟',a:'ربط المكونات',g:'مكونات الحاسوب',wrongs:['طباعة الصور','إخراج الصوت','إدخال الأحرف']},
 {q:'ما أداة تحريك مؤشر الشاشة؟',a:'الفأرة',g:'إدخال',wrongs:['الشاشة','السماعات','الطابعة']},
 {q:'ما الجهاز المستخدم لإخراج الصوت؟',a:'السماعات',g:'إخراج',wrongs:['لوحة المفاتيح','الكاميرا','الفأرة']}
];
const blank=()=>({q:'',a:'',g:'عام',wrongs:['','','']});
const norm=s=>String(s??'').trim();
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function alertMsg(msg,error=false){
 const e=$('toast');clearTimeout(toastTimer);e.textContent=msg;e.className='toast'+(error?' error':'');e.hidden=false;
 toastTimer=setTimeout(()=>e.hidden=true,4200);
}
function normalizeRow(r){
 const a=norm(r.a);const wrongs=Array.isArray(r.wrongs)?r.wrongs.slice(0,3):Array.isArray(r.choices)?r.choices.filter(x=>norm(x).toLocaleLowerCase()!==a.toLocaleLowerCase()).slice(0,3):[];
 while(wrongs.length<3)wrongs.push('');
 return {q:norm(r.q),a,g:norm(r.g)||'عام',wrongs,sourcePage:r.sourcePage||''};
}
function summary(){
 $('questionCount').textContent=String(rows.length);
 $('progressFill').style.width=(rows.length?Math.round(rows.filter(r=>norm(r.q)&&norm(r.a)).length*100/rows.length):0)+'%';
 $('modeShort').textContent=mode.toUpperCase();$('draftStatus').textContent=cloudId?'على حسابك':'مسودة محلية';
 $('previewName').textContent=modes.get(mode)[1];$('posterIcon').textContent=modes.get(mode)[2];
 $('previewSummary').textContent=rows.length+' أسئلة ضمن قالب '+modes.get(mode)[1];
 $('saveActivityName').textContent=$('activityTitle').value||'نشاط جديد';
 $('saveActivityMeta').textContent=rows.length+' أسئلة · '+modes.get(mode)[1]+' · '+$('grade').value;
}
function localSave(){
 try{localStorage.setItem(KEY+mode,JSON.stringify({version:8,mode,id:cloudId,title:$('activityTitle').value,subject:$('subject').value,grade:$('grade').value,time:$('roundTime').value,rows,updatedAt:Date.now()}))}catch(_){}
 summary();
}
function restore(){
 let d;try{d=JSON.parse(localStorage.getItem(KEY+mode)||'null')}catch(_){}
 if(d?.version===8&&Array.isArray(d.rows)&&d.rows.length>0&&d.rows.length<=80){
  rows=d.rows.map(normalizeRow);cloudId=d.id||'';
  $('activityTitle').value=d.title||'';
  for(const id of ['subject','grade'])if([...$(id).options].some(x=>x.value===d[id]))$(id).value=d[id];
  if([...$('roundTime').options].some(x=>x.value===String(d.time)))$('roundTime').value=String(d.time);
 }else{rows=Array.from({length:4},blank)}
}
function modeInfo(){
 const m=modes.get(mode);$('modeIcon').textContent=m[2];$('modeTitle').textContent=m[1];$('modeDesc').textContent=m[3];
 $('selectedLargeIcon').textContent=m[2];$('selectedLargeName').textContent=m[1];$('selectedLargeDesc').textContent=m[3];
 $('modeSelect').value=mode;
 $('modeCapability').textContent=choiceModes.has(mode)?'أضف خيارات خاطئة يدويًا أو اتركها فارغة للتوليد التلقائي.':mode==='truth'?'ضع السؤال والإجابة المرجعية. ستظهر للطالب عبارة «صح أم خطأ».':mode==='sort'?'يجب تقسيم الإجابات إلى مجموعتين مختلفتين على الأقل.':'كل قالب يطبّق آلية لعب خاصة على السؤال وإجابته.';
 $('modeHelp').textContent=choiceModes.has(mode)?'يمكنك إضافة ثلاثة خيارات خاطئة لكل سؤال.':'اكتب السؤال وإجابته، وسيتولى القالب تحويلهما إلى اللعبة.';
}
function step(n,force=false){
 if(!force&&n>=3&&!valid()){step(2,true);return}
 activeStep=n;
 for(let i=1;i<=4;i++){
  D.querySelector('[data-panel="'+i+'"]').hidden=i!==n;
  const b=D.querySelector('[data-step="'+i+'"]');b.classList.toggle('active',n===i);b.classList.toggle('done',i<n);b.setAttribute('aria-current',n===i?'step':'false');
 }
 $('libraryPanel').hidden=true;
 if(n===4)authCheck();
 window.scrollTo(0,0);
}
function renderRows(){
 const holder=$('questionList');holder.replaceChildren();
 rows.forEach((r,i)=>{
  const d=D.createElement('details');d.className='question-card';d.dataset.index=i;d.open=i===0;
  const wrong=choiceModes.has(mode)?'<div class="question-options-title">🧩 خيارات خاطئة (اختيارية)</div><div class="question-grid">'+[0,1,2].map(j=>'<label class="field"><span>الخيار الخاطئ '+(j+1)+'</span><input data-wrong="'+j+'" maxlength="100" value="'+esc(r.wrongs[j])+'" placeholder="اكتب خيارًا غير صحيح"></label>').join('')+'</div>':'';
  d.innerHTML='<summary><span class="question-index">'+(i+1)+'</span><span class="question-summary'+(!r.q?' empty':'')+'">'+esc(r.q||'اضغط لكتابة السؤال')+'</span><span class="question-badge">'+(r.a?'✓ إجابة محددة':'مطلوب')+'</span></summary>'+
  '<div class="question-content"><label class="field"><span>السؤال '+(i+1)+' <sup>*</sup></span><input data-field="q" maxlength="200" value="'+esc(r.q)+'" placeholder="نص السؤال"></label>'+
  '<div class="question-grid"><label class="field"><span class="correct-label">✓ الإجابة الصحيحة <sup>*</sup></span><input data-field="a" class="correct-input" maxlength="100" value="'+esc(r.a)+'" placeholder="الإجابة المعتمدة"></label>'+
  '<label class="field"><span>المجموعة / الوحدة</span><input data-field="g" maxlength="60" value="'+esc(r.g)+'" placeholder="مثال: الوحدة الأولى"></label></div>'+wrong+
  '<div class="question-actions"><div><button type="button" data-move="-1" class="btn btn-ghost move-question">↑ أعلى</button> <button type="button" data-move="1" class="btn btn-ghost move-question">↓ أسفل</button></div><button type="button" data-delete="'+i+'" class="btn btn-ghost delete-question">🗑 حذف السؤال</button></div></div>';
  holder.append(d);
 });
 summary();
}
function changeRow(e){
 const input=e.target.closest('input[data-field],input[data-wrong]');if(!input)return;
 const card=input.closest('.question-card');if(!card)return;
 const i=Number(card.dataset.index);if(!rows[i])return;
 if(input.hasAttribute('data-field'))rows[i][input.dataset.field]=input.value;
 else rows[i].wrongs[Number(input.dataset.wrong)]=input.value;
 card.querySelector('.question-summary').textContent=rows[i].q||'اضغط لكتابة السؤال';
 card.querySelector('.question-badge').textContent=norm(rows[i].a)?'✓ إجابة محددة':'مطلوب';
 localSave();
}
function actionRow(e){
 const b=e.target.closest('[data-delete],[data-move]');if(!b)return;
 const card=b.closest('.question-card'),i=Number(card?.dataset.index);if(!rows[i])return;
 if(b.hasAttribute('data-delete')){
  if(rows.length<=4){alertMsg('يجب إبقاء 4 أسئلة على الأقل.',true);return}
  rows.splice(i,1);
 }else{
  const j=i+Number(b.dataset.move);if(j<0||j>=rows.length)return;
  [rows[i],rows[j]]=[rows[j],rows[i]];
 }
 localSave();renderRows();
}
function addRow(){
 if(rows.length>=80){alertMsg('الحد الأعلى 80 سؤالًا.',true);return}
 rows.push(blank());localSave();renderRows();
 const card=$('questionList').lastElementChild;card.open=true;
 card.querySelector('[data-field="q"]').focus({preventScroll:true});card.scrollIntoView({block:'nearest'});
}
function valid(){
 if(!norm($('activityTitle').value)){alertMsg('اكتب اسمًا للنشاط.',true);$('activityTitle').focus({preventScroll:true});return false}
 if(rows.length<4||rows.length>80){alertMsg('أدخل من 4 إلى 80 سؤالًا.',true);return false}
 const unique=new Set(),groups=new Set();
 for(let i=0;i<rows.length;i++){
  const r=rows[i],q=norm(r.q),a=norm(r.a);
  if(!q||!a){
   alertMsg('أكمل السؤال والإجابة في البطاقة رقم '+(i+1),true);
   step(2,true);const c=$('questionList').children[i];c.open=true;c.querySelector('[data-field="'+(!q?'q':'a')+'"]').focus();return false
  }
  const key=(q+'|'+a).toLocaleLowerCase();
  if(unique.has(key)){alertMsg('السؤال رقم '+(i+1)+' مكرر.',true);return false}
  unique.add(key);groups.add(norm(r.g).toLocaleLowerCase());
  const others=r.wrongs.map(norm).filter(Boolean);
  const keys=[a,...others].map(x=>x.toLocaleLowerCase());
  if(new Set(keys).size!==keys.length){alertMsg('في السؤال '+(i+1)+' خيار مكرر أو يساوي الإجابة الصحيحة.',true);return false}
 }
 if(mode==='sort'&&groups.size<2){alertMsg('لعبة التصنيف تحتاج مجموعتين مختلفتين على الأقل.',true);return false}
 return true;
}
function payload(){
 return {title:norm($('activityTitle').value).slice(0,90),subject:$('subject').value,grade:$('grade').value,
  mode,time:Number($('roundTime').value)||25,
  rows:rows.map(r=>{
   const item={q:norm(r.q).slice(0,200),a:norm(r.a).slice(0,100),g:(norm(r.g)||'عام').slice(0,60)};
   const alts=r.wrongs.map(norm).filter(Boolean);
   if(choiceModes.has(mode)&&alts.length)item.choices=[item.a,...alts.slice(0,3)];
   if(r.sourcePage)item.sourcePage=Number(r.sourcePage);
   return item;
  })};
}
function preview(){
 if(!valid())return;
 try{sessionStorage.setItem(PREVIEW,JSON.stringify({mode,activity:payload(),createdAt:Date.now()}))}
 catch(_){alertMsg('يلزم السماح بالتخزين المؤقت للمعاينة.',true);return}
 $('previewOverlay').hidden=false;D.body.classList.add('modal-open');
 $('previewTopTitle').textContent='🎮 معاينة '+modes.get(mode)[1];
 $('gameFrame').src='/game-lab-preview.html?creatorPreview=1&mode='+encodeURIComponent(mode)+'&v=8';
 $('closePreview').focus({preventScroll:true});
}
function closePreview(){
 $('previewOverlay').hidden=true;$('gameFrame').src='about:blank';D.body.classList.remove('modal-open');
 $('launchPreview').focus({preventScroll:true});
}
async function api(path,data,guest=false){
 const headers={};if(data!==undefined)headers['Content-Type']='application/json';
 if(token&&!guest)headers.Authorization='Bearer '+token;
 const opts={headers,cache:'no-store'};
 if(data!==undefined){opts.method='POST';opts.body=JSON.stringify(data)}
 const r=await fetch(path,opts);
 let o;try{o=await r.json()}catch(_){throw Error('تعذر قراءة استجابة الخادم')}
 if(!r.ok||!o.ok)throw Error(o.error||'server_error');
 return o;
}
function authMsg(s,success=false,error=false){const el=$('authStatus');el.textContent=s;el.className='auth-status'+(success?' success':error?' error':'')}
function authView(isIn){$('loginBox').hidden=isIn;$('saveBox').hidden=!isIn}
async function authCheck(){
 try{token=localStorage.getItem(TOKEN)||''}catch(_){token=''}
 if(!token){authMsg('سجّل دخول المعلم لحفظ ونشر النشاط.');authView(false);return false}
 try{const res=await api('/api/auth/me');authMsg('✓ مرحبًا، '+(res.teacher?.name||'المعلم')+' — جاهز للحفظ والنشر.',true);authView(true);return true}
 catch(e){authMsg('تعذّر التحقق من الحساب: '+e.message,false,true);authView(false);return false}
}
async function login(e){
 e.preventDefault();const btn=$('loginButton');btn.disabled=true;
 try{
  const data=await api('/api/auth/login',{email:norm($('loginEmail').value),password:$('loginPassword').value},true);
  if(!data.token)throw Error('login_failed');
  token=data.token;try{localStorage.setItem(TOKEN,data.token)}catch(_){}
  $('loginPassword').value='';await authCheck();alertMsg('✓ تم تسجيل دخول المعلم.');
 }catch(err){alertMsg('فشل الدخول: '+err.message,true)}
 finally{btn.disabled=false}
}
async function cloudSave(){
 if(!valid())return null;
 if(!(await authCheck())){alertMsg('سجّل الدخول قبل الحفظ.',true);return null}
 const b=$('saveCloud');b.disabled=true;
 try{
  const data=await api('/api/game-lab/teacher/save',{id:cloudId||undefined,activity:payload()});
  cloudId=data.id;localSave();authMsg('✓ تم حفظ نشاطك على حساب المعلم.',true);alertMsg('✓ حُفظ النشاط.');
  return data;
 }catch(e){alertMsg('فشل الحفظ: '+e.message,true);return null}
 finally{b.disabled=false}
}
async function publish(){
 const saved=await cloudSave();if(!saved)return;
 const b=$('publishCloud');b.disabled=true;
 try{
  const res=await api('/api/game-lab/teacher/publish',{id:cloudId,maxAttempts:Number($('maxAttempts').value)||1});
  if(!res.publicCode)throw Error('missing_public_code');
  const link=location.origin+'/game-lab-play.html?game='+encodeURIComponent(res.publicCode);
  $('shareUrl').value=link;$('openStudentLink').href=link;
  $('shareQr').src='/api/qr?format=svg&text='+encodeURIComponent(link);
  $('shareBox').hidden=false;alertMsg('🚀 تم نشر النشاط، يمكنك مشاركة الرابط الآن!');
  $('shareBox').scrollIntoView({block:'nearest'});
 }catch(e){alertMsg('فشل النشر: '+e.message,true)}
 finally{b.disabled=false}
}
async function allModes(){
 if(!confirm('سيتم إنشاء 24 لعبة بهذا الدرس على حسابك. هل تريد المتابعة؟'))return;
 const saved=await cloudSave();if(!saved)return;
 const b=$('generateAll');b.disabled=true;
 try{
  const res=await api('/api/game-lab/teacher/generate-all',{sourceId:cloudId,confirm:true});
  alertMsg('✓ تم تجهيز '+res.templates+' لعبة ('+res.created+' جديدة، '+res.updated+' محدّثة).');
 }catch(e){alertMsg('تعذر التوليد: '+e.message,true)}
 finally{b.disabled=false}
}
async function library(){
 step(4,true);
 $('stepFour').hidden=true;$('libraryPanel').hidden=false;
 const div=$('libraryItems');div.textContent='جارٍ التحميل...';
 if(!(await authCheck())){div.textContent='سجّل دخول المعلم أولًا من الخطوة الرابعة.';return}
 try{
  const data=await api('/api/game-lab/teacher/list'),items=data.activities||[];
  div.replaceChildren();
  if(!items.length){div.textContent='لا توجد أنشطة محفوظة بعد.';return}
  for(const a of items){
   const el=D.createElement('article');el.className='library-item';
   const info=D.createElement('div'),title=D.createElement('h3'),meta=D.createElement('p'),b=D.createElement('button');
   title.textContent=a.title;meta.textContent=(modes.get(a.mode)?.[1]||a.mode)+' · '+a.questionCount+' سؤال · '+(a.published?'منشور':'مسودة');
   info.append(title,meta);b.className='btn btn-soft';b.textContent='✏️ تعديل';b.type='button';b.onclick=()=>loadSaved(a);
   el.append(info,b);div.append(el);
  }
 }catch(e){div.textContent='تعذر فتح المكتبة: '+e.message}
}
function loadSaved(a){
 const p=a.activity||a,newMode=modes.has(p.mode)?p.mode:mode;
 const data={version:8,mode:newMode,id:a.id,title:p.title,subject:p.subject,grade:p.grade,time:p.time,updatedAt:Date.now(),
  rows:(p.rows||[]).map(normalizeRow)};
 try{localStorage.setItem(KEY+newMode,JSON.stringify(data))}catch(_){}
 location.href='/game-lab-create.html?mode='+encodeURIComponent(newMode)+'&edit='+encodeURIComponent(a.id);
}
function importBulk(){
 const lines=$('bulkText').value.split(/\r?\n/).map(s=>s.trim()).filter(Boolean);
 if(!lines.length){alertMsg('الصق أسئلة أولًا.',true);return}
 if(lines.length>80){alertMsg('يمكن استيراد 80 سؤالًا بحد أقصى.',true);return}
 const newRows=[];
 for(let i=0;i<lines.length;i++){
  const parts=lines[i].split('|').map(norm);
  if(parts.length<2||!parts[0]||!parts[1]){alertMsg('السطر '+(i+1)+' غير مكتمل.',true);return}
  newRows.push({q:parts[0].slice(0,200),a:parts[1].slice(0,100),g:(parts[2]||'عام').slice(0,60),wrongs:['','','']});
 }
 if(!confirm('استبدال الأسئلة الحالية بالأسئلة المستوردة؟'))return;
 rows=newRows;while(rows.length<4)rows.push(blank());localSave();renderRows();hideImport();alertMsg('✓ استوردت '+newRows.length+' سؤال.');
}
function showImport(){$('textImportOverlay').hidden=false;D.body.classList.add('modal-open');$('bulkText').focus()}
function hideImport(){$('textImportOverlay').hidden=true;D.body.classList.remove('modal-open')}
function resetGame(){
 if(!confirm('مسح المسودة المحلية الحالية وإنشاء نشاط جديد؟'))return;
 try{localStorage.removeItem(KEY+mode)}catch(_){}
 rows=Array.from({length:4},blank);cloudId='';$('activityTitle').value='';
 $('shareBox').hidden=true;renderRows();localSave();step(2,true);
}
function start(){
 for(const [id,name,icon] of MODES){
  const o=D.createElement('option');o.value=id;o.textContent=icon+' '+name;$('modeSelect').append(o)
 }
 modeInfo();restore();renderRows();localSave();
 $('modeSelect').addEventListener('change',e=>{localSave();location.href='/game-lab-create.html?mode='+encodeURIComponent(e.target.value)});
 $('questionList').addEventListener('input',changeRow);$('questionList').addEventListener('click',actionRow);
 for(const id of ['activityTitle','subject','grade','roundTime'])$(id).addEventListener('input',localSave);
 $('addQuestion').onclick=addRow;$('addQuestionTop').onclick=addRow;
 $('sampleQuestions').onclick=()=>{
  if(rows.some(r=>norm(r.q))&&!confirm('استبدال الأسئلة الحالية بالمثال؟'))return;
  rows=sample.map(normalizeRow);if(!norm($('activityTitle').value))$('activityTitle').value='تحدي مكونات الحاسوب';
  localSave();renderRows();alertMsg('✓ أضفت 8 أسئلة نموذجية.');
 };
 $('importText').onclick=showImport;$('closeImport').onclick=hideImport;$('applyImport').onclick=importBulk;
 $('textImportOverlay').addEventListener('click',e=>{if(e.target===$('textImportOverlay'))hideImport()});
 $('startQuestions').onclick=()=>step(2,true);$('goBackOne').onclick=()=>step(1,true);
 $('goPreview').onclick=()=>step(3);$('goBackTwo').onclick=()=>step(2,true);
 $('launchPreview').onclick=preview;$('closePreview').onclick=closePreview;
 $('goSave').onclick=()=>step(4);$('goBackThree').onclick=()=>step(3,true);
 $('loginForm').addEventListener('submit',login);
 $('saveCloud').onclick=cloudSave;$('publishCloud').onclick=publish;$('generateAll').onclick=allModes;
 $('copyLink').onclick=async()=>{
  try{await navigator.clipboard.writeText($('shareUrl').value);alertMsg('✓ نُسخ الرابط.')}
  catch(_){$('shareUrl').select();alertMsg('حدّد الرابط وانسخه.',true)}
 };
 $('myLibrary').onclick=library;$('closeLibrary').onclick=()=>step(4,true);
 $('newGame').onclick=resetGame;
 $('helpToggle').onclick=()=>alertMsg('اختر القالب ← أدخل 4 أسئلة ← عاين ← احفظ وانشر. يمكن الرجوع إلى الخطوات في أي وقت.');
 D.querySelectorAll('[data-step]').forEach(el=>el.onclick=()=>step(Number(el.dataset.step)));
 D.addEventListener('keydown',e=>{
  if(e.key==='Escape'&&!$('previewOverlay').hidden)closePreview();
  else if(e.key==='Escape'&&!$('textImportOverlay').hidden)hideImport();
 });
 step(2,true);
}
if(D.readyState==='loading')D.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();