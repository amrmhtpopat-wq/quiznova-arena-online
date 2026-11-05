/* BOOYAH! student solo access and secure teacher-published practice. */
(()=>{
'use strict';
const el=id=>document.getElementById(id);
const clean=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const current={card:'',token:'',state:null,pending:false,timer:null,order:[]};
const params=new URLSearchParams(location.search);
const buttons=[...document.querySelectorAll('[data-student-mode]')];
function error(msg){el('soloError').textContent=msg||''}
async function api(op,data){
 const r=await fetch('/api/student/solo/'+op,{method:'POST',cache:'no-store',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
 const d=await r.json().catch(()=>({ok:false,error:'network'}));
 if(!r.ok||!d.ok)throw Object.assign(new Error(d.error||'network'),{payload:d});
 return d;
}
function mode(which,update=true){
 which=['live','card','solo'].includes(which)?which:'live';
 buttons.forEach(b=>{const active=b.dataset.studentMode===which;b.classList.toggle('is-active',active);b.setAttribute('aria-pressed',String(active))});
 el('joinView').classList.toggle('hidden',which==='solo');
 el('soloView').classList.toggle('hidden',which!=='solo');
 if(update){const url=new URL(location.href);url.searchParams.set('mode',which);history.replaceState(null,'',url.pathname+url.search+url.hash)}
 if(which==='card'){
  if(!el('cardCode').value&&current.card)el('cardCode').value=current.card;
  el('joinHint').textContent='أدخل رمز البطاقة لعرض بياناتك، ثم رمز الجلسة للانضمام إلى التحدي المباشر.';
  setTimeout(()=>el('cardCode').focus(),30);
 }
 if(which==='live')setTimeout(()=>el('roomCode').focus(),30);
 if(which==='solo'){
  const c=el('soloCardCode');
  if(!c.value)c.value=params.get('card')||el('cardCode').value||'';
  const old=sessionStorage.getItem('booyah_solo_token');
  if(old&&!current.token&&!current.state)void resume(old);
 }
}
buttons.forEach(b=>b.addEventListener('click',()=>mode(b.dataset.studentMode)));
async function resume(token){
 try{const d=await api('state',{token});current.token=token;current.state=d.state;el('soloQuizList').innerHTML='';el('soloCardForm').classList.add('hidden');render(d.state)}
 catch{sessionStorage.removeItem('booyah_solo_token');current.token='';current.state=null}
}
async function catalog(event){
 event.preventDefault();
 const card=el('soloCardCode').value.trim().toUpperCase();
 if(!card)return error('اكتب رمز بطاقة الطالب أولًا.');
 const button=el('soloLoadBtn');button.disabled=true;error('');
 try{
  const d=await api('catalog',{card});
  current.card=card;current.token='';current.state=null;
  clearInterval(current.timer);sessionStorage.removeItem('booyah_solo_token');
  el('soloPlayArea').innerHTML='';
  const info=el('soloStudentInfo');info.hidden=false;
  info.innerHTML='<b>مرحبًا '+clean(d.student.name)+'</b> • '+clean(d.student.className)+' • ⭐ '+Number(d.student.xp||0)+' XP';
  const quizzes=d.quizzes||[];
  if(!quizzes.length){el('soloQuizList').innerHTML='<p class="bo-solo-empty">لا توجد اختبارات فردية متاحة حاليًا. يستطيع معلمك إتاحتها من مكتبة الاختبارات.</p>';return}
  el('soloQuizList').innerHTML=quizzes.map((q,i)=>'<article class="bo-solo-quiz"><h3>'+clean(q.title)+'</h3><p>'+clean(q.subject)+' • '+clean(q.grade)+' • '+Number(q.questions||0)+' سؤال</p><button type="button" data-solo-id="'+i+'">ابدأ التدريب 🚀</button></article>').join('');
  el('soloQuizList').querySelectorAll('[data-solo-id]').forEach(b=>b.addEventListener('click',()=>start(quizzes[Number(b.dataset.soloId)].id,b)));
 }catch(e){error(e.message==='invalid_card'?'رمز البطاقة غير صحيح.':e.message==='rate_limited'?'عدد محاولات كبير، حاول لاحقًا.':'تعذر تحميل الاختبارات؛ تحقق من الاتصال.')}
 finally{button.disabled=false}
}
async function start(id,b){
 if(!id||!current.card)return;b.disabled=true;error('');
 try{
  const d=await api('start',{card:current.card,quizId:id});
  current.token=d.token;current.state=d.state;sessionStorage.setItem('booyah_solo_token',d.token);
  el('soloQuizList').innerHTML='';el('soloCardForm').classList.add('hidden');render(d.state);
 }catch(e){error(e.message==='not_published'?'لم يعد الاختبار متاحًا.':'تعذر بدء التدريب.')}finally{b.disabled=false}
}
function orderHtml(){return current.order.map((x,i)=>'<div class="bo-solo-order-row"><span>'+clean(x)+'</span><span><button type="button" data-move="'+i+',-1">↑</button> <button type="button" data-move="'+i+',1">↓</button></span></div>').join('')}
function bindOrder(){el('soloOrderList')?.querySelectorAll('[data-move]').forEach(b=>b.addEventListener('click',()=>{
 const [i,d]=b.dataset.move.split(',').map(Number),j=i+d;
 if(j<0||j>=current.order.length)return;
 [current.order[i],current.order[j]]=[current.order[j],current.order[i]];
 el('soloOrderList').innerHTML=orderHtml();bindOrder();
}))}
function questionInput(q){
 if(['single','multi','tf','poll'].includes(q.type)){
  const opts=q.type==='tf'?['صح','خطأ']:(q.options||[]);
  return '<div class="bo-solo-options">'+opts.map((v,i)=>'<label class="bo-solo-choice"><input type="'+(q.type==='multi'?'checkbox':'radio')+'" name="boAnswer" value="'+i+'"><span>'+clean(v)+'</span></label>').join('')+'</div>';
 }
 if(q.type==='short'||q.type==='estimate')return '<input id="soloTextAnswer" class="bo-solo-answer-input" '+(q.type==='estimate'?'type="number" step="any"':'')+' placeholder="اكتب الإجابة" autocomplete="off">';
 if(q.type==='order'){current.order=(q.items||[]).slice();return '<div id="soloOrderList">'+orderHtml()+'</div>'}
 if(q.type==='match')return (q.lefts||[]).map((x,i)=>'<label class="bo-solo-match-row"><span>'+clean(x)+'</span><select data-match="'+i+'"><option value="">اختر المطابقة</option>'+(q.rights||[]).map(y=>'<option value="'+clean(y)+'">'+clean(y)+'</option>').join('')+'</select></label>').join('');
 return '<p>نوع السؤال غير مدعوم</p>';
}
function answer(q){
 if(q.type==='order')return current.order.slice();
 if(q.type==='match'){const v={};document.querySelectorAll('[data-match]').forEach(e=>{v[e.dataset.match]=e.value});return v}
 if(q.type==='short'||q.type==='estimate')return el('soloTextAnswer')?.value.trim()||'';
 const selected=[...document.querySelectorAll('input[name="boAnswer"]:checked')].map(x=>Number(x.value));
 if(q.type==='multi')return selected;
 if(q.type==='tf')return selected.length?selected[0]===0:null;
 return selected.length?selected[0]:null;
}
function render(s){
 current.state=s;clearInterval(current.timer);
 if(s.finished)return finish(s);
 const q=s.question||{},box=el('soloPlayArea');
 box.innerHTML='<div class="bo-solo-progress-header"><span>'+clean(s.quizTitle)+'</span><span>السؤال '+(s.index+1)+' من '+s.total+'</span><span>🏆 '+Number(s.score)+' نقطة</span><span id="soloTimer"></span></div><form class="bo-solo-question" id="boSoloForm">'
  +(q.image?'<img class="bo-solo-question-image" src="'+clean(q.image)+'" alt="صورة السؤال">':'')
  +'<h2>'+clean(q.text)+'</h2>'+questionInput(q)
  +'<button type="submit" class="bo-solo-submit" id="boSoloSubmit">تأكيد الإجابة ✓</button></form>';
 bindOrder();
 el('boSoloForm').addEventListener('submit',e=>{e.preventDefault();void submit(answer(q))});
 const duration=Math.max(5,Math.min(300,Number(q.time)||20))*1000;
 const tick=()=>{
  const left=Math.max(0,Math.ceil((duration-(Date.now()-Number(s.startedAt||Date.now())))/1000));
  if(el('soloTimer'))el('soloTimer').textContent='⏱ '+left+' ث';
  if(left===0){clearInterval(current.timer);if(!current.pending)void submit(null)}
 };
 tick();current.timer=setInterval(tick,400);
}
async function submit(value){
 if(!current.token||!current.state||current.state.finished||current.pending)return;
 current.pending=true;clearInterval(current.timer);
 const button=el('boSoloSubmit');if(button)button.disabled=true;
 try{
  const d=await api('answer',{token:current.token,index:current.state.index,answer:value});
  current.state=d.state;
  el('soloPlayArea').innerHTML='<div class="bo-solo-feedback"><h2>'+(d.correct===true?'✅ إجابة صحيحة':d.correct===null?'✅ تم تسجيل مشاركتك':'💡 لا بأس، أكمل التحدي!')+'</h2><p>+'+Number(d.earned||0)+' نقطة</p></div>';
  setTimeout(()=>render(d.state),1000);
 }catch(e){
  if(e.message==='question_changed'&&e.payload?.state)render(e.payload.state);
  else{error('تعذر إرسال الإجابة. تحقق من الإنترنت وأعد المحاولة.');if(button)button.disabled=false}
 }finally{current.pending=false}
}
function finish(s){
 clearInterval(current.timer);sessionStorage.removeItem('booyah_solo_token');current.token='';
 el('soloCardForm').classList.remove('hidden');
 el('soloPlayArea').innerHTML='<div class="bo-solo-finish"><div style="font-size:48px">🏆</div><h2>أحسنت '+clean(s.name)+'!</h2><p>أجبت عن '+Number(s.correct)+' من '+Number(s.total)+' أسئلة</p><h2>'+Number(s.score)+' نقطة</h2><p>⭐ +'+Number(s.xpGain||0)+' XP • الإجمالي '+Number(s.xp||0)+' XP</p><p>'+clean(s.progress?.title||'مبتدئ')+'</p><a href="/student.html?mode=solo">العب مرة أخرى</a></div>';
}
el('soloCardForm').addEventListener('submit',catalog);
mode(['live','card','solo'].includes(params.get('mode'))?params.get('mode'):'live',false);
})();
