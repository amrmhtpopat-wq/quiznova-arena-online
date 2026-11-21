/* TEACH AND GAME — accessible semester-one library inside the ORIGINAL teacher studio. */
(function(){
"use strict";
var cat=window.TAG_SEMESTER1_CATALOG_V2,packs=window.TAG_SEMESTER1_PACKS_V2;
var el=document.getElementById("tagSemester1Mount");
if(!el||!cat||!packs||!window.QN9_TEACHER)return;
var allowed=cat.forTeacher(window.QN9_TEACHER.subject);
var subject=cat.teacherSubject(window.QN9_TEACHER.subject);
var clean=function(x){return String(x||"").replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]})};
if(!subject||!allowed.length){
 el.innerHTML='<div class="s1-empty">مكتبة الفصل الأول متاحة حاليًا لمعلمي الرياضيات والمهارات الرقمية حسب تخصص الحساب.</div>';
 return;
}
var list=allowed,ready=list.filter(function(x){return packs.forLesson(x).length===30}).length;
var grades=[...new Set(list.map(function(x){return x.grade}))];
el.innerHTML='<section class="s1-panel" dir="rtl" aria-label="مكتبة المنهاج الفصل الأول">'
 +'<div class="s1-head"><div><span class="s1-eyebrow">TAG CURRICULUM • الفصل الدراسي الأول</span>'
 +'<h3>مكتبة اختبارات الدروس</h3><p>اختر الصف ثم الوحدة والدرس. يظهر اختبار الدرس فقط عند اكتمال 30 سؤالًا صحيح البنية؛ راجع الأسئلة قبل النشر.</p></div>'
 +'<span class="s1-count" id="s1Ready">'+ready+' درسًا مكتملًا من '+list.length+'</span></div>'
 +'<div class="s1-path"><span>١. المادة <b id="s1Subject">'+clean(subject)+'</b></span><span>٢. الصف</span><span>٣. الوحدة</span><span>٤. الدرس</span></div>'
 +'<div class="s1-filters">'
 +'<label>الصف الدراسي<select id="s1Grade" aria-label="اختر الصف الدراسي"></select></label>'
 +'<label>الوحدة<select id="s1Unit" aria-label="اختر الوحدة"></select></label>'
 +'<label>الدرس<select id="s1Lesson" aria-label="اختر الدرس"></select></label>'
 +'</div>'
 +'<div class="s1-overview" id="s1Overview" role="status" aria-live="polite"></div>'
 +'<div class="s1-controls"><button type="button" class="s1-primary" id="s1Create" disabled>فتح الاختبار (30 سؤالًا)</button>'
 +'<button type="button" class="s1-secondary" id="s1Preview" disabled>معاينة الأسئلة والإجابات</button></div>'
 +'<div id="s1PreviewList" class="s1-preview" hidden></div>'
 +'<p class="s1-trust">هذه أسئلة إثرائية أصلية وليست نسخة معتمدة من الكتاب. الدروس غير المكتملة لا يمكن نشر اختبارها. '
 +'<a href="https://nccd.gov.jo/Ar/Pages/textbooks" target="_blank" rel="noopener noreferrer">المركز الوطني لتطوير المناهج</a></p>'
 +'</section>';
var g=document.getElementById("s1Grade"),u=document.getElementById("s1Unit"),d=document.getElementById("s1Lesson");
var overview=document.getElementById("s1Overview"),create=document.getElementById("s1Create");
var preview=document.getElementById("s1Preview"),previewList=document.getElementById("s1PreviewList");
function option(value,label){var o=document.createElement("option");o.value=value;o.textContent=label;return o}
function fill(select,arr,empty){
 select.replaceChildren();if(empty)select.append(option("",empty));
 arr.forEach(function(x){select.append(option(x.value,x.label))});
}
function state(){
 var l=cat.get(d.value);
 var pack=l?packs.forLesson(l):[];
 var complete=pack.length===30;
 create.disabled=!complete;preview.disabled=!complete;
 previewList.hidden=true;previewList.replaceChildren();preview.setAttribute("aria-expanded","false");
 if(!l){overview.innerHTML='<div class="s1-no">اختر درسًا لعرض حالة الاختبار.</div>';return}
 overview.innerHTML='<div class="s1-selected"><div><small>الصف '+clean(l.grade)+' • '+clean(l.unit)+'</small>'
 +'<h4>'+clean(l.lesson)+'</h4><p>'+ (complete?"اختبار جاهز للمراجعة: 30 سؤالًا، 4 خيارات لكل سؤال، دون تكرار."
 :"فهرس الدرس متاح، لكن حزمة الأسئلة لم تُستكمل أو لم تجتز التحقق بعد. لا يتم إنشاء أسئلة بديلة عشوائية.") +'</p></div>'
 +'<span class="s1-state '+(complete?"ok":"pending")+'">'+(complete?"30 / 30":"قيد الإعداد")+'</span></div>';
}
function lessons(){
 var chosen=list.filter(function(x){return x.grade===g.value&&x.unit===u.value});
 fill(d,chosen.map(function(x){return {value:x.id,label:x.lesson+(packs.forLesson(x).length===30?" ✓":" • قيد الإعداد")}}));
 state();
}
function units(){
 var filtered=list.filter(function(x){return x.grade===g.value});
 var unique=[...new Set(filtered.map(function(x){return x.unit}))];
 fill(u,unique.map(function(x){return {value:x,label:x}}));
 lessons();
}
fill(g,grades.map(function(x){return {value:x,label:"الصف "+x}}));
g.addEventListener("change",units);u.addEventListener("change",lessons);d.addEventListener("change",state);
preview.addEventListener("click",function(){
 var l=cat.get(d.value),q=l?packs.forLesson(l):[];
 if(q.length!==30)return;
 if(!previewList.hidden){previewList.hidden=true;preview.setAttribute("aria-expanded","false");return}
 var frag=document.createDocumentFragment();
 q.forEach(function(item,i){
  var block=document.createElement("details");block.className="s1-question";
  var head=document.createElement("summary");head.textContent=(i+1)+". "+item.text;
  var ul=document.createElement("div");ul.className="s1-answers";
  item.options.forEach(function(answer,idx){
   var span=document.createElement("span");span.textContent=String.fromCharCode(65+idx)+". "+answer;
   if(item.correct.includes(idx)){span.className="correct";span.setAttribute("aria-label","الإجابة الصحيحة: "+answer)}
   ul.append(span);
  });
  block.append(head,ul);frag.append(block);
 });
 previewList.append(frag);previewList.hidden=false;preview.setAttribute("aria-expanded","true");
});
create.addEventListener("click",function(){
 var l=cat.get(d.value),q=l?packs.forLesson(l):[];
 if(q.length!==30)return state();
 if(typeof window.TAG_LESSON_CREATE_V2!=="function")return;
 window.TAG_LESSON_CREATE_V2(l,q);
});
units();
window.TAG_SEMESTER1_UI_V2={subject:subject,lessonCount:list.length,readyCount:ready};
})();