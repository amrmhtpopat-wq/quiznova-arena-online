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
 ai_not_configured:'التوليد الذكي المجاني يحتاج مفتاح TAG AI API مجاني من Google AI Studio (مزود TAG AI) محفوظًا في إعدادات Render، دون تفعيل الفوترة.',
 ai_consent_required:'وافق أولًا على إرسال الصفحات المختارة إلى مزود الذكاء الاصطناعي.',
 ai_daily_limit:'وصلت إلى حد TAG AI (15 عملية خلال 24 ساعة متحركة). لا تُحتسب محاولات الاتصال الفاشلة أو النتائج غير القابلة للحفظ. جرّب بعد انتهاء مدة المحاولات السابقة، أو استخدم الاستخراج المحلي المجاني.',
 ai_global_daily_limit:'وصلت المنصة إلى حد الأمان اليومي لطلبات الذكاء الاصطناعي. حاول غدًا.',
 ai_too_many_pages:'لجودة أفضل وضمن الحدود المجانية، اختر 25 صفحة أو أقل في عملية التوليد الواحدة.',
 ai_source_quality_low:'الصفحات المختارة لا تحتوي على نص تعليمي مقروء كافٍ. افحص جودة النص، أو اختر صفحات شرح أخرى أو ارفع ملف PDF نصيًا سليمًا.',
 ai_invalid_key:'مفتاح TAG AI المجاني غير صالح أو غير متاح في المنطقة. تأكد من إنشائه عبر Google AI Studio (مزود TAG AI) دون حساب فوترة.',
 ai_no_credit:'لا يوجد رصيد مجاني متاح. لا تفعّل الفوترة؛ استخدم الاستخراج المحلي المجاني.',
 ai_rate_limited:'وصلت إلى حصة TAG AI المجانية أو الحد المؤقت. لن تُحاول المنصة استخدام خدمة مدفوعة. جرّب لاحقًا أو استخدم التوليد المحلي.',
 ai_provider_configuration:'تعذر استخدام نموذج TAG AI المجاني في هذا المشروع؛ تحقق من صلاحيات المفتاح المجاني أو استخدم الاستخراج المحلي.',
 ai_model_unavailable:'نموذجا TAG AI المجانيان غير متاحين لمشروعك حاليًا. تحقق من حالة مشروعك في Google AI Studio (مزود TAG AI)، دون تفعيل الفوترة.',
 ai_free_tier_unavailable:'Google رفض المستوى المجاني لهذا المشروع أو المنطقة. تحقق من حالة المشروع في AI Studio؛ لا حاجة لدفع أي شيء.',
 ai_access_denied:'Google رفض الوصول للمشروع (403). راجع حالة Free Tier وصلاحية المشروع والمفتاح في Google AI Studio (مزود TAG AI).',
 ai_network_error:'تعذر الاتصال بخوادم Google من Render. تأكد من أن خوادم Google متاحة وحاول مجددًا.',
 ai_timeout:'انتهت مهلة اتصال TAG AI المجاني. جرّب تحديد صفحات أقل ثم أعد المحاولة.',
 ai_provider_overloaded:'خدمة Google مشغولة حاليًا (503). وإذا تعذّر التوليد ستقدّم المنصة أسئلة محلية مستخرجة من الكتاب لمراجعتها.',
 ai_provider_unavailable:'تعذر الاتصال بمزوّد TAG AI الخارجي حاليًا. احتفظ بكتابك وأسئلتك، وجرّب مجددًا لاحقًا أو استخدم التوليد المحلي.',
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
 if(document.documentElement.dataset.tagView){
   const id=e.detail?.id||'';
   location.href='/tag-lab-assign.html'+(id?'?activity='+encodeURIComponent(id):'');
   return;
 }
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
  $('labBookMode').title=aiReady?'تمت إضافة مفتاح TAG AI مجاني؛ الخدمة جاهزة للاختبار':'يتطلب التوليد الذكي المجاني مفتاح GEMINI_API_KEY بدون فوترة';
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
  ?(enabled?'✓ مفتاح TAG AI موجود. ستُرسل الصفحات المختارة إلى TAG AI المجاني فقط عند موافقتك. لا يوجد انتقال إلى خدمة مدفوعة.':'يمكنك اختيار TAG AI المجاني من القائمة.')
  :'التوليد المجاني بالذكاء الاصطناعي غير مفعّل بعد. أنشئ مفتاح TAG AI مجانيًا من Google AI Studio (مزود TAG AI) دون ربط بطاقة أو حساب فوترة، ثم أضف GEMINI_API_KEY إلى Render. الاستخراج المحلي يعمل دائمًا دون مفتاح.';
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
   difficulty:$('labAiDifficulty').value,focus:$('labAiFocus').value,
   topic:$('labAiTopic').value.trim(),questionBalance:$('labAiQuestionBalance').value}
}
function clearBookReview(){
 if($('labBookSourceQuality'))$('labBookSourceQuality').textContent='';
 window.TG_BOOK_EDITOR_REUSE=false;
 bookDraftReady=false;
 $('labBookSaveCloud').disabled=true;
 $('labBookApprove').disabled=true;
 window.TG_CREATOR_PREVIEW_ROWS=null;
 window.TG_QUESTION_BANK_ROWS=null;
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
function reviewSelect(className,value,options){
 const control=document.createElement('select');control.className=className;
 for(const [id,label] of options){const opt=document.createElement('option');opt.value=id;opt.textContent=label;control.append(opt)}
 control.value=value;return control
}
function invalidBookQuestion(q,a){
 const question=String(q||'').normalize('NFKC').trim();
 const answer=String(a||'').normalize('NFKC').trim();
 const normalized=question.replace(/[\u064b-\u065f\u0670\u0640]/g,'')
  .replace(/[أإآٱ]/g,'ا').replace(/ى/g,'ي').replace(/\s+/g,' ').trim();
 if(!question||!answer)return true;
 if(/(?:ثم\s+)?(?:اجب|اقرا|حل)\s+(?:عن|علي|الاسئلة|الاسئله|السؤال|النص)/.test(normalized))return true;
 if(/(?:الاسئله|الاسئلة)\s+(?:التي\s+)?(?:تليه|تلي|التاليه|التالية)/.test(normalized))return true;
 if(/^ما\s+المقصود\s+ب[ـ]?\s*(?:ثم|اجب|اقرا|اكتب|اختر|حل)/.test(normalized))return true;
 if(/^[،؛:!?؟|)\]}]+/.test(answer))return true;
 for(const [start,end] of [['"','"'],['«','»'],['“','”']]){
  if(answer.startsWith(start)&&!answer.endsWith(end))return true;
 }
 if(/منالمتحان|المةصفحة|الصفحاتادد|السئلةجميع|ازلزي/.test(normalized))return true;
 return false
}
function renderBookReview(rows){
 const parent=$('labBookPreview');parent.replaceChildren();
 const intro=document.createElement('p');intro.className='hint';
 intro.textContent='راجع نوع السؤال والصعوبة والإجابة الصحيحة والبدائل قبل اعتمادها. لا تُنشر أي أسئلة تلقائيًا.';
 parent.append(intro);
 const validRows=(Array.isArray(rows)?rows:[]).filter(r=>!invalidBookQuestion(r?.q,r?.a));
 const removed=(Array.isArray(rows)?rows.length:0)-validRows.length;
 if(removed){
  const warning=document.createElement('p');warning.className='notice';
  warning.textContent='⚠️ استُبعد '+removed+' سؤالًا غير صالح بسبب تعليمات امتحان أو نص/إجابة مبتورة. لن تُعتمد هذه الأسئلة؛ أعد التوليد من صفحات الدرس.';
  parent.append(warning);
 }
 const types=[['mcq','🔘 اختيار من متعدد (4 خيارات)'],['true_false','✅ صح أو خطأ'],['short','🧠 فهم وإجابة قصيرة']];
 const levels=[['easy','سهل'],['medium','متوسط'],['hard','متقدم']];
 for(const [i,r] of validRows.entries()){
  const card=document.createElement('article');card.className='lab-bookrow tag-book-review-card';
  const header=document.createElement('div');header.className='tag-book-review-top';
  const keep=document.createElement('label');keep.className='tag-book-review-keep';
  const check=document.createElement('input');check.type='checkbox';check.checked=!r.requiresReview;check.className='tag-book-review-check';
  keep.append(check,document.createTextNode(' اعتماد السؤال '+(i+1)));
  const badge=document.createElement('small');badge.textContent='صفحة '+(r.sourcePage||'غير محددة')+' • '+(r.origin==='ai'?'TAG AI':'نص الكتاب');
  header.append(keep,badge);
  if(r.requiresReview){
   const warn=document.createElement('p');warn.className='notice';warn.style.margin='7px 0';
   warn.textContent='⚠️ يحتاج هذا السؤال مراجعة خاصة: '+(r.reviewReason||'تحقق من الإجابة مع صفحة الكتاب.');
   card.append(warn);
  }
  const row=document.createElement('div');row.className='tag-book-review-controls';
  const typeLabel=document.createElement('label');typeLabel.textContent='نوع السؤال';
  const kind=reviewSelect('tag-book-type',r.questionType||'short',types);typeLabel.append(kind);
  const levelLabel=document.createElement('label');levelLabel.textContent='مستوى الصعوبة';
  const level=reviewSelect('tag-book-difficulty',r.difficulty||'medium',levels);levelLabel.append(level);
  row.append(typeLabel,levelLabel);
  const questionLabel=document.createElement('label');questionLabel.textContent='نص السؤال أو العبارة';
  const question=reviewInput('question',r.q,200);questionLabel.append(question);
  const answerLabel=document.createElement('label');answerLabel.textContent='الإجابة الصحيحة';
  const answer=reviewInput('answer',r.a,100);answerLabel.append(answer);
  const choicesBlock=document.createElement('div');choicesBlock.className='tag-book-options';
  const choicesTitle=document.createElement('strong');choicesTitle.textContent='الخيارات الأربعة — يجب أن يتطابق أحدها مع الإجابة الصحيحة';
  choicesBlock.append(choicesTitle);
  const defaults=Array.isArray(r.choices)?r.choices:[];
  for(let j=0;j<4;j++){
   const field=document.createElement('label');field.textContent='الخيار '+(j+1);
   const input=document.createElement('input');input.type='text';input.className='tag-book-choice';
   input.maxLength=100;input.value=String(defaults[j]||'');input.dir='auto';field.append(input);
   choicesBlock.append(field);
  }
  const explainLabel=document.createElement('label');explainLabel.textContent='تفسير الإجابة للطالب (اختياري)';
  const explain=reviewInput('explanation',r.explanation||'',240);explain.rows=2;explainLabel.append(explain);
  const source=document.createElement('p');source.className='tag-book-evidence';
  source.textContent=r.sourceQuote?'الدليل من النص: «'+r.sourceQuote+'»':'قارن السؤال والإجابة مع صفحة الكتاب قبل الاعتماد.';
  card._tagSource=r;
  const updateChoices=()=>{choicesBlock.hidden=kind.value!=='mcq'};
  kind.addEventListener('change',()=>{updateChoices();bookDraftReady=false;$('labBookSaveCloud').disabled=true});
  updateChoices();card.append(header,row,questionLabel,answerLabel,choicesBlock,explainLabel,source);parent.append(card)
 }
 return validRows
}
function approveBookSuggestions(){
 const cards=[...$('labBookPreview').querySelectorAll('.tag-book-review-card')];
 if(!cards.length){message('labBookStatus','ولّد مقترحات أولًا ثم راجعها.',true);return}
 const accepted=[],seen=new Set();
 for(const card of cards){
  if(!card.querySelector('.tag-book-review-check').checked)continue;
  const q=card.querySelector('.tag-book-question').value.replace(/\s+/g,' ').trim().replaceAll('|',' ');
  const a=card.querySelector('.tag-book-answer').value.replace(/\s+/g,' ').trim().replaceAll('|',' ');
  const type=card.querySelector('.tag-book-type').value,level=card.querySelector('.tag-book-difficulty').value;
  const explanation=card.querySelector('.tag-book-explanation').value.trim().slice(0,240);
  if(!q||!a){message('labBookStatus','يوجد سؤال أو جواب فارغ ضمن الأسئلة المختارة.',true);return}
  if(invalidBookQuestion(q,a)){
   message('labBookStatus','تعذر اعتماد السؤال «'+q.slice(0,45)+'» لأن نصه أو إجابته غير صالح. عدّله أو ألغِ اختياره.',true);return
  }
  const key=(q+'|'+a).toLocaleLowerCase('ar');if(seen.has(key))continue;seen.add(key);
  const source=card._tagSource||{},row={q,a,g:source.g||'عام',sourcePage:source.sourcePage||null,
   sourceQuote:source.sourceQuote||'',origin:source.origin||'ai',questionType:type,
   difficulty:level};
  if(explanation)row.explanation=explanation;
  if(type==='mcq'){
   const choices=[...card.querySelectorAll('.tag-book-choice')].map(x=>x.value.replace(/\s+/g,' ').trim());
   if(choices.length!==4||choices.some(x=>!x)||new Set(choices.map(x=>x.toLocaleLowerCase('ar'))).size!==4||choices.filter(x=>x.toLocaleLowerCase('ar')===a.toLocaleLowerCase('ar')).length!==1){
    message('labBookStatus','راجع السؤال «'+q.slice(0,45)+'»: يتطلب الاختيار من متعدد 4 إجابات مختلفة تتضمن الإجابة الصحيحة مرة واحدة.',true);return
   }
   row.choices=choices
  }else if(type==='true_false'){
   if(a!=='صح'&&a!=='خطأ'){message('labBookStatus','إجابة سؤال الصح والخطأ يجب أن تكون «صح» أو «خطأ».',true);return}
   row.choices=['صح','خطأ']
  }
  accepted.push(row)
 }
 if(!accepted.length){message('labBookStatus','حدد سؤالًا موثوقًا واحدًا على الأقل.',true);return}
 $('activityData').value=accepted.map(r=>r.q+' | '+r.a+' | '+r.g+(r.sourcePage?' | '+r.sourcePage:'')).join('\n');
 const editingExisting=Boolean(window.TG_BOOK_EDITOR_REUSE);
 const book=editingExisting?null:books.find(x=>x.id===$('labBookSelect').value);
 if(book)$('activityTitle').value=('ألعاب '+book.name.replace(/\.(pdf|docx|txt)$/i,'')).slice(0,90);
 if(!editingExisting){
  window.BOOYAH_LAB_BOOK_ID=$('labBookSelect').value;
  window.BOOYAH_LAB_SOURCE_GROUP='';window.BOOYAH_LAB_IMAGE_ID='';
 }
 window.TG_QUESTION_BANK_ROWS=accepted.map(x=>({...x}));
 window.TG_CREATOR_PREVIEW_ROWS=accepted.map(x=>({...x}));
 document.dispatchEvent(new CustomEvent('gamelab:book-bank-accepted',{detail:{editingExisting}}));
 window.TG_BOOK_EDITOR_REUSE=false;
 bookDraftReady=accepted.length>=4;$('labBookSaveCloud').disabled=editingExisting||!bookDraftReady;
 if(bookDraftReady){$('applyContent').click();
  message('labBookStatus','✓ اعتمدت '+accepted.length+' أسئلة وحُفظت الخيارات والصعوبة والتفسير في المحرر؛ يمكنك حفظها بمكتبتك الخاصة.');
 }else message('labBookStatus','اعتمدت '+accepted.length+' أسئلة. أضف أسئلة موثوقة حتى يصبح العدد 4 على الأقل قبل الحفظ.',true);
 $('labBookSummary').textContent='أنواع الأسئلة: '+accepted.filter(x=>x.questionType==='mcq').length+' اختيار من متعدد، '+accepted.filter(x=>x.questionType==='true_false').length+' صح وخطأ، '+accepted.filter(x=>x.questionType==='short').length+' إجابة قصيرة. لم تُنشر للطلاب.';
 document.getElementById('builder')?.scrollIntoView({behavior:'smooth',block:'start'})
}
function showSourceQuality(report){
 const host=$('labBookSourceQuality');
 if(!host)return;
 host.replaceChildren();
 if(!report){host.textContent='لم تتوفر نتيجة فحص النص.';return}
 const heading=document.createElement('b');
 heading.textContent=(report.ready?'✅':'⚠️')+' نصوص صالحة: '+report.readablePages+' من '+report.selectedPages+' صفحة';
 host.append(heading);
 const description=document.createElement('p');description.textContent=report.message||'';
 description.style.margin='4px 0';host.append(description);
 const invalid=(report.pages||[]).filter(x=>!x.readable);
 if(invalid.length){
  const note=document.createElement('p');note.style.margin='4px 0';
  note.textContent='صفحات لم تُرسل إلى TAG AI بسبب ضعف النص: '+invalid.map(x=>x.page).join('، ');
  host.append(note)
 }
 const skipped=document.createElement('small');
 skipped.textContent='مقاطع مستبعدة: '+(report.excludedFragments||0)+' • هذا الفحص لا يستهلك محاولات الذكاء الاصطناعي.';
 host.append(skipped);
}
async function checkSourceQuality(){
 const params=requestDraft();
 const qs=new URLSearchParams({id:params.bookId,startPage:String(params.startPage),endPage:String(params.endPage)});
 const response=await request('/api/game-lab/pro/books/quality?'+qs.toString());
 showSourceQuality(response.quality);
 return response.quality
}
async function auditBookSource(){
 const button=$('labBookCheckSource');button.disabled=true;
 try{
  const report=await checkSourceQuality();
  message('labBookStatus',report.message||'اكتمل فحص الصفحات.',!report.ready)
 }catch(error){failed('labBookStatus',error)}
 finally{button.disabled=false}
}
async function generate(){
 const button=$('labBookGenerate');button.disabled=true;
 window.TG_BOOK_EDITOR_REUSE=false;
 bookDraftReady=false;$('labBookSaveCloud').disabled=true;$('labBookApprove').disabled=true;
 window.BOOYAH_LAB_BOOK_ID='';
 message('labBookStatus',$('labBookMode').value==='ai'?'🧠 جارٍ توليد أسئلة ذكية متنوعة والتحقق من اقتباسات الكتاب... قد يستغرق ذلك نصف دقيقة.':'أحلل مفاهيم الدرس وأهدافه وأمثلته ومعلوماته القابلة لصياغة أسئلة...');
 try{
  const mode=$('labBookMode').value,params=requestDraft();
  if(mode==='ai'&&!$('labAiConsent').checked)throw Error('ai_consent_required');
  if(mode==='ai'){
   const report=await checkSourceQuality();
   if(!report.ready)throw Error('ai_source_quality_low');
  }
  params.consent=mode==='ai'&&$('labAiConsent').checked;
  const response=await request('/api/game-lab/pro/books/'+(mode==='ai'?'ai':'draft'),params);
  const rows=Array.isArray(response.rows)?response.rows:[];
  if(response.sourceAudit)showSourceQuality(response.sourceAudit);
  const localFallback=response.fallbackFrom==='ai';
  const reviewable=renderBookReview(rows);
  $('labBookApprove').disabled=!reviewable.length;
  const breakdown=reviewable.length
   ?'أُنشئت '+reviewable.length+' أسئلة صالحة للمراجعة: '+reviewable.filter(r=>r.questionType==='mcq').length+' اختيار، '+reviewable.filter(r=>r.questionType==='true_false').length+' صح أو خطأ، '+reviewable.filter(r=>r.questionType==='short').length+' فهم وإجابة قصيرة. راجع الخيارات والأدلة قبل الاعتماد.'
   :(localFallback
     ?'تعذّر التوليد لدى Google، ولم يجد المحرك المحلي جملًا يمكن تحويلها إلى أسئلة مباشرة. هذا لا يعني أن الكتاب تالف. فحص جودة الصفحات أعلاه يوضح صلاحية النص؛ جرّب TAG AI مجددًا عندما تستقر الخدمة.'
     :'لم أجد أسئلة كافية من الصيغ المباشرة في الصفحات المحددة. جرّب صفحات شرح أخرى أو وسّع النطاق.');
  const needsReview=reviewable.filter(r=>r.requiresReview).length;
  const discarded=rows.length-reviewable.length;
  $('labBookSummary').textContent=(localFallback?'⚠️ تعذّر الاتصال بالنماذج المجانية المتاحة، والبديل الحالي استخراج نصي وليس ذكاءً اصطناعيًا. ':'')+breakdown+
   (needsReview?' ⚠️ '+needsReview+' أسئلة تحتاج مراجعة الإجابة قبل تحديد اعتمادها.':'')+
   (discarded?' 🛡️ استُبعد '+discarded+' سؤال مشوّه قبل عرضه.':'');
  message('labBookStatus',response.warning||'راجع المقترحات قبل اعتمادها.',reviewable.length<4);
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
 // The independent LAB uses a local roster on its separate assignment page.
 if(document.documentElement.dataset.tagView)return;
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
 // Legacy live rooms used official-platform records; keep disabled in LAB.
 if(document.documentElement.dataset.tagView)return;
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
  const playerUrl='https://tag-lab.onrender.com/?next='+encodeURIComponent(response.studentUrl);
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
$('labBookCheckSource').onclick=auditBookSource;
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
document.addEventListener('gamelab:edit-structured-bank',event=>{
 const rows=event.detail?.rows;
 if(!Array.isArray(rows)||!rows.length)return;
 window.TG_BOOK_EDITOR_REUSE=true;
 window.BOOYAH_LAB_BOOK_ID=event.detail?.bookId||'';
 const reviewable=renderBookReview(rows);
 bookDraftReady=false;$('labBookSaveCloud').disabled=true;
 $('labBookApprove').disabled=!reviewable.length;
 $('labBookSummary').textContent='تعديل بنك محفوظ: يمكنك تحرير الإجابات البديلة والصعوبة والتفسير، ثم الضغط على «اعتماد المختار»، وبعدها «حفظ النشاط» في مكتبتي لتحديث المسودة نفسها دون استهلاك TAG AI.';
 scroll('bookLab');
});
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
