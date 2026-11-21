/* Original TeachGame semester-one complete practice library.
   Keep existing reviewed-format packs, fill the remaining curriculum subjects by
   lesson-specific math/digital builders, and prevent incomplete packs from appearing.
   No cloud writes, account changes, student-card regeneration, or auto publishing.
*/
(function(root){
"use strict";
var C=root.TAG_SEMESTER1_CATALOG_V2,old=root.TAG_SEMESTER1_PACKS_V2;
var math=root.TAG_SEMESTER1_MATH_V3,digital=root.TAG_SEMESTER1_DIGITAL_V3;
if(!C||!old||!math||!digital)return;
var cache=Object.create(null);
function get(x){
 var l=typeof x==="string"?C.get(x):x;
 if(!l||!C.get(l.id))return [];
 if(Object.prototype.hasOwnProperty.call(cache,l.id))return cache[l.id];
 var original=old.forLesson(l),revisedMath=l.subject==="الرياضيات"&&/^(السادس|السابع|الثامن)$/.test(l.grade);
 var pack=revisedMath?math.forLesson(l):original.length===30?original:
  l.subject==="الرياضيات"?math.forLesson(l):
  l.subject==="المهارات الرقمية"?digital.forLesson(l):[];
 if(!old.validate(pack)||pack.some(function(q){
  return q.subject!==l.subject||q.grade!==l.grade||q.unit!==l.unit
  ||q.lesson!==l.lesson||q.semester!=="1"||q.reviewStatus!=="teacher_review_required"
  ||!q.explanation||!q.text;
 }))pack=[];
 cache[l.id]=pack;
 return pack;
}
var available=C.all.filter(function(l){return get(l).length===30}).map(function(l){return l.id});
root.TAG_SEMESTER1_PACKS_V2=Object.freeze({
 forLesson:get,validate:old.validate,available:Object.freeze(available),
 summary:Object.freeze({total:C.all.length,ready:available.length,questions:available.length*30,
  math:C.bySubject("الرياضيات").length,digital:C.bySubject("المهارات الرقمية").length}),
 status:"supplementary_original_teacher_review_required"
});
})(window);