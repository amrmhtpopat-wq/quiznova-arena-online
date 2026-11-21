/* Original TeachGame semester one: subject-specific problem builders, 2026/27.
   Supplementary ORIGINAL practice, not official copied examination questions.
   Teacher review is required before student publication. */
(function(root){
"use strict";
var C=root.TAG_SEMESTER1_CATALOG_V2,base=root.TAG_SEMESTER1_PACKS_V2;
if(!C||!base) return;
function gcd(a,b){a=Math.abs(a);b=Math.abs(b);while(b){var t=a%b;a=b;b=t}return a||1}
function frac(a,b){if(b<0){a=-a;b=-b}var g=gcd(a,b);return b/g===1?String(a/g):(a/g)+"/"+(b/g)}
function make(l,n,stem,answer,wrong){
 var a=String(answer),opts=[a],candidates=(wrong||[]).map(String);
 if(typeof answer==="number"&&isFinite(answer)){
  [answer+1,answer-1,answer+2,answer-2,answer+3,answer+5].forEach(function(v){candidates.push(String(v))});
 }
 for(var j=0;j<candidates.length&&opts.length<4;j++)if(candidates[j]!==a&&!opts.includes(candidates[j]))opts.push(candidates[j]);
 if(opts.length!==4||!stem)throw Error("Options "+l.id+" "+n+" "+stem);
 var offset=(n*3+l.lessonIndex)%4;opts=opts.slice(offset).concat(opts.slice(0,offset));
 return {id:"tag-s1-"+l.id+"-"+String(n+1).padStart(2,"0"),subject:l.subject,grade:l.grade,
 semester:"1",unit:l.unit,lesson:l.lesson,topic:l.lesson,type:"single",
 text:stem,options:opts,correct:[opts.indexOf(a)],
 difficulty:n<10?"easy":n<22?"medium":"hard",time:n<22?30:40,points:n<22?1000:1200,
 image:"",tags:["الفصل الأول",l.lesson,"مراجعة المعلم"],skill:l.lesson,
 source:"تدريبات إثرائية أصلية مستندة إلى موضوع الدرس، تحتاج مطابقة ومراجعة من معلم المادة",
 reviewStatus:"teacher_review_required",explanation:"الإجابة الصحيحة: "+a};
}
function numeric(l,n,stem,ans,step){step=step||1;return make(l,n,stem,ans,[ans+step,ans-step,ans+step*2,ans-step*2])}
function expr(l,n,stem,ans,wrong){return make(l,n,stem,ans,wrong)}
function mode(l){
 var [_,g,u,k]=l.id.split("-").map((x,i)=>i?Number(x):x);
 var m={
 "0-1":"abs,intcompare,intsum,intsub,intprod",
 "0-2":"fracsum,mixedsum,mixedprod,fracdiv,mixeddiv",
 "0-3":"decprod,decdiv,measurement,smaller",
 "0-4":"coord,translate,reflect,circleparts,construction,drawtriangle",
 
 "1-1":"rational,decimal,fraccompare,fracsum,fracprod,reverse",
 "1-2":"exponent,order,algebra,addexpr,monomial,guess",
 "1-3":"linear,fracperiod,seq,linearfunc,lineargraph",
 "1-4":"angles,parallel,triangle,polygon,rotate",
 "2-1":"roots,radicals,pythagoras,real,radicalexponent,radicalmul,scientific,percent",
 "2-2":"specialproduct,factor,quadraticfactor,diffsquare,fracexpr",
 "2-3":"standardline,linearprops,linereq,pointslop,perpendicular",
 "2-4":"congruenceSSS,congruenceASA,isosceles",
 "3-1":"diffsquare,quadraticfactor,sumcubes,diffcubes,gcd,lcm,fracexpr,fraceq",
 "3-2":"interval,ineqprop,linearineq,compoundineq",
 "3-3":"quadgraph,graphroots,graphroots,quadraticfactor,completing,quadraticformula",
 "3-4":"counting,sample,event,probability",
 "4-1":"linequad,twosquares,exponent,exponential",
 "4-2":"chord,sector,circleangles,circleeq,tangentcircle",
 "4-3":"trig,trigcycle,triggraph,trigeq",
 "4-4":"bearing,sineLaw,cosLaw,trianglearea,spatial"
 };
 var modes=m[g+"-"+u];return modes?modes.split(",")[k-1]:null;
}
function question(l,n){
 var m=mode(l),a=2+n,b=3+n%8,c=2+n%9,x=1+n%11;
 var f=function(s,ans,wr){return make(l,n,s,ans,wr)},v=function(s,ans,step){return numeric(l,n,s,ans,step)};
 var v1=n+2,v2=3+n%8;
 switch(m){
 case "intcompare":return f("قارن بين العددين الصحيحين −"+a+" و −"+(a+b)+"؛ أيهما أكبر؟","−"+a,["−"+(a+b),String(a),"−"+(a+1),String(a+b)]);
 case "intsum":return v("احسب: (−"+a+") + "+b+" .",b-a);
 case "intsub":return v("احسب: "+a+" − (−"+b+").",a+b);
 case "intprod":return v("احسب: (−"+a+") × (−"+b+").",a*b,b);
 case "mixedsum":return v("احسب: ("+a+" + 1/3) + ("+b+" + 2/3)؛ ما الناتج كعدد صحيح؟",a+b+1);
 case "mixedprod":return v("اضرب العدد الكسري ("+a+" + 1/2) في 2؛ ما الناتج؟",2*a+1);
 case "mixeddiv":return v("اقسم العدد الكسري ("+a+" + 1/2) على 1/2؛ ما الناتج؟",2*a+1);
 case "decdiv":{var d=(a*b/100);return v("احسب: "+d.toFixed(2)+" ÷ "+(b/10).toFixed(1)+" .",a/10,0.1)}
 case "measurement":return v("طول حبل "+(a/10).toFixed(1)+" متر؛ ما طوله بالسنتيمترات؟",10*a,10);
 case "smaller":return v("قسّم "+(a*b)+" قطعة بالتساوي على "+a+" مجموعات؛ كم قطعة في كل مجموعة؟",b);
 case "reflect":return f("انعكاس النقطة ("+a+"، "+b+") في محور y يعطي أي إحداثيين؟","(−"+a+"، "+b+")",["("+a+"، −"+b+")","(−"+b+"، "+a+")","("+a+"، "+b+")","("+b+"، −"+a+")"]);
 case "circleparts":return v("دائرة نصف قطرها "+a+" سم. ما طول قطرها بالسنتيمتر؟",2*a,2);
 case "construction":return v("عند إنشاء العمود المنصف لقطعة طولها "+(2*a)+" سم، ما طول كل نصف من القطعة؟",a);
 case "drawtriangle":return v("ارسم مثلثًا أطوال أضلاعه "+a+" سم و "+(a+1)+" سم و "+(a+2)+" سم. ما محيطه؟",3*a+3,3);
 case "radicals":return f("بسّط الجذر الصمّاء √("+(2*a*a)+").",a+"√2",[(a+1)+"√2",a+"√3",(2*a)+"√2",a+"√4"]);
 case "pythagoras":return v("مثلث قائم ضلعاه القائمان "+(3*a)+" و "+(4*a)+" سم. ما طول الوتر؟",5*a,a);
 case "radicalexponent":return v("إذا كان a موجبًا وقيمته "+a+"، ما قيمة (a²)^(1/2)؟",a);
 case "radicalmul":return v("ما قيمة "+a+"^(1/2) × "+a+"^(1/2) للأعداد الموجبة؟",a);
 case "specialproduct":return f("انشر مربع المقدار (x + "+a+")².","x² + "+2*a+"x + "+a*a,["x² + "+a+"x + "+a*a,"x² − "+2*a+"x + "+a*a,"x² + "+2*a+"x − "+a*a,"x² + "+a*a]);
 case "standardline":return v("المستقيم "+a+"x + "+b+"y = "+(b*c)+". ما المقطع الصادي عندما x=0؟",c);
 case "linereq":return f("ما معادلة مستقيم ميله "+a+" ومقطعه الصادي "+b+"؟","y = "+a+"x + "+b,["y = "+b+"x + "+a,"y = "+a+"x − "+b,"y = −"+a+"x + "+b,"x = "+a+"y + "+b]);
 case "pointslop":return f("يمر مستقيم بالنقطة (0، "+b+") وميله "+a+". ما معادلته؟","y = "+a+"x + "+b,["y = "+b+"x + "+a,"y = "+a+"x − "+b,"y = "+(a+1)+"x + "+b,"y = −"+a+"x + "+b]);
 case "perpendicular":return f("ما ميل مستقيم عمودي على مستقيم ميله "+a+"؟","−1/"+a,["1/"+a,"−"+a,String(a),"1/"+(a+1)]);
 case "congruenceSSS":return f("مثلث أول أطوال أضلاعه "+a+" و "+(a+1)+" و "+(a+2)+" سم، ومثلث آخر له الأطوال نفسها. ما قاعدة التطابق المناسبة؟","SSS",["ASA","AAS","AA","لا يوجد تطابق"]);
 case "congruenceASA":return f("تساوت زاويتان في مثلثين (إحداهما "+(30+n)+"°) والضلع المحصور بينهما. أي حالة تثبت التطابق؟","ASA",["SSS","AA","SSA","لا توجد حالة"]);
 case "isosceles":return v("مثلث متطابق الضلعين زاوية رأسه "+(20+2*n)+"°. ما قياس كل زاوية من زاويتي القاعدة؟",80-n);
 case "decimalplace": {var d=1+n%9,t=String(n+12)+"."+String(1000+d);return f("في العدد العشري "+t+" ما قيمة رقم منزلة جزء من عشرة آلاف؟",frac(d,10000),[frac(d,1000),frac(d,100),frac(d,10),"1/10000"])}
 case "deccompare": {var t=(n+5)/100,h=(n+6+(n%2?4:-4))/100,ans=t>h?"العدد الأول أكبر":"العدد الثاني أكبر";return f("قارن: "+t.toFixed(2)+" و "+h.toFixed(2)+"؛ أي عبارة صحيحة؟",ans,["العدد الأول أكبر","العدد الثاني أكبر","العددان متساويان","المقارنة غير ممكنة"])}
 case "percent":return f("حوّل الكسر "+a+"/100 إلى نسبة مئوية.",a+"%",[(a+1)+"%",(a*10)+"%",(a/10)+"%"]);
 case "fraccompare": {var first=n%2?a+4:a,second=n%2?a:a+4;return f("أي مقارنة صحيحة بين "+first+"/"+b+" و "+second+"/"+b+"؟",first>second?"الكسر الأول أكبر":"الكسر الثاني أكبر",["الكسر الأول أكبر","الكسر الثاني أكبر","الكسران متساويان","لا يمكن المقارنة"])}
 case "decprod": {var z=a*b/100;return v("احسب "+(a/10).toFixed(1)+" × "+(b/10).toFixed(1)+" = ؟",z,0.1)}
 case "estimate": {var r=10*a,t=10*b;return v("قدّر حاصل ضرب "+(r+2)+" × "+(t+3)+" بتقريب كل عامل لأقرب عشرة.",r*t,10)}
 case "fracprod":return f("احسب حاصل ضرب "+a+"/"+(b+2)+" × "+b+"/"+(a+3)+" في أبسط صورة.",frac(a*b,(b+2)*(a+3)),[frac(a+b,(b+2)*(a+3)),frac(a*b,(b+1)*(a+3)),frac(a*b+1,(b+2)*(a+3)),frac(a*b,(b+2)*(a+2))]);
 case "fracdiv":return f("احسب "+a+"/"+(b+2)+" ÷ "+b+"/"+(a+3)+" في أبسط صورة.",frac(a*(a+3),b*(b+2)),[frac(a*b,(b+2)*(a+3)),frac(a*(a+3),b*(b+3)),frac(a*b+1,(b+2)*(a+3)),frac(a*(a+2),b*(b+2))]);
 case "coord":return v("نقطة إحداثياها ("+a+"، "+b+"). إذا انسحبت أفقيًا "+(n+1)+" وحدة نحو اليمين، فما إحداثي x الجديد؟",a+n+1);
 case "algebra":return v("إذا كان x="+x+"، فما قيمة التعبير "+a+"x + "+b+"؟",a*x+b,a);
 case "relation":return v("العلاقة y = "+a+"x + "+b+". ما قيمة y عندما x="+x+"؟",a*x+b,a);
 case "equality":return v("إذا كان x + "+a+" = "+(a+b)+"، فما قيمة x التي تحفظ المساواة؟",b);
 case "wordexpr":return f("ما التعبير الجبري لعبارة «"+a+" أمثال x مضاف إليها "+b+"»؟",a+"x + "+b,[a+"x − "+b,b+"x + "+a,a+" + "+b+"x",a+"x × "+b]);
 case "linear":return v("حل المعادلة "+a+"x + "+b+" = "+(a*x+b)+"؛ أوجد x.",x);
 case "linearfunc":return v("إذا كان f(x) = "+a+"x + "+b+"، فأوجد f("+(n+3)+").",a*(n+3)+b,a);
 case "lineargraph":return v("رسم Linear Function: f(x) = "+a+"x + "+b+"؛ ما الإحداثي الصادي عند x="+(n+3)+"؟",a*(n+3)+b,a);
 case "rational":return f("أي كسر يمثل العدد النسبي "+a+" مقسومًا على "+b+"؟",a+"/"+b,[b+"/"+a,a+"/"+(b+1),(a+1)+"/"+b,(a+b)+"/"+b]);
 case "abs":return v("ما القيمة المطلقة للعدد −"+a+"؟",a);
 case "decimal":return f("حوّل العدد الكسري "+a+"/100 إلى عدد عشري.",(a/100).toFixed(2),[(a/10).toFixed(1),(a/1000).toFixed(3),(a+1)/100,(a/10).toFixed(2)]);
 case "fracsum":return f("احسب "+a+"/"+(b+4)+" + "+b+"/"+(b+4)+" في أبسط صورة.",frac(a+b,b+4),[frac(a-b,b+4),frac(a*b,b+4),frac(a+b,b+5),frac(a+b+1,b+4)]);
 case "reverse":return v("فكرت في عدد، ضاعفته ثم أضفت "+b+" فكان الناتج "+(2*a+b)+". ما العدد الأصلي؟",a);
 case "exponent":return v("ما قيمة "+(2+n%5)+"^"+(2+Math.floor(n/5))+"؟",(2+n%5)**(2+Math.floor(n/5)%5),2);
 case "order":return v("احسب بحسب أولويات العمليات: "+a+" + "+b+" × "+c+" .",a+b*c,b);
 case "addexpr":{var p=a+c,q=b+x;return f("بسّط: ("+a+"x + "+b+") + ("+c+"x + "+x+").",p+"x + "+q,[p+"x − "+q,(a*c)+"x + "+q,q+"x + "+(p+1),p+"x + "+(q+2),p+"x − "+(q+1)])}
 case "monomial":return f("وزّع الحد "+a+"x على ("+b+"x + "+c+").",(a*b)+"x² + "+(a*c)+"x",[(a+b)+"x² + "+(a*c)+"x",(a*b)+"x² + "+c+"x",(a*b)+"x + "+(a*c),(a*b)+"x² − "+(a*c)+"x"]);
 case "guess":return v("باستخدام التخمين والتحقق: ما العدد الذي إذا ضُرب في "+b+" ثم أضيف "+c+" أصبح "+(a*b+c)+"؟",a);
 case "fracperiod":return f("ما الكتابة العشرية الدورية للكسر "+(3*n+1)+"/3 ؟",n+".333…",[n+".666…",n+".5",n+".25",(n+1)+".333…"]);
 case "seq":return v("المتتالية الحسابية: "+a+"، "+(a+b)+"، "+(a+2*b)+"... ما الحد الخامس؟",a+4*b,b);
 case "angles":return v("زاويتان متكاملتان، قياس الأولى "+(20+n)+"°. ما قياس الثانية بالدرجات؟",160-n);
 case "parallel":return v("قاطع لمستقيمين متوازيين كوّن زاوية "+(20+n)+"°. ما قياس الزاوية المتناظرة معها؟",20+n);
 case "triangle":return v("مثلث قياس زاويتين فيه "+(20+n)+"° و "+(40+n)+"°. ما قياس الزاوية الثالثة؟",120-2*n);
 case "polygon":return v("ما مجموع قياسات الزوايا الداخلية لمضلع له "+(3+n)+" أضلاع (بالدرجات)؟",(n+1)*180,180);
 case "translate":return v("انسحبت النقطة ("+a+"، "+b+") نحو الأعلى "+c+" وحدات. ما الإحداثي الصادي الجديد؟",b+c);
 case "rotate":return f("ما صورة النقطة ("+a+"، "+b+") بدوران 90° عكس عقارب الساعة حول الأصل؟","(−"+b+"، "+a+")",["("+b+"، −"+a+")","("+a+"، −"+b+")","(−"+a+"، "+b+")","("+b+"، "+a+")"]);
 case "real":return v("ما الجذر التربيعي الرئيسي للعدد "+a*a+" ضمن الأعداد الحقيقية؟",a);
 case "properties":return v("باستخدام خاصية التوزيع، ما قيمة "+a+"("+b+" + "+c+")؟",a*(b+c),a);
 case "scientific":{var coefficient=a<10?a:a/10,power=a<10?4:5;return f("اكتب العدد "+a*10000+" بالصيغة العلمية القياسية.",coefficient+" × 10^"+power,[coefficient+" × 10^"+(power+1),coefficient+" × 10^"+(power-1),(coefficient+1)+" × 10^"+power,(coefficient/10)+" × 10^"+power])}
 case "roots":return v("بسّط الجذر التربيعي √("+(9*a*a)+") إلى عدد صحيح.",3*a,3);
 case "polyprod":return f("ما ناتج ضرب (x + "+a+")(x + "+b+") ؟","x² + "+(a+b)+"x + "+(a*b),["x² + "+(a*b)+"x + "+(a+b),"x² − "+(a+b)+"x + "+(a*b),"x² + "+(a+b)+"x − "+(a*b),"(x + "+(a+b)+")²"]);
 case "factor":return f("حلّل بإخراج عامل مشترك: "+(a*b)+"x + "+(a*c)+".",a+"("+b+"x + "+c+")",[b+"("+a+"x + "+c+")",a+"("+b+"x − "+c+")",a+"("+c+"x + "+b+")",a+"x("+b+" + "+c+")"]);
 case "group":return f("حلّل بالتجميع: "+a+"x + "+(a*b)+" + "+c+"x + "+(c*b)+".","("+(a+c)+")(x + "+b+")",["("+(a+c)+")(x − "+b+")","("+(a*b+c)+")(x + "+b+")",a+"(x + "+b+")",c+"(x + "+b+")"]);
 case "linearprops":return v("ما ميل Linear Function المعطى: f(x) = "+a+"x + "+b+"؟",a);
 case "mean":return v("ما المتوسط الحسابي للقيم "+a+"، "+(a+b)+"، "+(a+2*b)+"؟",a+b,b);
 case "median":return v("أوجد الوسيط للقيم المرتبة: "+a+"، "+(a+b)+"، "+(a+b+1)+"، "+(a+b+4)+"، "+(a+b+6)+".",a+b,b);
 case "modevalue":return v("ما المنوال للبيانات "+a+"، "+b+"، "+a+"، "+(b+3)+"، "+a+"؟",a);
 case "statsrel":return v("في مجموعة البيانات "+a+"، "+(a+3*b)+"، "+(a+9*b)+"، ما مقدار زيادة المتوسط الحسابي على الوسيط؟",b);
 case "statschange":return v("كان متوسط ثلاثة أعداد "+a+". إذا زادت كل قيمة بمقدار "+b+"، فما المتوسط الجديد؟",a+b);
 case "diffsquare":return f("حلّل فرق مربعين: x² − "+a*a+".","(x − "+a+")(x + "+a+")",["(x − "+a+")²","(x + "+a+")²","(x − "+(a*a)+")(x + 1)","(x − "+a+")(x − "+a+")"]);
 case "quadraticfactor":return f("ما تحليل x² + "+(a+b)+"x + "+a*b+" ؟","(x + "+a+")(x + "+b+")",["(x − "+a+")(x − "+b+")","(x + "+a+")(x − "+b+")","(x + "+(a+b)+")(x + 1)","(x − "+a+")(x + "+b+")"]);
 case "sumcubes":return f("حلّل مجموع المكعبين x³ + "+a**3+".","(x + "+a+")(x² − "+a+"x + "+a*a+")",["(x + "+a+")(x² + "+a+"x + "+a*a+")","(x − "+a+")(x² + "+a+"x + "+a*a+")","(x + "+a+")(x² − "+a+"x − "+a*a+")"]);
 case "diffcubes":return f("حلّل فرق المكعبين x³ − "+a**3+".","(x − "+a+")(x² + "+a+"x + "+a*a+")",["(x − "+a+")(x² − "+a+"x + "+a*a+")","(x + "+a+")(x² + "+a+"x + "+a*a+")","(x − "+a+")(x² + "+a+"x − "+a*a+")"]);
 case "gcd":{var p=2+n,q=3+n%7;return v("ما العامل المشترك الأكبر للعددين "+(p*q)+" و "+(p*(q+1))+"؟",p)}
 case "lcm":{var p=2+n,q=3+n%7;return v("ما المضاعف المشترك الأصغر للعددين "+p+" و "+(p*q)+"؟",p*q,p)}
 case "fracexpr":return f("بسّط المقدار الجبري "+(a*b)+"x/"+(a*c)+"، حيث المقام لا يساوي صفر.",frac(b,c)+"x",[frac(c,b)+"x",frac(a*b,a*c+1)+"x",(b+c)+"x",frac(b,c+1)+"x"]);
 case "fraceq":return v("حل المعادلة الكسرية x/"+a+" = "+b+" .",a*b,a);
 case "interval":return f("أي فترة تمثل حل المتباينة x ≥ "+a+"؟","["+a+", ∞)",["("+a+", ∞)","(−∞, "+a+"]","(−∞, "+a+")","["+a+", "+(a+1)+"]"]);
 case "ineqprop":return f("إذا كان x < −"+a+"، فماذا ينتج عن ضرب الطرفين بـ −1؟","−x > "+a,["−x < "+a,"−x = "+a,"−x ≥ "+a,"x > "+a]);
 case "linearineq":return f("حل المتباينة x + "+b+" < "+(a+b)+" .","x < "+a,["x > "+a,"x ≤ "+a,"x < "+(a+b),"x ≥ "+a]);
 case "compoundineq":return f("ما الفترة التي تحقق "+a+" < x < "+(a+b)+"؟","("+a+", "+(a+b)+")",["["+a+", "+(a+b)+"]","("+a+", "+(a+b)+"]","["+a+", "+(a+b)+")","(−∞, "+a+")"]);
 case "quadgraph":return v("ما إحداثي x لرأس المنحنى Quadratic Function: f(x)=(x − "+a+")² + "+b+"؟",a);
 case "graphroots":return v("للاقتران Quadratic Function: f(x)=(x − "+a+")(x − "+(a+b)+")؛ ما أصغر قيمة x عند التقاطع مع محور x؟",a);
 case "completing":return v("أكمل المربع لحل المعادلة x² + "+2*a+"x + "+a*a+" = 0؛ أوجد x.",-a);
 case "quadraticformula":return v("باستخدام Quadratic Formula، ما أصغر جذر للمعادلة x² − "+(2*a+b)+"x + "+(a*(a+b))+" = 0؟",a);
 case "counting":return v("لدى طالب "+a+" قمصان و "+b+" بناطيل، كم طريقة مختلفة لاختيار قميص وبنطال؟",a*b,b);
 case "sample":return v("تجربة اختيار بطاقة واحدة من "+a+" بطاقات مختلفة ثم رمي قطعة نقود. كم ناتجًا في فضاء العينة؟",2*a,2);
 case "event":return v("تحتوي مجموعة النتائج على الأعداد من 1 إلى "+(2*a)+". كم ناتجًا في حادث ظهور عدد زوجي؟",a);
 case "probability":return f("صندوق فيه "+a+" كرات حمراء و "+b+" زرقاء؛ ما احتمال سحب حمراء؟",frac(a,a+b),[frac(b,a+b),frac(a,a+b+1),frac(a+1,a+b),frac(b,a+b+1)]);
 case "linequad":{var xx=a,aa=b,bb=xx*xx-xx-aa;return v("نظام المعادلتين y=x+"+aa+" و y=x²"+(bb>=0?"+"+bb:bb)+". قيمة x="+xx+" تحقق المعادلتين؛ ما قيمة y؟",xx+aa)}
 case "twosquares":return v("في النظام x²="+a*a+" و y²="+b*b+"، ما قيمة x الموجبة؟",a);
 case "exponential":return v("حل المعادلة الأسية "+(2+n%4)+"^x = "+(2+n%4)**(n+2)+"؛ أوجد x.",n+2);
 case "chord":return v("في دائرة نصف قطرها "+(5*a)+" سم، يبعد وتر عن المركز "+(3*a)+" سم. ما طول الوتر؟",8*a,2);
 case "sector":return f("قطاع دائري زاويته المركزية 90° ونصف قطر دائرته "+(2*a)+" سم. ما طول قوسه بدلالة π؟",a+"π سم",[(2*a)+"π سم",(a/2)+"π سم",4*a+"π سم",a+"π² سم"]);
 case "circleangles":return v("زاوية محيطية تقابل القوس نفسه الذي تقابله زاوية مركزية قياسها "+(40+2*n)+"°. ما قياس الزاوية المحيطية؟",20+n);
 case "circleeq":return v("دائرة نصف قطرها "+a+"؛ ما قيمة r² في معادلتها القياسية؟",a*a,a);
 case "tangentcircle":return v("دائرتان متماستان خارجيًا، نصفا قطريهما "+a+" سم و "+b+" سم. ما المسافة بين مركزيهما؟",a+b);
 case "trig":{var k=1+n,ratio=n%3===0?"sin θ":n%3===1?"cos θ":"tan θ",ans=n%3===0?"3/5":n%3===1?"4/5":"3/4";return f("مثلث قائم: المقابل للزاوية θ طوله "+(3*k)+" سم والمجاور "+(4*k)+" سم والوتر "+(5*k)+" سم. ما قيمة "+ratio+"؟",ans,["3/5","4/5","3/4","4/3","5/3","5/4"])}
 case "trigcycle":{var kind=["sin","cos","sin","cos"][n%4],angle=[30,60,150,120][n%4]+360*n,answer=n%4===3?"−1/2":"1/2";return f("احسب "+kind+"("+angle+"°) باستخدام دورية الدوال المثلثية.",answer,["1/2","−1/2","√3/2","−√3/2","0"])}
 case "triggraph":{var k=2+n;return f("ما دورة Graphing Trigonometric Function: y=sin("+k+"x) بالدرجات؟",frac(360,k)+"°",[frac(360,k+1)+"°",frac(720,k)+"°",frac(180,k)+"°",frac(360,k+2)+"°"])}
 case "trigeq":return v("في الفترة من 0° إلى 180°، إذا كان sin(x)=sin("+(n+10)+"°)، ما الحل الآخر غير "+(n+10)+"°؟",170-n,2);
 case "bearing":return v("اتجاه حركة مركبة "+(10+n)+"° شرق الجنوب. ما زاوية الاتجاه من الشمال في اتجاه عقارب الساعة؟",170-n);
 case "sineLaw":return v("في مثلث: ضلع a طوله "+a+" مقابل زاوية 30°، وضلع b مقابل زاوية 90°. باستخدام قانون الجيوب، ما b؟",2*a);
 case "cosLaw":return v("مثلث ضلعاه "+(3*a)+" و "+(4*a)+" والزاوية بينهما 90°. باستخدام قانون جيوب التمام، ما الضلع الثالث؟",5*a);
 case "trianglearea":return v("احسب مساحة مثلث ضلعاه "+(2*a)+" سم و "+b+" سم والزاوية المحصورة بينهما 90°.",a*b,b);
 case "spatial":return v("في متوازي مستطيلات أبعاده "+(2*a)+" سم و "+(3*a)+" سم و "+(6*a)+" سم، ما طول القطر الفراغي باستعمال فيثاغورس ثلاثي الأبعاد؟",7*a,a);
 }
 return null;
}
var mathIdSet=C.bySubject("الرياضيات");
function generateMath(l){if(!l||l.subject!=="الرياضيات"||!mode(l))return [];var q=[];try{for(var i=0;i<30;i++)q.push(question(l,i))}catch(e){return []}return q.every(Boolean)&&base.validate(q)?q:[]}
root.TAG_SEMESTER1_MATH_V3=Object.freeze({forLesson:generateMath,mode:mode});
})(window);
