/* TAG Jordan Curriculum S1: source-indexed unit/lesson map, not textbook reproduction. */
(function(root){
'use strict';
const GRADES={6:'السادس',7:'السابع',8:'الثامن',9:'التاسع',10:'العاشر',11:'الحادي عشر'};
const SOURCE='https://nccd.gov.jo/Ar/Pages/textbooks';
const LINKS={
'math-6':'https://www.nccd.gov.jo/EBV4.0/Root_Storage/AR/Math/2025/G06/Books.Math.06.WB1_WEB.pdf',
'math-7':'https://www.nccd.gov.jo/EBV4.0/Root_Storage/AR/Math/2025/G07/Books.Math.07.WB_WEB.pdf',
'math-8':'https://www.nccd.gov.jo/EBV4.0/Root_Storage/AR/Math/2025/G08/MT08_WB1_WEB.pdf',
'math-9':SOURCE,
'math-10':'https://www.nccd.gov.jo/EBV4.0/Root_Storage/AR/Math/2025/G10/MA%2010%20WB%201_WEB.pdf',
'digital-7':SOURCE,'digital-8':SOURCE,'digital-9':SOURCE,
'digital-10':'https://nccd.gov.jo/EBV4.0/Root_Storage/AR/%D8%A7%D9%84%D9%85%D9%87%D8%A7%D8%B1%D8%A7%D8%AA%20%D8%A7%D9%84%D8%B1%D9%82%D9%85%D9%8A%D8%A9/G10/1/Digital%20Skills%20S1%20G10%20.pdf',
'digital-11':'https://www.nccd.gov.jo/EBV4.0/Root_Storage/AR/%D8%A7%D9%84%D9%85%D9%87%D8%A7%D8%B1%D8%A7%D8%AA%20%D8%A7%D9%84%D8%B1%D9%82%D9%85%D9%8A%D8%A9/G11/1/G11%20Digital%20Skills%20S1%20SB%20.pdf'
};
const RAW={
'math-6':[
['الأعداد الصحيحة والعمليات عليها','الأعداد الصحيحة والقيمة المطلقة|مقارنة الأعداد الصحيحة وترتيبها|جمع الأعداد الصحيحة|طرح الأعداد الصحيحة|ضرب الأعداد الصحيحة وقسمتها'],
['الكسور والعمليات عليها','جمع الكسور وطرحها|جمع الأعداد الكسرية وطرحها|ضرب الأعداد الكسرية|قسمة الكسور|قسمة الأعداد الكسرية'],
['العمليات على الأعداد العشرية','ضرب الأعداد العشرية|قسمة الأعداد العشرية|القياس: تطبيقات العمليات على الأعداد العشرية|خطة حل المسألة: حل مسألة أبسط'],
['التحويلات والإنشاءات الهندسية','المستوى الإحداثي|الانسحاب في المستوى الإحداثي|الانعكاس في المستوى الإحداثي|الدائرة وأجزاؤها|إنشاءات هندسية|رسم المثلث']],
'math-7':[
['الأعداد النسبية','العدد النسبي|كتابة العدد النسبي بالصورة العشرية|مقارنة الأعداد النسبية وترتيبها|جمع الأعداد النسبية وطرحها|ضرب الأعداد النسبية وقسمتها|خطة حل المسألة: الحل العكسي'],
['الأسس الصحيحة والمقادير الجبرية','قوانين الأسس الصحيحة|أولويات العمليات الحسابية|الحدود والمقادير الجبرية|جمع المقادير الجبرية وطرحها|ضرب المقادير الجبرية|خطة حل المسألة: التخمين والتحقق'],
['المعادلات الخطية','حل المعادلات|الكسور العشرية الدورية|المتتاليات|الاقترانات (Functions)|تمثيل الاقتران الخطي بيانيًا (Linear Function)'],
['الزوايا والمضلعات والتحويلات الهندسية','العلاقات بين الزوايا|المستقيمات المتوازية والقاطع|زوايا المثلث|زوايا المضلع|الدوران']],
'math-8':[
['الأعداد الحقيقية','الجذور التربيعية|الجذور الصماء|نظرية فيثاغورس|الأعداد الحقيقية|الأسس النسبية والجذور|ضرب الأسس النسبية وقسمتها|الصيغة العلمية|النسبة المئوية'],
['تحليل المقادير الجبرية','حالات خاصة من ضرب المقادير الجبرية|التحليل بإخراج العامل المشترك الأكبر|تحليل ثلاثيات الحدود x² + bx + c|حالات خاصة من التحليل|تبسيط المقادير الجبرية النسبية'],
['المعادلات الخطية بمتغيرين','المعادلة الخطية بالصورة القياسية|ميل المستقيم|معادلة المستقيم بصيغة الميل والمقطع|معادلة المستقيم بصيغة الميل ونقطة|المستقيمات المتوازية والمتعامدة'],
['المثلثات المتطابقة','تطابق المثلثات (SSS, SAS, HL)|تطابق المثلثات (ASA, AAS)|المثلثات المتطابقة الضلعين والمثلثات المتطابقة الأضلاع']],
'math-9':[
['المتباينات الخطية','المجموعات والفترات|حل المتباينات المركبة|حل معادلات القيمة المطلقة ومتبايناتها|تمثيل المتباينات الخطية بمتغيرين بيانيًا'],
['العلاقات والاقترانات (Relations and Functions)','الاقترانات (Functions)|تفسير التمثيلات البيانية|الاقتران التربيعي (Quadratic Function)|التحويلات الهندسية للاقتران التربيعي (Function Transformations)'],
['حل المعادلات التربيعية','حل المعادلات التربيعية بيانيًا|حل المعادلات التربيعية بالتحليل (1)|حل المعادلات التربيعية بالتحليل (2)|حل المعادلات التربيعية بإكمال المربع|حل المعادلات التربيعية بالقانون العام|حل المعادلات الخاصة'],
['الهندسة الإحداثية','المسافة في المستوى الإحداثي|البعد بين النقطة والمستقيم|البرهان الإحداثي']],
'math-10':[
['الأسس والمعادلات','حل نظام من معادلة خطية ومعادلة تربيعية|حل نظام من معادلتين تربيعيتين|تبسيط المقادير الأسية|حل المعادلة الأسية'],
['الدائرة','أوتار الدائرة وأقطارها ومماساتها|الأقواس والقطاعات الدائرية|الزوايا في الدائرة|معادلة الدائرة|الدوائر المتماسة'],
['حساب المثلثات','النسب المثلثية|النسب المثلثية للزوايا ضمن الدورة الواحدة|تمثيل الاقترانات المثلثية (Trigonometric Functions)|حل المعادلات المثلثية'],
['تطبيقات المثلثات','الاتجاه من الشمال|قانون الجيوب (Sine Rule)|قانون جيوب التمام (Cosine Rule)|استعمال sin لإيجاد مساحة المثلث|حل مسائل ثلاثية الأبعاد']],
'digital-7':[
['أنظمة الحوسبة (Computing Systems)','جهاز الحاسوب|مكونات الحاسوب المادية (Hardware)|مكونات الحاسوب البرمجية (Software)|أنظمة التشغيل (Operating Systems)|تفاعل الإنسان مع الحاسوب (HCI)'],
['شبكات الحاسوب (Computer Networks)','مقدمة إلى شبكات الحاسوب|مكونات شبكات الحاسوب|نماذج الربط في الشبكات السلكية|أنواع شبكات الحاسوب|التواصل باستخدام الشبكات|أداء الشبكة وفاعليتها']],
'digital-8':[
['أنظمة الحوسبة (Computing Systems)','إصلاح الأعطال وصيانة الحاسوب|صيانة المكونات المادية|إصلاح أعطال المكونات البرمجية|استخدام أدوات نظام التشغيل في اكتشاف الأعطال'],
['الخوارزميات والبرمجة (Algorithms & Programming)','مقدمة في برمجية Scratch|إنشاء مشروع في Scratch|عناصر التصميم في Scratch|اللبنات البرمجية في Scratch|المتغيرات في Scratch|لبنات التحكم في Scratch']],
'digital-9':[
['أثر الحوسبة (Impact of Computing)','وسائل التكنولوجيا الحديثة|التعلم الإلكتروني: الأدوات والمنصات|الجرائم الإلكترونية|التنمر الإلكتروني|الإعلام الرقمي'],
['الخوارزميات والبرمجة (Algorithms & Programming)','المتغيرات البرمجية في Scratch|الجمل الشرطية المركبة|حلقات التكرار المتداخلة|الدوال البرمجية والروتين الفرعي']],
'digital-10':[
['تحليل البيانات (Data Analysis)','البيانات والمعلومات (Information and Data)|أنواع البيانات وطرائق تنظيمها (Data Types)|التمثيل المرئي للبيانات (Data Visualization)|تحليل البيانات (Data Analysis)'],
['الخوارزميات والبرمجة (Algorithms & Programming)','مقدمة إلى المواقع الإلكترونية|إنشاء الصفحات الإلكترونية (HTML)|تنسيق النصوص (Text Formatting)|التعليقات والقوائم (Comments and Lists)|الصور (Images)|الوسائط المتعددة والارتباطات التشعبية|الجداول (Tables)']],
'digital-11':[
['الخوارزميات والبرمجة (Algorithms & Programming)','مقدمة في لغات البرمجة|أساسيات لغة Python|الجمل الشرطية في Python|الحلقات (Loops) في Python|القوائم (Lists) في Python|الدوال البرمجية (Functions) في Python'],
['الحوسبة والحياة (Computing and Life)','الحوسبة الخضراء (Green Computing)|النفايات الإلكترونية (Electronic Waste)|تطبيقات الحاسوب في الحياة اليومية']]
};
function norm(x){return String(x||'').toLowerCase().trim().replace(/[أإآ]/g,'ا').replace(/ة/g,'ه').replace(/\s+/g,' ')}
function keyOf(s){const n=norm(s);if(n.includes('رياض')||n==='math'||n==='mathematics')return 'math';if(n.includes('رقمي')||n.includes('حاسوب')||n==='digital'||n==='digital skills')return 'digital';return ''}
const courses=Object.entries(RAW).map(([id,rows])=>{
const bits=id.split('-'),subject=bits[0],grade=Number(bits[1]);
const units=rows.map((r,i)=>({
 id:id+'-u'+(i+1),title:r[0],number:i+1,
 lessons:r[1].split('|').map((title,j)=>Object.freeze({
  id:id+'-u'+(i+1)+'-l'+(j+1),title,number:j+1,unit:r[0],
  grade:GRADES[grade],gradeNum:grade,subject:subject==='math'?'الرياضيات':'المهارات الرقمية',
  semester:'الأول',sourceUrl:LINKS[id],sourceStatus:id==='math-9'?'needs_edition_confirmation':'toc_verified'
 }))
}));
return Object.freeze({id,grade,gradeName:GRADES[grade],subject,
 subjectName:subject==='math'?'الرياضيات':'المهارات الرقمية',
 semester:'الأول',sourceUrl:LINKS[id],sourceStatus:id==='math-9'?'needs_edition_confirmation':'toc_verified',
 units});
});
function courseFor(subject,grade){return courses.find(c=>c.subject===keyOf(subject)&&c.grade===Number(grade))||null}
function lessonById(id){for(const c of courses)for(const u of c.units)for(const l of u.lessons)if(l.id===id)return l;return null}
root.TAG_JORDAN_S1_COURSES_V1=Object.freeze({courses,grades:GRADES,keyOf,courseFor,lessonById,source:SOURCE,semester:'الأول'});
})(window);
