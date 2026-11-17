/* BOOYAHJO GAME LAB Pro V3: schoolbooks, assisted drafts, persistent media, cards and live rooms. */
(()=>{'use strict';
const $=id=>document.getElementById(id);
const key='qn9_teacher_token';
let books=[],bookId='',activities=[],students=[],images=[],imageUrl='',selectedImageId='',bookDraftReady=false,aiReady=false,aiModeTouched=false;
const errors={
 login_required:'سجّل دخول المعلم من «مكتبتي على الحساب» أولًا.',
 book_not_found:'الكتاب غير متاح في حساب المعلم.',
 upload_not_found:'انتهت جلسة رفع الكتاب أو لم يتم العثور عليها. أعد اختيار الملف ورفعه.',
 upload_expired:'انتهت مهلة رفع الكتاب. أعد المحاولة.',
 upload_chunk_order:'انقطع تسلسل رفع أجزاء الكتاب. أعد المحاولة.',
 upload_chunk_invalid:'حدث خطأ في جزء من الملف أثناء النقل. أعد المحاولة.',
 upload_incomplete:'الكتاب لم يُرفع بالكامل. حاول مرة أخرى.',
 book_limit:'بلغت الحد الأقصى للكتب المحفوظة. أرشف كتابًا قديمًا قبل رفع كتاب جديد.',

 file_too_large:'حجم الملف أكبر من المسموح (40 ميغابايت للكتب، و1.5 ميغابايت للصور).',
 book_has_no_extractable_text:'الكتاب ليس فيه نص قابل للاستخراج؛ قد يكون صورًا ممسوحة ضوئيًا ويحتاج OCR.',
 password_protected_pdf:'ملف PDF محمي بكلمة مرور ولا يمكن معالجته.',
 unsupported_book_format:'اختر PDF أو DOCX أو TXT.',
 book_limit:'وصلت للحد التجريبي من الكتب. أرشف كتابًا قديمًا قبل الرفع.',
 invalid_pages:'نطاق الصفحات غير صحيح.',
 empty_pages:'لا توجد نصوص في الصفحات المحددة.',
 ai_not_configured:'التوليد الذكي المجاني يحتاج مفتاح Gemini API مجاني من Google AI Studio محفوظًا في إعدادات Render، دون تفعيل الفوترة.',
 ai_consent_required:'وافق أولًا على إرسال الصفحات المختارة إلى مزود الذكاء الاصطناعي.',
 ai_daily_limit:'وصلت إلى الحد اليومي (10 عمليات توليد لكل معلم). جرّب غدًا أو استخدم الاستخراج المجاني.',
 ai_global_daily_limit:'وصلت المنصة إلى حد الأمان اليومي لطلبات الذكاء الاصطناعي. حاول غدًا.',
 ai_too_many_pages:'لجودة أفضل وضمن الحدود المجانية، اختر 25 صفحة أو أقل في عملية التوليد الواحدة.',
 ai_invalid_key:'مفتاح Gemini المجاني غير صالح أو غير متاح في المنطقة. تأكد من إنشائه عبر Google AI Studio دون حساب فوترة.',
 ai_no_credit:'لا يوجد رصيد مجاني متاح. لا تفعّل الفوترة؛ استخدم الاستخراج المحلي المجاني.',
 ai_rate_limited:'وصلت إلى حصة Gemini المجانية أو الحد المؤقت. لن تُحاول المنصة استخدام خدمة مدفوعة. جرّب لاحقًا أو استخدم التوليد المحلي.',
 ai_provider_configuration:'تعذر استخدام نموذج Gemini المجاني في هذا المشروع؛ تحقق من صلاحيات المفتاح المجاني أو استخدم الاستخراج المحلي.',
 ai_provider_unavailable:'خدمة Gemini المجانية غير متاحة الآن. يمكنك المتابعة بالاستخراج المحلي دون أي رسوم.',
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
  aiReady=Boolean(list.aiEnabled);
  $('labBookMode').querySelector('option[value="ai"]').disabled=!aiReady;
  if(!aiReady)$('labBookMode').value='extract';
  else if(!aiModeTouched)$('labBookMode').value='ai';
  $('labBookMode').title=aiReady?'تمت إضافة مفتاح Gemini مجاني؛ الخدمة جاهزة للاختبار':'يتطلب التوليد الذكي المجاني مفتاح GEMINI_API_KEY بدون فوترة';
  updateAiSettings();
 }catch(e){failed('labBookStatus',e)}
}
const MAX_BOOK_UPLOAD_BYTES=40000000;
const BOOK_UPLOAD_CHUNK_BYTES=1000000;
function bookUploadProgress(done,total){
 const pct=Math.min(100,Math.round(done*100/total));
 message('labBookStatus','☁️ جارٍ رفع الكتاب بأمان... '+pct+'% ('+(done/1000000).toFixed(1)+' من '+(total/1000000).toFixed(1)+' ميغابايت).');
 const bar=$('labBookUploadProgress');
 if(bar){bar.value=pct;bar.hidden=false}
}
async function uploadBook(){
 const file=$('labBookFile').files?.[0],button=$('labBookUpload'),bar=$('labBookUploadProgress');
 if(!file){message('labBookStatus','اختر ملف كتاب PDF أو DOCX أو TXT أولًا.',true);return}
 if(!/\.(pdf|docx|txt)$/i.test(file.name)){message('labBookStatus','صيغة الملف يجب أن تكون PDF أو Word DOCX أو TXT.',true);return}
 if(!file.size||file.size>MAX_BOOK_UPLOAD_BYTES){message('labBookStatus','حجم الكتاب يتجاوز 40 ميغابايت. اختر جزءًا أصغر من الكتاب أو قلّل حجم الصور ثم أعد المحاولة.',true);return}
 button.disabled=true;if(bar){bar.hidden=false;bar.value=0}
 let uploadId='';
 try{
  const section=$('labBookSection').value;
  let result;
  if(file.size<=6000000){
   message('labBookStatus','جارٍ رفع الكتاب إلى مكتبة المعلم...');
   const raw=await readAsBase64(file,6000000);
   result=await request('/api/game-lab/pro/books/upload',{filename:file.name,data:raw,section});
  }else{
   const start=await request('/api/game-lab/pro/books/upload/start',{
     filename:file.name,section,fileSize:file.size
   });
   uploadId=start.uploadId;
   const chunkBytes=Math.min(start.chunkBytes||BOOK_UPLOAD_CHUNK_BYTES,BOOK_UPLOAD_CHUNK_BYTES);
   for(let index=0,offset=0;offset<file.size;index++,offset+=chunkBytes){
     const end=Math.min(offset+chunkBytes,file.size);
     const raw=await readAsBase64(file.slice(offset,end),chunkBytes);
     const reply=await request('/api/game-lab/pro/books/upload/chunk',{
       uploadId,index,data:raw
     });
     bookUploadProgress(reply.uploaded||end,file.size);
   }
   message('labBookStatus','✓ اكتمل رفع الكتاب. جارٍ استخراج النص من صفحاته وحفظه...');
   result=await request('/api/game-lab/pro/books/upload/finish',{uploadId});
   uploadId='';
  }
  bookId=result.book.id;
  clearBookReview();
  await refreshBooks();
  if(bar)bar.value=100;
  message('labBookStatus','✓ تم حفظ الكتاب: '+result.book.name+' · '+result.book.pageCount+' صفحة. '+(result.book.notice||'راجع النص المستخرج قبل التوليد.'));
 }catch(e){
  failed('labBookStatus',e);
  if(uploadId)request('/api/game-lab/pro/books/upload/cancel',{uploadId}).catch(()=>{});
 }finally{button.disabled=false}
}
function updateAiSettings(){
 const enabled=$('labBookMode').value==='ai';
 $('labAiSettings').hidden=!enabled;
 const status=$('labAiStatus');
 status.textContent=aiReady
  ?(enabled?'✓ مفتاح Gemini موجود. ستُرسل الصفحات المختارة إلى Gemini المجاني فقط عند موافقتك. لا يوجد انتقال إلى خدمة مدفوعة.':'يمكنك اختيار Gemini المجاني من القائمة.')
  :'التوليد المجاني بالذكاء الاصطناعي غير مفعّل بعد. أنشئ مفتاح Gemini مجانيًا من Google AI Studio دون ربط بطاقة أو حساب فوترة، ثم أضف GEMINI_API_KEY إلى Render. الاستخراج المحلي يعمل دائمًا دون مفتاح.';
 $('labAiConsent').disabled=!enabled;
 if(!enabled)$('labAiConsent').checked=false;
}
function requestDraft(){
 const id=$('labBookSelect').value;
 if(!id)throw Error('اختر كتابًا من مكتبتك أولًا');
 return {bookId:id,startPage:Number($('labBookStart').value)||1,
   endPage:Number($('labBookEnd').value)||1,
   count:Number($('labBookCount').value)||12,
   subject:$('subject').value,grade:$('grade').value,
   difficulty:$('labAiDifficulty').value,focus:$('labAiFocus').value}
}
function clearBookReview(){
 bookDraftReady=false;
 $('labBookSaveCloud').disabled=true;
 $('labBookApprove').disabled=true;
 window.TG_CREATOR_PREVIEW_ROWS=null;
 window.BOOYAH_LAB_BOOK_ID='';
 const host=$('labBookPreview');
 host.replaceChildren();
 const hint=document.createElement('p');
 hint.className='hint';
 hint.textContent='اختر الكتاب والصفحات ثم استخرج مقترحات جديدة؛ لا تُعتمد الأسئلة دون مراجعتك.';
 host.append(hint);
 $('labBookSummary').textContent='';
}
function reviewInput(kind,value,maxLength){
 const control=document.createElement('textarea');
 control.className='tag-book-'+kind;
 control.value=String(value||'').slice(0,maxLength);
 control.maxLength=maxLength;
 control.rows=kind==='question'?2:3;
 control.spellcheck=true;
 control.dir='auto';
 control.addEventListener('input',()=>{bookDraftReady=false;$('labBookSaveCloud').disabled=true});
 return control
}
function renderBookReview(rows){
 const parent=$('labBookPreview');parent.replaceChildren();
 const explanation=document.createElement('p');
 explanation.className='hint';
 explanation.textContent='هذه اقتراحات وليست أسئلة معتمدة. افحص السؤال والجواب واقتباس المصدر، وعدّل أو استبعد أي مقترح غير صحيح، ثم انقل المختار إلى محرر الأنشطة.';
 parent.append(explanation);
 for(const [i,r] of rows.entries()){
  const card=document.createElement('article');card.className='lab-bookrow tag-book-review-card';
  const header=document.createElement('div');header.className='tag-book-review-top';
  const keep=document.createElement('label');keep.className='tag-book-review-keep';
  const check=document.createElement('input');check.type='checkbox';check.checked=true;check.className='tag-book-review-check';
  keep.append(check,document.createTextNode(' اعتماد المقترح '+(i+1)));
  const label=document.createElement('small');
  const kinds={explicit_qa:'سؤال وإجابة من الكتاب',definition:'تعريف من الكتاب',goal:'هدف أو غاية',process:'طريقة أو آلية',examples:'أمثلة من الدرس',function:'وظيفة أو دور',reason:'فهم وتفسير',list:'تعداد معلومات',fact:'معلومة صريحة'};
  label.textContent=(kinds[r.origin]||(r.origin==='ai'?'توليد ذكاء اصطناعي':'معلومة مقترحة'))+' · صفحة '+(r.sourcePage||'غير محددة');
  header.append(keep,label);
  const questionLabel=document.createElement('label');questionLabel.textContent='السؤال';
  const question=reviewInput('question',r.q,200);questionLabel.append(question);
  const answerLabel=document.createElement('label');answerLabel.textContent='الإجابة الصحيحة المقترحة';
  const answer=reviewInput('answer',r.a,100);answerLabel.append(answer);
  const source=document.createElement('p');source.className='tag-book-evidence';
  source.textContent=r.sourceQuote?'الدليل من النص: «'+r.sourceQuote+'»':'لا يوجد اقتباس داعم؛ طابق السؤال والإجابة مع صفحة الكتاب قبل اعتماده.';
  card.dataset.sourcePage=String(r.sourcePage||'');
  card.dataset.group=String(r.g||'عام');
  card.append(header,questionLabel,answerLabel,source);parent.append(card);
 }
}
function approveBookSuggestions(){
 const cards=[...$('labBookPreview').querySelectorAll('.tag-book-review-card')];
 if(!cards.length){message('labBookStatus','ولّد مقترحات أولًا، ثم راجعها.',true);return}
 const accepted=[],seen=new Set();
 for(const card of cards){
  if(!card.querySelector('.tag-book-review-check').checked)continue;
  const q=card.querySelector('.tag-book-question').value.replace(/\s+/g,' ').trim().replaceAll('|',' ');
  const a=card.querySelector('.tag-book-answer').value.replace(/\s+/g,' ').trim().replaceAll('|',' ');
  if(!q||!a){message('labBookStatus','يوجد سؤال أو جواب فارغ ضمن المقترحات المختارة. صححه أو استبعده.',true);return}
  const key=(q+'|'+a).toLocaleLowerCase('ar');
  if(seen.has(key))continue;seen.add(key);
  accepted.push({q,a,g:card.dataset.group||'عام',sourcePage:Number(card.dataset.sourcePage)||null})
 }
 if(!accepted.length){message('labBookStatus','حدد سؤالًا موثوقًا واحدًا على الأقل.',true);return}
 $('activityData').value=accepted.map(r=>r.q+' | '+r.a+' | '+r.g+(r.sourcePage?' | '+r.sourcePage:'')).join('\n');
 const book=books.find(x=>x.id===$('labBookSelect').value);
 if(book)$('activityTitle').value=('ألعاب '+book.name.replace(/\.(pdf|docx|txt)$/i,'')).slice(0,90);
 window.BOOYAH_LAB_BOOK_ID=$('labBookSelect').value;
 window.BOOYAH_LAB_SOURCE_GROUP='';window.BOOYAH_LAB_IMAGE_ID='';
 window.TG_CREATOR_PREVIEW_ROWS=null;
 bookDraftReady=accepted.length>=4;$('labBookSaveCloud').disabled=!bookDraftReady;
 if(bookDraftReady){
  $('applyContent').click();
  message('labBookStatus','✓ نُقلت '+accepted.length+' أسئلة مختارة إلى محرر الألعاب. راجعها مجددًا قبل الحفظ والنشر.');
 }else{
  message('labBookStatus','نقلت '+accepted.length+' أسئلة إلى المحرر. أضف أسئلة موثوقة حتى يصبح العدد 4 على الأقل ثم احفظها من مكتبتي.',true);
 }
 $('labBookSummary').textContent='تم نقل '+accepted.length+' مقترحًا مختارًا إلى المحرر، مع صفحات المصدر. لم تُنشر أي لعبة للطلاب.';
 document.getElementById('builder')?.scrollIntoView({behavior:'smooth',block:'start'});
}
async function generate(){
 const button=$('labBookGenerate');button.disabled=true;
 bookDraftReady=false;$('labBookSaveCloud').disabled=true;$('labBookApprove').disabled=true;
 window.BOOYAH_LAB_BOOK_ID='';
 message('labBookStatus',$('labBookMode').value==='ai'?'🧠 جارٍ توليد أسئلة ذكية متنوعة والتحقق من اقتباسات الكتاب... قد يستغرق ذلك نصف دقيقة.':'أحلل مفاهيم الدرس وأهدافه وأمثلته ومعلوماته القابلة لصياغة أسئلة...');
 try{
  const mode=$('labBookMode').value,params=requestDraft();
  if(mode==='ai'&&!$('labAiConsent').checked)throw Error('ai_consent_required');
  params.consent=mode==='ai'&&$('labAiConsent').checked;
  const response=await request('/api/game-lab/pro/books/'+(mode==='ai'?'ai':'draft'),params);
  const rows=Array.isArray(response.rows)?response.rows:[];
  renderBookReview(rows);
  $('labBookApprove').disabled=!rows.length;
  $('labBookSummary').textContent=rows.length
   ?'أُنشئت '+rows.length+' أسئلة من أصل '+params.count+' مطلوبة، بصيغ متنوعة. راجع كل سؤال وإجابة ومصدره قبل اعتمادها.'
   :'لم أجد أسئلة كافية وواضحة في الصفحات المحددة. جرّب صفحات أخرى أو وسّع النطاق بدل إنشاء أسئلة غير موثوقة.';
  message('labBookStatus',response.warning||'راجع المقترحات قبل اعتمادها.',rows.length<4);
 }catch(e){failed('labBookStatus',e)}
 finally{button.disabled=false}
}
async function archiveBook(){
 const id=$('labBookSelect').value,book=books.find(x=>x.id===id);
 if(!book){message('labBookStatus','اختر كتابًا أولًا.',true);return}
 if(!confirm('أرشفة «'+book.name+'»؟ سيختفي من قائمة الكتب المتاحة للتوليد، لكن الأنشطة المحفوظة لن تُحذف.'))return;
 try{await request('/api/game-lab/pro/books/archive',{bookId:id,confirm:true});bookId='';clearBookReview();await refreshBooks();message('labBookStatus','✓ أُرشف الكتاب دون حذف أنشطتك المحفوظة.')}catch(e){failed('labBookStatus',e)}
}
async function showPages(){
 clearBookReview();
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
$('labBookMode').onchange=()=>{aiModeTouched=true;updateAiSettings()};
updateAiSettings();
$('labBookApprove').onclick=approveBookSuggestions;
$('labBookSaveCloud').onclick=()=>{
 if(!bookDraftReady){message('labBookStatus','يلزم أربع أسئلة موثوقة على الأقل.',true);return}
 if(!token()){message('labBookStatus','سجّل دخول المعلم أولًا ثم احفظ المسودة.',true);scroll('cloud');return}
 document.dispatchEvent(new CustomEvent('gamelab:save-book-draft',{detail:{bookId:$('labBookSelect').value}}));
};
$('labBookArchive').onclick=archiveBook;
$('labBookPages').onclick=showPages;
$('labBookOpenEditor').onclick=()=>scroll('builder');
$('activityData').addEventListener('input',()=>{window.TG_CREATOR_PREVIEW_ROWS=null});
$('labBookSelect').onchange=e=>{bookId=e.target.value;clearBookReview();renderBooks()};
$('labAssignType').onchange=renderTargetChoices;
$('labAssignRefresh').onclick=loadStudents;
$('labAssignActivity').onchange=showAssignments;
$('labAssignSave').onclick=saveAssignments;
$('labLiveCreate').onclick=createRoom;
$('labLiveRefresh').onclick=refreshRooms;
$('labSaveImageCloud').onclick=uploadImage;
if(token()){void refreshBooks();void loadStudents();void refreshImages();void refreshRooms()}
})();
