/* Validate every requested Jordan Grade→Unit→Lesson map and 30-question pack. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const sandbox={window:{}};vm.createContext(sandbox);
const sources=[
 'tag-jordan-s1-courses-v1.js','tag-jordan-s1-math-v1.js',
 'tag-jordan-s1-digital-g7.js','tag-jordan-s1-digital-g8.js',
 'tag-jordan-s1-digital-g9.js','tag-jordan-s1-digital-g10.js',
 'tag-jordan-s1-digital-g11.js','tag-jordan-s1-digital-v1.js',
 'tag-jordan-s1-tests-v1.js'
];
for(const file of sources)vm.runInContext(fs.readFileSync(file,'utf8'),sandbox,{filename:file,timeout:10000});
const api=sandbox.window.TAG_JORDAN_S1_TESTS_V1,syllabus=sandbox.window.TAG_JORDAN_S1_COURSES_V1;
assert.ok(api,'Lesson test API must load');
assert.equal(syllabus.courses.length,10);
assert.deepEqual(Array.from(syllabus.courses.filter(c=>c.subject==='math').map(c=>c.grade)),[6,7,8,9,10]);
assert.deepEqual(Array.from(syllabus.courses.filter(c=>c.subject==='digital').map(c=>c.grade)),[7,8,9,10,11]);
assert.equal(api.coursesForTeacher('الرياضيات').length,5);
assert.equal(api.coursesForTeacher('مهارات رقمية').length,5);
assert.equal(api.coursesForTeacher('اللغة العربية').length,0);
let lessons=0,total=0,subjectCount={math:0,digital:0};
for(const course of syllabus.courses){
 assert.equal(course.semester,'الأول');
 assert.ok(course.units.length>=2);
 const owner=course.subjectName,other=course.subject==='math'?'المهارات الرقمية':'الرياضيات';
 for(const unit of course.units){
  assert.ok(unit.title.length>=5);
  assert.ok(unit.lessons.length>=3);
  for(const lesson of unit.lessons){
   lessons++;
   const rows=api.questionsFor(lesson.id,owner);
   assert.equal(rows.length,30,'Expected exactly 30 distinct original questions in '+lesson.id+' ('+lesson.title+'), got '+rows.length);
   assert.equal(api.questionsFor(lesson.id,other).length,0,'Cross-subject leak '+lesson.id);
   const dedupe=new Set(),ids=new Set();
   for(const q of rows){
    assert.equal(q.subject,lesson.subject);
    assert.equal(q.grade,lesson.grade);
    assert.equal(q.semester,'1');
    assert.equal(q.unit,lesson.unit);
    assert.equal(q.lesson,lesson.title);
    assert.equal(q.type,'single');
    assert.equal(q.reviewStatus,'teacher_review_required');
    assert.ok(q.sourceUrl.startsWith('https://'));
    assert.equal(q.options.length,4);
    assert.equal(new Set(q.options).size,4,'Duplicate options: '+lesson.id+' / '+q.text);
    assert.equal(q.correct.length,1);
    assert.ok(Number.isInteger(q.correct[0])&&q.correct[0]>=0&&q.correct[0]<4);
    assert.ok(q.options[q.correct[0]].length>0);
    assert.ok(!dedupe.has(q.text),'Duplicate prompt '+lesson.id+' '+q.text);dedupe.add(q.text);
    assert.ok(!ids.has(q.id));ids.add(q.id);
   }
   const summary=api.lessonSummary(lesson.id,owner);
   assert.equal(summary.available,30);
   assert.equal(summary.ready,true);
   subjectCount[course.subject]+=30;total+=30;
  }
 }
}
const math=syllabus.courses.filter(c=>c.subject==='math').flatMap(c=>c.units.flatMap(u=>u.lessons));
const functionLessons=math.filter(l=>/Functions|Function|Trigonometric/i.test(l.title));
assert.ok(functionLessons.length>=4);
assert.ok(functionLessons.some(l=>api.questionsFor(l.id,'الرياضيات').some(q=>q.text.includes('f(x)'))),'Expect English f(x) mathematical function notation');
assert.ok(math.some(l=>api.questionsFor(l.id,'الرياضيات').some(q=>q.text.includes('sin('))),'Expect English sin() notation');
console.log('PASS Jordan S1 lesson quizzes:',{courses:syllabus.courses.length,lessons,questions:total,subjectCount});
