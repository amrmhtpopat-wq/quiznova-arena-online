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
const blank=()=>({q:'',a:'',g:'عام',wrongs:['','',''],explanation:'',sourcePage:'',markerX:50,markerY:50});
const norm=s=>String(s??'').trim();
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function alertMsg(msg,error=false){
 const e=$('toast');clearTimeout(toastTimer);e.textContent=msg;e.className='toast'+(error?' error':'');e.hidden=false;
 toastTimer=setTimeout(()=>e.hidden=true,4200);
}
function normalizeRow(r){
 const a=norm(r.a);const wrongs=Array.isArray(r.wrongs)?r.wrongs.slice(0,3):Array.isArray(r.choices)?r.choices.filter(x=>norm(x).toLocaleLowerCase()!==a.toLocaleLowerCase()).slice(0,3):[];
 while(wrongs.length<3)wrongs.push('');
 return {q:norm(r.q),a,g:norm(r.g)||'عام',wrongs,sourcePage:r.sourcePage||'',explanation:norm(r.explanation||''),markerX:r.markerX??50,markerY:r.markerY??50};
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
 try{localStorage.setItem(KEY+mode,JSON.stringify({version:8,mode,id:cloudId,title:$('activityTitle').value,subject:$('subject').value,grade:$('grade').value,time:$('roundTime').value,rows,imageId:$('v9ImageId')?.value||'',teamNames:[$('v9Team1')?.value||'الفريق الأزرق',$('v9Team2')?.value||'الفريق الذهبي',$('v9Team3')?.value||''].filter(Boolean),updatedAt:Date.now()}))}catch(_){}
 summary();
}
function restore(){
 let d;try{d=JSON.parse(localStorage.getItem(KEY+mode)||'null')}catch(_){}
 if(d?.version===8&&Array.isArray(d.rows)&&d.rows.length>0&&d.rows.length<=80){
  rows=d.rows.map(normalizeRow);cloudId=d.id||'';
  if($('v9ImageId'))$('v9ImageId').value=d.imageId||'';
  if(Array.isArray(d.teamNames)){
   ['v9Team1','v9Team2','v9Team3'].forEach((id,i)=>{if($(id))$(id).value=d.teamNames[i]||''});
  }
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
  const labels={
   pairs:['بطاقة السؤال / المفهوم','البطاقة المطابقة / تعريفه','الموضوع'],flash:['الوجه الأمامي للبطاقة','الوجه الخلفي (الإجابة)','الوحدة'],
   memory:['البطاقة الأولى','البطاقة المطابقة','الوحدة'],sort:['السؤال التوضيحي','العنصر المطلوب تصنيفه','المجموعة الصحيحة'],
   order:['الخطوة الصحيحة بالترتيب','وصف الخطوة (اختياري للشرح)','المرحلة'],anagram:['التعريف أو التلميح','الكلمة المطلوب ترتيب حروفها','الموضوع'],
   crossword:['تعريف الكلمة','الكلمة في الشبكة (2–10 حروف)','الموضوع'],wordsearch:['تلميح الكلمة','الكلمة المطلوب العثور عليها','الموضوع'],
   cloze:['اكتب الجملة مع ___ مكان الفراغ','الكلمة الناقصة','الموضوع'],truth:['العبارة أو السؤال','الإجابة المرجعية الصحيحة','الموضوع'],
   diagram:['السؤال عن جزء الصورة','اسم الجزء الصحيح','الوحدة'],hidden:['السؤال المطلوب استنتاجه من الصورة','الإجابة عند الكشف','الموضوع'],
   wheel:['سؤال يظهر عند توقف العجلة','الإجابة عند الكشف','الموضوع'],boxes:['سؤال مخفي داخل الصندوق','الإجابة عند الفتح','الموضوع'],
   survey:['نص الاستفتاء (يمكن تكراره)','خيار التصويت','الموضوع'],exit:['سؤال تأمل / بطاقة خروج','إجابة إرشادية للمعلم','الموضوع'],
   story:['قرار داخل الموقف التعليمي','المسار أو القرار الصحيح','مرحلة القصة'],
   bingo:['تعريف المصطلح','المصطلح الموجود على البطاقة','الموضوع'],
   board:['سؤال المنافسة','الإجابة المرجعية','الفريق / المحور'],teams:['سؤال التحدي','الإجابة الصحيحة','الموضوع']
  };
  const names=labels[mode]||['نص السؤال','الإجابة الصحيحة','المجموعة / الوحدة'];
  const modeExtra=(mode==='diagram'?'<div class="question-grid"><label class="field"><span>موضع العلامة أفقيا X %</span><input data-field="markerX" type="number" min="0" max="100" step="1" value="'+esc(r.markerX)+'"></label><label class="field"><span>موضع العلامة عموديا Y %</span><input data-field="markerY" type="number" min="0" max="100" step="1" value="'+esc(r.markerY)+'"></label></div>':'')+
  '<div class="question-grid"><label class="field"><span>💡 شرح أو تغذية راجعة بعد الإجابة (اختياري)</span><input data-field="explanation" maxlength="240" value="'+esc(r.explanation||'')+'" placeholder="لماذا الإجابة صحيحة؟"></label><label class="field"><span>رقم صفحة الكتاب (اختياري)</span><input data-field="sourcePage" type="number" min="1" max="350" value="'+esc(r.sourcePage||'')+'" placeholder="مثال: 24"></label></div>';
  d.innerHTML='<summary><span class="question-index">'+(i+1)+'</span><span class="question-summary'+(!r.q?' empty':'')+'">'+esc(r.q||'اضغط لكتابة السؤال')+'</span><span class="question-badge">'+(r.a?'✓ إجابة محددة':'مطلوب')+'</span></summary>'+
  '<div class="question-content"><label class="field"><span>'+esc(names[0])+' '+(i+1)+' <sup>*</sup></span><input data-field="q" maxlength="200" value="'+esc(r.q)+'" placeholder="نص السؤال"></label>'+
  '<div class="question-grid"><label class="field"><span class="correct-label">✓ '+esc(names[1])+' <sup>*</sup></span><input data-field="a" class="correct-input" maxlength="100" value="'+esc(r.a)+'" placeholder="الإجابة المعتمدة"></label>'+
  '<label class="field"><span>'+esc(names[2])+'</span><input data-field="g" maxlength="60" value="'+esc(r.g)+'" placeholder="مثال: الوحدة الأولى"></label></div>'+wrong+modeExtra+
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
  if(r.sourcePage&&(Number(r.sourcePage)<1||Number(r.sourcePage)>350)){alertMsg('رقم صفحة المصدر غير صالح في السؤال '+(i+1),true);return false}
  if(mode==='diagram'&&(!Number.isFinite(Number(r.markerX))||!Number.isFinite(Number(r.markerY))||Number(r.markerX)<0||Number(r.markerX)>100||Number(r.markerY)<0||Number(r.markerY)>100)){alertMsg('حدد موضع العلامة كنسبة مئوية بين 0 و100.',true);return false}
  if(mode==='crossword'&&(Array.from(a.replace(/\s/g,'')).length<2||Array.from(a.replace(/\s/g,'')).length>10)){alertMsg('الكلمات المتقاطعة تحتاج إجابات من 2 إلى 10 حروف.',true);return false}
  if(mode==='wordsearch'&&(Array.from(a.replace(/\s/g,'')).length<2||Array.from(a.replace(/\s/g,'')).length>12)){alertMsg('البحث عن الكلمات يحتاج إجابات من 2 إلى 12 حرفًا.',true);return false}
 }
 if(mode==='sort'&&groups.size<2){alertMsg('لعبة التصنيف تحتاج مجموعتين مختلفتين على الأقل.',true);return false}
 return true;
}
function payload(){
 return {title:norm($('activityTitle').value).slice(0,90),subject:$('subject').value,grade:$('grade').value,
  mode,time:Number($('roundTime').value)||25,
  imageId:$('v9ImageId')?.value||'',
  teamNames:(mode==='board'||mode==='teams')?[$('v9Team1')?.value||'الفريق الأزرق',$('v9Team2')?.value||'الفريق الذهبي',...(mode==='board'&&$('v9Team3')?.value?[$('v9Team3').value]:[])]:[],
  rows:rows.map(r=>{
   const item={q:norm(r.q).slice(0,200),a:norm(r.a).slice(0,100),g:(norm(r.g)||'عام').slice(0,60)};
   const alts=r.wrongs.map(norm).filter(Boolean);
   if(choiceModes.has(mode)&&alts.length)item.choices=[item.a,...alts.slice(0,3)];
   if(r.sourcePage)item.sourcePage=Number(r.sourcePage);
   if(norm(r.explanation))item.explanation=norm(r.explanation).slice(0,240);
   if(mode==='diagram'){item.markerX=Number(r.markerX??50);item.markerY=Number(r.markerY??50)}
   return item;
  })};
}
function preview(){
 if(!valid())return;
 try{sessionStorage.setItem(PREVIEW,JSON.stringify({mode,activity:payload(),createdAt:Date.now()}))}
 catch(_){alertMsg('يلزم السماح بالتخزين المؤقت للمعاينة.',true);return}
 $('previewOverlay').hidden=false;D.body.classList.add('modal-open');
 $('previewTopTitle').textContent='🎮 معاينة '+modes.get(mode)[1];
 const previewUrl='/game-lab-preview.html?creatorPreview=1&mode='+encodeURIComponent(mode)+'&v=10.1';
 $('previewNewTab').href=previewUrl;
 $('gameFrame').src=previewUrl;
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
 if((mode==='diagram'||mode==='hidden')&&$('v9ImageUpload')?.files?.length&&!$('v9ImageId')?.value){
  alertMsg('ارفَع الصورة للحفظ الدائم قبل حفظ هذا النشاط.',true);return null
 }
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
const CLASSROOM_MODES=new Set(['quiz','fast','truth','pairs','wheel','boxes']);
function classroomSettings(){
 return {duration:Number($('v10LiveDuration').value)||25,
  teams:$('v10LiveTeams').checked,showFeedback:$('v10LiveFeedback').checked,
  cardRequired:$('v10LiveCardsOnly').checked,enforceGrade:$('v10LiveGrade').checked};
}
async function launchSavedLive(activityId){
 if(!CLASSROOM_MODES.has(mode)){
  alertMsg('المنافسة المتزامنة متاحة حاليًا لست ألعاب: Quiz وFast وTrue/False وPairs وWheel وBoxes.',true);
  return;
 }
 const btn=$('v10StartLive');btn.disabled=true;
 $('v10LiveStatus').textContent='جارٍ إعداد غرفة الفصل...';
 try{
  const body={activityId,...classroomSettings()};
  const room=await api('/api/game-lab/live/create',body);
  if(!room.code||!room.teacherUrl)throw Error('لم يستطع الخادم إنشاء رمز الجلسة');
  const roomUrl=room.teacherUrl;
  $('v10OpenLive').href=roomUrl;$('v10OpenLive').hidden=false;
  $('v10LiveStatus').textContent='✓ أُنشئت الغرفة: '+room.code+' — افتح شاشة المعلم للمشاركة';
  window.location.assign(roomUrl);
 }catch(e){
  $('v10LiveStatus').textContent='تعذر بدء الحصة: '+e.message;
  alertMsg('تعذر بدء الحصة: '+e.message,true);
 }finally{btn.disabled=false}
}
async function startLive(){
 if(!CLASSROOM_MODES.has(mode))return;
 const saved=await cloudSave();if(!saved)return;
 await launchSavedLive(saved.id);
}
async function classroomHistory(){
 const holder=$('v10Rooms');holder.hidden=false;holder.replaceChildren();
 holder.textContent='جارٍ استرجاع جلسات الفصل...';
 if(!(await authCheck())){holder.textContent='سجّل الدخول إلى حساب المعلم لعرض سجل الجلسات.';return}
 try{
  const data=await api('/api/game-lab/live/rooms');
  holder.replaceChildren();
  const list=Array.isArray(data.rooms)?data.rooms:[];
  if(!list.length){holder.textContent='لم تنشئ جلسات مباشرة بعد.';return}
  for(const room of list){
   if(!/^[A-Z2-9]{6}$/.test(room.code))continue;
   const row=D.createElement('div');row.className='v10-room-record';
   const detail=D.createElement('div');const title=D.createElement('strong');
   title.textContent=room.title||'جلسة تعليمية';
   const sub=D.createElement('small');
   sub.textContent=room.code+' · '+({lobby:'انتظار',question:'جارية',results:'نتائج الجولة',finished:'مكتملة'}[room.status]||'محفوظة');
   detail.append(title,sub);
   const open=D.createElement('a');open.className='btn btn-soft';
   open.href='/game-lab-live.html?host='+encodeURIComponent(room.code);
   open.textContent='↗ الغرفة والنتائج';
   row.append(detail,open);holder.append(row);
  }
 }catch(e){holder.textContent='تعذر عرض الجلسات: '+e.message}
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
   const classroom=D.createElement('button');classroom.type='button';classroom.className='btn btn-primary';
   classroom.textContent='🎮 حصة مباشرة';classroom.hidden=!CLASSROOM_MODES.has(a.mode);
   classroom.onclick=async()=>{
    if(!CLASSROOM_MODES.has(a.mode))return;
    const oldMode=mode;mode=a.mode;
    try{await launchSavedLive(a.id)}finally{mode=oldMode}
   };
   const reports=D.createElement('button');reports.type='button';reports.className='btn btn-ghost v9-open-report';reports.dataset.id=a.id;reports.dataset.title=a.title;reports.textContent='📊 النتائج';
   const actions=D.createElement('div');actions.className='v9-library-actions';actions.append(b,classroom,reports);
   el.append(info,actions);div.append(el);
  }
 }catch(e){div.textContent='تعذر فتح المكتبة: '+e.message}
}
function loadSaved(a){
 const p=a.activity||a,newMode=modes.has(p.mode)?p.mode:mode;
 const data={version:8,mode:newMode,id:a.id,title:p.title,subject:p.subject,grade:p.grade,time:p.time,updatedAt:Date.now(),
  rows:(p.rows||[]).map(normalizeRow),imageId:p.imageId||'',teamNames:p.teamNames||[]};
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
  const words=['معالج','ذاكرة','مفاتيح','تخزين','شاشة','لوحة','فأرة','صوت'];
  rows=sample.map((row,i)=>{
   const r=normalizeRow(row);
   if(mode==='crossword'||mode==='wordsearch'||mode==='anagram')r.a=words[i];
   if(mode==='cloze')r.q='أكمل العبارة: وظيفة الجزء ____ هي '+row.g;
   if(mode==='survey')r.q='ما موضوع المهارات الرقمية الأكثر فائدة بالنسبة لك؟';
   return r;
  });
  if(!norm($('activityTitle').value))$('activityTitle').value='تحدي مكونات الحاسوب';
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
 $('v10StartLive').onclick=startLive;
 $('v10History').onclick=classroomHistory;
 $('v10ClassroomLaunch').hidden=!CLASSROOM_MODES.has(mode);
 $('v10LiveDuration').value=$('roundTime').value||'25';
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