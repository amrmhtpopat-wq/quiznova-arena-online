/* Node 22: strict acceptance tests for the original TeachGame semester-one library. */
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const ctx=vm.createContext({window:{}});
for(const file of ['tag-semester1-catalog-v2.js','tag-semester1-packs-v2.js']){
 vm.runInContext(fs.readFileSync(file,'utf8'),ctx,{timeout:20000,filename:file});
}
const c=ctx.window.TAG_SEMESTER1_CATALOG_V2,p=ctx.window.TAG_SEMESTER1_PACKS_V2;
assert.ok(c&&p);
assert.equal(c.all.length,153);
assert.equal(c.bySubject('الرياضيات').length,106);
assert.equal(c.bySubject('المهارات الرقمية').length,47);
assert.deepEqual(Array.from(new Set(c.bySubject('الرياضيات').map(x=>x.grade))),['السادس','السابع','الثامن','التاسع','العاشر']);
assert.deepEqual(Array.from(new Set(c.bySubject('المهارات الرقمية').map(x=>x.grade))),['السابع','الثامن','التاسع','العاشر','الأول ثانوي']);
assert.equal(c.forTeacher('الرياضيات').length,106);
assert.equal(c.forTeacher('رياضيات').length,106);
assert.equal(c.forTeacher('المهارات الرقمية').length,47);
assert.equal(c.forTeacher('مهارات رقمية').length,47);
assert.equal(c.forTeacher('التربية الإسلامية').length,0);
assert.equal(c.get('m-3-3-2').lesson.startsWith('Zeros of Quadratic Functions'),true);
assert.ok(c.all.every(l=>l.semester==='1'&&l.questionTarget===30&&l.lesson&&l.unit));
const ids=new Set(),globalQuestions=new Set();
let ready=0,missing=0;
for(const lesson of c.all){
 assert.ok(!ids.has(lesson.id),'duplicate lesson '+lesson.id);ids.add(lesson.id);
 const questions=p.forLesson(lesson);
 assert.ok(questions.length===0||questions.length===30,'incomplete pack exposed '+lesson.id);
 if(!questions.length){missing++;continue}
 ready++;
 const stems=new Set();
 for(const q of questions){
  assert.equal(q.subject,lesson.subject);
  assert.equal(q.grade,lesson.grade);
  assert.equal(q.unit,lesson.unit);
  assert.equal(q.lesson,lesson.lesson);
  assert.equal(q.semester,'1');
  assert.equal(q.reviewStatus,'teacher_review_required');
  assert.equal(q.type,'single');
  assert.equal(q.options.length,4);
  assert.equal(new Set(q.options).size,4);
  assert.equal(q.correct.length,1);
  assert.ok(q.correct[0]>=0&&q.correct[0]<4);
  assert.ok(q.options[q.correct[0]]);
  assert.ok(!stems.has(q.text),'duplicate question text within lesson: '+lesson.id);
  assert.ok(!globalQuestions.has(q.id),'duplicate question id '+q.id);
  stems.add(q.text);globalQuestions.add(q.id);
 }
}
assert.equal(p.available.length,ready);
assert.ok(ready>=25,'too few validated packs '+ready);
for(const grade of ['السابع','الثامن','التاسع','العاشر','الأول ثانوي']){
 assert.ok(c.bySubject('المهارات الرقمية').some(l=>l.grade===grade&&p.forLesson(l).length===30),'digital grade missing '+grade);
}
assert.ok(p.forLesson('m-1-3-4').every(q=>/f\(x\)|f\(\d+\)/.test(q.text)));
assert.ok(p.forLesson('m-3-3-2').every(q=>/Quadratic Function/.test(q.text)));
console.log('PASS TAG Semester 1: '+c.all.length+' catalogued lessons; '+ready+' complete ×30='+ready*30+' original questions; '+missing+' clearly pending.');
