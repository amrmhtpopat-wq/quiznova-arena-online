/* TAG Jordan semester-one ORIGINAL mathematical exercises.
 * 30 algorithmically verified answers for each explicitly mapped lesson.
 * Teacher review still required; no official textbook exercise is reproduced.
 * Function/trigonometric names, variables and formulas remain in English.
 */
(function(root){
'use strict';
const FAMILIES={
'math-6':[
['absolute','compare','add_signed','subtract_signed','multiply_signed'],
['fraction_add','fraction_mixed','fraction_multiply','fraction_divide','fraction_divide'],
['decimal_multiply','decimal_divide','decimal_context','word_arithmetic'],
['coordinate','translate','reflect','circle_parts','angles','triangle_construction']],
'math-7':[
['rational','rational_decimal','compare_fraction','fraction_add','fraction_multiply','word_arithmetic'],
['powers','order','algebra','algebra_add','distribute','word_arithmetic'],
['linear_solve','repeating','sequences','function','linear_graph'],
['angles','parallel_angles','triangle_angles','polygon_angles','rotate']],
'math-8':[
['sqrt','sqrt','pythagoras','real_numbers','powers','powers','scientific','percent'],
['expand','common_factor','factor_trinomial','difference_squares','algebra_fraction'],
['linear_standard','slope','linear_graph','point_slope','parallel_lines'],
['congruence','congruence','isosceles']],
'math-9':[
['interval','compound_inequality','absolute_equation','graph_inequality'],
['function','function','quadratic','quadratic_transform'],
['quadratic','factor_trinomial','factor_trinomial','complete_square','quadratic_formula','quadratic'],
['distance','point_to_line','coordinate']],
'math-10':[
['linear_quadratic_system','two_quadratic_system','powers','exponential'],
['circle_parts','arc','inscribed_angle','circle_equation','circle_tangent'],
['trig','trig','trig_graph','trig_equation'],
['bearings','sine_rule','cosine_rule','triangle_area','pythagoras']]
};
function fmt(x){
 if(typeof x==='string')return x;
 if(!Number.isFinite(x))return 'غير معرف';
 return String(Math.round(x*10000)/10000);
}
function numeric(text,answer,i,wrong){
 const a=Number(answer);
 const variants=(wrong||[a+1,a-1,a+2,a-2,a+3,a*2,a+5]).map(fmt);
 const output=[fmt(answer)];
 for(const item of variants)if(item!==output[0]&&!output.includes(item))output.push(item);
 if(output.length<4)return null;
 return item(text,output.slice(0,4),0,i);
}
function item(text,choices,correct,i){
 if(new Set(choices.map(String)).size!==4)return null;
 const offset=((i%4)+4)%4,cycled=choices.slice(offset).concat(choices.slice(0,offset));
 return {text,options:cycled.map(String),correct:[(correct-offset+4)%4]};
}
const div=(n,d)=>Math.round(n/d*10000)/10000;
function generate(f,i,lesson){
 const a=2+i,b=2+(Math.floor(i/5)%11),c=1+(Math.floor(i/7)%8);
 const x=(i%2===0?-1:1)*a,y=(i%3===0?-1:1)*b;
 const p=2+i,q=2+(Math.floor(i/3)%7);
 let tx='',ans=0,wrong=null,choices=null,correct=0;
 switch(f){
 case 'absolute':tx='ما القيمة المطلقة للعدد '+x+'؟';ans=Math.abs(x);break;
 case 'compare':return item('ما علامة المقارنة الصحيحة بين '+x+' و '+y+'؟',
 ['>','<','=','لا يمكن المقارنة'],x>y?0:x<y?1:2,i);
 case 'add_signed':tx='احسب ناتج '+x+' + ('+y+').';ans=x+y;break;
 case 'subtract_signed':tx='احسب ناتج '+x+' − ('+y+').';ans=x-y;break;
 case 'multiply_signed':tx='احسب ناتج ('+x+') × ('+y+').';ans=x*y;wrong=[-ans,ans+a,ans-a,ans+2];break;
 case 'fraction_add':tx='إذا كان المقام المشترك 13، ما بسط ('+p+'/13) + ('+q+'/13)؟';ans=p+q;break;
 case 'fraction_mixed':tx='ما مجموع العددين الكسريين '+a+' و '+b+' وكسريهما المتماثلان 1/2 و1/2 على صورة عدد صحيح؟';ans=a+b+1;break;
 case 'fraction_multiply':tx='ما بسط الناتج قبل الاختصار ('+p+'/11) × ('+q+'/7)؟';ans=p*q;break;
 case 'fraction_divide':tx='ما قيمة ('+p+'/9) ÷ (1/9)؟';ans=p;break;
 case 'decimal_multiply':tx='ما ناتج '+fmt(a/10)+' × '+b+'؟';ans=a*b/10;break;
 case 'decimal_divide':tx='ما ناتج '+fmt(a*b/10)+' ÷ '+b+'؟';ans=a/10;break;
 case 'decimal_context':tx='ثمن الوحدة '+fmt(a/10)+' دنانير. ما ثمن '+b+' وحدات؟';ans=a*b/10;break;
 case 'word_arithmetic':tx='مع طالب '+(a+b+c)+' دينارًا. أنفق '+a+' ثم '+b+' دنانير. كم بقي معه؟';ans=c;break;
 case 'coordinate':tx='إذا كانت النقطة P('+x+', '+y+')، فما الإحداثي السيني لها؟';ans=x;break;
 case 'translate':tx='النقطة P('+x+', '+y+') انسحبت '+p+' وحدات إلى اليمين. ما الإحداثي السيني الجديد؟';ans=x+p;break;
 case 'reflect':tx='النقطة P('+x+', '+y+') انعكست حول المحور x. ما الإحداثي الصادي للصورة؟';ans=-y;break;
 case 'circle_parts':tx='دائرة نصف قطرها '+a+' سم. كم طول قطرها بالسنتيمتر؟';ans=2*a;break;
 case 'angles':tx='زاويتان متكاملتان، قياس الأولى '+(a*5)+'°. ما قياس الثانية؟';ans=180-a*5;break;
 case 'triangle_construction':tx='مثلث متساوي الساقين زاوية رأسه '+(20+a*3)+'°. كم قياس كل زاوية من زاويتي القاعدة؟';ans=(180-(20+a*3))/2;break;
 case 'rational':tx='ما العدد الصحيح المكافئ للكسر ('+(a*3)+'/3)؟';ans=a;break;
 case 'rational_decimal':tx='ما الصورة العشرية للكسر '+a+'/10؟';ans=a/10;break;
 case 'compare_fraction':tx='عند المقارنة بين '+p+'/15 و '+q+'/15، ما البسط الأكبر؟';ans=Math.max(p,q);if(p===q)return numeric('ما مجموع بسطَي الكسرين '+p+'/15 و '+q+'/15؟',p+q,i);break;
 case 'powers':tx='إذا كان الأساس '+p+'، فما قيمة '+p+'²؟';ans=p*p;wrong=[p*2,p*p+1,p*p-1,p*p*p];break;
 case 'order':tx='ما نتيجة '+a+' + '+p+' × '+q+' حسب أولويات العمليات؟';ans=a+p*q;wrong=[(a+p)*q,a+p+q,a*p*q,ans+2];break;
 case 'algebra':tx='إذا كان x = '+a+' فما قيمة 3x + '+b+'؟';ans=3*a+b;break;
 case 'algebra_add':tx='ما معامل x في ( '+a+'x + '+b+' ) + ( '+p+'x + '+q+' ) ؟';ans=a+p;break;
 case 'distribute':tx='ما معامل x الناتج من توزيع '+a+' على ( '+p+'x + '+b+' )؟';ans=a*p;break;
 case 'linear_solve':tx='حل المعادلة x + '+a+' = '+(a+b)+'. ما قيمة x؟';ans=b;break;
 case 'repeating':tx='قرّب الكسر '+a+'/9 إلى أقرب جزء من ألف.';ans=Math.round(a/9*1000)/1000;wrong=[div(a,10),div(a,11),Math.round((a+1)/9*1000)/1000,Math.round((a-1)/9*1000)/1000];break;
 case 'sequences':tx='في المتتالية الحسابية '+a+'، '+(a+p)+'، '+(a+2*p)+'، ... ما الحد الرابع؟';ans=a+3*p;break;
 case 'function':tx='Given the function f(x) = '+p+'x + '+b+', find f('+a+').';ans=p*a+b;break;
 case 'linear_graph':tx='For the Linear Function f(x) = '+p+'x + '+b+', what is the y-intercept?';ans=b;break;
 case 'parallel_angles':tx='قاطع يقطع مستقيمين متوازيين. إذا كانت إحدى الزوايا المتناظرة '+(a*5)+'°، فما قياس الزاوية المناظرة الأخرى؟';ans=a*5;break;
 case 'triangle_angles':tx='في مثلث زاويتاه '+(a*4)+'° و '+(b*3)+'°. ما الزاوية الثالثة؟';ans=180-a*4-b*3;break;
 case 'polygon_angles':tx='مضلع منتظم عدد أضلاعه '+(a+3)+'. ما مجموع زواياه الداخلية بالدرجات؟';ans=(a+1)*180;break;
 case 'rotate':tx='دُوّرت النقطة P('+a+', '+b+') 180° حول الأصل. ما الإحداثي السيني للصورة؟';ans=-a;break;
 case 'sqrt':tx='ما الجذر التربيعي الموجب للعدد '+(a*a)+'؟';ans=a;break;
 case 'pythagoras':tx='مثلث قائم ضلعاه القائمان '+(3*p)+' و '+(4*p)+' سم. ما طول الوتر؟';ans=5*p;break;
 case 'real_numbers':tx='ما ناتج الجذر التربيعي الموجب لـ '+(a*a)+' مضروبًا في '+p+'؟';ans=a*p;break;
 case 'scientific':tx='اكتب القيمة العددية للعدد '+a+' × 10³.';ans=a*1000;wrong=[a*100,a*10000,a+1000,ans+100];break;
 case 'percent':tx='ما قيمة '+(p*5)+'% من '+(b*20)+'؟';ans=p*b;break;
 case 'expand':tx='ما الحد الثابت في مربع المقدار (x + '+a+')²؟';ans=a*a;break;
 case 'common_factor':tx='ما العامل العددي المشترك الأكبر بين '+(a*6)+'x و '+(a*9)+'؟';ans=a*3;break;
 case 'factor_trinomial':tx='For x² + '+(a+b)+'x + '+a*b+', what is the constant term?';ans=a*b;break;
 case 'difference_squares':tx='ما قيمة الحد الثابت في (x + '+a+')(x − '+a+') ؟';ans=-a*a;break;
 case 'algebra_fraction':tx='إذا كان x ≠ 0، فما قيمة ('+(a*p)+'x)/('+p+'x)؟';ans=a;break;
 case 'linear_standard':tx='في المعادلة '+a+'x + '+b+'y = '+(a*3+b*2)+'، هل النقطة (3,2) تحققها؟';return item(tx,['نعم، لأنها تحقق المعادلة','لا، لأنها تحقق معادلة أخرى','فقط إذا x = 0','فقط إذا y = 0'],0,i);
 case 'slope':tx='يمر مستقيم بالنقطتين (1, '+b+') و (3, '+(b+2*p)+'). ما ميله؟';ans=p;break;
 case 'point_slope':tx='يمر مستقيم ميله '+p+' بالنقطة (0, '+b+'). ما y-intercept؟';ans=b;break;
 case 'parallel_lines':tx='The line y = '+p+'x + '+a+' is parallel to y = mx + '+b+'. Find m.';ans=p;break;
 case 'congruence':return item('مثلثان لهما الأضلاع المتناظرة '+a+' سم و '+p+' سم و '+(a+p-1)+' سم نفسها. ما معيار التطابق المباشر؟',['SSS','SAS','ASA','AAS'],0,i);
 case 'isosceles':tx='في مثلث متساوي الساقين زاوية الرأس '+(2*a)+'°. ما زاوية القاعدة؟';ans=90-a;break;
 case 'interval':return item('إذا كانت x > '+a+'، أي وصف يمثل مجال الحل؟',['('+a+', ∞)','['+a+', ∞)','(−∞, '+a+')','(−∞, '+a+']'],0,i);
 case 'compound_inequality':tx='إذا كانت '+a+' < x < '+(a+b)+'، فكم عدد القيم الصحيحة لـ x؟';ans=b-1;break;
 case 'absolute_equation':tx='حل |x| = '+a+'. ما قيمة الحل الموجب؟';ans=a;break;
 case 'graph_inequality':tx='For y > '+p+'x + '+b+', which y satisfies the inequality when x = 0?';ans=b+a;wrong=[b,b-a,b-1,b-2];break;
 case 'quadratic':tx='For the Quadratic Function f(x) = x² + '+p+'x + '+b+', find f('+a+').';ans=a*a+p*a+b;break;
 case 'quadratic_transform':tx='For g(x) = (x − '+a+')² + '+b+', what is the x-coordinate of the vertex?';ans=a;break;
 case 'complete_square':tx='What number completes the square of x² + '+(2*a)+'x + ... ?';ans=a*a;break;
 case 'quadratic_formula':tx='For x² − '+(a+b)+'x + '+a*b+' = 0, what is the sum of the two roots?';ans=a+b;break;
 case 'distance':tx='What is the distance between A(0,0) and B('+(3*p)+','+(4*p)+')?';ans=5*p;break;
 case 'point_to_line':tx='What is the distance from P('+a+','+b+') to the vertical line x = '+(a+p)+'?';ans=p;break;
 case 'linear_quadratic_system':tx='In the first quadrant, solve x² = '+(a*a)+' and y = x + '+b+'. What is y?';ans=a+b;break;
 case 'two_quadratic_system':tx='In the first quadrant, solve x² = '+(a*a)+' and y² = '+(b*b)+'. What is x + y?';ans=a+b;break;
 case 'exponential':tx='Solve '+p+'^x = '+(p*p*p)+'. Find x.';ans=3;wrong=[1,2,4,5];break;
 case 'arc':tx='A central angle of '+(a*5)+'° subtends an arc in a circle. What is the arc measure in degrees?';ans=a*5;break;
 case 'inscribed_angle':tx='An inscribed angle intercepts an arc of '+(a*6)+'°. Find the angle measure.';ans=a*3;break;
 case 'circle_equation':tx='For the circle (x − '+a+')² + (y − '+b+')² = '+(p*p)+', find the radius.';ans=p;break;
 case 'circle_tangent':return item('لدائرة نصف قطرها '+a+' سم، ما زاوية تقاطع المماس مع نصف القطر عند نقطة التماس؟',['90°','45°','60°','180°'],0,i);
 case 'trig':return item('For a right triangle, what is sin(θ) when opposite = '+a+' and hypotenuse = '+(a+b)+'?', [a+'/'+(a+b),(a+b)+'/'+a,b+'/'+(a+b),a+'/'+b],0,i);
 case 'trig_graph':tx='For the Trigonometric Function f(x) = '+p+'sin(x), what is its amplitude?';ans=p;break;
 case 'trig_equation':return item('For 0° ≤ θ ≤ 90°, solve sin(θ) = sin('+(10+i*2)+'°). Find θ.',[(10+i*2)+'°',(9+i*2)+'°',(11+i*2)+'°',(12+i*2)+'°'],0,i);
 case 'bearings':tx='If a compass turns clockwise '+(a*10)+'° from North, what is its bearing in degrees?';ans=a*10;break;
 case 'sine_rule':return item('For the Sine Rule, if A = 30°, B = 90° and a = '+p+' cm, find b.',[fmt(2*p)+' cm',fmt(p/2)+' cm',fmt(p)+' cm',fmt(3*p)+' cm'],0,i);
 case 'cosine_rule':tx='Using the Cosine Rule with sides '+a+', '+b+' and included angle 90°, what is c²?';ans=a*a+b*b;break;
 case 'triangle_area':tx='Using Area = ½ab sin(C) for a = '+a+', b = '+(2*p)+' and C = 90°, find area.';ans=a*p;break;
 default:return null;
 }
 return numeric(tx,ans,i,wrong);
}
function questionsFor(lesson){
 if(!lesson||lesson.subject!=='الرياضيات')return [];
 const pieces=String(lesson.id).split('-'),course=pieces.slice(0,2).join('-');
 const unit=Number(pieces[2]?.slice(1))-1,l=Number(pieces[3]?.slice(1))-1;
 const family=FAMILIES[course]?.[unit]?.[l];
 if(!family)return [];
 const out=[],signatures=new Set();
 for(let i=0;i<120&&out.length<30;i++){
  const n=generate(family,i,lesson);
  if(!n||!n.text||n.options.length!==4||n.correct.length!==1)continue;
  const sig=n.text+'|'+n.options[n.correct[0]];
  if(signatures.has(sig))continue;
  signatures.add(sig);
  out.push(Object.freeze({
   id:'jos1_'+lesson.id+'_'+String(out.length+1).padStart(2,'0'),
   subject:'الرياضيات',grade:lesson.grade,semester:'1',
   unit:lesson.unit,lesson:lesson.title,type:'single',
   text:n.text,options:n.options,correct:n.correct,
   difficulty:out.length%3===0?'easy':out.length%3===1?'medium':'hard',
   time:35,points:1000,skill:lesson.title,
   explanation:'تم توليد المثال حسابيًا للتحقق من الإجابة؛ راجع صياغته وملاءمته للدرس قبل النشر.',
   reviewStatus:'teacher_review_required',origin:'tag_jordan_s1_original',
   source:'تدريبات رياضيات أصلية مرتبطة بموضوع الدرس — تحتاج مراجعة المعلم',
   sourceUrl:lesson.sourceUrl||'https://nccd.gov.jo/Ar/Pages/textbooks',
   tags:['الأردن','الفصل الأول','رياضيات','تدريبات أصلية']
  }));
 }
 return out;
}
root.TAG_JORDAN_S1_MATH_V1=Object.freeze({questionsFor,FAMILIES});
})(window);
