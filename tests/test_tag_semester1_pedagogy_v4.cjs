/* Teaching quality gate: 4,500 questions; arithmetic and curriculum-specific oracles.
   This is an automated editorial/content check, NOT official textbook approval.
*/
const assert=require("node:assert/strict");
const fs=require("node:fs"),vm=require("node:vm");
const context=vm.createContext({window:{}});
for(const file of ["tag-semester1-catalog-v2.js","tag-semester1-packs-v2.js","tag-semester1-math-v3.js","tag-semester1-digital-v3.js","tag-semester1-unified-v3.js"]){
 vm.runInContext(fs.readFileSync(file,"utf8"),context,{filename:file,timeout:20000});
}
const C=context.window.TAG_SEMESTER1_CATALOG_V2,P=context.window.TAG_SEMESTER1_PACKS_V2;
assert.equal(C.all.length,150);
assert.equal(P.available.length,150);
assert.equal(P.summary.questions,4500);
const canonical=x=>String(x).trim().replace(/−/g,"-");
function number(s){
 const x=canonical(s);
 if(/^-?\d+(?:\.\d+)?$/.test(x))return +x;
 if(/^-?\d+(?:\.\d+)?\/-?\d+(?:\.\d+)?$/.test(x)){const a=x.split("/").map(Number);return a[0]/a[1]}
 return null;
}
function ans(q){return q.options[q.correct[0]]}
function close(a,b,msg){assert.ok(Math.abs(a-b)<1e-7,msg+" got "+a+" expected "+b)}
let total=0,math=0,digital=0,independentChecks=0,correctPositions=[0,0,0,0];
for(const l of C.all){
 const q=P.forLesson(l),stems=new Set();
 assert.equal(q.length,30,"missing questions "+l.id);
 for(const item of q){
  total++;
  if(l.subject==="الرياضيات")math++;else digital++;
  assert.equal(item.lesson,l.lesson,item.id);
  assert.equal(item.grade,l.grade,item.id);
  assert.equal(item.subject,l.subject,item.id);
  assert.equal(item.semester,"1",item.id);
  assert.equal(item.reviewStatus,"teacher_review_required",item.id);
  assert.equal(item.options.length,4,item.id);
  assert.equal(new Set(item.options.map(canonical)).size,4,item.id+" repeated options");
  assert.ok(item.text.length>12&&item.text.length<220,"invalid prompt "+item.id);
  assert.ok(item.options.every(x=>String(x).trim().length&&String(x).length<180),item.id);
  assert.ok(item.explanation&&item.explanation.length>=20,"missing explanatory feedback "+item.id);
  assert.ok(!stems.has(item.text),"repeated question "+item.id);
  stems.add(item.text);
  assert.ok(item.correct[0]>=0&&item.correct[0]<4,item.id);
  correctPositions[item.correct[0]]++;
  const target=number(ans(item));
  if(target!==null){
   assert.ok(item.options.every((x,i)=>i===item.correct[0]||number(x)!==target),
    "equivalent numerical distractor "+item.id);
  }
 }
 const a=q.map(ans);
 if(l.id==="m-0-1-3"||l.id==="m-0-1-4"||l.id==="m-0-1-5"){
  for(const v of q){
   const expr=canonical(v.text.split("احسب:")[1]).replace(/[؟.]/g,"").replace(/×/g,"*").replace(/÷/g,"/");
   assert.match(expr,/^[0-9+\-*/() ]+$/,"unexpected arithmetic syntax "+v.id);
   const expected=Function("return ("+expr+")")();
   close(number(ans(v)),expected,v.id);independentChecks++;
  }
 }
 if(l.id==="m-1-2-1"||l.id==="m-4-1-3"){
  for(const item of q){
   const str=item.text.replace(/−/g,"-");
   const parts=[...str.matchAll(/(\d+)\^(\d+)/g)].map(x=>[+x[1],+x[2]]);
   assert.ok(parts.length>=1,"missing exponent "+item.id);
   let expected;
   if(parts.length===1)expected=String(parts[0][0]**parts[0][1]);
   else if(str.includes("×"))expected=parts[0][0]+"^"+(parts[0][1]+parts[1][1]);
   else if(str.includes("÷"))expected=parts[0][0]+"^"+(parts[0][1]-parts[1][1]);
   else assert.fail("unknown exponent form "+item.id);
   assert.equal(ans(item),expected,"exponent semantic mismatch "+item.id);independentChecks++;
  }
 }
 if(l.id==="m-2-4-1"){
  for(let i=0;i<30;i++){assert.equal(ans(q[i]),["SSS","SAS","HL"][i%3]);independentChecks++;}
 }
 if(l.id==="m-2-4-2"){
  for(let i=0;i<30;i++){assert.equal(ans(q[i]),["ASA","AAS","التشابه لا التطابق بالضرورة"][i%3]);independentChecks++;}
 }
 if(l.id==="m-4-3-1"){
  for(const item of q){
   const m=item.text.match(/المقابل (\d+) سم والمجاور (\d+) سم والوتر (\d+) سم/);
   assert.ok(m,"missing triangle measurements "+item.id);
   const [o,a,h]=m.slice(1).map(Number);
   close(o*o+a*a,h*h,item.id+" invalid right triangle");
   let expect=item.text.includes("sin θ")?o/h:item.text.includes("cos θ")?a/h:o/a;
   close(number(ans(item)),expect,item.id+" trig ratio");independentChecks++;
  }
 }
 if(l.id==="m-4-3-2"){
  const rootValue=s=>{
   const t=canonical(s);
   if(t.includes("√")){const sign=t[0]==="-"?-1:1;const m=t.match(/√(\d+)\/(\d+)/);return sign*Math.sqrt(+m[1])/(+m[2]);}
   return number(s);
  };
  for(const item of q){
   const m=item.text.match(/(sin|cos)\((\d+)°\)/);
   assert.ok(m,"missing trig angle "+item.id);
   const v=+m[2]*Math.PI/180;
   const expected=m[1]==="sin"?Math.sin(v):Math.cos(v);
   close(rootValue(ans(item)),expected,item.id+" trig cycle");independentChecks++;
  }
 }
 if(l.id==="m-2-1-7"){
  for(const item of q){
   const m=item.text.match(/العدد (\d+)/),val=ans(item).match(/(\d+(?:\.\d+)?) × 10\^(\d+)/);
   assert.ok(m&&val,"invalid scientific notation "+item.id);
   assert.ok(+val[1]>=1&&+val[1]<10,item.id);
   close(+val[1]*10**+val[2],+m[1],item.id);independentChecks++;
  }
 }
 if(l.id==="m-4-4-5"){
  for(const item of q){
   const m=item.text.match(/أبعاده (\d+) سم و (\d+) سم و (\d+) سم/);
   assert.ok(m,"missing 3D dimensions "+item.id);
   const t=m.slice(1).map(Number);
   close(number(ans(item)),Math.hypot(...t),item.id);independentChecks++;
  }
 }
 if(l.id==="m-4-1-4"){
  for(const item of q){
   const m=item.text.match(/(\d+)\^x = (\d+)/);
   assert.ok(m,"missing exponential equation "+item.id);
   close((+m[1])**number(ans(item)),+m[2],item.id);independentChecks++;
  }
 }
 if(l.subject==="المهارات الرقمية"&&l.id!=="d-1-1-1"&&l.id!=="d-2-1-2"&&l.id!=="d-3-1-3"&&l.id!=="d-4-1-1"&&l.id!=="d-5-1-2"){
  assert.ok(q.slice(0,5).every(v=>v.text.includes("التعريف")),"missing recall level "+l.id);
  assert.ok(q.slice(10,15).every(v=>v.text.includes("الموقف")),"missing applied level "+l.id);
  assert.ok(q.slice(20,25).every(v=>v.text.includes("تمييز")),"missing comparison level "+l.id);
 }
}
assert.equal(total,4500);assert.equal(math,3090);assert.equal(digital,1410);
assert.ok(correctPositions.every(n=>n>900&&n<1300),"skewed answer position");
assert.ok(independentChecks>=270,"insufficient independent computation checks");
const html=fs.readFileSync("studio.html","utf8");
assert.ok(html.includes("tag-semester1-unified-v3.js"));
console.log("PASS pedagogical QA: "+total+" items inspected, "+independentChecks+" independent math proofs, "+digital+" digital items, balanced choices "+correctPositions.join("/"));
