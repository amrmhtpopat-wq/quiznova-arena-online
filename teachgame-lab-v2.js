/* TeachGame Game Lab V2 — accessible game gallery, quick quiz workflow and real local classroom games.
   Saved quizzes use the existing DB / QN9_SAVE_NOW teacher sync. These teacher-led games do not
   claim to create student result records or replace the existing live/solo quiz engines. */
(function () {
  'use strict';
  const host=document.getElementById('view-gamelab');
  if(!host)return;
  const $=s=>host.querySelector(s);
  const esc=v=>String(v==null?'':v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','"':'&#39;'}[c]));
  const id=()=>Date.now().toString(36)+Math.random().toString(36).slice(2,9);
  const quizList=()=>typeof DB==='undefined'?[]:DB.quizzes;
  const makeQ=()=>({id:id(),text:'',options:['','','',''],correct:0});
  const state={step:1,source:'saved',quizId:'',title:'',grade:'السابع',questions:[makeQ()],template:'quiz',runtime:null,busy:false,notice:''};
  const games={
    quiz:{title:'تحدي الأسئلة',detail:'ألوان واضحة ونقاط وتصحيح مباشر.',art:'quiz'},
    wheel:{title:'عجلة الحظ',detail:'تدور العجلة وتختار سؤالًا عشوائيًا.',art:'wheel'},
    boxes:{title:'افتح الصندوق',detail:'اكشف الأسئلة من صناديق مرقّمة.',art:'boxes'},
    pairs:{title:'مطابقة البطاقات',detail:'اقلب البطاقات وابحث عن الأزواج الصحيحة.',art:'pairs'}
  };
  function message(t){state.notice=t;const m=$('#tg2Notice');if(m){m.textContent=t;m.hidden=!t} if(window.toast && t)window.toast(t)}
  function existingQuiz(){return quizList().find(q=>String(q.id)===state.quizId)||null}
  function currentQuiz(){return state.source==='saved'?existingQuiz():{
    id:state.quizId||id(),title:state.title.trim(),grade:state.grade,
    subject:window.QN9_TEACHER?.subject||'عام',section:'',createdAt:Date.now(),
    settings:{randomQuestions:false,randomOptions:false,showFeedback:true,speedBonus:false,bossEnabled:false},
    questions:state.questions.map(q=>({id:q.id,type:'single',text:q.text.trim(),options:q.options.map(x=>x.trim()),correct:[Number(q.correct)],time:25,points:1000,difficulty:'medium',grade:state.grade,subject:window.QN9_TEACHER?.subject||'عام',unit:'عام',tags:[],image:'',skill:'',explanation:''}))
  }}
  function validate(){
    if(state.source==='saved'){
      if(!existingQuiz()){message('اختر اختبارًا محفوظًا، أو أنشئ أسئلة جديدة.');return false}
      if(!(existingQuiz().questions||[]).length){message('الاختبار المختار لا يحتوي على أسئلة.');return false}
    }else{
      if(!state.title.trim()){message('اكتب عنوان الاختبار أولًا.');$('#tg2Title')?.focus();return false}
      if(!state.questions.length){message('أضف سؤالًا واحدًا على الأقل.');return false}
      for(let i=0;i<state.questions.length;i++){
        const q=state.questions[i];
        if(!q.text.trim()||q.options.some(x=>!x.trim())){message('أكمل نص السؤال '+(i+1)+' وجميع الخيارات الأربعة.');return false}
        if(new Set(q.options.map(x=>x.trim().toLowerCase())).size!==q.options.length){message('لا تكرر نفس الخيار في السؤال '+(i+1)+'.');return false}
      }
    }
    message('');return true;
  }
  function findPairs(quiz){
    const items=[];
    for(const q of quiz.questions||[]){
      if(q.type==='match' && Array.isArray(q.pairs)){
        q.pairs.forEach(p=>{if(p.left&&p.right)items.push({a:String(p.left),b:String(p.right)})});
      }else if(q.type==='single'&&Array.isArray(q.options)&&Array.isArray(q.correct)){
        const right=q.options[Number(q.correct[0])];
        if(q.text&&right)items.push({a:String(q.text),b:String(right)});
      }else if(q.type==='tf'){
        if(q.text)items.push({a:String(q.text),b:q.correct===true?'صح':'خطأ'});
      }
    }
    return items.slice(0,6);
  }
  function playable(quiz,game){
    if(game==='quiz')return (quiz.questions||[]).some(q=>q.type==='single'||q.type==='tf');
    if(game==='pairs')return findPairs(quiz).length>=2;
    return (quiz.questions||[]).some(q=>q.text);
  }
  function art(key){
    if(key==='wheel')return '<div class="tg2-art tg2-art-wheel"><span class="tg2-arrow">▼</span><span class="tg2-disc"></span></div>';
    if(key==='boxes')return '<div class="tg2-art tg2-art-boxes"><span class="tg2-boxes"><i>?</i><i>★</i><i>?</i><i>3</i><i>?</i><i>6</i></span></div>';
    if(key==='pairs')return '<div class="tg2-art tg2-art-pairs"><span class="tg2-pair-art"><i>★</i><i>◆</i><i>🎯</i><i>◆</i><i>★</i><i>🎯</i></span></div>';
    return '<div class="tg2-art tg2-art-quiz"><span class="tg2-quiz-art"><b>ما الإجابة الصحيحة؟</b><span></span><span></span><span></span></span></div>';
  }
  function renderSteps(){
    const steps=[['1','جهّز الأسئلة'],['2','اختر اللعبة'],['3','شغّل النشاط']];
    $('#tg2Steps').innerHTML=steps.map(s=>'<button type="button" class="tg2-step '+(state.step===Number(s[0])?'is-active':'')+'" data-tg-action="step" data-step="'+s[0]+'" aria-current="'+(state.step===Number(s[0])?'step':'false')+'"><b>'+s[0]+'</b>'+s[1]+'</button>').join('');
  }
  function renderSource(){
    const all=quizList().filter(q=>(q.questions||[]).length);
    if(!state.quizId && all.length)state.quizId=String(all[0].id);
    let html='<div class="tg2-section-head"><div><h3>كيف تريد تجهيز الأسئلة؟</h3><p>ابدأ باختبار محفوظ أو اكتب الأسئلة هنا مباشرة.</p></div><span class="tg2-badge">الخطوة 1 من 3</span></div>';
    html+='<div class="tg2-source-grid"><button type="button" class="tg2-source '+(state.source==='saved'?'is-active':'')+'" data-tg-action="source" data-source="saved" aria-pressed="'+(state.source==='saved')+'"><span class="tg2-source-ico">📚</span><span><strong>اختبار محفوظ</strong><small>استخدم أسئلتك السابقة في لعبة جديدة.</small></span></button>';
    html+='<button type="button" class="tg2-source '+(state.source==='quick'?'is-active':'')+'" data-tg-action="source" data-source="quick" aria-pressed="'+(state.source==='quick')+'"><span class="tg2-source-ico">✏️</span><span><strong>إنشاء اختبار سريع</strong><small>أدخل الأسئلة والخيارات في صفحة بسيطة.</small></span></button></div>';
    if(state.source==='saved'){
      html+='<label class="tg2-field" for="tg2Existing">اختر الاختبار <select id="tg2Existing">'+all.map(q=>'<option value="'+esc(q.id)+'" '+(String(q.id)===state.quizId?'selected':'')+'>'+esc(q.title)+' — '+(q.questions||[]).length+' سؤال</option>').join('')+'</select></label>';
      if(!all.length)html+='<div class="tg2-empty">لا توجد اختبارات محفوظة. اختر «إنشاء اختبار سريع» أو استخدم محرر الأسئلة المتقدم.</div>';
      html+='<p class="tg2-note">لا يتم تغيير الاختبار الأصلي عند استخدامه في لعبة أخرى. جميع الاختبارات السابقة تبقى في مكتبتك.</p>';
    }else{
      html+='<div class="tg2-fields"><label class="tg2-field">عنوان الاختبار<input id="tg2Title" maxlength="130" placeholder="مثال: مراجعة الدرس الأول" value="'+esc(state.title)+'"></label><label class="tg2-field">الصف<select id="tg2Grade">'+['الأول','الثاني','الثالث','الرابع','الخامس','السادس','السابع','الثامن','التاسع','العاشر','الحادي عشر','الثاني عشر'].map(g=>'<option '+(state.grade===g?'selected':'')+'>'+g+'</option>').join('')+'</select></label></div>';
      html+='<div class="tg2-questions">'+state.questions.map((q,i)=>{
        let item='<div class="tg2-question" data-question="'+esc(q.id)+'"><div class="tg2-qhead"><span>السؤال '+(i+1)+'</span><button class="tg2-btn tg2-btn-subtle" data-tg-action="remove-q" data-idx="'+i+'" type="button" '+(state.questions.length===1?'disabled':'')+'>حذف</button></div>';
        item+='<label class="tg2-field">نص السؤال<input maxlength="500" data-q-field="text" data-idx="'+i+'" value="'+esc(q.text)+'" placeholder="اكتب السؤال هنا"></label><span class="tg2-note">حدّد الإجابة الصحيحة من الدائرة بجانب الخيار.</span><div class="tg2-options">';
        q.options.forEach((o,j)=>{item+='<label class="tg2-opt"><input type="radio" name="tg2correct'+i+'" data-idx="'+i+'" data-correct="'+j+'" '+(Number(q.correct)===j?'checked':'')+' aria-label="الخيار '+(j+1)+' هو الصحيح"><input type="text" maxlength="220" data-idx="'+i+'" data-option="'+j+'" value="'+esc(o)+'" placeholder="الخيار '+(j+1)+'"></label>'});
        return item+'</div></div>';
      }).join('')+'</div><button type="button" class="tg2-add" style="margin-top:12px;width:100%" data-tg-action="add-q">＋ إضافة سؤال جديد</button>';
    }
    html+='<div class="tg2-actions"><button type="button" class="tg2-btn tg2-btn-subtle" data-tg-action="advanced">✦ محرر الاختبارات المتقدم</button><button type="button" class="tg2-btn tg2-btn-primary" data-tg-action="next">التالي: اختيار اللعبة ←</button></div>';
    return html;
  }
  function renderGallery(){
    let html='<div class="tg2-section-head"><div><h3>اختر شكل اللعبة</h3><p>كل قالب يقدم تجربة مختلفة باستخدام نفس الأسئلة.</p></div><span class="tg2-badge">الخطوة 2 من 3</span></div>';
    html+='<div class="tg2-gallery">'+Object.entries(games).map(([key,g])=>'<button type="button" class="tg2-game-card '+(key===state.template?'is-active':'')+'" data-tg-action="template" data-template="'+key+'" aria-pressed="'+(key===state.template)+'"><span class="tg2-selection">'+(key===state.template?'✓':'○')+'</span>'+art(key)+'<h4>'+g.title+'</h4><p>'+g.detail+'</p></button>').join('')+'</div>';
    html+='<div class="tg2-actions"><button class="tg2-btn tg2-btn-subtle" data-tg-action="back" type="button">→ السابق</button><button class="tg2-btn tg2-btn-primary" data-tg-action="next" type="button">التالي: معاينة اللعبة ←</button></div>';
    return html;
  }
  function renderLaunch(){
    const quiz=currentQuiz(),g=games[state.template];
    let html='<div class="tg2-section-head"><div><h3>نشاطك جاهز للمعاينة</h3><p>راجع الإعدادات ثم شغّل اللعبة داخل الصف.</p></div><span class="tg2-badge">الخطوة 3 من 3</span></div>';
    html+='<div class="tg2-source-grid"><div class="tg2-source" style="cursor:default"><span class="tg2-source-ico">📘</span><span><strong>'+esc(quiz.title||'اختبار جديد')+'</strong><small>'+esc(quiz.grade||'—')+' · '+(quiz.questions||[]).length+' سؤال</small></span></div><div class="tg2-source" style="cursor:default"><span class="tg2-source-ico">🎮</span><span><strong>'+g.title+'</strong><small>'+g.detail+'</small></span></div></div>';
    if(!playable(quiz,state.template))html+='<p class="tg2-note">هذا القالب يحتاج نوعًا مناسبًا من الأسئلة. «تحدي الأسئلة» يتطلب اختيارًا واحدًا أو صح/خطأ؛ و«مطابقة البطاقات» تتطلب زوجين على الأقل من أسئلة المطابقة أو الاختيار.</p>';
    html+='<p class="tg2-note">هذه ألعاب صفية بإشراف المعلم. منافسات الطلاب المباشرة وحفظ نتائجهم تظل عبر «صف مباشر» و«تشغيل فردي» الحاليين.</p>';
    html+='<div class="tg2-actions"><button type="button" class="tg2-btn tg2-btn-subtle" data-tg-action="back">→ السابق</button><div style="display:flex;gap:9px;flex-wrap:wrap"><button type="button" class="tg2-btn tg2-btn-subtle" data-tg-action="live">صف مباشر للطلاب</button><button type="button" class="tg2-btn tg2-btn-primary" data-tg-action="start" '+(!playable(quiz,state.template)?'disabled':'')+'>▶ تشغيل '+g.title+'</button></div></div>';
    if(state.runtime)html+='<div id="tg2Arena" style="margin-top:20px" aria-live="polite"></div>';
    return html;
  }
  function render(){
    if(!$('#tg2Main'))return;
    renderSteps();
    $('#tg2Main').innerHTML=state.step===1?renderSource():state.step===2?renderGallery():renderLaunch();
    const notice=$('#tg2Notice');notice.textContent=state.notice;notice.hidden=!state.notice;
    if(state.step===3 && state.runtime)renderArena();
  }
  async function saveQuick(){
    if(state.source!=='quick')return true;
    if(!validate())return false;
    if(state.busy)return false;
    state.busy=true;
    try{
      const saved=currentQuiz(),all=quizList(),pos=all.findIndex(q=>String(q.id)===String(state.quizId)),fresh=all.slice();
      if(pos>=0)fresh[pos]=saved;else fresh.push(saved);
      DB.quizzes=fresh;state.quizId=String(saved.id);
      if(typeof window.QN9_SAVE_NOW!=='function'||!(await window.QN9_SAVE_NOW())){
        message('تعذر تأكيد الحفظ السحابي. بقيت الأسئلة على الجهاز، ولم نبدأ التشغيل. أعد المحاولة.');
        return false;
      }
      message('تم حفظ الاختبار بنجاح في مكتبة المعلم.');
      return true;
    }catch(e){message('حدث خطأ أثناء حفظ الاختبار. أعد المحاولة قبل التشغيل.');return false}
    finally{state.busy=false}
  }
  function answerText(q){
    if(!q)return '';
    if(q.type==='single'||q.type==='multi'){
      const idx=Array.isArray(q.correct)?q.correct:[q.correct];
      return idx.map(i=>q.options&&q.options[Number(i)]).filter(Boolean).join('، ')||'غير محددة';
    }
    if(q.type==='tf')return q.correct?'صح':'خطأ';
    if(q.type==='short')return (q.answers||[]).filter(Boolean).join('، ')||'راجع المعلم';
    if(q.type==='match')return (q.pairs||[]).map(p=>p.left+' ← '+p.right).join(' | ');
    if(q.type==='order')return (q.items||[]).join(' ← ');
    if(q.type==='estimate')return String(q.estimateAnswer??'راجع المعلم');
    return 'راجع المعلم';
  }
  function start(quiz){
    let qs=(quiz.questions||[]).filter(q=>q.text);
    if(state.template==='quiz')qs=qs.filter(q=>q.type==='single'||q.type==='tf');
    const r={type:state.template,questions:qs,index:0,score:0,answered:false,chosen:-1,used:[],showAnswer:false,angle:0,spinning:false,selected:-1,flipped:[],matched:[],locked:false};
    if(state.template==='pairs'){
      const pairs=findPairs(quiz);
      const cards=[];
      pairs.forEach((p,i)=>{cards.push({id:i,text:p.a});cards.push({id:i,text:p.b})});
      for(let i=cards.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[cards[i],cards[j]]=[cards[j],cards[i]]}
      r.cards=cards;
    }
    state.runtime=r;render();
    $('#tg2Arena')?.scrollIntoView({behavior:'smooth',block:'start'});
  }
  function arenaTop(r){return '<div class="tg2-arena-top"><span>🎮 '+esc(games[r.type].title)+'</span><span>'+(r.type==='quiz'?'⭐ '+r.score+' نقطة':'📘 نشاط صفي')+'</span></div>'}
  function qHtml(q){return '<div class="tg2-prompt">'+esc(q.text||'السؤال')+'</div>'+(q.image&&/^\/assets\/[a-zA-Z0-9_./-]+\.(svg|png|jpe?g|webp)$/.test(q.image)?'<img src="'+esc(q.image)+'" loading="lazy" alt="صورة السؤال" style="display:block;max-height:160px;max-width:90%;margin:auto;border-radius:12px">':'')}
  function renderArena(){
    const r=state.runtime,slot=$('#tg2Arena');if(!r||!slot)return;
    let html='<div class="tg2-arena">'+arenaTop(r);
    if(r.type==='quiz'){
      if(r.index>=r.questions.length)html+='<div class="tg2-prompt">🎉 انتهى التحدي!</div><p style="text-align:center">مجموع نقاطك: '+r.score+' من '+(r.questions.length*100)+' نقطة</p><div class="tg2-arena-foot"><button class="tg2-btn tg2-btn-primary" data-tg-action="restart">إعادة اللعب</button></div>';
      else{
        const q=r.questions[r.index],opts=q.type==='tf'?['صح','خطأ']:(q.options||[]).filter(x=>String(x).trim());
        const correct=q.type==='tf'?(q.correct===true?0:1):Number(Array.isArray(q.correct)?q.correct[0]:q.correct);
        html+='<p style="text-align:center;color:#cde7ff">السؤال '+(r.index+1)+' / '+r.questions.length+'</p>'+qHtml(q)+'<div class="tg2-answergrid">'+opts.map((o,i)=>'<button type="button" class="tg2-answer '+(r.answered?(i===correct?'is-correct':i===r.chosen?'is-wrong':''):'')+'" data-tg-action="answer" data-choice="'+i+'" '+(r.answered?'disabled':'')+'>'+esc(o)+'</button>').join('')+'</div>';
        if(r.answered)html+='<div class="tg2-feedback">'+(r.chosen===correct?'✅ إجابة صحيحة! +100 نقطة':'💡 الإجابة الصحيحة: '+esc(opts[correct]||''))+'</div><div class="tg2-arena-foot"><button class="tg2-btn tg2-btn-primary" data-tg-action="quiz-next">'+(r.index===r.questions.length-1?'عرض النتيجة':'السؤال التالي ←')+'</button></div>';
      }
    }else if(r.type==='wheel'){
      if(r.used.length===r.questions.length && r.selected<0)html+='<div class="tg2-prompt">🎉 تم عرض جميع الأسئلة!</div><div class="tg2-arena-foot"><button class="tg2-btn tg2-btn-primary" data-tg-action="restart">إعادة اللعب</button></div>';
      else if(r.selected>=0){
        const q=r.questions[r.selected];html+=qHtml(q);
        if(r.showAnswer)html+='<div class="tg2-feedback">✅ الإجابة: '+esc(answerText(q))+'</div>';
        html+='<div class="tg2-arena-foot">'+(!r.showAnswer?'<button class="tg2-btn tg2-btn-subtle" data-tg-action="reveal">إظهار الإجابة</button>':'')+'<button class="tg2-btn tg2-btn-primary" data-tg-action="wheel-next">'+(r.used.length===r.questions.length?'إنهاء':'سؤال جديد')+'</button></div>';
      }else html+='<div class="tg2-wheel-wrap"><div id="tg2SpinDisk" class="tg2-wheel" style="transform:rotate('+(r.spinning?r.spinStart:r.angle)+'deg)"></div></div><p style="text-align:center">الأسئلة المتبقية: '+(r.questions.length-r.used.length)+'</p><div class="tg2-arena-foot"><button class="tg2-btn tg2-btn-primary" data-tg-action="spin" '+(r.spinning?'disabled':'')+'>'+(r.spinning?'تدور العجلة...':'🎡 أدر العجلة')+'</button></div>';
    }else if(r.type==='boxes'){
      html+='<p style="text-align:center">اختر صندوقًا لكشف السؤال الموجود بداخله</p><div class="tg2-box-grid">'+r.questions.map((q,i)=>'<button class="tg2-game-box '+(r.used.includes(i)?'is-done':'')+'" type="button" data-tg-action="box" data-idx="'+i+'" '+(r.used.includes(i)?'disabled':'')+'>'+(r.used.includes(i)?'✓':(i+1))+'</button>').join('')+'</div>';
      if(r.selected>=0){
        const q=r.questions[r.selected];html+=qHtml(q);
        if(r.showAnswer)html+='<div class="tg2-feedback">✅ الإجابة: '+esc(answerText(q))+'</div>';
        html+='<div class="tg2-arena-foot">'+(!r.showAnswer?'<button class="tg2-btn tg2-btn-subtle" data-tg-action="reveal">إظهار الإجابة</button>':'')+'<button class="tg2-btn tg2-btn-primary" data-tg-action="box-next">إغلاق السؤال</button></div>';
      }else if(r.used.length===r.questions.length)html+='<div class="tg2-prompt">🎉 تم فتح جميع الصناديق!</div><div class="tg2-arena-foot"><button class="tg2-btn tg2-btn-primary" data-tg-action="restart">إعادة اللعب</button></div>';
    }else if(r.type==='pairs'){
      const allMatched=r.matched.length===r.cards.length/2;
      if(allMatched)html+='<div class="tg2-prompt">🌟 رائع! تمت مطابقة جميع البطاقات.</div><div class="tg2-arena-foot"><button class="tg2-btn tg2-btn-primary" data-tg-action="restart">إعادة اللعب</button></div>';
      else html+='<p style="text-align:center">اكشف بطاقتين لتكوين زوج صحيح. الأزواج المكتملة: '+r.matched.length+' / '+(r.cards.length/2)+'</p><div class="tg2-pair-grid">'+r.cards.map((card,i)=>{
        const matched=r.matched.includes(card.id),open=matched||r.flipped.includes(i);
        return '<button type="button" class="tg2-pair-tile '+(matched?'is-matched':open?'is-open':'')+'" data-tg-action="flip" data-idx="'+i+'" '+(matched||r.locked?'disabled':'')+' aria-label="بطاقة رقم '+(i+1)+'">'+(open?esc(card.text):'❖ '+(i+1))+'</button>';
      }).join('')+'</div>';
    }
    html+='</div><div class="tg2-arena-foot"><button class="tg2-btn tg2-btn-subtle" data-tg-action="close-game">إغلاق اللعبة والعودة للإعدادات</button></div>';
    slot.innerHTML=html;
  }
  function sourceSelect(newSource){if(newSource!==state.source)state.quizId='';state.source=newSource;state.notice='';state.runtime=null;render()}
  async function handleAction(action,button){
    if(action==='source'){sourceSelect(button.dataset.source);return}
    if(action==='template'){state.template=button.dataset.template;render();return}
    if(action==='add-q'){if(state.questions.length>=50){message('الحد الأقصى في المحرر السريع 50 سؤالًا.');return}state.questions.push(makeQ());render();return}
    if(action==='remove-q'){state.questions.splice(Number(button.dataset.idx),1);render();return}
    if(action==='advanced'){if(typeof window.openNewQuiz==='function')window.openNewQuiz();return}
    if(action==='step'){
      const dest=Number(button.dataset.step);
      if(dest>1&&!validate())return;
      state.step=dest;state.runtime=null;render();return;
    }
    if(action==='back'){state.step=Math.max(1,state.step-1);state.runtime=null;render();return}
    if(action==='next'){if(state.step===1&&!validate())return;state.step=Math.min(3,state.step+1);state.runtime=null;render();return}
    if(action==='live'){
      if(state.source==='quick'&&!(await saveQuick()))return;
      const q=currentQuiz();if(q && window.go)window.go('live',{quizId:q.id});return;
    }
    if(action==='start'){
      if(!validate())return;
      if(state.source==='quick'&&!(await saveQuick()))return;
      const q=currentQuiz();if(!playable(q,state.template)){message('يرجى اختيار لعبة مناسبة لنوع أسئلتك.');return}
      start(q);return;
    }
    const r=state.runtime;if(!r)return;
    if(action==='close-game'){state.runtime=null;render();return}
    if(action==='restart'){start(state.source==='quick'?(existingQuiz()||currentQuiz()):currentQuiz());return}
    if(action==='answer'&&!r.answered){
      const q=r.questions[r.index],correct=q.type==='tf'?(q.correct===true?0:1):Number(Array.isArray(q.correct)?q.correct[0]:q.correct);
      r.chosen=Number(button.dataset.choice);r.answered=true;if(r.chosen===correct)r.score+=100;renderArena();return;
    }
    if(action==='quiz-next'){r.index++;r.answered=false;r.chosen=-1;renderArena();return}
    if(action==='box'){const i=Number(button.dataset.idx);if(r.used.includes(i))return;r.used.push(i);r.selected=i;r.showAnswer=false;renderArena();return}
    if(action==='box-next'){r.selected=-1;r.showAnswer=false;renderArena();return}
    if(action==='reveal'){r.showAnswer=true;renderArena();return}
    if(action==='wheel-next'){r.selected=-1;r.showAnswer=false;renderArena();return}
    if(action==='spin'&&!r.spinning){
      const remaining=r.questions.map((_,i)=>i).filter(i=>!r.used.includes(i));
      if(!remaining.length)return;
      r.spinning=true;const selected=remaining[Math.floor(Math.random()*remaining.length)];
      r.spinStart=r.angle;r.angle+=1440+Math.floor(Math.random()*8)*45;renderArena();
      requestAnimationFrame(()=>{const wheel=$('#tg2SpinDisk');if(wheel)wheel.style.transform='rotate('+r.angle+'deg)'});
      setTimeout(()=>{if(state.runtime!==r)return;r.spinning=false;r.selected=selected;r.used.push(selected);renderArena()},1500);
      return;
    }
    if(action==='flip'&&!r.locked){
      const i=Number(button.dataset.idx);if(r.flipped.includes(i)||r.matched.includes(r.cards[i].id))return;
      r.flipped.push(i);
      if(r.flipped.length===2){
        if(r.cards[r.flipped[0]].id===r.cards[r.flipped[1]].id){r.matched.push(r.cards[i].id);r.flipped=[]}
        else{r.locked=true;const current=r;setTimeout(()=>{if(state.runtime!==current)return;r.flipped=[];r.locked=false;renderArena()},850)}
      }
      renderArena();return;
    }
  }
  host.addEventListener('click',e=>{
    const b=e.target.closest('[data-tg-action]');if(!b||b.disabled)return;
    e.preventDefault();Promise.resolve(handleAction(b.dataset.tgAction,b)).catch(err=>{console.error(err);message('حدث خطأ غير متوقع. أعد المحاولة.')});
  });
  host.addEventListener('input',e=>{
    const el=e.target,i=Number(el.dataset.idx);
    if(el.id==='tg2Title')state.title=el.value;
    if(el.dataset.qField==='text'&&state.questions[i])state.questions[i].text=el.value;
    if(el.dataset.option!==undefined&&state.questions[i])state.questions[i].options[Number(el.dataset.option)]=el.value;
  });
  host.addEventListener('change',e=>{
    const el=e.target,i=Number(el.dataset.idx);
    if(el.id==='tg2Existing')state.quizId=el.value;
    if(el.id==='tg2Grade')state.grade=el.value;
    if(el.dataset.correct!==undefined&&state.questions[i])state.questions[i].correct=Number(el.dataset.correct);
  });
  window.TG_LAB_V2={render,open:()=>window.go&&window.go('gamelab')};
  render();
})();
