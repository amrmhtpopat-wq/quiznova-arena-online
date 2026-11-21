/* Unified TAG Jordan S1 lesson tests: independent of legacy generic bank.
 * No quiz or question is saved to teacher cloud storage until teacher saves.
 */
(function(w){
'use strict';
const syllabus=w.TAG_JORDAN_S1_COURSES_V1;
const math=w.TAG_JORDAN_S1_MATH_V1;
const digital=w.TAG_JORDAN_S1_DIGITAL_V1;
if(!syllabus||!math||!digital)return;
const cache=new Map();
const normalize=s=>String(s||'').replace(/\s+/g,' ').trim();
function coursesForTeacher(subject){
 const key=syllabus.keyOf(subject);
 return key?syllabus.courses.filter(c=>c.subject===key):[];
}
function rawQuestions(lesson){
 return lesson.subject==='الرياضيات'?math.questionsFor(lesson):digital.questionsFor(lesson);
}
function validate(question){
 if(!question||!normalize(question.text)||question.type!=='single')return false;
 if(!Array.isArray(question.options)||question.options.length!==4)return false;
 if(question.options.some(x=>!normalize(x)))return false;
 if(new Set(question.options.map(normalize)).size!==4)return false;
 if(!Array.isArray(question.correct)||question.correct.length!==1)return false;
 const answer=question.correct[0];
 if(!Number.isInteger(answer)||answer<0||answer>3)return false;
 return question.reviewStatus==='teacher_review_required';
}
function questionsFor(lessonId,subject){
 const lesson=syllabus.lessonById(lessonId);
 if(!lesson||!syllabus.keyOf(subject)||syllabus.keyOf(subject)!==syllabus.keyOf(lesson.subject))return [];
 if(!cache.has(lessonId)){
  const raw=rawQuestions(lesson),seen=new Set();
  const valid=raw.filter(q=>{
   if(!validate(q)||seen.has(normalize(q.text)))return false;
   seen.add(normalize(q.text));return true;
  });
  cache.set(lessonId,Object.freeze(valid));
 }
 return cache.get(lessonId).map(q=>({...q,options:[...q.options],correct:[...q.correct]}));
}
function lessonSummary(lessonId,teacherSubject){
 const lesson=syllabus.lessonById(lessonId);
 if(!lesson||syllabus.keyOf(teacherSubject)!==syllabus.keyOf(lesson.subject))return null;
 const result=questionsFor(lessonId,teacherSubject);
 return {lesson,available:result.length,ready:result.length===30,
   needsReview:true,sourceStatus:lesson.sourceStatus,
   message:result.length===30?'30 سؤالًا تدريبيًا أصلـيًا جاهزًا للمراجعة':'هذا الدرس بحاجة إلى استكمال '+(30-result.length)+' سؤال قبل إتاحة اختبار 30 سؤالًا'};
}
w.TAG_JORDAN_S1_TESTS_V1=Object.freeze({coursesForTeacher,questionsFor,lessonSummary});
})(window);
