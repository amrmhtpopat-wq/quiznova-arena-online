'use strict';
/* TAG SMART MATH phase 3: genuine role-aware, server-backed classroom pilot.
   All scored answers are checked on the server; no solution keys are sent before submission. */
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state={user:null,page:'home',assignments:[],report:null,progress:null,attempt:null,feedback:null,chosen:null,selectedAssignment:null,busy:false};
const phases={foundation:'التأسيس',application:'التطبيق',reasoning:'التفكير'};
async function api(path,method='GET',data){
  const options={method,credentials:'same-origin',headers:{'Accept':'application/json'}};
  if(data!==undefined){options.headers['Content-Type']='application/json';options.body=JSON.stringify(data)}
  if(method!=='GET' && path!=='/api/login' && state.user)options.headers['X-CSRF-Token']=state.user.csrf;
  let r;
  try{r=await fetch(path,options)}catch{throw new Error('تعذر الاتصال بالخادم. تحقق من الشبكة ثم أعد المحاولة؛ إجاباتك المحفوظة لن تضيع.')}
  const val=await r.json().catch(()=>({error:'رد غير متوقع من الخادم'}));
  if(!r.ok){const e=new Error(val.error||'تعذر إكمال الطلب');e.status=r.status;e.code=val.code;e.details=val;throw e}
  return val;
}
function alertError(err){const a=$('alert');a.textContent=String(err?.message||err);a.classList.remove('hidden');clearTimeout(alertError.timer);alertError.timer=setTimeout(()=>a.classList.add('hidden'),6500)}
function basePage(h,title,subtitle,buttons=''){return `<div class="sectiontitle"><div><div class="eyebrow">${esc(h)}</div><h2>${esc(title)}</h2><div class="small">${esc(subtitle)}</div></div>${buttons}</div>`}
function btn(action,text,cls='',extra=''){return `<button class="btn ${cls}" data-action="${esc(action)}" ${extra}>${text}</button>`}
function nav(){if(!state.user)return '';
 const items=state.user.role==='teacher'?[['home','الرئيسية'],['create','إنشاء تكليف'],['report','تقارير الطلاب']]:[['home','تدريباتي'],['progress','تقدمي']];
 return `<nav class="nav" aria-label="القائمة المدرسية">${items.map(([id,label])=>btn('page-'+id,label,state.page===id?'active':'')).join('')}${btn('logout','خروج','ghost')}</nav>`}
function mobileNav(){const m=$('mobileNav');if(!state.user){m.classList.add('hidden');return}
 const items=state.user.role==='teacher'?[['home','الرئيسية'],['create','التكليفات'],['report','التقارير']]:[['home','تدريباتي'],['progress','تقدمي']];
 m.classList.remove('hidden');m.innerHTML=items.map(([id,label])=>`<button data-action="page-${id}" class="${state.page===id?'active':''}">${esc(label)}</button>`).join('')+`<button data-action="logout">خروج</button>`}
function loginPage(){return `<section class="hero"><div><div class="eyebrow">TAG SCHOOL PILOT • مستقلة عن الموقع الرسمي</div><h1>الرياضيات الآن <strong class="accent">من أجهزة الطلاب إلى المعلم.</strong></h1><p>تدريب من 30 سؤالًا على درس حل المعادلات للصف السابع، مع حفظ المحاولة على الخادم ومتابعة النتائج الفعلية للشعبة التجريبية.</p><div class="chip-row"><span class="pill">5 طلاب تجريبيين</span><span class="pill">حفظ مركزي</span><span class="pill">تصحيح آمن</span></div></div><div class="hero-art"><div class="math-tile">3x + 4 = 19<span>السؤال 7 من 30</span></div></div></section>
 <section class="box login"><h2>دخول النسخة المدرسية</h2><p>استخدم حساب المعلم أو أحد حسابات الطلاب التجريبية. هذه ليست حسابات TAG الأصلية.</p>
 <form id="loginForm"><label class="field">اسم المستخدم <input name="username" required autocomplete="username" placeholder="teacher أو student01"></label><label class="field">كلمة المرور<input type="password" name="password" required autocomplete="current-password" placeholder="كلمة مرور التجربة"></label><button class="btn primary" type="submit" style="width:100%">الدخول إلى المساحة المدرسية</button></form>
 <div class="banner" style="margin-top:18px">للاختبار التعليمي ببيانات وهمية فقط: <b dir="ltr">teacher</b> أو <b dir="ltr">student01 – student05</b><br>احصل على كلمة مرور التجربة من منسق الاختبار. قد تُمسح النتائج عند إعادة تشغيل الخادم؛ صدّر تقرير CSV بعد كل جلسة. لا تستخدم أسماء الطلاب أو بياناتهم الحقيقية.</div></section>`}
function teacherHome(){const report=state.report||{attempts:[],students:[]};const finished=report.attempts.filter(x=>x.status==='finished');const avg=finished.length?Math.round(finished.reduce((s,x)=>s+x.percent,0)/finished.length):0;
 return `<section class="hero"><div><div class="eyebrow">مساحة المعلم • ${esc(state.user.classroom)}</div><h1>متابعة طلابك، <strong class="accent">بدون كتابة الأسئلة.</strong></h1><p>كل تكليف ينشئ 30 سؤالًا متدرجًا تلقائيًا. يمكنك متابعة من بدأ التدريب ومن أكمله والمهارات التي تحتاج إلى مراجعة.</p>${btn('page-create','إنشاء تدريب جديد','primary')}${btn('page-report','متابعة نتائج الطلاب','')}</div><div class="hero-art"><div class="math-tile">TAG × 30<span>تأسيس ← تطبيق ← تفكير</span></div></div></section>
 <div class="sectiontitle"><h2>ملخص الشعبة التجريبية</h2></div><div class="grid">${metric(report.students.length,'طلاب في التجربة')}${metric(finished.length,'تدريبات مكتملة')}${metric(avg+'%','متوسط النتيجة المكتملة')}</div>
 <div class="sectiontitle"><h2>التكليفات</h2>${btn('page-create','تكليف جديد','sm')}</div>${assignmentList(true)}`}
function metric(n,l){return `<div class="metric"><b>${esc(n)}</b><small>${esc(l)}</small></div>`}
function assignmentList(teacher=false){const rows=state.assignments;
 if(!rows.length)return `<div class="box empty">لا توجد تكليفات حاليًا.</div>`;
 return rows.map(a=>`<article class="item"><div><h3>${esc(a.title)}</h3><p>${esc(a.classroom)} • ${a.question_count} سؤالًا • ${a.mode==='practice'?'تدريب بالتصحيح الفوري':'اختبار بعد التسليم'} • حد المحاولات: ${a.max_attempts}</p></div><div class="chip-row">${teacher?'<span class="pill good">منشور للشعبة</span>':a.active_id?`${btn('resume-'+a.active_id,'إكمال السابق','primary sm')}${btn('new-'+a.id,'بدء جديد','ghost sm')}`:`${btn('start-'+a.id,'ابدأ التدريب','primary sm')}`}${!teacher&&a.finished?`<span class="pill">أنهيت ${a.finished} محاولة</span>`:''}</div></article>`).join('')}
function studentHome(){return `<section class="hero"><div><div class="eyebrow">أهلًا ${esc(state.user.display_name)} • ${esc(state.user.classroom)}</div><h1>اختر تدريبك، <strong class="accent">وأكمل من حيث توقفت.</strong></h1><p>أسئلة متجددة، وتصحيح فوري في وضع التدريب. نتيجتك تُحفظ على الخادم لتراها أنت ومعلم شعبتك.</p>${btn('page-progress','اعرض تقدمي','')}</div><div class="hero-art"><div class="math-tile">x + 8 = 17<span>حل • تعلم • أتقن</span></div></div></section>
 <div class="sectiontitle"><h2>تدريبات الصف السابع</h2><span class="pill">الفصل الأول</span></div>${assignmentList()}
 <div class="banner">يتم حفظ الإجابة بعد الضغط على «تحقق وأرسل». لا تظهر نتائج طلاب آخرين في حسابك.</div>`}
function createPage(){return `${basePage('المعلم / التكليفات','إنشاء تدريب للطلاب','التدريب منشأ آليًا لدرس حل المعادلات؛ لا حاجة لكتابة 30 سؤالًا.')}
 <section class="box" style="max-width:800px"><form id="createForm"><div class="formgrid">
 <label class="field full">عنوان التكليف <input name="title" maxlength="90" required value="تدريب حل المعادلات — الصف السابع"></label>
 <label class="field">الشعبة <select name="classroom"><option>${esc(state.user.classroom)}</option></select></label>
 <label class="field">عدد الأسئلة <select name="count"><option value="30">30 سؤالًا (أساسي)</option><option value="15">15 سؤالًا</option><option value="10">10 أسئلة</option><option value="5">5 أسئلة</option></select></label>
 <label class="field">نمط العمل <select name="mode"><option value="practice">تدريب — تصحيح بعد كل إجابة</option><option value="exam">اختبار — تصحيح بعد الإنهاء</option></select></label>
 <label class="field">المحاولات المكتملة المسموحة <select name="max_attempts"><option value="2">محاولتان</option><option value="1">محاولة واحدة</option><option value="3">3 محاولات</option><option value="5">5 محاولات</option></select></label></div>
 <div class="banner">يتوزع تدريب 30 سؤالًا إلى 10 تأسيس + 12 تطبيق + 8 تفكير، ويغطي ست مهارات في درس حل المعادلات.</div>
 <button class="btn primary" type="submit">إنشاء ونشر التكليف للشعبة</button></form></section>
 <div class="sectiontitle"><h2>تكليفاتي الحالية</h2></div>${assignmentList(true)}`}
function reportPage(){const report=state.report||{attempts:[],students:[]};const completed=report.attempts.filter(a=>a.status==='finished');let weak={};for(const a of report.attempts)for(const [key,val] of Object.entries(a.skills||{})){const d=weak[key]||{name:val.name,total:0,correct:0};d.total+=val.total;d.correct+=val.correct;weak[key]=d}
 const weakList=Object.values(weak).filter(x=>x.total).sort((a,b)=>a.correct/a.total-b.correct/b.total);
 return `${basePage('المعلم / التقارير','متابعة النتائج الحقيقية','البيانات أدناه ناتجة عن محاولات محفوظة على الخادم، ولا توجد علامات وهمية.',`<a class="btn sm" href="/api/teacher/report.csv">تصدير CSV / Excel</a>`)}
 <div class="grid">${metric(report.students.length,'طلاب الشعبة')}${metric(report.attempts.length,'محاولات مسجلة')}${metric(completed.length,'محاولات مكتملة')}</div>
 <div class="sectiontitle"><h2>سجل الطلاب</h2><span class="small">تحديث تلقائي كل 15 ثانية</span></div><div class="box tablewrap" style="padding:0"><table><thead><tr><th>الطالب</th><th>الشعبة</th><th>التكليف</th><th>الحالة</th><th>النتيجة</th></tr></thead><tbody>${report.attempts.length?report.attempts.map(a=>`<tr><td>${esc(a.display_name)}</td><td>${esc(a.classroom)}</td><td>${esc(a.title)}</td><td><span class="pill ${a.status==='finished'?'good':'neutral'}">${a.status==='finished'?'مكتمل':a.status==='active'?'قيد التدريب':'متروك'}</span></td><td>${a.percent===null?'—':esc(a.percent)+'%'}</td></tr>`).join(''):`<tr><td colspan="5" class="empty">لم تُسجل أي محاولة بعد. ادخل بحساب طالب وابدأ التدريب.</td></tr>`}</tbody></table></div>
 <div class="sectiontitle"><h2>المهارات التي تحتاج إلى متابعة</h2></div><section class="box">${weakList.length?weakList.map(k=>{const rate=Math.round(k.correct*100/k.total);return `<div class="skill"><div class="row"><strong>${esc(k.name)}</strong><span>${rate}% • ${k.total} إجابة</span></div><div class="progress"><i style="width:${rate}%"></i></div></div>`}).join(''):'<div class="empty">لا توجد إجابات كافية لعرض تحليل المهارات بعد.</div>'}<p class="small">هذه مؤشرات تشخيصية، وليست أحكامًا نهائية على إتقان الطالب.</p></section>`}
function progressPage(){const r=state.progress||{attempts:[],skills:{}};const complete=r.attempts.filter(x=>x.status==='finished');const avg=complete.length?Math.round(complete.reduce((n,a)=>n+a.percent,0)/complete.length):0;
return `${basePage('الطالب / تقدمي','تقدمي في المعادلات','نتائج محفوظة على الخادم، تظهر عند الدخول من أي جهاز بالحساب نفسه.')}
<div class="grid">${metric(complete.length,'تدريبات مكتملة')}${metric(avg+'%','متوسط الدقة')}${metric(r.attempts.filter(x=>x.status==='active').length,'تدريبات غير مكتملة')}</div>
<div class="sectiontitle"><h2>خريطة المهارات</h2></div><section class="box">${Object.values(r.skills||{}).length?Object.values(r.skills).map(x=>`<div class="skill"><div class="row"><b>${esc(x.name)}</b><span>${esc(x.rate)}% • ${esc(x.level)}</span></div><div class="progress"><i style="width:${x.rate}%"></i></div></div>`).join(''):'<p class="muted">تظهر خريطة مهاراتك بعد إنهاء تدريب.</p>'}</section>
<div class="sectiontitle"><h2>سجل محاولاتي</h2></div>${r.attempts.length?r.attempts.map(a=>`<article class="item"><div><h3>${esc(a.title)}</h3><p>${esc(a.started_at.slice(0,10))} • ${a.status==='finished'?'مكتمل':a.status==='active'?'قيد التدريب':'متروك'} • ${a.percent===null?'—':a.percent+'%'}</p></div>${a.status==='finished'?btn('resume-'+a.id,'عرض النتيجة','sm'):a.status==='active'?btn('resume-'+a.id,'استكمال التدريب','sm primary'):''}</article>`).join(''):'<div class="box empty">لم تبدأ أي تدريب بعد.</div>'}`}
function practicePage(){const a=state.attempt;if(!a)return '<div class="box empty">اختر تدريبًا للبدء.</div>';
 if(a.status==='finished')return resultPage();const q=a.question;if(!q)return '<div class="box empty">تعذر تحميل السؤال الحالي.</div>';
 const pct=Math.round((a.index/a.count)*100);
 return `<section class="question"><div class="row wrap"><div><div class="eyebrow">الصف السابع • حل المعادلات</div><h2>${esc(a.title)}</h2></div><span class="pill">${a.mode==='practice'?'وضع التدريب':'وضع الاختبار'}</span></div>
 <div class="row"><strong>السؤال ${a.index+1} من ${a.count}</strong><span class="small">${esc(phases[q.phase]||q.phase)} • ${esc(q.skill_name)}</span></div><div class="progress"><i style="width:${pct}%"></i></div>
 <article class="box" style="margin-top:15px"><h2>${esc(q.prompt)}</h2><div class="equation" dir="ltr">${esc(q.math)}</div>
 ${state.feedback?feedbackBlock():`<form id="answerForm"><div style="margin:15px 0">${q.kind==='mcq'?`<div class="choices">${q.options.map(n=>`<button type="button" data-choice="${esc(n)}" class="${String(state.chosen)===String(n)?'selected':''}" aria-pressed="${String(state.chosen)===String(n)}">${esc(n)}</button>`).join('')}</div>`:`<label class="field" for="answerNum">اكتب قيمة x <small>تُقبل الأرقام العربية والإنجليزية</small></label><input id="answerNum" class="answerinput" inputmode="decimal" autocomplete="off" aria-label="إجابتك الرقمية" required placeholder="x = ؟">`}</div><div class="row mobwrap">${btn('page-home','حفظ والعودة','ghost')}<button type="submit" class="btn primary">تحقق وأرسل الإجابة</button></div></form>`}</article>
 <p class="small" style="text-align:center">تُحفظ الإجابات على الخادم. يمكن العودة إلى التدريب من جهاز آخر باستخدام الحساب نفسه.</p></section>`}
function feedbackBlock(){const f=state.feedback.feedback||{},isCorrect=f.correct;
 return `<section class="feedback ${isCorrect?'':'bad'}"><h3>${isCorrect?'✓ أحسنت، إجابة صحيحة':'✦ جرّب أن تفهم سبب الخطأ'}</h3>${f.expected!==undefined?`<p>الإجابة الصحيحة: <strong dir="ltr">x = ${esc(f.expected)}</strong></p><p>${esc(f.hint)}</p><ol>${(f.steps||[]).map(s=>`<li>${esc(s)}</li>`).join('')}</ol>`:'<p>تم تسجيل إجابتك. سيظهر التصحيح بعد الانتهاء من الاختبار.</p>'}
 ${btn('next-question',state.feedback.finished?'عرض نتيجتي':'السؤال التالي','primary')}</section>`}
function resultPageContent(r){if(!r)return '';
 const skills=Object.values(r.skills||{});
 return `<section class="box" style="max-width:840px;margin:auto"><div class="eyebrow">نتيجة التدريب</div><h2>أحسنت على إكمال المحاولة!</h2><div class="resultnum">${esc(r.correct)} / ${esc(r.count)}</div><div class="row" style="justify-content:center"><span class="pill good">${esc(r.percent)}% دقة الإجابة</span></div><div class="sectiontitle"><h2>إتقان المهارات</h2></div>${skills.map(s=>`<div class="skill"><div class="row"><b>${esc(s.name)}</b><small>${esc(s.correct)} من ${esc(s.total)} • ${esc(s.level)}</small></div><div class="progress"><i style="width:${esc(s.rate)}%"></i></div></div>`).join('')}
 <p class="small">لا تعني محاولة واحدة الوصول إلى الإتقان؛ كرر التدريب لاحقًا للتحقق من ثبات المهارة.</p><div class="chip-row">${btn('page-home','تدريب جديد','primary')}${btn('page-progress','تقدمي','ghost')}</div></section>`}
function resultPage(){return resultPageContent(state.attempt?.lastResult)}
function render(){mobileNav();const view=$('view');const u=state.user;
 if(!u){view.innerHTML=loginPage();return}
 let html=nav();
 if(state.page==='home')html+=u.role==='teacher'?teacherHome():studentHome();
 else if(state.page==='create'&&u.role==='teacher')html+=createPage();
 else if(state.page==='report'&&u.role==='teacher')html+=reportPage();
 else if(state.page==='progress'&&u.role==='student')html+=progressPage();
 else if(state.page==='practice'&&u.role==='student')html+=practicePage();
 else if(state.page==='result'&&u.role==='student')html+=resultPage();
 else html+='<div class="box empty">الصفحة غير متاحة لهذا الدور.</div>';
 view.innerHTML=html;
 window.scrollTo({top:0,behavior:'instant'});
}
async function refresh(){if(!state.user)return;
 const ass=await api('/api/assignments');state.assignments=ass.items;
 if(state.user.role==='teacher')state.report=await api('/api/teacher/report');
 else state.progress=await api('/api/student/progress');
 render();}
async function resume(id){state.attempt=await api('/api/attempts/'+encodeURIComponent(id));state.feedback=null;state.chosen=null;
 if(state.attempt.status==='finished'){state.attempt.lastResult=await api('/api/attempts/'+encodeURIComponent(id)+'/result');state.page='result'}else state.page='practice';render()}
async function start(id,fresh=false){
 try{const data=await api('/api/attempts/start','POST',{assignment_id:id,new:fresh});await resume(data.attempt_id)}
 catch(e){if(e.code==='active_attempt'){
  const yes=confirm('لديك تدريب غير منتهٍ. اضغط «موافق» لإكماله، أو «إلغاء» لبدء تدريب جديد دون حذف نتائج المحاولات المكتملة.');
  if(yes)await resume(e.details.attempt_id);else if(confirm('هل تريد بدء تدريب جديد؟ ستُلغى المحاولة غير المكتملة فقط.'))await start(id,true);
 }else alertError(e)}
}
async function answerSubmit(form){if(state.busy)return;const a=state.attempt;const q=a.question;
 const val=q.kind==='mcq'?state.chosen:form.querySelector('#answerNum')?.value;
 if(val===null||val===undefined||String(val).trim()===''){alertError('اختر إجابة أو اكتب قيمة x أولًا.');return}
 state.busy=true;
 try{const result=await api('/api/attempts/'+encodeURIComponent(a.id)+'/answer','POST',{index:a.index,answer:val});
   state.feedback=result;render();
 }catch(e){alertError(e)}finally{state.busy=false}}
async function nextQuestion(){const a=state.attempt;if(state.feedback?.finished){a.lastResult=await api('/api/attempts/'+encodeURIComponent(a.id)+'/result');state.page='result';await refresh();return}await resume(a.id)}
async function logout(){try{await api('/api/logout','POST',{})}catch{}state.user=null;state.assignments=[];state.attempt=null;state.report=null;state.page='home';render()}
async function perform(action){if(!action)return;
 if(action==='logout')return logout();
 if(action==='refresh-report'){await refresh();return}
 if(action.startsWith('page-')){const p=action.slice(5);state.page=p;await refresh();return}
 if(action.startsWith('resume-'))return resume(action.slice(7));
 if(action.startsWith('start-'))return start(action.slice(6));
 if(action.startsWith('new-'))return start(action.slice(4),true);
 if(action==='next-question')return nextQuestion();}
document.addEventListener('click',async e=>{const choice=e.target.closest('[data-choice]');if(choice){state.chosen=choice.dataset.choice;document.querySelectorAll('[data-choice]').forEach(x=>{x.classList.toggle('selected',x===choice);x.setAttribute('aria-pressed',String(x===choice))});return}
 const b=e.target.closest('[data-action]');if(b){try{await perform(b.dataset.action)}catch(err){alertError(err)}}});
document.addEventListener('submit',async e=>{if(!['loginForm','createForm','answerForm'].includes(e.target.id))return;e.preventDefault();const form=e.target;const submit=form.querySelector('button[type=submit]');if(submit)submit.disabled=true;
 try{
 if(form.id==='loginForm'){const fd=new FormData(form);await api('/api/login','POST',{username:fd.get('username'),password:fd.get('password')});state.user=await api('/api/me');state.page='home';await refresh()}
 else if(form.id==='createForm'){const fd=new FormData(form);await api('/api/assignments','POST',{title:fd.get('title'),classroom:fd.get('classroom'),count:Number(fd.get('count')),mode:fd.get('mode'),max_attempts:Number(fd.get('max_attempts'))});state.page='home';await refresh()}
 else if(form.id==='answerForm')await answerSubmit(form);
 }catch(err){alertError(err)}finally{if(submit&&submit.isConnected)submit.disabled=false}
});
(async()=>{try{state.user=await api('/api/me');await refresh()}catch(e){if(e.status!==401)alertError(e);render()}})();

// Teacher monitor refreshes automatically while visible; no polling for student answer screens.
setInterval(async()=>{
  if(document.hidden||!state.user||state.user.role!=='teacher'||!['home','report'].includes(state.page))return;
  try{const current=state.page,pos=window.scrollY;
    state.report=await api('/api/teacher/report');
    state.assignments=(await api('/api/assignments')).items;
    if(state.page===current){render();window.scrollTo({top:pos,behavior:'instant'})}
  }catch(e){/* Last valid report stays visible; an explicit action shows connection errors. */}
},15000);
