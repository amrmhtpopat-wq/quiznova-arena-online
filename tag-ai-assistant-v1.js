/* TAG AI Assistant V1 — safe teacher-only, explicit consent, editable preview, no auto-publish. */
(()=>{'use strict';
 const d=document;
 if(d.getElementById('tagaiOpen'))return;
 const token=()=>{try{return localStorage.getItem('qn9_teacher_token')||''}catch(_){return ''}};
 const draftKey='tag_lab_question_draft_v31',selectedKey='tag_lab_selected_game';
 const native=(name,cls,content)=>{
  const e=d.createElement(name);if(cls)e.className=cls;
  if(content!==undefined)e.textContent=content;return e
 };
 const s={rows:[],title:'',request:null,busy:false,lastFocus:null};
 const errorMap={
  login_required:'سجّل الدخول إلى حساب معلم TAG LAB أولًا.',
  ai_not_configured:'TAG AI غير مفعّل على هذه الخدمة. تحقّق من إعداد GEMINI_API_KEY على Render.',
  ai_prompt_length:'اكتب طلبًا واضحًا يتكون من 12 إلى 1400 حرف.',
  ai_personal_data:'احذف البريد الإلكتروني أو رقم الهاتف أو رمز بطاقة الطالب من طلبك.',
  ai_consent_required:'وافق أولًا على إرسال نص الطلب إلى مزوّد TAG AI.',
  ai_count_invalid:'اختر عددًا من 4 إلى 25 سؤالًا.',
  ai_daily_limit:'وصلت إلى الحد اليومي لتوليد الأسئلة على حسابك.',
  ai_global_daily_limit:'وصلت المنصة إلى الحد اليومي لتوليد الأسئلة.',
  ai_rate_limited:'بلغت الحصة المؤقتة لدى TAG AI، جرّب لاحقًا.',
  ai_access_denied:'مزود TAG AI رفض المفتاح أو صلاحية المشروع.',
  ai_model_unavailable:'نموذج TAG AI غير متاح في المشروع حاليًا.',
  ai_invalid_response:'لم تصل أسئلة صالحة من TAG AI. جرّب طلبًا أوضح.',
  ai_timeout:'انتهت مهلة التوليد. جرّب عددًا أقل من الأسئلة.',
  ai_network_error:'تعذّر الاتصال بمزود TAG AI من Render.',
  ai_provider_configuration:'إعدادات النموذج لا تسمح بالتوليد بهذا الطلب.',
  ai_provider_unavailable:'خدمة TAG AI غير متاحة الآن.',
 };
 const fab=native('button','tagai-fab tagai-robot-trigger');fab.id='tagaiOpen';fab.type='button';
 fab.setAttribute('aria-haspopup','dialog');fab.setAttribute('aria-expanded','false');
 fab.setAttribute('aria-label','فتح المساعد الذكي TAG AI');fab.title='افتح مساعد TAG AI';
 const bot=native('img','tagai-robot-art');bot.alt='';bot.width=49;bot.height=58;
 bot.src='/assets/brand/tag-ai-robot-slow-v1.svg';bot.decoding='async';bot.draggable=false;
 const prefersReduced=window.matchMedia?.('(prefers-reduced-motion: reduce)');
 if(prefersReduced?.matches)bot.src='/assets/brand/tag-ai-robot-still-v1.svg';
 prefersReduced?.addEventListener?.('change',e=>{
  bot.src=e.matches?'/assets/brand/tag-ai-robot-still-v1.svg':'/assets/brand/tag-ai-robot-slow-v1.svg'
 });
 fab.append(bot);
 const overlay=native('div','tagai-overlay');overlay.hidden=true;overlay.id='tagaiOverlay';
 const shell=native('section','tagai-shell');shell.setAttribute('role','dialog');
 shell.setAttribute('aria-modal','true');shell.setAttribute('aria-labelledby','tagaiTitle');
 const top=native('div','tagai-top'),header=native('div');
 const title=native('h2',null,'✦ المساعد الذكي TAG AI');title.id='tagaiTitle';
 header.append(title,native('small',null,'أنشئ أسئلة لمسابقتك، وراجعها ثم انقلها لمحرر النشاط'));
 const close=native('button','tagai-close','×');close.type='button';close.setAttribute('aria-label','إغلاق المساعد');
 top.append(header,close);shell.append(top);
 const main=native('div','tagai-body');
 const form=native('form');form.id='tagaiForm';
 const promptWrap=native('div','tagai-prompt');
 const promptLabel=native('label',null,'ماذا تريد أن تنشئ؟');promptLabel.htmlFor='tagaiPrompt';
 const prompt=native('textarea');prompt.id='tagaiPrompt';prompt.maxLength=1400;prompt.required=true;
 prompt.placeholder='أنشئ لي مسابقة للصف السابع من درس وحدات الإدخال، 15 سؤالًا بمستويات مختلفة.';
 promptWrap.append(promptLabel,prompt);form.append(promptWrap);
 const fields=native('div','tagai-grid');
 const mkField=(text,id,input)=>{
  const outer=native('div','tagai-field'),label=native('label',null,text);label.htmlFor=id;input.id=id;
  outer.append(label,input);fields.append(outer);return input
 };
 const count=mkField('عدد الأسئلة','tagaiCount',native('input'));
 count.type='number';count.min='4';count.max='25';count.step='1';count.value='15';
 const difficulty=mkField('المستوى','tagaiDifficulty',native('select'));
 [['balanced','متدرج: سهل، متوسط، صعب'],['easy','سهل'],['advanced','متقدم']].forEach(([v,t])=>{
  const option=native('option',null,t);option.value=v;difficulty.append(option)
 });
 const subject=mkField('المبحث (اختياري)','tagaiSubject',native('input'));
 subject.placeholder='المهارات الرقمية';subject.maxLength=60;
 const grade=mkField('الصف (اختياري)','tagaiGrade',native('input'));
 grade.placeholder='السابع';grade.maxLength=35;
 form.append(fields);
 const consentWrap=native('label','tagai-consent');
 const consent=native('input');consent.type='checkbox';consent.required=true;consent.id='tagaiConsent';
 consentWrap.append(consent,native('span',null,'أوافق على إرسال نص الطلب فقط إلى Google عبر TAG AI للتوليد. لن أضع أسماء الطلاب أو رموزهم أو معلوماتهم الشخصية. الأسئلة الناتجة تحتاج مراجعة المعلم قبل الحفظ أو النشر.'));
 form.append(consentWrap);
 const controls=native('div','tagai-buttons');
 const generate=native('button','tagai-primary','✦ إنشاء الأسئلة');generate.type='submit';
 const account=native('a','tagai-secondary','الدخول إلى حساب المعلم');
 account.href='/tag-lab-account.html';account.hidden=!!token();account.style.textDecoration='none';
 controls.append(generate,account);form.append(controls);
 const status=native('p','tagai-status');status.id='tagaiStatus';
 status.setAttribute('role','status');status.setAttribute('aria-live','polite');
 form.append(status);main.append(form);
 const results=native('section','tagai-results');results.hidden=true;
 results.setAttribute('aria-label','مراجعة أسئلة TAG AI');
 const rh=native('div','tagai-results-head');
 const rhText=native('h3',null,'مراجعة الأسئلة قبل النقل');
 const badge=native('small','tagai-rules','يمكنك تعديل أي سؤال أو إجابة أو خيار.');
 rh.append(rhText,badge);results.append(rh);
 const questionContainer=native('div','tagai-questions');results.append(questionContainer);
 const actions=native('div','tagai-actions-fixed');
 const modeWrap=native('div','tagai-field');
 const modeLabel=native('label',null,'القالب الذي تريد فتحه');modeLabel.htmlFor='tagaiMode';
 const mode=native('select');mode.id='tagaiMode';
 [['quiz','تحدي الاختبار'],['fast','سباق الوقت'],['wheel','عجلة الحظ'],['boxes','الصناديق الغامضة'],
  ['pairs','توصيل الأزواج']].forEach(([v,label])=>{const x=native('option',null,label);x.value=v;mode.append(x)});
 modeWrap.append(modeLabel,mode);actions.append(modeWrap);
 const hint=native('p','tagai-rules','لن تُحفظ الأسئلة أو تُنشر تلقائيًا. بعد النقل راجعها داخل محرر النشاط واضغط حفظ بنفسك.');
 const transfer=native('button','tagai-primary','نقل الأسئلة إلى محرر النشاط ←');transfer.type='button';
 actions.append(hint,transfer);results.append(actions);
 main.append(results);shell.append(main);overlay.append(shell);
 d.body.append(fab,overlay);
 // A fixed floating mascot used to overlap bottom buttons. Keep it visible
 // inside the shared topbar instead, retaining exactly the same animated SVG.
 const headerDock=d.querySelector('.tagv-topbar .tagv-header-actions');
 if(headerDock){
  headerDock.append(fab);
  fab.classList.add('tagai-header-dock');
 }
 function notify(message,isError=false){status.textContent=message;status.dataset.error=String(isError)}
 function open(){
  s.lastFocus=d.activeElement;overlay.hidden=false;d.body.classList.add('tagai-modal-open');
  fab.setAttribute('aria-expanded','true');account.hidden=!!token();
  setTimeout(()=>prompt.focus(),0)
 }
 function shut(){
  overlay.hidden=true;d.body.classList.remove('tagai-modal-open');
  fab.setAttribute('aria-expanded','false');s.lastFocus?.focus?.()
 }
 fab.addEventListener('click',open);close.addEventListener('click',shut);
 overlay.addEventListener('click',event=>{if(event.target===overlay&&!s.busy)shut()});
 d.addEventListener('keydown',e=>{
  if(overlay.hidden)return;
  if(e.key==='Escape'&&!s.busy){e.preventDefault();shut()}
  if(e.key==='Tab'){
   const candidates=[...shell.querySelectorAll('input:not([disabled]),textarea:not([disabled]),select:not([disabled]),button:not([disabled]),a[href]')].filter(x=>x.getClientRects().length);
   if(!candidates.length)return;
   const first=candidates[0],last=candidates[candidates.length-1];
   if(e.shiftKey&&d.activeElement===first){e.preventDefault();last.focus()}
   if(!e.shiftKey&&d.activeElement===last){e.preventDefault();first.focus()}
  }
 });
 function field(label,initial,onChange,multiline=false){
  const outer=native('label','tagai-field'),name=native('span',null,label);
  const input=native(multiline?'textarea':'input');input.value=initial||'';
  if(multiline)input.rows=2;
  input.maxLength=multiline?200:100;
  input.addEventListener('input',()=>onChange(input.value));
  outer.append(name,input);return outer
 }
 function render(){
  questionContainer.replaceChildren();
  rhText.textContent='مراجعة '+s.rows.length+' سؤالًا — '+s.title;
  s.rows.forEach((row,i)=>{
   const card=native('article','tagai-question');
   const head=native('div','tagai-qtop');
   head.append(native('strong',null,'السؤال '+(i+1)),
               native('span','tagai-difficulty',({easy:'سهل',medium:'متوسط',hard:'متقدم'})[row.difficulty]||'متوسط'));
   const del=native('button','tagai-danger','حذف السؤال');del.type='button';
   del.addEventListener('click',()=>{if(s.rows.length<=4){notify('احتفظ بأربعة أسئلة على الأقل لنقل النشاط.',true);return}
    s.rows.splice(i,1);render()});
   head.append(del);card.append(head);
   card.append(field('نص السؤال',row.q,value=>row.q=value,true));
   card.append(field('الإجابة الصحيحة',row.a,value=>row.a=value));
   if(row.questionType==='mcq'){
    const grid=native('div','tagai-choice-grid');
    (row.choices||[]).forEach((val,idx)=>grid.append(field('الخيار '+(idx+1),val,value=>row.choices[idx]=value)));
    card.append(grid)
   }else if(row.questionType==='true_false'){
    const options=native('div','tagai-field');
    const label=native('label',null,'إجابة صح أو خطأ');
    const sel=native('select');
    [['صح','صح'],['خطأ','خطأ']].forEach(([v,t])=>{const o=native('option',null,t);o.value=v;sel.append(o)});
    sel.value=row.a;sel.onchange=()=>{row.a=sel.value;card.querySelector('label.tagai-field input')?.setAttribute('value',row.a)};
    options.append(label,sel);card.append(options)
   }
   const info=native('p','tagai-rules','النوع: '+(row.questionType==='mcq'?'اختيار متعدد':row.questionType==='true_false'?'صح أو خطأ':'إجابة قصيرة'));
   card.append(info);
   card.append(field('شرح الإجابة (اختياري)',row.explanation||'',value=>row.explanation=value,true));
   questionContainer.append(card)
  });
 }
 function validRows(){
  const rows=[];const seen=new Set();
  for(let i=0;i<s.rows.length;i++){
   const r=s.rows[i],q=String(r.q||'').trim().slice(0,200),a=String(r.a||'').trim().slice(0,100);
   if(q.length<9||!a)throw Error('السؤال '+(i+1)+' يحتاج نصًا واضحًا وإجابة.');
   if(seen.has(q.toLowerCase()))throw Error('يوجد سؤال مكرر رقم '+(i+1));
   seen.add(q.toLowerCase());
   const choices=Array.isArray(r.choices)?r.choices.map(x=>String(x||'').trim().slice(0,100)):[];
   if(r.questionType==='mcq'&&(choices.length!==4||new Set(choices.map(x=>x.toLowerCase())).size!==4||!choices.includes(a)||choices.some(x=>!x)))
    throw Error('السؤال '+(i+1)+': يجب وجود أربعة خيارات مختلفة، ويطابق أحدها الإجابة الصحيحة تمامًا.');
   if(r.questionType==='true_false'&&!['صح','خطأ'].includes(a))
    throw Error('السؤال '+(i+1)+' يجب أن تكون إجابته صح أو خطأ.');
   rows.push({...r,q,a,choices:r.questionType==='mcq'?choices:r.questionType==='true_false'?['صح','خطأ']:[],
             g:String(r.g||'عام').slice(0,60),sourcePage:undefined})
  }
  if(rows.length<4)throw Error('يحتاج النشاط أربعة أسئلة مكتملة على الأقل.');
  return rows
 }
 form.addEventListener('submit',async e=>{
  e.preventDefault();if(s.busy)return;
  if(!token()){notify('سجّل الدخول إلى حساب معلم TAG LAB أولًا.',true);account.hidden=false;return}
  if(!consent.checked){notify('يجب الموافقة على إرسال طلبك أولًا.',true);return}
  s.busy=true;generate.disabled=true;generate.textContent='جارٍ توليد الأسئلة...';notify('يُنشئ TAG AI المسودة. لن تُنشر قبل مراجعتها.');
  try{
   const body={prompt:prompt.value.trim(),count:Number(count.value),difficulty:difficulty.value,
               subject:subject.value.trim(),grade:grade.value.trim(),consent:true};
   const response=await fetch('/api/game-lab/ai-assistant/generate',{
    method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+token()},
    body:JSON.stringify(body),cache:'no-store'});
   const data=await response.json().catch(()=>({}));
   if(!response.ok||!data.ok)throw Error(data.error||'network_error');
   s.title=String(data.title||'مسابقة تعليمية').slice(0,90);
   s.rows=(data.rows||[]).map(row=>({...row,choices:[...(row.choices||[])]}));
   s.request=body;results.hidden=false;render();
   notify('✓ تم إنشاء '+s.rows.length+' أسئلة. راجعها وعدّلها ثم انقلها إلى المحرر.');
   results.scrollIntoView({block:'nearest',behavior:'smooth'});
  }catch(err){notify(errorMap[err.message]||'تعذّر التوليد: '+err.message,true)}
  finally{s.busy=false;generate.disabled=false;generate.textContent='✦ إنشاء الأسئلة'}
 });
 transfer.addEventListener('click',()=>{
  try{
   const rows=validRows(),destination=mode.value;
   if(!confirm('هل تريد نقل '+rows.length+' سؤالًا إلى محرر '+mode.selectedOptions[0].textContent+'؟ ستستبدل مسودة هذا القالب في المحرر، دون تغيير الأنشطة المحفوظة.'))return;
   const payload={rows,title:s.title,subject:s.request?.subject||'عام',
     grade:s.request?.grade||'عام',time:'25'};
   const editorReady=location.pathname==='/tag-lab-create.html'&&typeof window.TAG_LAB_V33_IMPORT==='function';
   if(editorReady){
    window.TAG_LAB_V33_SELECT?.(destination);
    window.TAG_LAB_V33_IMPORT(destination,payload);
    const panel=d.getElementById('tagV33Editor');shut();
    panel?.scrollIntoView({behavior:'smooth',block:'start'});
   }else{
    const transferData={ts:Date.now(),title:payload.title,subject:payload.subject,grade:payload.grade,
        bookId:'',rows};
    sessionStorage.setItem(draftKey,JSON.stringify(transferData));
    sessionStorage.setItem(selectedKey,destination);
    location.href='/tag-lab-create.html';
   }
  }catch(err){notify(err.message||'تعذر نقل المسودة.',true)}
 });
})();
