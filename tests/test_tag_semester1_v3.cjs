/* Exact completion + safety acceptance tests for TAG semester one V3. Node 22. */
const assert=require("node:assert/strict");
const fs=require("node:fs"),vm=require("node:vm");
const context=vm.createContext({window:{}});
for(const file of [
 "tag-semester1-catalog-v2.js",
 "tag-semester1-packs-v2.js",
 "tag-semester1-math-v3.js",
 "tag-semester1-digital-v3.js",
 "tag-semester1-unified-v3.js"
]){
 vm.runInContext(fs.readFileSync(file,"utf8"),context,{filename:file,timeout:20000});
}
const C=context.window.TAG_SEMESTER1_CATALOG_V2;
const P=context.window.TAG_SEMESTER1_PACKS_V2;
const M=context.window.TAG_SEMESTER1_MATH_V3;
const D=context.window.TAG_SEMESTER1_DIGITAL_V3;
assert.ok(C&&P&&M&&D,"missing curriculum components");
assert.equal(C.all.length,153);
assert.equal(C.bySubject("الرياضيات").length,106);
assert.equal(C.bySubject("المهارات الرقمية").length,47);
assert.equal(D.conceptCount,47);
assert.equal(P.summary.total,153);
assert.equal(P.summary.ready,153);
assert.equal(P.summary.questions,4590);
assert.equal(P.available.length,153);
assert.equal(C.forTeacher("الرياضيات").length,106);
assert.equal(C.forTeacher("مهارات رقمية").length,47);
assert.equal(C.forTeacher("التربية الإسلامية").length,0);
const ids=new Set(),questionIds=new Set();
let count=0;
for(const lesson of C.all){
 assert.ok(!ids.has(lesson.id),"duplicate lesson id "+lesson.id);ids.add(lesson.id);
 const q=P.forLesson(lesson);
 assert.equal(q.length,30,"incomplete lesson "+lesson.id+" "+lesson.lesson);
 assert.equal(P.forLesson(lesson.id),q,"cache stability "+lesson.id);
 assert.ok(P.available.includes(lesson.id),"unlisted lesson "+lesson.id);
 const stems=new Set();
 for(const item of q){
  assert.equal(item.subject,lesson.subject);
  assert.equal(item.grade,lesson.grade);
  assert.equal(item.lesson,lesson.lesson);
  assert.equal(item.unit,lesson.unit);
  assert.equal(item.semester,"1");
  assert.equal(item.reviewStatus,"teacher_review_required");
  assert.equal(item.type,"single");
  assert.equal(item.options.length,4);
  assert.equal(new Set(item.options).size,4,"duplicate option in "+item.id);
  assert.equal(item.correct.length,1);
  assert.ok(item.correct[0]>=0&&item.correct[0]<4);
  assert.ok(item.options[item.correct[0]]);
  assert.ok(item.text.trim());
  assert.ok(item.explanation.trim());
  assert.ok(!stems.has(item.text),"repeated stem "+item.id);stems.add(item.text);
  assert.ok(!questionIds.has(item.id),"duplicate id "+item.id);questionIds.add(item.id);
  count++;
 }
}
assert.equal(count,4590);
for(const l of C.bySubject("الرياضيات"))assert.equal(P.forLesson(l).length,30,"missing math "+l.id);
for(const l of C.bySubject("المهارات الرقمية"))assert.equal(P.forLesson(l).length,30,"missing digital "+l.id);
for(const l of C.all.filter(x=>x.lesson.includes("Function")||x.lesson.includes("اقتران"))){
 const q=P.forLesson(l);
 assert.ok(q.some(x=>/Function|f\(x\)|f\(/.test(x.text)),"math functions English "+l.id);
}
for(const n of [0,5,8,10,29]){
 const q=P.forLesson("m-2-1-4")[n],val=(n+2)*10000,correct=q.options[q.correct[0]];
 const match=correct.match(/^(\d+(?:\.\d+)?) × 10\^(\d+)$/);
 assert.ok(match,"invalid scientific notation "+correct);
 assert.ok(Number(match[1])>=1&&Number(match[1])<10);
 assert.equal(Number(match[1])*10**Number(match[2]),val);
}
for(const n of [0,1,2,29]){
 const q=P.forLesson("m-4-4-5")[n];
 assert.equal(q.options[q.correct[0]],String(7*(n+2)),"3D Pythagoras answer");
}
for(const n of [0,1,2,29]){
 const q=P.forLesson("m-4-3-1")[n];
 assert.ok(["3/5","4/5","3/4"].includes(q.options[q.correct[0]]));
}
const studio=fs.readFileSync("studio.html","utf8");
for(const script of ["tag-semester1-math-v3.js","tag-semester1-digital-v3.js","tag-semester1-unified-v3.js"])
 assert.ok(studio.includes(script),"missing script from teacher studio "+script);
assert.ok(studio.indexOf("tag-semester1-packs-v2.js")<studio.indexOf("tag-semester1-math-v3.js"));
assert.ok(studio.indexOf("tag-semester1-math-v3.js")<studio.indexOf("tag-semester1-digital-v3.js"));
assert.ok(studio.indexOf("tag-semester1-digital-v3.js")<studio.indexOf("tag-semester1-unified-v3.js"));
console.log("PASS: "+count+" original questions across "+P.summary.ready+" lesson packs, scope + format + answer checks; no student cloud writes.");
