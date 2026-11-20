/* TAG studio textbook -> editable quiz. Reuse authenticated TAG LAB endpoints.
 * The AI button is available ONLY when a provider is explicitly configured.
 * Offline extraction is clearly labeled and never misrepresented as AI.
 */
(function(){
'use strict';
const panel=document.getElementById('tagBookMaker');
if(!panel)return;
const el=id=>document.getElementById(id);
let books=[],selectedBook=null,resultRows=[],resultMode='extract',working=false,aiEnabled=false;
const errors={
 upload_not_found:'انتهت جلسة الرفع. أعد رفع الكتاب.',
 upload_expired:'انتهت مهلة رفع الكتاب. أعد المحاولة.',
 file_too_large:'حجم الكتاب يتجاوز 40 ميغابايت. يمكنك تقسيمه إلى ملفات أصغر.',
 book_limit:'وصلت إلى الحد الأقصى (12 كتابًا). أرشف كتابًا غير مطلوب ثم أعد الرفع.',
 unsupported_book_format:'الصيغ المقبولة: PDF وDOCX وTXT فقط.',
 invalid_pdf:'الملف ليس PDF صالحًا.',
 invalid_docx:'ملف Word تالف أو غير صالح.',
 password_protected_pdf:'الكتاب محمي بكلمة مرور، أزل الحماية قبل الرفع.',
 too_many_pages:'الكتاب يزيد على 350 صفحة. اختر ملفًا أصغر أو قسّمه.',
 book_has_no_extractable_text:'الملف لا يحتوي على نص قابل للاستخراج. قد يكون صورًا ممسوحة ضوئيًا وتحتاج إلى OCR.',
 invalid_pages:'تحقق من أرقام الصفحات المختارة.',
 empty_pages:'الصفحات المختارة لا تحتوي على نص قابل للاستخراج.',
 ai_too_many_pages:'اختر 25 صفحة أو أقل لكل طلب TAG AI.',
 ai_not_configured:'TAG AI غير مفعّل على الخادم. يمكنك استخدام الاستخراج المباشر أو تفعيل مزود Gemini.',
 ai_consent_required:'يجب الموافقة على إرسال نص الصفحات المختارة إلى مزود الذكاء الاصطناعي.',
 ai_daily_limit:'بلغت حد TAG AI اليومي لهذا المعلم (10 محاولات). يمكنك استخدام الاستخراج المباشر.',
 ai_global_daily_limit:'بلغت المنصة الحد اليومي المشترك. يمكنك استخدام الاستخراج المباشر.',
 ai_rate_limited:'مزود TAG AI أوقف الطلبات مؤقتًا بسبب الحصة أو المعدل. لا تحتسب الأسئلة غير الناتجة.',
 ai_model_unavailable:'نموذج الذكاء الاصطناعي غير متاح حاليًا للخدمة.',
 ai_invalid_key:'مفتاح مزود الذكاء الاصطناعي غير صالح ويحتاج إلى تصحيح من مدير المنصة.',
 ai_free_tier_unavailable:'خطة Gemini المجانية لا تتوفر لهذا الحساب أو البلد.',
 ai_provider_unavailable:'تعذر الاتصال بمزود TAG AI. جرّب الاستخراج المباشر.',
 ai_network_error:'حدث خلل اتصال بمزود الذكاء الاصطناعي.',
 ai_timeout:'استغرق توليد الأسئلة وقتًا أطول من المسموح.',
 ai_empty_response:'لم يرجع النموذج أسئلة قابلة للقراءة. اختر صفحات أوضح.',
 ai_invalid_response:'إجابة مزود الذكاء الاصطناعي غير صالحة. حاول تحديد صفحات أوضح.',
 ai_access_denied:'خدمة الذكاء الاصطناعي ترفض الاتصال حاليًا.',
 ai_provider_configuration:'يحتاج مزود TAG AI إلى ضبط الإعدادات.',
 login_required:'انتهت الجلسة. سجل دخولك من جديد.',
 book_not_found:'الكتاب غير متاح في حسابك.',
 invalid_question_count:'اختر عددًا بين 4 و25.'
};
const message=code=>errors[code]||'تعذر إتمام العملية ('+String(code||'network_error').slice(0,60)+').';
function notice(text,isError){
 const node=el('tagBookStatus');
 node.textContent=text;
 node.classList.toggle('is-error',!!isError);
}
function setBusy(value){
 working=value;
 ['tagBookUpload','tagBookExtract','tagBookArchive','tagBookSelect','tagBookFile','tagBookAi','tagBookApply'].forEach(id=>{
  const item=el(id);if(item)item.disabled=value||(id==='tagBookAi'&&!aiEnabled)||(id==='tagBookApply'&&!resultRows.length);
 });
}
async function request(path,body){
 const opts={headers:{Authorization:'Bearer '+String(window.QN9_TOKEN||'')},cache:'no-store'};
 if(body!==undefined){
  opts.method='POST';opts.headers['Content-Type']='application/json';opts.body=JSON.stringify(body);
 }
 let response;
 try{response=await fetch(path,opts)}
 catch(_){throw new Error('network_error')}
 let json;
 try{json=await response.json()}catch(_){throw new Error('invalid_response')}
 if(!response.ok||json.ok===false)throw new Error(json.error||'server_error');
 return json;
}
function makeOption(value,label){
 const o=document.createElement('option');o.value=value;o.textContent=label;return o;
}
function fillGrade(){
 const from=document.querySelectorAll('#genGrade option');
 const target=el('tagBookGrade');
 target.replaceChildren();
 Array.from(from).filter(o=>o.value!=='all').forEach(o=>target.append(makeOption(o.value,o.textContent)));
 target.value=el('genGrade').value!=='all'?el('genGrade').value:'السابع';
}
function clearResults(){
 resultRows=[];resultMode='extract';
 el('tagBookQuestions').replaceChildren();
 el('tagBookResults').hidden=true;
 setBusy(working);
}
async function refreshBooks(preferred){
 const data=await request('/api/game-lab/pro/books');
 aiEnabled=!!data.aiEnabled;
 books=Array.isArray(data.books)?data.books:[];
 const select=el('tagBookSelect'),previous=preferred||select.value;
 select.replaceChildren(makeOption('','اختر كتابًا من مكتبتك'));
 books.forEach(b=>select.append(makeOption(b.id,b.name+' — '+b.pageCount+' صفحة')));
 const found=books.find(b=>b.id===previous)||books[0]||null;
 select.value=found?found.id:'';
 el('tagBookAi').title=aiEnabled?'يستخدم TAG AI نص الصفحات المحددة فقط':'يحتاج تفعيل مفتاح Gemini على الخادم';
 el('tagBookAi').disabled=working||!aiEnabled;
 el('tagBookDetails').textContent=books.length
  ?'لديك '+books.length+' من 12 كتابًا محفوظًا. '+(aiEnabled?'TAG AI متاح وفق حصة الاستخدام.':'TAG AI غير متاح حاليًا؛ استخراج الأسئلة المباشر متاح دون مزود خارجي.')
  :'لم ترفع أي كتاب بعد. اختر كتابًا ثم اضغط رفع الكتاب. '+(aiEnabled?'':'الاستخراج المباشر متاح مجانًا.');
 await chooseBook(found?found.id:'');
}
async function chooseBook(id){
 selectedBook=books.find(b=>b.id===id)||null;
 clearResults();
 const preview=el('tagBookPagesPreview');
 preview.replaceChildren();
 if(!selectedBook){
  el('tagBookPagesInfo').open=false;
  el('tagBookDetails').textContent=books.length?el('tagBookDetails').textContent:'ارفع كتابًا أولًا.';
  return;
 }
 el('tagBookStart').value='1';
 el('tagBookEnd').value=String(Math.min(10,Number(selectedBook.pageCount)||1));
 el('tagBookStart').max=String(selectedBook.pageCount);
 el('tagBookEnd').max=String(selectedBook.pageCount);
 const response=await request('/api/game-lab/pro/books/pages?id='+encodeURIComponent(id));
 const pages=Array.isArray(response.pages)?response.pages:[];
 const valid=pages.filter(p=>String(p.preview||'').trim().length>10).length;
 const title=document.createElement('p');
 title.textContent='تم استخراج نص من '+valid+' صفحة من أصل '+selectedBook.pageCount+'. النص غير القابل للاستخراج (الصور الممسوحة) لا يصل إلى TAG AI.';
 preview.append(title);
 pages.slice(0,20).forEach(p=>{
  const block=document.createElement('details'),summary=document.createElement('summary'),body=document.createElement('p');
  summary.textContent='صفحة '+p.p+(p.preview?' • معاينة':' • لا يوجد نص');
  body.textContent=p.preview||'لا يوجد نص قابل للاستخراج في هذه الصفحة.';
  block.append(summary,body);preview.append(block);
 });
 if(pages.length>20){
  const more=document.createElement('p');
  more.textContent='تُعرض معاينة أول 20 صفحة فقط؛ يمكنك تحديد أي نطاق من صفحات الكتاب للتوليد.';
  preview.append(more);
 }
}
function fileBase64(blob){
 return blob.arrayBuffer().then(buffer=>{
  const bytes=new Uint8Array(buffer);
  const chunks=[];
  for(let i=0;i<bytes.length;i+=8192)
   chunks.push(String.fromCharCode.apply(null,bytes.subarray(i,i+8192)));
  return btoa(chunks.join(''));
 });
}
async function uploadFile(){
 if(working)return;
 const file=el('tagBookFile').files[0];
 if(!file)return notice('اختر كتاب PDF أو Word أو TXT أولًا.',true);
 if(!/\.(pdf|docx|txt)$/i.test(file.name))return notice(message('unsupported_book_format'),true);
 if(!file.size||file.size>40_000_000)return notice(message('file_too_large'),true);
 setBusy(true);clearResults();
 let uploadId='';
 try{
  notice('جارٍ بدء رفع '+file.name+' ...');
  const init=await request('/api/game-lab/pro/books/upload/start',{
   filename:file.name,fileSize:file.size,section:el('tagBookTopic').value.trim()||'كتاب كامل'
  });
  uploadId=init.uploadId;
  const chunkSize=Number(init.chunkBytes)||1_000_000;
  for(let offset=0,index=0;offset<file.size;offset+=chunkSize,index++){
   const encoded=await fileBase64(file.slice(offset,offset+chunkSize));
   await request('/api/game-lab/pro/books/upload/chunk',{uploadId,index,data:encoded});
   notice('جارٍ رفع الكتاب: '+Math.round(100*Math.min(file.size,offset+chunkSize)/file.size)+'٪');
  }
  notice('اكتمل الرفع. جارٍ استخراج النص وترقيم الصفحات...');
  const done=await request('/api/game-lab/pro/books/upload/finish',{uploadId});
  uploadId='';
  await refreshBooks(done.book?.id);
  el('tagBookFile').value='';
  notice('تم حفظ الكتاب في مكتبتك: '+done.book.name+' • '+done.book.pageCount+' صفحة. يمكنك اختيار الصفحات الآن.');
 }catch(error){
  notice(message(error.message),true);
  if(uploadId){try{await request('/api/game-lab/pro/books/upload/cancel',{uploadId})}catch(_){}}
 }finally{setBusy(false)}
}
function inputSettings(mode){
 const book=selectedBook;
 if(!book)throw new Error('book_not_found');
 const start=Number(el('tagBookStart').value),end=Number(el('tagBookEnd').value),count=Number(el('tagBookCount').value);
 if(!Number.isInteger(start)||!Number.isInteger(end)||start<1||end<start||end>Number(book.pageCount))throw new Error('invalid_pages');
 if(mode==='ai'&&end-start+1>25)throw new Error('ai_too_many_pages');
 if(!Number.isInteger(count)||count<4||count>25)throw new Error('invalid_question_count');
 if(mode==='ai'&&!el('tagBookAiConsent').checked)throw new Error('ai_consent_required');
 return {
  bookId:book.id,startPage:start,endPage:end,count,
  grade:el('tagBookGrade').value,subject:window.QN9_TEACHER?.subject||'عام',
  difficulty:el('tagBookDifficulty').value,focus:el('tagBookFocus').value,
  questionMix:el('tagBookQuestionMix').value,
  consent:mode==='ai'
 };
}
function element(tag,className,text){
 const node=document.createElement(tag);
 if(className)node.className=className;
 if(text!==undefined)node.textContent=String(text);
 return node;
}
function renderQuestions(payload,mode){
 resultRows=Array.isArray(payload.rows)?payload.rows:[];
 resultMode=mode;
 const root=el('tagBookQuestions');
 root.replaceChildren();
 resultRows.forEach((q,i)=>{
  const card=element('article','tag-book-question');
  const head=element('div','tag-book-question-head');
  const select=element('input');
  select.type='checkbox';select.className='tag-book-pick';select.value=String(i);
  select.setAttribute('aria-label','اختيار السؤال '+(i+1));
  const title=element('strong','',String(i+1)+'. '+q.q);
  head.append(select,title);
  card.append(head);
  const answer=element('p','tag-book-answer','✓ الإجابة المقترحة: '+q.a);
  card.append(answer);
  if(q.questionType==='mcq'&&Array.isArray(q.choices)){
   const choices=element('ol','tag-book-choices');
   q.choices.forEach(item=>{const li=element('li',String(item)===String(q.a)?'is-correct':'',item);choices.append(li)});
   card.append(choices);
  }
  const details=element('details','tag-book-evidence');
  const summary=element('summary','','📖 المصدر: صفحة '+q.sourcePage+' — عرض المقتطف');
  const quote=element('blockquote','','«'+String(q.sourceQuote||'')+'»');
  details.append(summary,quote);card.append(details);
  const note=element('small','',q.questionType==='mcq'?'اختيار من متعدد':q.questionType==='true_false'?'صح أو خطأ':'إجابة قصيرة');
  card.append(note);
  if(mode==='ai'&&aiEnabled){
   const retry=element('button','tag-book-retry','↻ إعادة توليد هذا السؤال');
   retry.type='button';retry.setAttribute('aria-label','إعادة توليد سؤال '+(i+1)+' من صفحة المصدر');
   retry.addEventListener('click',()=>void retryQuestion(i));
   card.append(retry);
  }
  root.append(card);
 });
 el('tagBookResults').hidden=!resultRows.length;
 const hint=el('tagBookResultHint');
 hint.textContent=payload.warning||'هذه مسودات مرتبطة بصفحات المصدر؛ راجع الصياغة والإجابة قبل الاعتماد.';
 const stats=payload.generationStats,statsBox=el('tagBookEngineStats');
 if(stats){
  const coverage=stats.coverage||{};
  statsBox.textContent='TAG AI V2 • المطلوب '+stats.requested+' • المقبول '+resultRows.length+
    ' • المستبعد '+(stats.rejected||0)+' • مقاطع الدرس '+(stats.sections||1)+
    ' • صفحات مغطاة '+(coverage.coveredPages||0)+' من '+(coverage.extractablePages||payload.sourcePages)+
    ' • طلبات AI المستخدمة '+(stats.providerCalls||1)+
    '. مطابقة المقتطف لا تغني عن مراجعة صحة السؤال والإجابة.';
 }else statsBox.textContent='مصادر مستخرجة من الكتاب. راجع الإجابة وكل سؤال قبل الاعتماد.';
 if(resultRows.length)notice('ظهرت '+resultRows.length+' أسئلة من '+payload.sourcePages+' صفحات. حدد المناسب ثم أضفه إلى محرر الاختبار.');
 else notice(payload.warning||'لم يُعثر على أسئلة موثقة. جرّب نطاق صفحات أكثر وضوحًا.',true);
}
async function retryQuestion(index){
 if(working||!aiEnabled||!selectedBook)return;
 const target=resultRows[index];
 if(!target||!target.sourcePage)return;
 let args;
 try{args=inputSettings('ai')}catch(error){return notice(message(error.message),true)}
 args.retryQuestion=String(target.q||'');
 args.retryPage=Number(target.sourcePage);
 args.excludeQuestions=resultRows.map(q=>String(q.q||'')).filter(Boolean).slice(0,25);
 setBusy(true);
 try{
  notice('جارٍ إعادة صياغة السؤال من الصفحة '+args.retryPage+' والتحقق من الاقتباس...');
  const result=await request('/api/game-lab/pro/books/ai/retry',args);
  if(!Array.isArray(result.rows)||!result.rows.length){
   return notice(result.warning||'لم يُعثر على بديل موثق؛ بقي السؤال القديم كما هو.',true);
  }
  const checked=Array.from(panel.querySelectorAll('.tag-book-pick:checked'),n=>Number(n.value));
  const newRows=resultRows.slice();
  newRows[index]=result.rows[0];
  renderQuestions({rows:newRows,warning:result.warning,sourcePages:result.sourcePages,
                   generationStats:result.generationStats},'ai');
  checked.forEach(i=>{const input=panel.querySelector('.tag-book-pick[value="'+i+'"]');if(input)input.checked=true;});
  notice('تم استبدال السؤال '+(index+1)+' بسؤال موثق المصدر. راجع الإجابة والخيارات.');
 }catch(error){notice(message(error.message),true)}
 finally{setBusy(false)}
}
async function generate(mode){
 if(working)return;
 let args;
 try{args=inputSettings(mode)}catch(error){return notice(message(error.message),true)}
 if(mode==='ai'&&!aiEnabled)return notice(message('ai_not_configured'),true);
 setBusy(true);clearResults();
 try{
  notice(mode==='ai'?'يحلل TAG AI مقاطع الدرس، ويولّد أسئلة متنوعة، ثم يدقق الاقتباسات والتكرار ويحاول إصلاح النواقص ضمن الحصة المتاحة...':'جارٍ استخراج الأسئلة والأجوبة المكتوبة صراحة في الكتاب...');
  const result=await request('/api/game-lab/pro/books/'+(mode==='ai'?'ai':'draft'),args);
  renderQuestions(result,mode);
 }catch(error){notice(message(error.message),true)}
 finally{setBusy(false)}
}
function applySelected(){
 if(working||!resultRows.length)return;
 const ids=Array.from(panel.querySelectorAll('.tag-book-pick:checked'),x=>Number(x.value));
 if(!ids.length)return notice('حدد سؤالًا واحدًا على الأقل.',true);
 const selected=ids.map(i=>resultRows[i]).filter(Boolean);
 const grade=el('tagBookGrade').value,topic=el('tagBookTopic').value.trim();
 if(typeof window.TAG_ACCEPT_BOOK_ROWS!=='function')return notice('محرر الاختبار غير جاهز. حدّث الصفحة وأعد المحاولة.',true);
 const response=window.TAG_ACCEPT_BOOK_ROWS(selected,selectedBook,grade,topic,resultMode);
 if(!response.ok)return notice('تعذر إدخال الأسئلة إلى المحرر: '+response.error,true);
 notice('تم نقل '+response.count+' سؤال إلى محرر الاختبار كمسودة. راجع الإجابات واضغط حفظ بعد الانتهاء.');
}
async function archiveSelected(){
 if(working||!selectedBook)return notice('اختر كتابًا للأرشفة.',true);
 if(!confirm('هل تريد أرشفة '+selectedBook.name+'؟ سيختفي من قائمتك، ولا تتأثر الاختبارات المحفوظة.'))return;
 setBusy(true);
 try{
  await request('/api/game-lab/pro/books/archive',{bookId:selectedBook.id,confirm:true});
  selectedBook=null;await refreshBooks('');
  notice('تمت أرشفة الكتاب بنجاح.');
 }catch(error){notice(message(error.message),true)}
 finally{setBusy(false)}
}
el('tagBookUpload').addEventListener('click',()=>void uploadFile());
el('tagBookAi').addEventListener('click',()=>void generate('ai'));
el('tagBookExtract').addEventListener('click',()=>void generate('extract'));
el('tagBookArchive').addEventListener('click',()=>void archiveSelected());
el('tagBookSelect').addEventListener('change',()=>{void chooseBook(el('tagBookSelect').value).catch(e=>notice(message(e.message),true))});
el('tagBookToggleAll').addEventListener('click',()=>{
 const inputs=Array.from(panel.querySelectorAll('.tag-book-pick'));
 const checked=inputs.every(item=>item.checked);
 inputs.forEach(item=>item.checked=!checked);
 el('tagBookToggleAll').textContent=checked?'تحديد الكل':'إلغاء التحديد';
});
el('tagBookApply').addEventListener('click',applySelected);
const lib=el('tagBookFromLibrary');
if(lib)lib.addEventListener('click',()=>{
 if(typeof window.go==='function')window.go('generator');
 panel.scrollIntoView({block:'start',behavior:'smooth'});
});
fillGrade();setBusy(false);
refreshBooks('').catch(e=>{notice(message(e.message),true);setBusy(false)});
})();
