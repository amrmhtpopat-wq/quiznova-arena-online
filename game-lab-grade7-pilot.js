/* Grade 7 Jordanian Digital Skills pilot: reviewed questions, no student data or book uploads. */
(()=>{
 'use strict';
 const $=id=>document.getElementById(id);
 const button=$('loadGrade7Pilot');
 if(!button)return;
 button.addEventListener('click',async()=>{
  button.disabled=true;const prev=button.textContent;button.textContent='جارٍ تحميل مثال الصف السابع...';
  try{
    const reply=await fetch('/api/game-lab/pilot/grade7',{cache:'no-store'});
    if(!reply.ok)throw Error('pilot_unavailable');
    const payload=await reply.json();
    if(!payload.ok||!payload.pilot||!Array.isArray(payload.pilot.rows))throw Error('pilot_invalid');
    const model=payload.pilot;
    // Always begin as an unsaved draft. Never overwrite the teacher's current saved activity.
    if($('cloudNew'))$('cloudNew').click();
    $('activityTitle').value=model.title;
    $('subject').value=model.subject;
    $('grade').value=model.grade;
    $('roundTime').value=String(model.time);
    $('activityData').value=model.rows.map(row=>
      [row.q,row.a,row.g,row.sourcePage].map(v=>String(v??'').replace(/\|/g,' ')).join(' | ')
    ).join('\n');
    if($('cloudMode'))$('cloudMode').value=model.mode||'quiz';
    window.BOOYAH_LAB_BOOK_ID='';
    window.BOOYAH_LAB_IMAGE_ID='';
    window.BOOYAH_LAB_SOURCE_GROUP='';
    $('applyContent').click();
    const msg=$('grade7PilotStatus');
    msg.textContent='✓ تم تحميل '+model.rows.length+' سؤالًا تدريبيًا من موضوعات الوحدة الأولى (صفحات '+model.source.pages+'). راجعها قبل الحفظ أو النشر. هذا مثال تعليمي، وليس نسخة الكتاب الكاملة.';
    msg.className='good';
    document.getElementById('builder').scrollIntoView({behavior:'smooth',block:'start'});
  }catch(e){
    const msg=$('grade7PilotStatus');
    msg.textContent='تعذر تحميل مثال المنهاج، جرّب فتح الصفحة مجددًا. '+e.message;
    msg.className='notice';
  }finally{button.disabled=false;button.textContent=prev}
 });
})();