/* TAG Jordan Digital Skills S1 • 30 original knowledge/application MCQs per
 * explicitly mapped lesson. Each six verified-concept candidates is tested
 * through definition, concept, scenario and critical application questions.
 * Original supplementary material, never copied from copyrighted textbooks.
 */
(function(w){
'use strict';
function item(question,correct,alternatives,offset){
 const unique=[String(correct)];
 for(const candidate of alternatives){
  const str=String(candidate);
  if(!unique.includes(str))unique.push(str);
  if(unique.length===4)break;
 }
 if(unique.length!==4)return null;
 const shift=offset%4,options=unique.slice(shift).concat(unique.slice(0,shift));
 return {text:question,options,correct:[(4-shift)%4]};
}
function questionsFor(lesson){
 if(!lesson||lesson.subject!=='المهارات الرقمية')return [];
 const id=String(lesson.id||''),bits=id.split('-');
 if(bits.length!==4||bits[0]!=='digital')return [];
 const grade=Number(bits[1]),unit=Number(bits[2].slice(1))-1,number=Number(bits[3].slice(1))-1;
 const concepts=w.TAG_S1_DIGITAL_FACTS?.[grade]?.[unit]?.[number];
 if(!Array.isArray(concepts)||concepts.length!==6)return [];
 if(concepts.some(c=>!c.term||!c.definition||!c.example))return [];
 const rows=[];
 for(let i=0;i<concepts.length;i++){
  const c=concepts[i];
  // Distractors belong to the same lesson and are therefore meaningful,
  // but can never use the exact correct answer.
  const others=[1,2,3,4,5].map(offset=>concepts[(i+offset)%6]);
  const variants=[
   ['أي مصطلح يطابق التعريف الآتي: '+c.definition+'؟',c.term,others.map(x=>x.term)],
   ['ما الوصف الصحيح لمفهوم '+c.term+'؟',c.definition,others.map(x=>x.definition)],
   ['أي مفهوم يظهر في الموقف الآتي: '+c.example+'؟',c.term,others.slice().reverse().map(x=>x.term)],
   ['ما المثال التطبيقي الأكثر ارتباطًا بـ '+c.term+'؟',c.example,others.map(x=>x.example)],
   ['أثناء درس '+lesson.title+'، أي وصف يفسّر الموقف: '+c.example+'؟',c.definition,others.slice().reverse().map(x=>x.definition)]
  ];
  for(let k=0;k<variants.length;k++){
   const variant=variants[k],result=item(variant[0],variant[1],variant[2],i+k);
   if(!result)continue;
   rows.push(Object.freeze({
    id:'jos1_'+lesson.id+'_'+String(rows.length+1).padStart(2,'0'),
    subject:'المهارات الرقمية',grade:lesson.grade,semester:'1',
    unit:lesson.unit,lesson:lesson.title,
    type:'single',text:result.text,options:result.options,correct:result.correct,
    time:30,points:1000,skill:c.term,
    difficulty:k===0?'easy':k===4?'hard':'medium',
    explanation:'المفهوم: '+c.term+'. '+c.definition+'. مثال تطبيقي: '+c.example+'.',
    reviewStatus:'teacher_review_required',origin:'tag_jordan_s1_original',
    source:'تدريبات رقمية أصلية حسب موضوع الدرس — تحتاج مراجعة المعلم وكتاب الفصل الأول',
    sourceUrl:lesson.sourceUrl||'https://nccd.gov.jo/Ar/Pages/textbooks',
    tags:['الأردن','الفصل الأول','المهارات الرقمية','تطبيقات مفاهيمية']
   }));
  }
 }
 return rows;
}
w.TAG_JORDAN_S1_DIGITAL_V1=Object.freeze({questionsFor});
})(window);
