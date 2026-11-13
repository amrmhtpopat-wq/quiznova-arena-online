/* TEACH AND GAME V12.8 — show only server-approved, teacher-published tests on a student's card. */
(()=>{
'use strict';
const section=document.getElementById('boCardQuizzes');
if(!section)return;
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let requestSeq=0, items=[], visibleCard='';
function clear(){
 requestSeq++;
 visibleCard='';
 items=[];
 section.hidden=true;
 section.innerHTML='';
}
window.BOOYAH_HIDE_CARD_TESTS=clear;
window.BOOYAH_SHOW_CARD_TESTS=async function(card){
 const code=String(card||'').trim().toUpperCase();
 const seq=++requestSeq;
 visibleCard=code;
 items=[];
 section.hidden=false;
 section.innerHTML='<div class="bo-card-test-header"><h3>📚 الاختبارات المتاحة لصفك</h3><span>جاري التحميل...</span></div>';
 try{
  const response=await fetch('/api/student/solo/catalog',{
   method:'POST',cache:'no-store',credentials:'same-origin',
   headers:{'Content-Type':'application/json'},
   body:JSON.stringify({card:code})
  });
  const data=await response.json();
  if(!response.ok||!data.ok)throw new Error(data.error||'catalog_unavailable');
  if(seq!==requestSeq||code!==visibleCard||document.getElementById('cardProfile').hidden)return;
  items=Array.isArray(data.quizzes)?data.quizzes:[];
  section.innerHTML='<div class="bo-card-test-header"><h3>📚 اختبارات صفك المفعّلة</h3><span>'+esc(data.student?.className||'')+'</span></div>'
   +(items.length
     ? '<div class="bo-card-test-grid">'+items.map((q,index)=>
       '<article class="bo-card-test-item"><b>'+esc(q.title||'اختبار')+'</b>'
       +'<small>'+esc(q.subject||'')+' · '+esc(q.grade||'')+(q.section?' / '+esc(q.section):' · كل الشعب')+'</small>'
       +'<small>'+Number(q.questions||0)+' سؤال · المتبقي '+Number(q.remaining||0)+' من '+Number(q.maxAttempts||1)+' محاولة</small>'
       +'<button type="button" data-card-quiz="'+index+'"'+(Number(q.remaining||0)<1?' disabled':'')+'>'
       +(Number(q.remaining||0)<1?'انتهت المحاولات 🔒':'ابدأ الاختبار ←')+'</button></article>').join('')+'</div>'
     : '<p class="bo-card-test-empty">لا توجد اختبارات مفعّلة لصفك حاليًا. ستظهر هنا عندما يتيح معلمك اختبارًا مطابقًا لصفك وشعبتك.</p>');
 }catch(_error){
  if(seq!==requestSeq)return;
  section.innerHTML='<p class="bo-card-test-empty">تعذر تحميل اختبارات الصف حاليًا؛ حاول عرض البطاقة مرة أخرى.</p>';
 }
};
section.addEventListener('click',event=>{
 const button=event.target.closest('[data-card-quiz]');
 if(!button||button.disabled)return;
 const quiz=items[Number(button.dataset.cardQuiz)];
 if(quiz&&visibleCard&&typeof window.BOOYAH_START_CARD_QUIZ==='function'){
  window.BOOYAH_START_CARD_QUIZ(visibleCard,quiz.id);
 }
});
})();