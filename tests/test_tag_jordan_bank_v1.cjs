/* Run with Node 22: validates that supplementary packs are safe and subject-scoped. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const scope={window:{}};
vm.runInNewContext(fs.readFileSync('tag-jordan-curriculum-v1.js','utf8'),scope,{timeout:7000});
const lib=scope.window.TAG_JORDAN_CURRICULUM_V1;
assert.ok(lib,'Jordan curriculum pack not loaded');
assert.equal(lib.grades.length,12);
assert.equal(lib.canonicalSubject('الرياضيات'),'الرياضيات');
assert.equal(lib.subjectKey('اللغة الانجليزية'),'english');
assert.equal(lib.subjectKey('تربية إسلامية'),'islamic');
assert.equal(lib.subjectKey('مهارات رقمية'),'digital');
const all=lib.all;
assert.ok(all.length>=3500,'Need substantive introductory material; found '+all.length);
const ids=new Set(),sig=new Set(),counts={};
for(const q of all){
 assert.ok(!ids.has(q.id),'Duplicate '+q.id);ids.add(q.id);
 const key=[q.subject,q.grade,q.type,q.text].join('|');
 assert.ok(!sig.has(key),'Duplicate question '+key);sig.add(key);
 assert.ok(lib.grades.includes(q.grade),'Unknown grade for '+q.id);
 assert.ok(String(q.text||'').length>=15,q.id+' very short');
 assert.equal(q.type,'single');
 assert.equal(q.options.length,4);
 assert.equal(new Set(q.options).size,4,q.id+' options must be distinct');
 assert.equal(q.correct.length,1);
 assert.ok(Number.isInteger(q.correct[0])&&q.correct[0]>=0&&q.correct[0]<4);
 assert.equal(q.reviewStatus,'teacher_review_required');
 assert.match(q.source,/تحتاج مراجعة المعلم/);
 assert.equal(q.sourceUrl,'https://nccd.gov.jo/Ar/Pages/textbooks');
 assert.equal(q.image,'');
 counts[q.subject]=(counts[q.subject]||0)+1;
}
for(const subject of ['الرياضيات','الثقافة المالية','العلوم','اللغة العربية','اللغة الإنجليزية','الدراسات الاجتماعية','التربية الإسلامية']){
 assert.ok(counts[subject]>10,subject+' missing');
 const questions=lib.questionsForTeacher(subject);
 assert.equal(questions.length,counts[subject]);
 assert.ok(questions.every(q=>q.subject===subject),'Leaking other subjects to '+subject);
}
assert.equal(lib.questionsForTeacher('مادة غير مسجلة').length,0,'Do not guess unknown curriculum');
assert.equal(lib.questionsForTeacher('مهارات رقمية').length,0,'Digital subject uses existing reviewed seed pack, no fabricated questions');
const gradeMath=lib.questionsForTeacher('الرياضيات').filter(q=>q.grade==='السابع');
assert.ok(gradeMath.length>100,'7th maths must have ample examples');
assert.ok(gradeMath.some(q=>q.options[q.correct[0]].startsWith('-')),'Integers must include negative answers');
console.log('PASS TAG Jordan supplementary bank: '+all.length+' original questions, '+ids.size+' unique IDs; by subject:',counts);
