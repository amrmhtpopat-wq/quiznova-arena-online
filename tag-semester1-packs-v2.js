/* TAG Semester 1 — validated original supplementary question packs.
 * Ready only when exactly 30 UNIQUE questions with 4 valid alternatives are supplied.
 * NEVER auto-save the shared bank into teachers' accounts.
 */
(function(root){
"use strict";
var C=root.TAG_SEMESTER1_CATALOG_V2;if(!C)return;
function gcd(a,b){a=Math.abs(a);b=Math.abs(b);while(b){var t=a%b;a=b;b=t}return a||1}
function fraction(a,b){var g=gcd(a,b);return b/g===1?String(a/g):a/g+"/"+b/g}
function make(l,n,stem,answer,bad){
 var s=String(answer),opt=[s].concat(bad.map(String).filter(function(x){return x!==s}));
 opt=[...new Set(opt)].slice(0,4);
 if(opt.length!==4||!String(stem).trim())throw Error("Invalid alternatives for "+l.id+" "+n);
 var shift=(n+l.lessonIndex)%4;
 opt=opt.slice(shift).concat(opt.slice(0,shift));
 return {id:"tag-s1-"+l.id+"-"+String(n+1).padStart(2,"0"),subject:l.subject,
 grade:l.grade,semester:"1",unit:l.unit,lesson:l.lesson,topic:l.lesson,
 type:"single",text:stem,options:opt,correct:[opt.indexOf(s)],
 difficulty:n<10?"easy":n<22?"medium":"hard",time:n<22?30:40,points:n<22?1000:1200,
 image:"",tags:["الفصل الأول",l.lesson,"تحتاج مراجعة"],skill:l.lesson,
 source:"تدريب إثرائي أصلي يتطلب مراجعة معلم المادة",reviewStatus:"teacher_review_required",
 explanation:"الإجابة الصحيحة: "+s};
}
function num(l,n,stem,a,step){
 step=step||1;
 return make(l,n,stem,a,[a+step,a-step,a+step*2,a-step*2,a+step*3]);
}
function math(l){
 var f={
 "m-0-1-1":function(n){var a=3+2*n,b=2+(7*n%31),k=n%3;return num(l,n,k===0?"احسب: "+a+" + "+b:k===1?"احسب: (−"+a+") + "+b:"احسب: (−"+a+") + (−"+b+")",k===0?a+b:k===1?-a+b:-a-b)},
 "m-0-1-2":function(n){var a=10+n,b=3+(7*n%24),k=n%3;return num(l,n,k===0?"احسب: "+a+" − (−"+b+")":k===1?"احسب: (−"+a+") − "+b:"احسب: "+a+" − "+b,k===0?a+b:k===1?-a-b:a-b)},
 "m-0-1-3":function(n){var a=2+n%11,b=3+Math.floor(n/11)*4+n%7,k=n%3;return num(l,n,k===0?"(−"+a+") × "+b+" = ؟":k===1?"(−"+a*b+") ÷ "+a+" = ؟":"(−"+a+") × (−"+b+") = ؟",k===0?-a*b:k===1?-b:a*b)},
 "m-0-1-5":function(n){var a=2+n%6,b=2+Math.floor(n/6)%5,z=a**b;return num(l,n,"ما قيمة "+a+"^"+b+"؟",z,Math.max(2,Math.floor(z/5)))},
 "m-0-1-6":function(n){var a=2+n;return num(l,n,"ما الجذر التربيعي الرئيسي للعدد "+a*a+"؟",a)},
 "m-0-1-7":function(n){var a=2+n;return num(l,n,"ما الجذر التكعيبي للعدد "+a*a*a+"؟",a)},
 "m-0-3-6":function(n){var a=2+n%7,b=3+2*n,x=2+n;return num(l,n,"حل المعادلة: "+a+"x + "+b+" = "+(a*x+b)+" .",x)},
 "m-1-1-2":function(n){var a=2+n;return num(l,n,"ما القيمة المطلقة للعدد −"+a+"؟",a)},
 "m-1-1-5":function(n){var a=1+n%11,b=3+n%13,d=3+Math.floor(n/8),x=n%2?-a:a,k=x+b;return make(l,n,"أوجد نتيجة ("+x+"/"+d+") + ("+b+"/"+d+") في أبسط صورة.",fraction(k,d),[fraction(k+d,d),fraction(k-d,d),fraction(x-b,d),fraction(b,d),fraction(k+2*d,d)])},
 "m-1-2-1":function(n){var a=2+n%5,b=2+Math.floor(n/5)%6,z=a**b;return num(l,n,"ما قيمة "+a+"^"+b+"؟",z,Math.max(2,Math.floor(z/5)))},
 "m-1-3-1":function(n){var a=2+n%7,b=3+2*n,x=2+n;return num(l,n,"إذا كان "+a+"x + "+b+" = "+(a*x+b)+"، فما x؟",x)},
 "m-1-3-4":function(n){var a=1+n%8,b=2+n%11,x=2+Math.floor(n/8);return num(l,n,"إذا كان f(x) = "+a+"x + "+b+"، فما f("+x+")؟",a*x+b,a)},
 "m-1-3-5":function(n){var a=1+n%7,b=2+Math.floor(n/7),x=1+n%8;return num(l,n,"للاقتران Linear Function: f(x) = "+a+"x + "+b+"، ما إحداثي y عندما x="+x+"؟",a*x+b,a)},
 "m-2-2-1":function(n){var a=1+n,s=2+n%7;return num(l,n,"النمط: "+a+"، "+(a+s)+"، "+(a+2*s)+"؛ ما الحد الرابع؟",a+3*s,s)},
 "m-2-3-1":function(n){var a=2+n%8,b=1+n,x=2+Math.floor(n/8);return num(l,n,"للدالة Function: f(x) = "+a+"x + "+b+"، أوجد f("+x+").",a*x+b,a)},
 "m-2-3-2":function(n){var a=2+n%9,b=1+n;return num(l,n,"ما ميل Linear Function: f(x) = "+a+"x + "+b+"؟",a)},
 "m-2-3-3":function(n){var a=2+n%9,b=1+n;return num(l,n,"ما المقطع الصادي لرسم Linear Function: f(x) = "+a+"x + "+b+"؟",b)},
 "m-2-4-1":function(n){var a=5+n,s=3+n%8;return num(l,n,"ما المتوسط الحسابي للأعداد "+a+"، "+(a+s)+"، "+(a+2*s)+"؟",a+s,s)},
 "m-3-2-3":function(n){var k=4+n;return num(l,n,"ما أكبر عدد صحيح يحقق x < "+k+"؟",k-1)},
 "m-3-3-2":function(n){var p=2+n%7,q=3+Math.floor(n/7),sum=p+q;return num(l,n,"في Quadratic Function: f(x) = x² − "+sum+"x + "+p*q+"، ما مجموع أصفاره؟",sum)},
 "m-3-3-4":function(n){var p=2+n%8,q=3+Math.floor(n/8);return num(l,n,"ما مجموع جذري المعادلة x² − "+(p+q)+"x + "+p*q+" = 0 ؟",p+q)},
 "m-3-4-4":function(n){var red=2+n,blue=3+n%9,total=red+blue;return make(l,n,"صندوق فيه "+red+" كرات حمراء و"+blue+" زرقاء. ما احتمال سحب كرة حمراء؟",fraction(red,total),[fraction(blue,total),fraction(red,total+1),fraction(red+1,total),fraction(blue,total+1)])},
 "m-4-1-4":function(n){var a=2+n%4,x=2+Math.floor(n/4)%8;return num(l,n,"حل المعادلة الأسية: "+a+"^x = "+a**x+" .",x)},
 "m-4-2-4":function(n){var a=1+n%8,b=2+Math.floor(n/8),r=2+n;return num(l,n,"دائرة مركزها ("+a+"، "+b+") ونصف قطرها "+r+"؛ ما r² في المعادلة القياسية؟",r*r,Math.max(2,Math.floor(r/3)))}
 };
 if(!Object.prototype.hasOwnProperty.call(f,l.id))return [];
 var q=[];for(var i=0;i<30;i++)q.push(f[l.id](i));return q;
}
var originalDigital={
 "d-1-1-1":[
 ["أي تسلسل يصف عمل نظام الحاسوب؟","إدخال → معالجة → إخراج","إخراج → حذف → إدخال","تخزين → إيقاف → عرض","إخراج → إدخال → معالجة"],
 ["ما الجهاز الذي يُصنّف حاسوبًا محمولًا؟","الحاسوب المحمول Laptop","الطابعة","السماعة","الماسح الضوئي"],
 ["بماذا يتميز الحاسوب عن الآلة الحاسبة التقليدية؟","تنفيذ برامج متنوعة ومعالجة أنواع مختلفة من البيانات","يعمل دون طاقة","لا يقبل إدخال بيانات","لا يمكنه تخزين الملفات"],
 ["ما المقصود بالبيانات Data؟","حقائق أولية قبل تنظيمها ومعالجتها","النتائج النهائية فقط","نظام تشغيل الحاسوب","أحد أنواع الشاشات"],
 ["ما الذي نحصل عليه بعد معالجة البيانات وتفسيرها؟","معلومات Information","كابل شبكة","طاقة كهربائية","لوحة مفاتيح"],
 ["أي مثال يمثل إدخالًا في الحاسوب؟","كتابة اسم الطالب بلوحة المفاتيح","ظهور النتيجة على الشاشة","طباعة التقرير","سماع التنبيه من السماعات"],
 ["أي مثال يمثل إخراجًا؟","عرض جدول على الشاشة","تحريك الفأرة","مسح رمز QR بالكاميرا","إدخال رقم سري"],
 ["أي مهمة تمثل المعالجة؟","حساب مجموع العلامات بواسطة البرنامج","النقر على زر","طباعة ورقة","توصيل شاحن"],
 ["ما وسيلة حفظ ملف بعد إغلاق البرنامج؟","وحدة التخزين","الذاكرة المؤقتة وحدها","الميكروفون","لوحة المفاتيح"],
 ["ما المقصود بالنظام الحاسوبي؟","مكونات مادية وبرمجية تعمل معًا لأداء مهام","الشاشة وحدها","برنامج رسم فقط","طابعة دون حاسوب"],
 ["أي جهاز يجمع خصائص الحوسبة والاتصال؟","الهاتف الذكي","الكابل الكهربائي","المكبر السلبي","لوح الكتابة الورقي"],
 ["ما دور المستخدم في نظام الحاسوب؟","إدخال الطلبات والتفاعل مع النتائج","استبدال جميع الدارات","إنتاج الكهرباء مباشرة","منع تنفيذ البرامج"],
 ["ما المقصود بالتعليمات البرمجية؟","أوامر تُوجّه الحاسوب لتنفيذ خطوات","أسلاك الشبكة","أجزاء الطابعة","حافظة الجهاز"],
 ["ما الفرق بين الحاسوب المكتبي والمحمول؟","المحمول مصمم لسهولة النقل والعمل ببطارية","المكتبي بلا معالج","المحمول بلا شاشة","المكتبي لا يخزن ملفات"],
 ["ما فائدة تنظيم الملفات في مجلدات؟","سهولة العثور عليها وإدارتها","زيادة حجم الشاشة","تغيير سرعة الإنترنت دائمًا","إلغاء الحاجة للنسخ الاحتياطي"],
 ["متى يُستخدم الحاسوب في التعليم؟","عند تشغيل تطبيقات تعلم وأنشطة رقمية","فقط عند شحن الهاتف","عند إطفاء جميع الأجهزة","لتخزين الكهرباء"],
 ["ما معنى أن الجهاز رقمي؟","يعالج البيانات باستخدام تمثيل رقمي","يعمل بلا برامج","يعتمد على الورق فقط","لا يتيح حفظ البيانات"],
 ["أي مثال يوضح نظام إدخال ومعالجة وإخراج؟","كتابة علامتين وحساب المتوسط ثم عرضه","إغلاق الجهاز قبل إدخال البيانات","فتح ملف فارغ فقط","فصل الشاشة عن الطاقة"],
 ["كيف تتواصل مع الحاسوب باستخدام اللمس؟","بالضغط على عناصر واجهة الشاشة اللمسية","بتغيير القرص الصلب","بإزالة النظام","بفصل البطارية"],
 ["ما الوظيفة الأساسية لوحدة المعالجة المركزية CPU؟","تنفيذ التعليمات والعمليات","عرض الصور وحدها","طباعة الورق","نقل الصوت عبر الهواء"],
 ["ما الفرق بين المعلومة والبيان الخام؟","المعلومة نتيجة تنظيم البيانات وتفسيرها","البيان نتيجة جاهزة دومًا","لا يمكن معالجة البيانات","المعلومات لا تستخدم في القرار"],
 ["ما فائدة حفظ نسخة احتياطية؟","استرجاع الملفات عند فقد الأصل","زيادة دقة الشاشة","تبريد المعالج","تغيير لغة لوحة المفاتيح"],
 ["كيف يستفيد متجر من نظام الحاسوب؟","تسجيل المبيعات وحساب المخزون","تحويل الورق إلى كهرباء","الاستغناء عن البيانات","منع حفظ المعاملات"],
 ["ما الاستخدام الأنسب للحاسوب في المستشفى؟","تنظيم السجلات والمواعيد بصورة آمنة","كشف كلمات مرور المراجعين","تعطيل النسخ الاحتياطي","إرسال معلومات المرضى للجميع"],
 ["ماذا يحدث إذا لم تُقدَّم مدخلات لبرنامج ينتظرها؟","قد يظل البرنامج منتظرًا الإدخال","يطبع تلقائيًا دون شروط","يتحول إلى طابعة","يمحو نظام التشغيل دائمًا"],
 ["ما المقصود بالبرنامج التطبيقي؟","برنامج يؤدي مهمة للمستخدم مثل معالجة النصوص","المعالج المركزي نفسه","سلك الكهرباء","جزء من لوحة المفاتيح"],
 ["أي موقف يتطلب مراعاة خصوصية البيانات؟","تسجيل معلومات طلاب في برنامج المدرسة","تغيير لون الخلفية","تنظيف لوحة المفاتيح","توصيل الشاشة"],
 ["ما المقصود بالدقة في معالجة البيانات؟","الحصول على نتائج صحيحة من مدخلات وقواعد صحيحة","كبر الشاشة","ارتفاع صوت السماعات","وجود عدد أكبر من الأسلاك"],
 ["لماذا يجب التأكد من صحة المدخلات؟","لأن البيانات الخاطئة قد تنتج معلومات خاطئة","لأن المعالج لا ينفذ أوامر","لمنع تخزين أي ملف","لتغيير شكل الأيقونات"],
 ["أي عبارة تصف تفاعل الإنسان والحاسوب؟","يقدم الإنسان أوامر ويتلقى استجابة عبر واجهة","الحاسوب يفهم نية المستخدم دون إدخال","لا توجد وسيلة تفاعل","يعمل الإنسان بديلًا للمعالج"]
 ]
};
function valid(q){
 return q.length===30&&q.every(function(v,i){
  return v.text&&v.options.length===4&&new Set(v.options).size===4
    &&v.correct.length===1&&v.correct[0]>=0&&v.correct[0]<4
    &&q.findIndex(function(w){return w.text===v.text})===i;
 });
}
function forLesson(x){
 var l=typeof x==="string"?C.get(x):x;if(!l)return [];
 var pack=[];
 try{if(l.subject==="الرياضيات")pack=math(l);
 else if(Object.prototype.hasOwnProperty.call(originalDigital,l.id))
 pack=originalDigital[l.id].map(function(a,i){return make(l,i,a[0],a[1],a.slice(2))});
 }catch(e){return []}
 return valid(pack)?pack:[];
}
root.TAG_SEMESTER1_PACKS_V2=Object.freeze({
 forLesson:forLesson,validate:valid,
 available:Object.freeze(C.all.filter(function(l){return forLesson(l).length===30}).map(function(l){return l.id}))
});
})(window);
