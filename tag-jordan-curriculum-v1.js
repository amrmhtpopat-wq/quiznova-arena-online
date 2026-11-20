/* TAG Jordan curriculum library V1.
 * This is an ORIGINAL supplementary question bank, not an NCCD book reproduction.
 * Material/grade index: https://nccd.gov.jo/Ar/Pages/textbooks
 * The book-specific unit/lesson map must be reviewed before asserting textbook alignment.
 * Questions are STATIC and READ-ONLY; they are never copied into teacher cloud data
 * until the teacher explicitly selects them to create and save a quiz.
 */
(function(root){
"use strict";
const grades=["الأول","الثاني","الثالث","الرابع","الخامس","السادس","السابع","الثامن","التاسع","العاشر","الحادي عشر","الثاني عشر"];
const names={math:"الرياضيات",arabic:"اللغة العربية",english:"اللغة الإنجليزية",science:"العلوم",digital:"المهارات الرقمية",financial:"الثقافة المالية",islamic:"التربية الإسلامية",social:"الدراسات الاجتماعية",professional:"التربية المهنية",history:"التاريخ",geography:"الجغرافيا",physics:"الفيزياء",chemistry:"الكيمياء",biology:"العلوم الحياتية",earth:"علوم الأرض والبيئة",arts:"التربية الفنية"};
const aliases={
 math:["الرياضيات","رياضيات","الرياضيات/الأعمال","math"],
 arabic:["اللغة العربية","عربي","العربيه","اللغة العربيه"],
 english:["اللغة الإنجليزية","اللغة الانجليزية","انجليزي","الإنجليزي","english"],
 science:["العلوم","علوم","science"],
 digital:["المهارات الرقمية","مهارات رقمية","الحاسوب","حاسوب","digital skills","digital"],
 financial:["الثقافة المالية","الثقافه الماليه","ثقافة مالية","financial"],
 islamic:["التربية الإسلامية","التربيه الاسلاميه","دين","اسلامية","تربية إسلامية"],
 social:["الدراسات الاجتماعية","الدراسات الإجتماعية","اجتماعيات","اجتماعية","social studies"],
 professional:["التربية المهنية","مهني","تربية مهنية"],
 history:["التاريخ","تاريخ","تاريخ الأردن"],
 geography:["الجغرافيا","جغرافيا"],
 physics:["الفيزياء","فيزياء"],
 chemistry:["الكيمياء","كيمياء"],
 biology:["العلوم الحياتية","الأحياء","احياء"],
 earth:["علوم الأرض والبيئة","علوم الارض","الأرض والبيئة"],
 arts:["التربية الفنية","الفنون","فنون"]
};
const standardize=v=>String(v||"").toLowerCase().trim().replace(/[أإآ]/g,"ا").replace(/ة/g,"ه").replace(/ى/g,"ي").replace(/[ًٌٍَُِّْ]/g,"").replace(/\s+/g," ");
function subjectKey(raw){
 const value=standardize(raw);
 for(const [key,items] of Object.entries(aliases)){
   if(items.some(item=>standardize(item)===value))return key;
 }
 return "";
}
const subjectName=v=>names[subjectKey(v)]||String(v||"").trim();
const SOURCE="تدريبات إثرائية أصلية؛ تحتاج مراجعة المعلم وفق كتاب الصف والطبعة";
const SOURCE_URL="https://nccd.gov.jo/Ar/Pages/textbooks";
const bank=[];
const signatures=new Set();
function add(key,grade,topic,type,text,options,correct,difficulty="medium"){
 if(!names[key]||!grades.includes(grade))return;
 const signature=[key,grade,type,text].join("|");
 if(signatures.has(signature))return;
 signatures.add(signature);
 const id="jo26_"+key+"_"+String(bank.length+1).padStart(5,"0");
 bank.push({id,subject:names[key],grade,semester:"عام",unit:"تدريبات إثرائية — "+topic,
   topic,lesson:topic,difficulty,type,text,options:options||[],correct,
   time:difficulty==="hard"?35:25,points:difficulty==="hard"?1200:1000,
   tags:["الأردن","إثرائي","مراجعة المعلم",topic],skill:topic,image:"",
   explanation:"راجع تفسير الإجابة مع معلم المادة وكتاب الصف قبل نشر السؤال.",
   source:SOURCE,sourceUrl:SOURCE_URL,reviewStatus:"teacher_review_required",
   curriculum:"الأردني — تدريب إثرائي غير معتمد كتابيًا"});
}
function numeric(key,grade,topic,text,answer,index,difficulty="medium"){
 if(!Number.isSafeInteger(answer))return;
 let distractors=[answer+1,answer-1,answer+2,answer-2,answer+10,answer-10,answer+3]
   .filter(v=>(answer<0||v>=0)&&Number.isSafeInteger(v)&&v!==answer);
 const distinct=[answer,...new Set(distractors)].slice(0,4);
 while(distinct.length<4)distinct.push(answer+distinct.length+7);
 const shift=index%4;
 const options=[...distinct.slice(shift),...distinct.slice(0,shift)].map(String);
 add(key,grade,topic,"single",text,options,[options.indexOf(String(answer))],difficulty);
}
for(let g=1;g<=12;g++){
 const grade=grades[g-1],n=92;
 for(let i=0;i<n;i++){
  const a=2+(i%23),b=2+Math.floor(i/23)*5+(i%3);
  if(g===1){
   const x=1+(i%10),y=1+(Math.floor(i/10)%9);
   numeric("math",grade,"الجمع ضمن 20",`ما ناتج ${x} + ${y}؟`,x+y,i,"easy");
   const z=10+(i%10),w=1+(Math.floor(i/10)%9);
   numeric("math",grade,"الطرح ضمن 20",`ما ناتج ${z} − ${w}؟`,z-w,i+1,"easy");
  }else if(g===2){
   const x=10+(i%60),y=1+(Math.floor(i/6)%25);
   numeric("math",grade,"جمع الأعداد",`احسب ${x} + ${y}.`,x+y,i,"easy");
   numeric("math",grade,"طرح الأعداد",`احسب ${x+y} − ${x}.`,y,i+1,"easy");
  }else if(g===3){
   const x=2+(i%11),y=2+(Math.floor(i/11)%9);
   numeric("math",grade,"الضرب",`احسب حاصل ضرب ${x} × ${y}.`,x*y,i,"easy");
   numeric("math",grade,"القسمة",`ما ناتج ${x*y} ÷ ${x}؟`,y,i+1,"medium");
  }else if(g===4){
   const x=11+(i%45),y=3+(Math.floor(i/9)%11);
   numeric("math",grade,"ضرب الأعداد",`احسب ${x} × ${y}.`,x*y,i,"medium");
   numeric("math",grade,"مساحة المستطيل",`مستطيل طوله ${x} سم وعرضه ${y} سم؛ ما مساحته بالسم المربع؟`,x*y,i+1);
  }else if(g===5){
   const x=10+(i%75),y=2+(Math.floor(i/11)%15);
   numeric("math",grade,"الأعشار",`إذا جمعنا ${x} عشرًا و${y} عشرًا، فكم عشرًا نحصل؟`,x+y,i,"medium");
   numeric("math",grade,"العمليات الحسابية",`احسب ${x} × ${y}.`,x*y,i+1);
  }else if(g===6){
   const x=12+(i%65),y=2+(Math.floor(i/10)%14);
   numeric("math",grade,"النسبة والتناسب",`إذا كان ثمن القطعة ${y} دنانير، فما ثمن ${x} قطعة بالسعر نفسه؟`,x*y,i);
   numeric("math",grade,"النسب المئوية",`ما قيمة 10% من ${x*10}؟`,x,i+1);
  }else if(g===7){
   const x=12+(i%68),y=2+(Math.floor(i/10)%10);
   numeric("math",grade,"الأعداد الصحيحة",`احسب (${x}) − (${x+y}).`,0-y,i,"medium");
   numeric("math",grade,"معادلات من خطوة واحدة",`إذا كان س + ${y} = ${x+y}، فما قيمة س؟`,x,i+1);
  }else if(g===8){
   const x=5+(i%80),y=2+(Math.floor(i/10)%10);
   numeric("math",grade,"المعادلات الخطية",`حل المعادلة: ${y}س + ${x} = ${y*5+x}.`,5,i,"medium");
   numeric("math",grade,"الأسس",`احسب ${y}² + ${x}.`,y*y+x,i+1);
  }else if(g===9){
   const x=3+(i%80),y=2+(Math.floor(i/10)%10);
   numeric("math",grade,"الدوال",`إذا كانت د(س) = ${y}س + ${x}، فما د(4)؟`,y*4+x,i);
   numeric("math",grade,"مساحة المثلث",`مثلث قاعدته ${x*2} سم وارتفاعه ${y} سم؛ ما مساحته بالسم المربع؟`,x*y,i+1);
  }else{
   const x=2+(i%78),y=1+(Math.floor(i/10)%12);
   numeric("math",grade,"التعويض في الدوال",`إذا كانت د(س)=س² + ${y}س + ${x}، أوجد د(3).`,9+y*3+x,i);
   numeric("math",grade,"المعادلات الخطية مراجعة",`حل: ${y}س + ${x} = ${x+y*7}.`,7,i+1);
  }
 }
}
// Financial reasoning and numeracy: 2 original scenarios per parameter set.
for(let g=7;g<=10;g++){
 const grade=grades[g-1];
 for(let i=0;i<120;i++){
  const amount=100+(i%30)*10,spent=10+Math.floor(i/30)*15+(i%7);
  numeric("financial",grade,"الميزانية الشخصية",
   `يمتلك طالب ${amount} دينارًا، وأنفق ${spent} دينارًا على احتياجاته. كم دينارًا تبقى له؟`,
   amount-spent,i,"medium");
  const savings=2+(i%26),weeks=2+Math.floor(i/26);
  numeric("financial",grade,"الادخار والتخطيط",
   `يوفر طالب ${savings} دنانير كل أسبوع لمدة ${weeks} أسابيع. ما مجموع ما ادخره؟`,
   savings*weeks,i+1,"medium");
 }
}
// Extra applied science numeracy for upper basic grades (general practice).
for(let g=7;g<=10;g++){
 const grade=grades[g-1];
 for(let i=0;i<72;i++){
  const speed=2+(i%24),hours=1+Math.floor(i/24);
  numeric("science",grade,"المسافة والسرعة",
   `جسم يتحرك بسرعة ثابتة ${speed} كم/ساعة لمدة ${hours} ساعات. ما المسافة التي يقطعها بالكيلومترات؟`,
   speed*hours,i,"medium");
 }
}
// Original general knowledge questions. All are marked supplementary, not official textbook excerpts.
const facts=[
 ["science","الخلايا","ما الوحدة الأساسية لبناء أجسام الكائنات الحية؟","الخلية",["الضوء","الصوت","الهواء"]],
 ["science","الطاقة","ما مصدر الطاقة الأساسي للأرض؟","الشمس",["القمر","النجوم القريبة فقط","الرياح فقط"]],
 ["science","المادة","ما حالة الماء عند تجمده؟","صلبة",["غازية","بلازما","سائلة"]],
 ["science","المادة","ماذا نسمي انتقال الماء السائل إلى بخار؟","التبخر",["التكاثف","الانصهار","التجمد"]],
 ["science","المادة","ماذا نسمي تحول البخار إلى قطرات ماء؟","التكاثف",["التبخر","الترشيح","الذوبان"]],
 ["science","النباتات","ما العضو الذي يمتص الماء من التربة في النبات؟","الجذر",["الزهرة","الثمرة","الورقة"]],
 ["science","الحواس","ما العضو المسؤول عن حاسة السمع؟","الأذن",["اللسان","العين","الأنف"]],
 ["science","القوى","ما القوة التي تجذب الأجسام نحو الأرض؟","الجاذبية",["الاحتكاك فقط","الطفو فقط","المغناطيسية دائمًا"]],
 ["science","الضوء","كيف ينتقل الضوء في وسط متجانس شفاف؟","في خطوط مستقيمة",["في دوائر دائمًا","لا ينتقل","في خطوط متكسرة دائمًا"]],
 ["science","الجهاز التنفسي","ما العضو الذي يساعد على تبادل الأكسجين وثاني أكسيد الكربون؟","الرئتان",["المعدة","الكبد","الكليتان"]],
 ["science","الدوائر الكهربائية","ماذا يحدث عند فتح دائرة كهربائية بسيطة؟","يتوقف مرور التيار",["يزداد التيار بلا حدود","يتولد تيار جديد","تصبح البطارية أكبر"]],
 ["science","الصوت","بماذا ينتج الصوت؟","اهتزاز الأجسام",["اللون وحده","الظل وحده","الثبات المطلق"]],
 ["science","الصحة","ما السلوك الذي يساعد على منع انتقال كثير من الميكروبات؟","غسل اليدين بالماء والصابون",["عدم تنظيف الأسطح","مشاركة الأدوات الشخصية","ترك الجروح مكشوفة"]],
 ["science","الكواكب","ما الكوكب الذي نعيش عليه؟","الأرض",["المريخ","الزهرة","المشتري"]],
 ["science","التغيرات الفيزيائية","أي مما يأتي تغير فيزيائي؟","انصهار الثلج",["احتراق الخشب","صدأ الحديد","تعفن الطعام"]],
 ["science","الأنظمة البيئية","ما اسم الكائن الذي يصنع غذاءه بنفسه؟","المنتِج",["المستهلك الأول دائمًا","المحلل فقط","المفترس"]],
 ["financial","الادخار","ما المقصود بالادخار؟","تخصيص جزء من المال للمستقبل",["إنفاق كل المال فورًا","الاقتراض دون خطة","تجاهل المصروفات"]],
 ["financial","الميزانية","ما فائدة إعداد ميزانية شخصية؟","تنظيم الدخل والمصروفات",["زيادة المال تلقائيًا","منع الشراء نهائيًا","ضمان عدم تغير الأسعار"]],
 ["financial","الاحتياجات والرغبات","أي مما يأتي مثال واضح على حاجة أساسية؟","مياه الشرب",["لعبة جديدة","إكسسوار للزينة","حلوى إضافية"]],
 ["financial","الأمان المالي","ما التصرف الأفضل لحماية الرقم السري للبطاقة؟","عدم مشاركته مع الآخرين",["إرساله في مجموعة عامة","كتابته على البطاقة","نشره على الإنترنت"]],
 ["financial","الشراء الواعي","ماذا تفعل قبل شراء منتج بسعر مرتفع؟","تقارن السعر بالجودة والحاجة",["تشتري دون سؤال","تهمل ميزانيتك","تعتمد على الإعلان وحده"]],
 ["financial","الديون","لماذا يجب التفكير قبل الاقتراض؟","لأن القرض يستلزم السداد وفق الشروط",["لأن القرض هدية دائمًا","لأنه لا توجد التزامات","لأن جميع القروض بلا تكلفة"]],
 ["financial","المخاطر","ما المقصود بصندوق الطوارئ؟","مال مخصص للنفقات غير المتوقعة",["مال لتزيين الغرفة","مال لإعلانات المتاجر","مال لاستخدامه مرة كل يوم"]],
 ["financial","العمل","ما مفهوم الدخل؟","المال الذي يحصل عليه الفرد من مصادره",["المال الذي أنفقه فقط","قائمة أسعار المتجر","الضريبة وحدها"]],
 ["financial","التخطيط","لماذا تحدد هدفًا ماليًا واضحًا؟","لتوجه قرارات الادخار والإنفاق",["لتنفق بلا حساب","لتفقد القدرة على المقارنة","لتزيد الديون دائمًا"]],
 ["social","الجغرافيا الأردنية","ما عاصمة المملكة الأردنية الهاشمية؟","عمّان",["إربد","العقبة","الكرك"]],
 ["social","الجغرافيا الأردنية","أي مدينة أردنية تقع على ساحل البحر الأحمر؟","العقبة",["السلط","عجلون","المفرق"]],
 ["social","الجغرافيا الأردنية","ما اسم البحر الذي تقع قربه مدينة العقبة؟","البحر الأحمر",["البحر الأسود","بحر قزوين","بحر البلطيق"]],
 ["social","المواطنة","أي سلوك يمثل المحافظة على الممتلكات العامة؟","استخدامها بعناية",["إتلافها","الكتابة على جدرانها","إهمال نظافتها"]],
 ["social","المواطنة","ماذا يحقق احترام القوانين داخل المدرسة؟","تنظيم الحقوق والواجبات",["إلغاء التعاون","منع التعلم","زيادة الفوضى"]],
 ["social","البيئة","ما التصرف الذي يقلل النفايات؟","إعادة استخدام ما يصلح",["رمي الورق في الشارع","إهدار الموارد","شراء غير الضروري دائمًا"]],
 ["islamic","الأخلاق","أي قيمة تعني قول الحق وتجنب الكذب؟","الصدق",["الرياء","الغش","الظلم"]],
 ["islamic","الأخلاق","ما السلوك الذي يدل على الأمانة؟","إعادة ما اؤتمنت عليه إلى صاحبه",["إخفاء حق الآخرين","أخذ ما ليس لك","الغش"]],
 ["islamic","العبادات","كم عدد الصلوات المفروضة في اليوم والليلة؟","خمس",["ثلاث","أربع","ست"]],
 ["islamic","الأخلاق","كيف يُظهر الطالب احترام والديه؟","بالقول الحسن والتعاون معهما",["بالإساءة إليهما","برفع الصوت عليهما","بتجاهل حقوقهما"]],
 ["islamic","القرآن الكريم","ما اسم الكتاب المنزل على النبي محمد صلى الله عليه وسلم؟","القرآن الكريم",["التوراة","الإنجيل","الزبور"]],
 ["islamic","السيرة","في أي مدينة وُلد النبي محمد صلى الله عليه وسلم؟","مكة المكرمة",["المدينة المنورة","القدس","الطائف"]],
 ["professional","السلامة المهنية","ما التصرف الصحيح قبل إصلاح جهاز كهربائي؟","فصل مصدر الكهرباء وفق تعليمات السلامة",["لمس الأسلاك المكشوفة","سكب الماء","العمل دون إرشاد"]],
 ["professional","التخطيط","ما فائدة قائمة الأدوات قبل بدء مشروع عملي؟","التأكد من توافر الاحتياجات",["تضييع المواد","زيادة الأخطاء عمدًا","إلغاء ترتيب الخطوات"]]
];
for(const [key,topic,text,correct,wrong] of facts){
 const applicable=key==="science"?grades.slice(3,10):key==="financial"?grades.slice(6,10):key==="professional"?grades.slice(4,10):key==="social"?grades.slice(3,10):grades.slice(2,10);
 for(const grade of applicable){
  const options=[correct,...wrong];
  const shift=(grades.indexOf(grade)+text.length)%4;
  const shuffled=options.slice(shift).concat(options.slice(0,shift));
  add(key,grade,topic,"single",text,shuffled,[shuffled.indexOf(correct)],"easy");
 }
}
const ENGLISH=[
 ["apple","تفاحة"],["book","كتاب"],["teacher","معلم"],["student","طالب"],["school","مدرسة"],["window","نافذة"],["door","باب"],["table","طاولة"],["chair","كرسي"],["family","أسرة"],["friend","صديق"],["water","ماء"],["garden","حديقة"],["library","مكتبة"],["doctor","طبيب"],["hospital","مستشفى"],["computer","حاسوب"],["keyboard","لوحة مفاتيح"],["mountain","جبل"],["river","نهر"],["travel","يسافر"],["learn","يتعلم"],["protect","يحمي"],["discover","يكتشف"],["environment","بيئة"],["important","مهم"],["healthy","صحي"],["careful","حذر"],["possible","ممكن"],["different","مختلف"],["prepare","يحضّر"],["improve","يحسّن"],["compare","يقارن"],["explain","يشرح"],["culture","ثقافة"],["knowledge","معرفة"],["solution","حل"],["research","بحث"],["community","مجتمع"],["responsible","مسؤول"]
];
for(let g=1;g<=10;g++){
 const grade=grades[g-1], start=g<=3?0:g<=6?8:18;
 const words=ENGLISH.slice(start,start+22);
 words.forEach(([english,arabic],i)=>{
  const distractors=[1,3,7].map(n=>words[(i+n)%words.length][1]);
  const opts=[arabic,...distractors],shift=(g+i)%4,ordered=opts.slice(shift).concat(opts.slice(0,shift));
  add("english",grade,"Vocabulary","single",`Choose the Arabic meaning of: ${english}`,ordered,[ordered.indexOf(arabic)],g<=3?"easy":"medium");
  const otherWords=[1,3,7].map(n=>words[(i+n)%words.length][0]),enOpts=[english,...otherWords],nshift=(g+i+2)%4;
  const enAnswers=enOpts.slice(nshift).concat(enOpts.slice(0,nshift));
  add("english",grade,"Vocabulary","single",`Choose the English word for: ${arabic}`,enAnswers,[enAnswers.indexOf(english)],g<=3?"easy":"medium");
 });
}
const ARABIC_NOUNS=["مدرسة","كتاب","حديقة","معلم","نافذة","طالب","مدينة","قلم","صديق","جبل","نهر","طريق","شجرة","منزل","علم","طائرة","زهرة","حقيبة","كرة","حاسوب"];
const ARABIC_VERBS=["يقرأ","يكتب","يشرب","ينطلق","يسافر","يشرح","يستمع","يتعلم","يتعاون","يبتسم","جلس","ذهب","رسم","فهم","وصل","عاد","أنجز","نظّم","رتّب","ساعد"];
const ARABIC_HARF=["من","إلى","على","في","عن","حتى","هل","لم","لن","بـ"];
for(let g=1;g<=10;g++){
 const grade=grades[g-1];
 ARABIC_NOUNS.forEach((word,i)=>add("arabic",grade,"أنواع الكلمة","single",`ما نوع الكلمة «${word}» في الاستعمال المعتاد؟`,["فعل","اسم","حرف","جملة"],[1],g<=3?"easy":"medium"));
 if(g>=3){
  ARABIC_VERBS.forEach((word,i)=>add("arabic",grade,"أنواع الكلمة","single",`اختر نوع الكلمة «${word}».`,["اسم","حرف","فعل","جملة"],[2]));
  ARABIC_HARF.forEach((word,i)=>add("arabic",grade,"أنواع الكلمة","single",`إلى أي نوع تنتمي الكلمة «${word}» في استعمالها حرفًا؟`,["حرف","اسم","فعل","صفة"],[0],"easy"));
 }
}
function forTeacher(raw){
 const key=subjectKey(raw);
 if(!key)return [];
 return bank.filter(q=>subjectKey(q.subject)===key);
}
root.TAG_JORDAN_CURRICULUM_V1=Object.freeze({
 grades:Object.freeze(grades), subjects:Object.freeze(names), canonicalSubject:subjectName,
 subjectKey, sourceUrl:SOURCE_URL, questionsForTeacher:forTeacher,
 stats:()=>Object.freeze({total:bank.length,bySubject:Object.fromEntries(Object.keys(names).map(k=>[names[k],bank.filter(q=>subjectKey(q.subject)===k).length]))}),
 all:bank
});
})(window);
