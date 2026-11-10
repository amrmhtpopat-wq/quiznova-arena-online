/* BOOYAHJO GAME LAB Pro V3: schoolbooks, assisted drafts, persistent media, cards and live rooms. */
(()=>{'use strict';
const $=id=>document.getElementById(id);
const key='qn9_teacher_token';
let books=[],bookId='',activities=[],students=[],images=[],imageUrl='',selectedImageId='';
const errors={
 login_required:'سجّل دخول المعلم من «مكتبتي على الحساب» أولًا.',
 book_not_found:'الكتاب غير متاح في حساب المعلم.',
 file_too_large:'الملف أكبر من الحجم المسموح.',
 book_has_no_extractable_text:'الكتاب ليس فيه نص قابل للاستخراج؛ قد يكون صورًا ممسوحة ضوئيًا ويحتاج OCR.',
 password_protected_pdf:'ملف PDF محمي بكلمة مرور ولا يمكن معالجته.',
 unsupported_book_format:'اختر PDF أو DOCX أو TXT.',
 book_limit:'وصلت للحد التجريبي من الكتب. أرشف كتابًا قديمًا قبل الرفع.',
 invalid_pages:'نطاق الصفحات غير صحيح.',
 empty_pages:'لا توجد نصوص في الصفحات المحددة.',
 ai_not_configured:'التوليد بالذكاء الاصطناعي غير مفعّل لعدم وجود مفتاح API على الخادم. استخدم الاستخراج المجاني أو أضف المفتاح عبر إعدادات Render الآمنة.',
 ai_consent_required:'وافق أولًا على إرسال الصفحات المختارة إلى مزود الذكاء الاصطناعي.',
 ai_daily_limit:'وصلت إلى الحد اليومي التجريبي (10 عمليات لكل معلم).',
 ai_provider_unavailable:'مزود الذكاء الاصطناعي غير متاح الآن. جرّب الاستخراج المجاني.',
 ai_invalid_response:'لم يُرجع النموذج أسئلة صالحة. أعد المحاولة.',
 publish_first:'انشر النشاط أولًا ثم أضفه إلى بطاقات الطلاب.',
 invalid_targets:'اختر الطلاب أو الشعب المطلوبة.',
 activity_not_found:'اختر نشاطًا موجودًا.',
 invalid_card:'رمز البطاقة غير صحيح.',
 class_not_found:'الشعبة غير موجودة في حسابك.',
 student_not_found:'الطالب غير موجود في حسابك.',
 unsupported_text_encoding:'استخدم ملف TXT بترميز UTF-8.',
 media_limit:'وصلت إلى الحد التجريبي من الصور المخزنة.',
 invalid_image:'نوع الصورة لا يطابق محتواها.'
};
function message(id,txt,isError=false){
 const target=$(id);if(!target)return;
 target.className=isError?'notice':'good';
 target.textContent=txt;
}
function failed(id,e){message(id,errors[e.message]||e.message||'حدث خطأ في الاتصال',true)}
function token(){return localStorage.getItem(key)||''}
function requireAuth(){if(!token())throw Error('login_required')}
async function request(url,data){
 requireAuth();
 const opts={cache:'no-store',headers:{Authorization:'Bearer '+token()}};
 if(data!==undefined){opts.method='POST';opts.headers['Content-Type']='application/json';opts.body=JSON.stringify(data)}
 const res=await fetch(url,opts);
 let json;try{json=await res.json()}catch(_){throw Error('bad_response')}
 if(!res.ok||!json.ok)throw Error(json.error||'server_error');
 return json;
}
async function readAsBase64(file,maximum){
 if(!file)throw Error('file_required');
 if(file.size>maximum||file.size<1)throw Error('file_too_large');
 const url=await new Promise((resolve,reject)=>{
  const reader=new FileReader();reader.onerror=()=>reject(Error('read_failed'));
  reader.onload=()=>resolve(String(reader.result));reader.readAsDataURL(file)
 });
 return url.split(',')[1]||'';
}
function opt(value,label){const o=document.createElement('option');o.value=value;o.textContent=label;return o}
function btn(text,handler,style='button alt small'){
 const button=document.createElement('button');button.type='button';button.className=style;button.textContent=text;button.onclick=handler;return button;
}
function showActivityOptions(){
 for(const id of ['labAssignActivity','labLiveActivity']){
  const select=$(id),previous=select.value;select.replaceChildren();select.append(opt('','اختر نشاطًا محفوظًا'));
  for(const item of activities.filter(x=>id==='labLiveActivity'||x.published)){
   select.append(opt(item.id,item.title+' • '+(item.published?'منشور':'مسودة')+' • '+item.questionCount+' أسئلة'));
  }
  if(activities.some(x=>x.id===previous))select.value=previous;
 }
}
document.addEventListener('gamelab:library',e=>{
 activities=e.detail?.items||[];
 showActivityOptions();
 if(token()){
  void loadStudents();
  void refreshBooks();
  void refreshImages();
  void refreshRooms();
 }
});
document.addEventListener('gamelab:assign',e=>{
 $('labAssignActivity').value=e.detail.id;scroll('studentAssignments');void showAssignments();
});
document.addEventListener('gamelab:live',e=>{
 $('labLiveActivity').value=e.detail.id;scroll('liveLab');
});
function scroll(id){document.getElementById(id)?.scrollIntoView({behavior:'smooth',block:'start'})}
function renderBooks(){
 const select=$('labBookSelect'),previous=bookId||select.value;select.replaceChildren();
 select.append(opt('','اختر كتابًا محفوظًا'));
 for(const b of books)select.append(opt(b.id,b.name+' · '+b.pageCount+' صفحة'));
 if(books.some(b=>b.id===previous))select.value=previous;
 bookId=select.value;
 const selected=books.find(x=>x.id===bookId);
 if(selected){$('labBookStart').max=selected.pageCount;$('labBookEnd').max=selected.pageCount;
  $('labBookEnd').value=Math.min(selected.pageCount,15);
  message('labBookStatus','📚 '+selected.name+' · '+selected.pageCount+' صفحات. حدّد نطاق الصفحات ثم اختر طريقة التوليد.')}
}
async function refreshBooks(){
 if(!token())return;
 try{
  const list=await request('/api/game-lab/pro/books');
  books=list.books||[];
  renderBooks();
  $('labBookMode').querySelector('option[value="ai"]').disabled=!list.aiEnabled;
  if(!list.aiEnabled)$('labBookMode').value='extract';
  $('labBookMode').title=list.aiEnabled?'الذكاء الاصطناعي متاح':'خدمة الذكاء الاصطناعي بحاجة إلى مفتاح API آمن';
 }catch(e){failed('labBookStatus',e)}
}
async function uploadBook(){
 const file=$('labBookFile').files?.[0],b=$('labBookUpload');
 b.disabled=true;message('labBookStatus','جارٍ قراءة الكتاب ورفع النص إلى المكتبة...');
 try{
  const raw=await readAsBase64(file,6000000);
  const result=await request('/api/game-lab/pro/books/upload',{
   filename:file.name,data:raw,section:$('labBookSection').value});
  bookId=result.book.id;
  await refreshBooks();
  message('labBookStatus','✓ تم حفظ الكتاب: '+result.book.name+' · '+result.book.pageCount+' صفحة. راجع الصفحات قبل توليد المسودة.');
 }catch(e){failed('labBookStatus',e)}finally{b.disabled=false}
}
function requestDraft(){
 const id=$('labBookSelect').value;
 if(!id)throw Error('اختر كتابًا من مكتبتك أولًا');
 return {bookId:id,startPage:Number($('labBookStart').value)||1,
   endPage:Number($('labBookEnd').value)||1,
   count:Number($('labBookCount').value)||12,
   subject:$('subject').value,grade:$('grade').value}
}
async function generate(){
 const b=$('labBookGenerate');b.disabled=true;message('labBookStatus','جارٍ استخراج الأسئلة من الكتاب المحدد...');
 try{
  const mode=$('labBookMode').value,params=requestDraft();
  if(mode==='ai'&&!$('labAiConsent').checked)throw Error('ai_consent_required');
  params.consent=mode==='ai'&&$('labAiConsent').checked;
  const response=await request('/api/game-lab/pro/books/'+(mode==='ai'?'ai':'draft'),params);
  const src=response.rows||[];
  if(!src.length){message('labBookStatus',response.warning||'لم يتم استخراج أسئلة. جرّب صفحات أو درسًا آخر.',true);return}
  const parent=$('labBookPreview');parent.replaceChildren();
  for(const [i,r] of src.entries()){
   const el=document.createElement('div');el.className='lab-bookrow';
   const q=document.createElement('b');q.textContent=(i+1)+'. '+r.q;el.append(q);
   const answer=document.createElement('small');answer.textContent='الإجابة المقترحة: '+r.a+' · صفحة '+r.sourcePage;
   el.append(answer);parent.append(el);
  }
  $('activityData').value=src.map(x=>x.q.replaceAll('|',' ')+' | '+x.a.replaceAll('|',' ')+' | '+x.g.replaceAll('|',' ')+(x.sourcePage?' | '+x.sourcePage:'')).join('\n');
  const book=books.find(x=>x.id===params.bookId);
  if(book)$('activityTitle').value=('ألعاب '+book.name.replace(/\.(pdf|docx|txt)$/i,'')).slice(0,90);
  window.BOOYAH_LAB_BOOK_ID=params.bookId;
  $('applyContent').click();
  $('labBookSummary').textContent='✓ جرى تحويل '+src.length+' سؤالًا إلى محرر الألعاب. يمكنك تحريرها وتبديل أي قالب من الـ24 قالبًا.';
  message('labBookStatus',response.warning||'✓ هذه مسودة جاهزة لمراجعة المعلم.');
 }catch(e){failed('labBookStatus',e)}finally{b.disabled=false}
}
async function showPages(){
 try{
  const params=requestDraft();
  const result=await request('/api/game-lab/pro/books/pages?id='+encodeURIComponent(params.bookId));
  const host=$('labBookPreview');host.replaceChildren();
  const pages=result.pages.filter(x=>x.p>=params.startPage&&x.p<=params.endPage).slice(0,30);
  for(const p of pages){
   const d=document.createElement('div');d.className='lab-bookrow';
   const title=document.createElement('b');title.textContent='الصفحة '+p.p;
   const preview=document.createElement('small');preview.textContent=p.preview||'لا يوجد نص مستخرج من هذه الصفحة';
   d.append(title,preview);host.append(d);
  }
  $('labBookSummary').textContent='أظهرت '+pages.length+' صفحة من النص المستخرج. تجنّب الاعتماد على الكتاب المصوّر الذي لم تُستخرج نصوصه.';
 }catch(e){failed('labBookStatus',e)}
}

async function loadStudents(){
 if(!token())return;
 try{
  const result=await request('/api/teacher/students');students=result.students||[];
  renderTargetChoices();
 }catch(e){failed('labAssignStatus',e)}
}
function renderTargetChoices(){
 const kind=$('labAssignType').value;
 const host=$('labAssignTargets');host.replaceChildren();
 if(kind==='all'){const p=document.createElement('p');p.className='hint';p.textContent='سيظهر النشاط لجميع بطاقات الطلاب المرتبطة بحسابك.';host.append(p);return}
 let choices=[];
 if(kind==='class'){
  choices=[...new Set(students.map(x=>x.className||x.class_name).filter(Boolean))]
   .sort((a,b)=>a.localeCompare(b,'ar')).map(name=>({value:name,label:name}));
 }else{
  choices=students.map(s=>({value:s.id,label:s.name+' — '+(s.className||s.class_name||'')}))
 }
 if(!choices.length){host.textContent='لم يُعثر على شعب أو طلاب. أضف الطلاب أولًا من لوحة المعلم.';return}
 for(const item of choices){
  const line=document.createElement('label'),input=document.createElement('input');
  input.type='checkbox';input.value=item.value;input.className='lab-target-input';
  const name=document.createElement('span');name.textContent=item.label;line.append(input,name);host.append(line)
 }
}
async function showAssignments(){
 const aid=$('labAssignActivity').value;
 if(!aid)return;
 try{
  const reply=await request('/api/game-lab/pro/assignments?id='+encodeURIComponent(aid));
  const targets=reply.targets||[];
  const selectedType=targets[0]?.target_type||$('labAssignType').value;
  $('labAssignType').value=selectedType;renderTargetChoices();
  const chosen=targets.filter(x=>x.target_type===selectedType).map(x=>x.target_value);
  for(const input of $('labAssignTargets').querySelectorAll('input'))input.checked=chosen.includes(input.value);
  const display=$('labAssignedPreview');display.replaceChildren();
  if(!targets.length){
   const p=document.createElement('p');p.className='hint';p.textContent='غير مسند لأي بطاقة بعد. يستطيع المعلم نشر النشاط أولًا.';display.append(p);
  }else{
   for(const x of targets){
    const item=document.createElement('div');item.className='lab-bookrow';
    item.textContent=(x.target_type==='all'?'كل الطلاب':x.target_type==='class'?'الشعبة':'بطاقة الطالب')+' · '+x.target_value;
    display.append(item)
   }
  }
  message('labAssignStatus','✓ تم جلب الإسنادات الحالية لهذا النشاط.');
 }catch(e){failed('labAssignStatus',e)}
}
async function saveAssignments(){
 const aid=$('labAssignActivity').value;
 if(!aid){message('labAssignStatus','اختر لعبة منشورة أولًا.',true);return}
 const typ=$('labAssignType').value;
 const targets=typ==='all'?[{type:'all',value:'*'}]:
  [...$('labAssignTargets').querySelectorAll('.lab-target-input:checked')]
   .map(x=>({type:typ,value:x.value}));
 if(!targets.length){message('labAssignStatus','حدد شعبة أو بطاقة طالب واحدة على الأقل.',true);return}
 try{
  const res=await request('/api/game-lab/pro/assignments/save',{activityId:aid,targets});
  message('labAssignStatus','✓ تم إضافة النشاط إلى '+res.targets.length+' هدف/أهداف في بطاقات الطلاب. يمكن فتح ألعاب البطاقة من بوابة الطالب.');
  await showAssignments();
 }catch(e){failed('labAssignStatus',e)}
}
async function refreshImages(){
 if(!token())return;
 try{
  const response=await request('/api/game-lab/pro/media');images=response.images||[];
  const host=$('labMediaCloudList');if(!host)return;
  host.replaceChildren();
  for(const img of images){
   const b=btn('🖼️ '+img.name,()=>selectSavedImage(img.id),'button alt small');
   host.append(b)
  }
 }catch(e){message('labMediaStatus',errors[e.message]||e.message,true)}
}
async function uploadImage(){
 const file=$('labImageFile').files?.[0];
 if(!file){message('labMediaStatus','اختر صورة الدرس أولًا.',true);return}
 try{
  const data=await readAsBase64(file,1500000);
  const response=await request('/api/game-lab/pro/media/upload',{
    filename:file.name,mime:file.type,data});
  window.BOOYAH_LAB_IMAGE_ID=response.image.id;
  selectedImageId=response.image.id;
  message('labMediaStatus','✓ حُفظت الصورة في مكتبتك. عند حفظ النشاط ستُربط الصورة باللعبة المخصصة.');
  await refreshImages();
 }catch(e){message('labMediaStatus',errors[e.message]||e.message,true)}
}
async function selectSavedImage(id){
 try{
  const response=await fetch('/api/game-lab/pro/image?id='+encodeURIComponent(id),
    {headers:{Authorization:'Bearer '+token()},cache:'no-store'});
  if(!response.ok)throw Error('media_not_found');
  const blob=await response.blob();
  if(imageUrl)URL.revokeObjectURL(imageUrl);
  imageUrl=URL.createObjectURL(blob);
  window.BOOYAH_LAB_GAME_IMAGE=imageUrl;
  window.BOOYAH_GAME_LAB_IMAGE=imageUrl;
  window.BOOYAH_LAB_IMAGE_ID=id;selectedImageId=id;
  $('labImagePreview').src=imageUrl;$('labImagePreview').classList.remove('hide');
  message('labMediaStatus','✓ تم اختيار الصورة المحفوظة. اضغط حفظ النشاط على الحساب لتصبح متاحة للطالب.');
 }catch(e){message('labMediaStatus',errors[e.message]||e.message,true)}
}
window.addEventListener('pagehide',()=>{if(imageUrl)URL.revokeObjectURL(imageUrl)});

async function refreshRooms(){
 if(!token())return;
 try{
  const result=await request('/api/game-lab/live/rooms');
  const list=$('labLiveRooms');list.replaceChildren();
  for(const room of result.rooms||[]){
   const row=document.createElement('div');row.className='saved';
   const label=document.createElement('div');
   const b=document.createElement('b');b.textContent=room.title;
   const sm=document.createElement('small');sm.textContent=room.code+' · '+room.status;
   label.append(b,sm);
   row.append(label,btn('🎥 فتح',()=>window.open('/game-lab-live.html?host='+room.code,'_blank','noopener'),'button small'));
   list.append(row)
  }
  if(!(result.rooms||[]).length)list.textContent='لم تُنشئ منافسات بعد.';
 }catch(e){failed('labLiveStatus',e)}
}
async function createRoom(){
 const aid=$('labLiveActivity').value;
 if(!aid){message('labLiveStatus','اختر نشاطًا من مكتبتك أولًا.',true);return}
 const teams=$('labLiveMode').value==='teams';
 const names=$('labLiveTeams').value.split(/[،,]/g).map(x=>x.trim()).filter(Boolean);
 const button=$('labLiveCreate');button.disabled=true;
 try{
  const response=await request('/api/game-lab/live/create',{
   activityId:aid,duration:Number($('labLiveDuration').value)||30,teams,
   teamNames:names,showFeedback:$('labLiveFeedback').checked});
  const code=response.code;$('labLiveCode').textContent=code;
  const hostUrl=location.origin+response.teacherUrl;
  const playerUrl=location.origin+response.studentUrl;
  $('labLiveTeacherLink').href=hostUrl;$('labLiveStudentLink').href=playerUrl;
  $('labLiveUrl').value=playerUrl;
  $('labLiveQR').src='/api/qr?format=svg&text='+encodeURIComponent(playerUrl);
  $('labLiveCreated').classList.remove('hide');
  message('labLiveStatus','✓ تم إنشاء غرفة '+code+'. افتح شاشة المعلم واضغط بدء، ثم شارك الرابط مع الطلاب.');
  await refreshRooms();
 }catch(e){failed('labLiveStatus',e)}finally{button.disabled=false}
}
$('labBookUpload').onclick=uploadBook;
$('labBookRefresh').onclick=refreshBooks;
$('labBookGenerate').onclick=generate;
$('labBookPages').onclick=showPages;
$('labBookOpenEditor').onclick=()=>scroll('builder');
$('labBookSelect').onchange=e=>{bookId=e.target.value;renderBooks()};
$('labAssignType').onchange=renderTargetChoices;
$('labAssignRefresh').onclick=loadStudents;
$('labAssignActivity').onchange=showAssignments;
$('labAssignSave').onclick=saveAssignments;
$('labLiveCreate').onclick=createRoom;
$('labLiveRefresh').onclick=refreshRooms;
$('labSaveImageCloud').onclick=uploadImage;
if(token()){void refreshBooks();void loadStudents();void refreshImages();void refreshRooms()}
})();
