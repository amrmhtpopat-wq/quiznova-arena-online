/* TAG Jordan Semester One class→unit→lesson→30-question tests.
 * Client-only, read-only public study packs. Teacher's subject is selected
 * from their authenticated server profile; no cross-subject shortcuts.
 */
(function(){
'use strict';
const syllabus=window.TAG_JORDAN_S1_COURSES_V1;
const library=window.TAG_JORDAN_S1_TESTS_V1;
const root=document.getElementById('tagS1Panel');
if(!syllabus||!library||!root)return;
const id=s=>document.getElementById(s);
const teacherSubject=window.QN9_TEACHER?.subject||'';
const courses=library.coursesForTeacher(teacherSubject);
let grade='',unitId='',lessonId='';
function opt(value,label){
 const element=document.createElement('option');
 element.value=String(value);element.textContent=label;return element;
}
function textTag(tag,name,value){
 const el=document.createElement(tag);
 if(name)el.className=name;
 el.textContent=String(value||'');
 return el;
}
function clearView(){
 lessonId='';
 id('tagS1Lessons').replaceChildren();
 id('tagS1Lessons').hidden=true;
 id('tagS1ExamPreview').hidden=true;
 id('tagS1ExamSamples').replaceChildren();
 id('tagS1Lesson').replaceChildren(opt('','اختر الدرس'));
 id('tagS1Lesson').disabled=true;
}
function currentCourse(){
 return courses.find(c=>c.grade===Number(grade))||null;
}
function currentUnit(){
 const course=currentCourse();
 return course?.units.find(u=>u.id===unitId)||null;
}
function renderUnits(){
 clearView();
 const course=currentCourse();
 const unitInput=id('tagS1Unit');
 unitInput.replaceChildren(opt('','اختر الوحدة الدراسية'));
 if(!course){
  unitInput.disabled=true;id('tagS1Hint').textContent='اختر الصف الدراسي لعرض وحداته ودروسه في الفصل الأول.';
  return;
 }
 course.units.forEach(u=>unitInput.append(opt(u.id,'الوحدة '+u.number+' — '+u.title)));
 unitInput.disabled=false;
 id('tagS1Hint').textContent='الصف '+course.gradeName+' • '+course.units.length+' وحدات • اختر الوحدة لعرض الاختبارات.';
}
function renderLessons(){
 clearView();
 const unit=currentUnit(),course=currentCourse();
 if(!unit)return;
 const list=id('tagS1Lessons'),select=id('tagS1Lesson');
 for(const lesson of unit.lessons){
  const info=library.lessonSummary(lesson.id,teacherSubject);
  select.append(opt(lesson.id,lesson.number+' — '+lesson.title));
  const button=document.createElement('button');
  button.type='button';button.className='tag-s1-lesson-card';button.dataset.lesson=lesson.id;
  button.setAttribute('aria-label','اختر اختبار '+lesson.title);
  button.append(textTag('strong','',lesson.number+'. '+lesson.title));
  const badges=textTag('div','tag-s1-lesson-meta','');
  badges.append(textTag('span',info?.ready?'':'is-pending',info?.ready?'30 سؤالًا للمراجعة':'يحتاج استكمال'));
  if(lesson.sourceStatus==='needs_edition_confirmation')
   badges.append(textTag('span','is-pending','تحقق من الطبعة'));
  button.append(badges);
  button.addEventListener('click',()=>{select.value=lesson.id;renderPreview(lesson.id)});
  list.append(button);
 }
 select.disabled=false;list.hidden=false;
 id('tagS1Hint').textContent='الوحدة: '+unit.title+' • '+unit.lessons.length+
  ' دروس. اضغط درسًا لمعاينة بعض الأسئلة، أو اختره من القائمة.';
}
function renderPreview(selectedId){
 lessonId=selectedId;
 const info=library.lessonSummary(lessonId,teacherSubject);
 const exam=id('tagS1ExamPreview'),open=id('tagS1OpenExam');
 if(!info){exam.hidden=true;return}
 const all=library.questionsFor(lessonId,teacherSubject);
 id('tagS1ExamTitle').textContent=info.lesson.title;
 id('tagS1ExamCount').textContent=all.length;
 id('tagS1ExamMeta').textContent='الصف '+info.lesson.grade+' • '+info.lesson.unit+
  ' • '+all.length+' سؤالًا • الفصل الأول';
 id('tagS1ExamReview').textContent=info.ready
  ?'تدريبات أصلية تحتاج مراجعة الإجابات وملاءمتها قبل حفظ الاختبار أو نشره.'
  :'اختبار الدرس غير مكتمل. لن يعرض TAG عددًا مضللًا من الأسئلة.';
 const sample=id('tagS1ExamSamples');
 sample.replaceChildren();
 all.slice(0,3).forEach((q,i)=>{
  const c=textTag('article','tag-s1-sample','');
  c.append(textTag('strong','',(i+1)+'. '+q.text));
  c.append(textTag('small','','الإجابة المقترحة: '+q.options[q.correct[0]]));
  sample.append(c);
 });
 if(info.lesson.sourceStatus==='needs_edition_confirmation')
  sample.append(textTag('p','tag-s1-source-caution','تنبيه: تطابق أسماء هذه الوحدة والدرس مع طبعة كتاب المدرسة يحتاج تدقيقًا قبل استخدامها.'));
 open.disabled=!info.ready;
 open.textContent=info.ready?'✎ فتح 30 سؤالًا في محرر الاختبار':'اختبار الدرس يحتاج استكمالًا';
 exam.hidden=false;
 id('tagS1Lessons').querySelectorAll('button[data-lesson]').forEach(el=>{
  const selected=el.dataset.lesson===selectedId;
  el.classList.toggle('is-selected',selected);
  el.setAttribute('aria-pressed',String(selected));
 });
}
id('tagS1Grade').addEventListener('change',e=>{
 grade=e.target.value;unitId='';
 id('tagS1Unit').value='';
 renderUnits();
});
id('tagS1Unit').addEventListener('change',e=>{unitId=e.target.value;renderLessons()});
id('tagS1Lesson').addEventListener('change',e=>renderPreview(e.target.value));
id('tagS1OpenExam').addEventListener('click',()=>{
 if(!lessonId)return;
 if(typeof window.TAG_OPEN_S1_LESSON_EXAM!=='function'){
  id('tagS1Hint').textContent='محرر الاختبارات لم يكتمل تحميله. أعد فتح صفحة المكتبة.';
  return;
 }
 const result=window.TAG_OPEN_S1_LESSON_EXAM(lessonId);
 if(!result?.ok)id('tagS1Hint').textContent='تعذر فتح الاختبار: '+(result?.error||'راجع عدد الأسئلة');
});
function init(){
 const gradeSelect=id('tagS1Grade');
 gradeSelect.replaceChildren(opt('','اختر الصف'));
 for(const course of courses)gradeSelect.append(opt(course.grade,course.gradeName));
 id('tagS1TeacherSubject').textContent='مادة المعلم: '+(syllabus.keyOf(teacherSubject)?courses[0]?.subjectName:'غير محددة');
 id('tagS1CourseCount').textContent=courses.length+' صفوف متاحة';
 const lessonCount=courses.reduce((sum,course)=>sum+course.units.reduce((n,u)=>n+u.lessons.length,0),0);
 id('tagS1LessonTotal').textContent=lessonCount+' درسًا في الفصل الأول';
 if(!courses.length){
  id('tagS1Hint').textContent='هذه المكتبة مخصصة حاليًا لمعلمي الرياضيات (السادس–العاشر) والمهارات الرقمية (السابع–الأول الثانوي). تظهر المادة بحسب تخصص حساب المعلم.';
  gradeSelect.disabled=true;
 }else{
  id('tagS1Hint').textContent='اختر الصف أولًا؛ ستظهر الوحدات والدروس الخاصة بمبحث '+courses[0].subjectName+' فقط.';
 }
}
init();
})();
