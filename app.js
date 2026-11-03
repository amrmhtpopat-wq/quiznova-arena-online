const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];

const DB = {
  get quizzes(){ return JSON.parse(localStorage.getItem('qn3_quizzes')||localStorage.getItem('qn2_quizzes')||localStorage.getItem('qn_quizzes')||'[]') },
  set quizzes(v){ localStorage.setItem('qn3_quizzes', JSON.stringify(v)) },
  get results(){ return JSON.parse(localStorage.getItem('qn3_results')||localStorage.getItem('qn2_results')||localStorage.getItem('qn_results')||'[]') },
  set results(v){ localStorage.setItem('qn3_results', JSON.stringify(v)) },
  get bank(){ return JSON.parse(localStorage.getItem('qn3_bank')||localStorage.getItem('qn2_bank')||'[]') },
  set bank(v){ localStorage.setItem('qn3_bank', JSON.stringify(v)) },
  get settings(){ return JSON.parse(localStorage.getItem('qn3_settings')||localStorage.getItem('qn2_settings')||localStorage.getItem('qn_settings')||'{}') },
  set settings(v){ localStorage.setItem('qn3_settings', JSON.stringify(v)) }
};

let builderQuestions = [];
let editingQuizId = null;
let game = null;
let liveRoom = null;
let liveHostToken = '';
let liveStageToken = '';
let livePollTimer = null;
let liveSaved = false;
let liveAutoRevealIndex = -1;
let serverInfo = null;

const viewMeta = {
  dashboard:['لوحة التحكم','اختبارات صفية أكثر تنوعًا وتحكمًا'],
  generator:['المولّد الذكي','أنشئ اختبارًا متوازنًا من بنك الأسئلة بضغطة واحدة'],
  builder:['إنشاء اختبار','استوديو متقدم للأسئلة والوسائط والمهارات العملية'],
  bank:['بنك الأسئلة','صنّف أسئلتك وأعد استخدامها بذكاء'],
  media:['مكتبة الصور','صور جاهزة مصنفة وصورك المضافة؛ اخترها للأسئلة بسهولة'],
  library:['مكتبة الاختبارات','كل اختباراتك المحفوظة محليًا'],
  live:['صف مباشر','غرفة صفية مباشرة عبر الإنترنت — QR وPIN من أي مكان'],
  play:['تشغيل فردي','طالب واحد أو محطة تعلم على نفس الجهاز'],
  results:['النتائج والتحليل','متابعة الأداء وأصعب الأسئلة'],
  settings:['الإعدادات','الهوية والنسخ الاحتياطي']
};

function uid(){ return Date.now().toString(36)+Math.random().toString(36).slice(2,8) }
function escapeHtml(v=''){ return String(v).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])) }
function toast(msg){ const t=$('#toast'); t.textContent=msg; t.classList.add('show'); clearTimeout(t._tm); t._tm=setTimeout(()=>t.classList.remove('show'),2500) }
function shuffle(arr){ const a=[...arr]; for(let i=a.length-1;i>0;i--){ const j=Math.floor(Math.random()*(i+1)); [a[i],a[j]]=[a[j],a[i]] } return a }
function normalize(s){ return String(s??'').trim().toLowerCase().replace(/[أإآ]/g,'ا').replace(/ة/g,'ه').replace(/ى/g,'ي').replace(/[ًٌٍَُِّْ]/g,'').replace(/\s+/g,' ') }
function formatTime(sec){ const m=Math.floor(sec/60), s=Math.max(0,Math.round(sec%60)); return `${m}:${String(s).padStart(2,'0')}` }
function download(name,text,type='application/json'){ const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([text],{type})); a.download=name; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),500) }
function clone(x){ return JSON.parse(JSON.stringify(x)) }
function difficultyName(d){ return ({easy:'سهل',medium:'متوسط',hard:'صعب',mixed:'متنوع'})[d]||'متوسط' }
function typeName(t){ return ({single:'اختيار واحد',multi:'اختيارات متعددة',tf:'صح/خطأ',short:'إجابة قصيرة',order:'ترتيب وسحب',match:'مطابقة',poll:'استطلاع'})[t]||t }
function typeIcon(t){ return ({single:'🔘',multi:'☑️',tf:'✅',short:'⌨️',order:'↕',match:'🔗',poll:'📊'})[t]||'❓' }
function qSignature(q){ return normalize(q.text)+'|'+q.type+'|'+normalize(q.subject||'')+'|'+normalize(q.grade||'') }
function openModal(html){ $('#modalContent').innerHTML=html; $('#modal').classList.remove('hidden') }
function closeModal(){ $('#modal').classList.add('hidden'); $('#modalContent').innerHTML='' }
$$('[data-closemodal]').forEach(x=>x.onclick=closeModal);

function go(view){
  $$('.view').forEach(v=>v.classList.remove('active')); const target=$('#view-'+view); if(target)target.classList.add('active');
  $$('.nav-item').forEach(b=>b.classList.toggle('active',b.dataset.view===view));
  $('#pageTitle').textContent=viewMeta[view][0]; $('#pageSubtitle').textContent=viewMeta[view][1]; $('#sidebar').classList.remove('open');
  if(view==='dashboard')renderDashboard(); if(view==='generator')renderGenerator(); if(view==='library')renderLibrary(); if(view==='play')renderPlaySelect(); if(view==='results')renderResults(); if(view==='bank')renderBank(); if(view==='media')renderMediaLibrary(); if(view==='live')renderLiveLanding();
}
window.go=go;
$$('.nav-item').forEach(b=>b.onclick=()=>go(b.dataset.view));
$$('[data-jump]').forEach(b=>b.onclick=()=>go(b.dataset.jump));
$('#menuBtn').onclick=()=>$('#sidebar').classList.toggle('open');
$('#quickGenerate').onclick=()=>go('generator');
$$('[data-modejump]').forEach(b=>b.onclick=()=>{ go('play'); setTimeout(()=>$('#playMode').value=b.dataset.modejump,0) });
$$('.book-chip').forEach(b=>b.addEventListener('click',()=>setTimeout(()=>{if($('#genGrade')){$('#genGrade').value=b.dataset.grade;renderGeneratorUnits();updateGeneratorPool()}},20)));

function blankQuestion(type='single'){
  const base={id:uid(),type,text:'',time:20,points:1000,difficulty:'medium',subject:'المهارات الرقمية',grade:'السابع',unit:'عام',tags:[],image:''};
  if(type==='single')Object.assign(base,{options:['','','',''],correct:[0]});
  if(type==='multi')Object.assign(base,{options:['','','',''],correct:[0,1]});
  if(type==='tf')Object.assign(base,{correct:true});
  if(type==='short')Object.assign(base,{answers:['']});
  if(type==='order')Object.assign(base,{items:['','','']});
  if(type==='match')Object.assign(base,{pairs:[{left:'',right:''},{left:'',right:''},{left:'',right:''}]});
  if(type==='poll')Object.assign(base,{options:['','','',''],points:0});
  return base;
}

function sampleBank(){
  const main=Array.isArray(window.CURRICULUM_BANK)?window.CURRICULUM_BANK:[];
  const extra=Array.isArray(window.CURRICULUM_PLUS)?window.CURRICULUM_PLUS:[];
  return [...main,...extra].map((q,i)=>({...clone(q),image:q.image||`/assets/questions/${String(i%99+1).padStart(2,'0')}.svg`,id:q.id||`qnseed_${i+1}`,subject:q.subject||'المهارات الرقمية'}));
}

function demoQuizForGrade(grade){
  const all=sampleBank().filter(q=>q.grade===grade), titles={السابع:'تحدي السابع – أنظمة الحوسبة والشبكات',الثامن:'تحدي الثامن – الأعطال والبرمجة',التاسع:'تحدي التاسع – أثر الحوسبة والبرمجة'};
  return {id:uid(),title:titles[grade]||`تحدي ${grade}`,subject:'المهارات الرقمية',grade,section:'',createdAt:Date.now(),settings:{randomQuestions:false,randomOptions:true,showFeedback:true,speedBonus:true,bossEnabled:true},questions:shuffle(all).slice(0,10).map(q=>({...q,id:uid()}))};
}
function demoQuiz(){ return demoQuizForGrade('السابع') }

function migrateAndSeed(){
  let qs=DB.quizzes.map(q=>{ q.settings=q.settings||{}; q.settings.bossEnabled=!!q.settings.bossEnabled; q.questions=(q.questions||[]).map(x=>Object.assign({difficulty:'medium',unit:'عام',subject:q.subject||'عام',grade:q.grade||'السابع',tags:[],image:''},x)); return q });
  if(!qs.length)qs=['السابع','الثامن','التاسع'].map(demoQuizForGrade);
  const illustrationBySig=new Map(sampleBank().map(q=>[qSignature(q),q.image]));
  qs.forEach(quiz=>(quiz.questions||[]).forEach(q=>{if(!q.image && illustrationBySig.has(qSignature(q)))q.image=illustrationBySig.get(qSignature(q))}));
  DB.quizzes=qs;
  let bank=DB.bank||[]; bank.forEach(q=>{if(!q.image && illustrationBySig.has(qSignature(q)))q.image=illustrationBySig.get(qSignature(q))}); const seenIds=new Set(bank.map(x=>x.id)); const seenSig=new Set(bank.map(qSignature));
  sampleBank().forEach(q=>{if(!seenIds.has(q.id)&&!seenSig.has(qSignature(q))){bank.push(q);seenIds.add(q.id);seenSig.add(qSignature(q))}});
  DB.bank=bank;
}
migrateAndSeed();

function renderDashboard(){
  const q=DB.quizzes,r=DB.results,b=DB.bank; const avg=r.length?Math.round(r.reduce((a,x)=>a+(x.percent||0),0)/r.length):0;
  $('#statBank').textContent=b.length; $('#statQuizzes').textContent=q.length; $('#statAttempts').textContent=r.length; $('#statAverage').textContent=avg+'%';
  $('#recentQuizzes').innerHTML=q.slice(-5).reverse().map(x=>`<div class="list-row"><div class="meta"><div class="qicon">${x.settings?.bossEnabled?'👑':'🎯'}</div><div><strong>${escapeHtml(x.title)}</strong><small>${escapeHtml(x.subject)} • ${x.questions.length} سؤال</small></div></div><button class="text-btn" onclick="playQuizById('${x.id}')">تشغيل</button></div>`).join('')||'<p>لا توجد اختبارات.</p>';
}

// ---------- Generator ----------
function bankSubjects(){ return [...new Set(DB.bank.map(q=>q.subject||'عام'))].sort() }
function renderGenerator(){
  const current=$('#genSubject').value; $('#genSubject').innerHTML='<option value="all">كل المواد</option>'+bankSubjects().map(s=>`<option ${s===current?'selected':''}>${escapeHtml(s)}</option>`).join('');
  renderGeneratorUnits(); updateGeneratorPool();
}
function renderGeneratorUnits(){ const s=$('#genSubject').value,g=$('#genGrade').value; const units=[...new Set(DB.bank.filter(q=>(s==='all'||q.subject===s)&&(g==='all'||q.grade===g)).map(q=>q.unit||'عام'))].sort(); const cur=$('#genUnit').value; $('#genUnit').innerHTML='<option value="all">كل الوحدات والموضوعات</option>'+units.map(u=>`<option ${u===cur?'selected':''}>${escapeHtml(u)}</option>`).join('') }
function selectedGenTypes(){ return $$('#genTypes input:checked').map(x=>x.value) }
function generatorPool(){ const s=$('#genSubject').value,g=$('#genGrade').value,u=$('#genUnit').value,d=$('#genDifficulty').value,types=selectedGenTypes(); return DB.bank.filter(q=>(s==='all'||q.subject===s)&&(g==='all'||q.grade===g)&&(u==='all'||q.unit===u)&&(d==='mixed'||q.difficulty===d)&&types.includes(q.type)) }
function updateGeneratorPool(){ const pool=generatorPool(); $('#poolCount').textContent=pool.length; const count=Math.max(1,+$('#genCount').value||10),d=$('#genDifficulty').value; let html=''; if(d==='mixed'){ const e=Math.round(count*.3),m=Math.round(count*.45),h=Math.max(0,count-e-m); html=`<span class="plan-chip">🟢 سهل ≈ ${e}</span><span class="plan-chip">🟡 متوسط ≈ ${m}</span><span class="plan-chip">🔴 صعب ≈ ${h}</span>` } else html=`<span class="plan-chip">المستوى: ${difficultyName(d)}</span>`; html+=`<span class="plan-chip">الأنواع المحددة: ${selectedGenTypes().length}</span>`; $('#difficultyPlan').innerHTML=html }
['genSubject','genGrade','genUnit','genDifficulty','genCount'].forEach(id=>$('#'+id).addEventListener('change',()=>{ if(id==='genSubject'||id==='genGrade')renderGeneratorUnits(); updateGeneratorPool() }));
$('#genCount').addEventListener('input',updateGeneratorPool);
$('#genMinus').onclick=()=>{ $('#genCount').value=Math.max(1,(+$('#genCount').value||10)-1);updateGeneratorPool() };
$('#genPlus').onclick=()=>{ $('#genCount').value=Math.min(120,(+$('#genCount').value||10)+1);updateGeneratorPool() };
$$('#genTypes .type-pick').forEach(l=>l.onclick=()=>setTimeout(()=>{l.classList.toggle('active',l.querySelector('input').checked);updateGeneratorPool()},0));
function balancedPick(pool,count){
  if(pool.length<=count)return shuffle(pool);
  const byType={}; pool.forEach(q=>(byType[q.type]??=[]).push(q)); Object.values(byType).forEach(a=>a.sort(()=>Math.random()-.5));
  let result=[]; const types=shuffle(Object.keys(byType)); let safety=1000;
  while(result.length<count && safety--){ let added=false; for(const t of types){ if(byType[t].length && result.length<count){ result.push(byType[t].pop());added=true } } if(!added)break }
  return result;
}
function generateFromBank(){
  let pool=generatorPool(),count=Math.max(1,Math.min(120,+$('#genCount').value||10)); if(!pool.length)return toast('لا توجد أسئلة مطابقة لهذه الفلاتر');
  let chosen=[]; const d=$('#genDifficulty').value;
  if(d==='mixed'){
    const ratios={easy:.30,medium:.45,hard:.25}; const desired={easy:Math.round(count*ratios.easy),medium:Math.round(count*ratios.medium)}; desired.hard=count-desired.easy-desired.medium;
    ['easy','medium','hard'].forEach(level=>{ const part=balancedPick(pool.filter(q=>q.difficulty===level),desired[level]); chosen.push(...part) });
    if(chosen.length<count){ const used=new Set(chosen.map(q=>q.id)); chosen.push(...balancedPick(pool.filter(q=>!used.has(q.id)),count-chosen.length)) }
  } else chosen=balancedPick(pool,count);
  chosen=shuffle(chosen).slice(0,count); if(chosen.length<count)toast(`المتاح ${chosen.length} سؤال فقط من أصل ${count} مطلوب`);
  resetBuilder(); const subject=$('#genSubject').value==='all'?(chosen[0]?.subject||'عام'):$('#genSubject').value; const grade=$('#genGrade').value==='all'?(chosen[0]?.grade||'السابع'):$('#genGrade').value;
  $('#quizTitle').value=$('#genTitle').value.trim()||`اختبار ذكي - ${subject}`; $('#quizSubject').value=subject; $('#quizGrade').value=grade; builderQuestions=chosen.map(q=>({...clone(q),id:uid()})); renderQuestions(); go('builder'); toast(`تم إنشاء اختبار من ${builderQuestions.length} سؤال متنوع`);
}
$('#generateQuiz').onclick=generateFromBank;
$('#previewPool').onclick=()=>{ const p=generatorPool(); openModal(`<div class="overline">PREVIEW</div><h3>الأسئلة المتاحة (${p.length})</h3><div class="modal-list">${p.slice(0,80).map(q=>`<div class="modal-item"><div><b>${typeIcon(q.type)} ${escapeHtml(q.text)}</b><small style="display:block;color:#7b8397">${difficultyName(q.difficulty)} • ${escapeHtml(q.unit||'عام')}</small></div></div>`).join('')||'<p>لا توجد أسئلة.</p>'}</div>`) };

// ---------- Builder ----------
function resetBuilder(){ editingQuizId=null; $('#quizTitle').value=''; $('#quizSubject').value='المهارات الرقمية'; $('#quizGrade').value='السابع'; $('#quizSection').value=''; $('#randomQuestions').checked=true; $('#randomOptions').checked=true; $('#showFeedback').checked=true; $('#speedBonus').checked=true; $('#bossEnabled').checked=false; builderQuestions=[blankQuestion('single')]; renderQuestions() }
function addQuestion(type='single'){ const q=blankQuestion(type); q.subject=$('#quizSubject').value||'المهارات الرقمية';q.grade=$('#quizGrade').value;builderQuestions.push(q);renderQuestions() }
$('#addQuestion').onclick=()=>addQuestion('single'); $$('#quickTypes [data-addtype]').forEach(b=>b.onclick=()=>addQuestion(b.dataset.addtype)); $('#resetBuilder').onclick=resetBuilder;
$('#loadDemo').onclick=()=>{ const d=demoQuiz();editingQuizId=null;fillBuilder(d);toast('تم تحميل نموذج متقدم') };
function getQ(id){ return builderQuestions.find(x=>x.id===id) }
function renderQuestions(){ $('#questionCount').textContent=`${builderQuestions.length} سؤال`; $('#questionsEditor').innerHTML=builderQuestions.map((q,i)=>questionEditor(q,i)).join('') }
function questionEditor(q,i){
  return `<div class="question-card" data-qid="${q.id}">
  <div class="question-top"><div class="question-number">${i+1}</div><select onchange="changeType('${q.id}',this.value)">${['single','multi','tf','short','order','match','poll'].map(t=>`<option value="${t}" ${q.type===t?'selected':''}>${typeName(t)}</option>`).join('')}</select><select class="difficulty-select ${q.difficulty}" onchange="updateQ('${q.id}','difficulty',this.value);renderQuestions()"><option value="easy" ${q.difficulty==='easy'?'selected':''}>سهل</option><option value="medium" ${q.difficulty==='medium'?'selected':''}>متوسط</option><option value="hard" ${q.difficulty==='hard'?'selected':''}>صعب</option></select><div class="spacer"></div><button class="icon-btn" onclick="duplicateQuestion('${q.id}')">⧉</button><button class="icon-btn danger" onclick="removeQuestion('${q.id}')">✕</button></div>
  <div class="question-row"><input value="${escapeHtml(q.text)}" oninput="updateQ('${q.id}','text',this.value)" placeholder="اكتب السؤال هنا..."><input value="${escapeHtml(q.unit||'عام')}" oninput="updateQ('${q.id}','unit',this.value)" placeholder="الوحدة / الموضوع"><input type="number" min="5" max="300" value="${q.time||20}" oninput="updateQ('${q.id}','time',+this.value)" title="الوقت بالثواني"><input type="number" min="0" step="100" value="${q.points??1000}" oninput="updateQ('${q.id}','points',+this.value)" title="النقاط"></div>
  <div class="question-media-row">${q.image?`<img class="question-media-preview" src="${q.image}">`:''}<label class="btn btn-soft" style="font-size:9px">🖼 ${q.image?'تغيير الصورة':'إضافة صورة'}<input type="file" accept="image/*" hidden onchange="attachImage('${q.id}',this)"></label><button type="button" class="btn btn-soft" onclick="chooseFromMedia('${q.id}')">▧ مكتبة الصور</button>${q.image?`<button class="btn btn-danger-soft" onclick="removeImage('${q.id}')">حذف الصورة</button>`:''}</div>
  ${typeEditor(q)}</div>`;
}
function typeEditor(q){
  if(q.type==='single'||q.type==='multi'||q.type==='poll')return `<div class="options-editor">${q.options.map((o,j)=>`<div class="option-line"><div class="marker">${['أ','ب','ج','د','هـ','و'][j]||j+1}</div><input value="${escapeHtml(o)}" oninput="updateOption('${q.id}',${j},this.value)" placeholder="الخيار ${j+1}">${q.type==='poll'?'<span></span>':`<label><input type="${q.type==='single'?'radio':'checkbox'}" name="correct-${q.id}" ${q.correct?.includes(j)?'checked':''} onchange="setCorrect('${q.id}',${j},this.checked)"> صحيح</label>`}<button class="icon-btn remove-option" onclick="removeOption('${q.id}',${j})">−</button></div>`).join('')}<button class="add-option" onclick="addOption('${q.id}')">+ خيار</button></div>`;
  if(q.type==='tf')return `<div class="options-editor"><label class="toggle-line"><input type="radio" name="tf-${q.id}" ${q.correct===true?'checked':''} onchange="updateQ('${q.id}','correct',true)"> ✅ صح</label><label class="toggle-line"><input type="radio" name="tf-${q.id}" ${q.correct===false?'checked':''} onchange="updateQ('${q.id}','correct',false)"> ❌ خطأ</label></div>`;
  if(q.type==='short')return `<div class="options-editor">${q.answers.map((a,j)=>`<div class="option-line"><div class="marker">${j+1}</div><input value="${escapeHtml(a)}" oninput="updateShort('${q.id}',${j},this.value)" placeholder="إجابة مقبولة"><span></span><button class="icon-btn" onclick="removeShort('${q.id}',${j})">−</button></div>`).join('')}<button class="add-option" onclick="addShort('${q.id}')">+ إجابة بديلة</button></div>`;
  if(q.type==='order')return `<div class="options-editor">${q.items.map((a,j)=>`<div class="option-line"><div class="marker">${j+1}</div><input value="${escapeHtml(a)}" oninput="updateItem('${q.id}',${j},this.value)" placeholder="الخطوة ${j+1}"><span></span><button class="icon-btn" onclick="removeItem('${q.id}',${j})">−</button></div>`).join('')}<button class="add-option" onclick="addItem('${q.id}')">+ خطوة</button></div>`;
  if(q.type==='match')return `<div class="options-editor">${q.pairs.map((p,j)=>`<div class="pair-line"><div class="marker">${j+1}</div><input value="${escapeHtml(p.left)}" oninput="updatePair('${q.id}',${j},'left',this.value)" placeholder="العنصر"><div class="pair-arrow">↔</div><input value="${escapeHtml(p.right)}" oninput="updatePair('${q.id}',${j},'right',this.value)" placeholder="المطابقة"><button class="icon-btn remove-pair" onclick="removePair('${q.id}',${j})">−</button></div>`).join('')}<button class="add-option" onclick="addPair('${q.id}')">+ زوج مطابقة</button></div>`;
  return '';
}
window.updateQ=(id,k,v)=>{ const q=getQ(id); if(q)q[k]=v };
window.changeType=(id,type)=>{ const i=builderQuestions.findIndex(x=>x.id===id),old=builderQuestions[i],n=blankQuestion(type); ['id','text','time','points','difficulty','subject','grade','unit','tags','image'].forEach(k=>n[k]=old[k]); if(type==='poll')n.points=0; builderQuestions[i]=n;renderQuestions() };
window.removeQuestion=id=>{builderQuestions=builderQuestions.filter(x=>x.id!==id);renderQuestions()};
window.duplicateQuestion=id=>{const q=clone(getQ(id));q.id=uid();builderQuestions.splice(builderQuestions.findIndex(x=>x.id===id)+1,0,q);renderQuestions()};
window.updateOption=(id,j,v)=>getQ(id).options[j]=v;
window.setCorrect=(id,j,checked)=>{const q=getQ(id); if(q.type==='single')q.correct=[j];else{if(checked&&!q.correct.includes(j))q.correct.push(j);if(!checked)q.correct=q.correct.filter(x=>x!==j)}};
window.addOption=id=>{getQ(id).options.push('');renderQuestions()}; window.removeOption=(id,j)=>{const q=getQ(id);if(q.options.length<=2)return toast('يجب أن يبقى خياران على الأقل');q.options.splice(j,1);if(q.correct)q.correct=q.correct.filter(x=>x!==j).map(x=>x>j?x-1:x);renderQuestions()};
window.updateShort=(id,j,v)=>getQ(id).answers[j]=v; window.addShort=id=>{getQ(id).answers.push('');renderQuestions()}; window.removeShort=(id,j)=>{if(getQ(id).answers.length>1)getQ(id).answers.splice(j,1);renderQuestions()};
window.updateItem=(id,j,v)=>getQ(id).items[j]=v; window.addItem=id=>{getQ(id).items.push('');renderQuestions()}; window.removeItem=(id,j)=>{if(getQ(id).items.length>2)getQ(id).items.splice(j,1);renderQuestions()};
window.updatePair=(id,j,k,v)=>getQ(id).pairs[j][k]=v; window.addPair=id=>{getQ(id).pairs.push({left:'',right:''});renderQuestions()}; window.removePair=(id,j)=>{if(getQ(id).pairs.length>2)getQ(id).pairs.splice(j,1);renderQuestions()};
async function optimizeImage(file){
  if(!/^image\/(png|jpe?g|webp|gif)$/i.test(file.type))throw Error('اختر صورة JPG/PNG/WebP');
  if(file.size>8_000_000)throw Error('حجم الصورة كبير، اختر صورة أقل من 8MB');
  const img=await createImageBitmap(file);const max=1000,scale=Math.min(1,max/Math.max(img.width,img.height));
  const canvas=document.createElement('canvas');canvas.width=Math.max(1,Math.round(img.width*scale));canvas.height=Math.max(1,Math.round(img.height*scale));
  canvas.getContext('2d').drawImage(img,0,0,canvas.width,canvas.height);img.close?.();
  return canvas.toDataURL('image/jpeg',0.76);
}
window.attachImage=async(id,input)=>{const f=input.files[0];if(!f)return;try{getQ(id).image=await optimizeImage(f);renderQuestions();toast('تمت إضافة الصورة للسؤال')}catch(e){toast(e.message||'تعذر قراءة الصورة')}}; window.removeImage=id=>{getQ(id).image='';renderQuestions()};
function fillBuilder(q){$('#quizTitle').value=q.title;$('#quizSubject').value=q.subject||'المهارات الرقمية';$('#quizGrade').value=q.grade||'السابع';$('#quizSection').value=q.section||'';$('#randomQuestions').checked=!!q.settings?.randomQuestions;$('#randomOptions').checked=!!q.settings?.randomOptions;$('#showFeedback').checked=q.settings?.showFeedback!==false;$('#speedBonus').checked=q.settings?.speedBonus!==false;$('#bossEnabled').checked=!!q.settings?.bossEnabled;builderQuestions=clone(q.questions||[]);renderQuestions()}
function validateQuestion(q){if(!q.text.trim())return 'يوجد سؤال بدون نص'; if((q.type==='single'||q.type==='multi')&&q.options.some(x=>!x.trim()))return 'يوجد خيار فارغ'; if(q.type==='single'&&q.correct.length!==1)return 'سؤال اختيار بدون إجابة صحيحة'; if(q.type==='multi'&&q.correct.length<1)return 'سؤال متعدد بدون إجابة صحيحة'; if(q.type==='short'&&!q.answers.some(x=>x.trim()))return 'سؤال قصير بدون إجابة مقبولة'; if(q.type==='order'&&q.items.some(x=>!x.trim()))return 'سؤال ترتيب يحتوي خطوة فارغة'; if(q.type==='match'&&q.pairs.some(p=>!p.left.trim()||!p.right.trim()))return 'سؤال مطابقة يحتوي خانة فارغة'; return ''}
function syncQuestionsToBank(questions,quizMeta){let bank=DB.bank,seen=new Set(bank.map(qSignature)),added=0;questions.filter(q=>q.type!=='poll').forEach(q=>{const x=clone(q);x.id=uid();x.subject=quizMeta.subject;x.grade=quizMeta.grade;if(!seen.has(qSignature(x))){bank.push(x);seen.add(qSignature(x));added++}});DB.bank=bank;return added}
$('#saveQuiz').onclick=()=>{const title=$('#quizTitle').value.trim();if(!title)return toast('اكتب عنوان الاختبار أولًا');if(!builderQuestions.length)return toast('أضف سؤالًا واحدًا على الأقل');for(const q of builderQuestions){const e=validateQuestion(q);if(e)return toast(e)}const subject=$('#quizSubject').value.trim()||'عام',grade=$('#quizGrade').value;builderQuestions.forEach(q=>{q.subject=subject;q.grade=grade});const obj={id:editingQuizId||uid(),title,subject,grade,section:$('#quizSection').value.trim(),createdAt:Date.now(),settings:{randomQuestions:$('#randomQuestions').checked,randomOptions:$('#randomOptions').checked,showFeedback:$('#showFeedback').checked,speedBonus:$('#speedBonus').checked,bossEnabled:$('#bossEnabled').checked},questions:clone(builderQuestions)};const arr=DB.quizzes,idx=arr.findIndex(x=>x.id===obj.id);if(idx>=0)arr[idx]=obj;else arr.push(obj);DB.quizzes=arr;editingQuizId=obj.id;const added=syncQuestionsToBank(obj.questions,obj);toast(`تم حفظ الاختبار${added?` وإضافة ${added} سؤال للبنك`:''}`);renderDashboard()};
$('#addFromBank').onclick=()=>showBankPicker();
function showBankPicker(){const items=DB.bank;openModal(`<div class="overline">QUESTION BANK</div><h3>أضف من بنك الأسئلة</h3><p>حدد الأسئلة ثم أضفها للاختبار الحالي.</p><div class="modal-list">${items.map(q=>`<label class="modal-item"><input type="checkbox" value="${q.id}" class="bank-pick"><div><b>${typeIcon(q.type)} ${escapeHtml(q.text)}</b><small style="display:block;color:#7b8397">${difficultyName(q.difficulty)} • ${escapeHtml(q.unit||'عام')}</small></div></label>`).join('')}</div><button class="btn btn-primary" id="confirmBankPick" style="margin-top:12px">إضافة المحدد</button>`);$('#confirmBankPick').onclick=()=>{const ids=$$('.bank-pick:checked').map(x=>x.value);const map=new Map(DB.bank.map(q=>[q.id,q]));ids.forEach(id=>{const q=clone(map.get(id));q.id=uid();builderQuestions.push(q)});renderQuestions();closeModal();toast(`تمت إضافة ${ids.length} سؤال`)}}

// ---------- Library ----------
function renderLibrary(){const term=normalize($('#librarySearch').value),list=DB.quizzes.filter(x=>!term||normalize(x.title+' '+x.subject).includes(term));$('#quizLibrary').innerHTML=list.map(x=>`<div class="quiz-card"><div class="quiz-cover">${x.settings?.bossEnabled?'👑':'🎮'}</div><h4>${escapeHtml(x.title)}</h4><p>${escapeHtml(x.subject)} • الصف ${escapeHtml(x.grade||'—')}</p><div class="card-meta"><span class="chip">${x.questions.length} سؤال</span><span class="chip">${x.settings?.randomQuestions?'خلط':'ثابت'}</span>${x.settings?.bossEnabled?'<span class="chip">Boss</span>':''}</div><div class="card-actions"><button class="btn btn-primary" onclick="playQuizById('${x.id}')">تشغيل</button><button class="btn btn-secondary" onclick="editQuiz('${x.id}')">تعديل</button><button class="icon-btn" onclick="exportQuiz('${x.id}')">↥</button><button class="icon-btn danger" onclick="deleteQuiz('${x.id}')">✕</button></div></div>`).join('')||'<p>لا توجد اختبارات مطابقة.</p>'}
$('#librarySearch').oninput=renderLibrary; window.editQuiz=id=>{const q=DB.quizzes.find(x=>x.id===id);if(!q)return;editingQuizId=id;fillBuilder(q);go('builder')};window.deleteQuiz=id=>{if(!confirm('حذف هذا الاختبار؟'))return;DB.quizzes=DB.quizzes.filter(x=>x.id!==id);renderLibrary();renderDashboard()};window.exportQuiz=id=>{const q=DB.quizzes.find(x=>x.id===id);download((q.title||'quiz')+'.json',JSON.stringify(q,null,2))};
$('#importQuiz').onclick=()=>$('#importFile').click();$('#importFile').onchange=e=>{const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=()=>{try{const q=JSON.parse(r.result);if(!Array.isArray(q.questions))throw 0;q.id=uid();q.questions=q.questions.map(x=>Object.assign({difficulty:'medium',unit:'عام',image:''},x));const a=DB.quizzes;a.push(q);DB.quizzes=a;syncQuestionsToBank(q.questions,q);renderLibrary();toast('تم استيراد الاختبار')}catch{toast('ملف غير صالح')}};r.readAsText(f);e.target.value=''};
window.playQuizById=id=>{go('play');setTimeout(()=>$('#playQuizSelect').value=id,0)};

// ---------- Bank ----------
function renderBank(){const term=normalize($('#bankSearch').value),d=$('#bankDifficulty').value,t=$('#bankType').value;const all=DB.bank,gd=$('#bankGrade').value,un=$('#bankUnit').value,filtered=all.filter(q=>(!term||normalize(q.text+' '+(q.tags||[]).join(' ')+' '+q.unit+' '+(q.topic||'')).includes(term))&&(d==='all'||q.difficulty===d)&&(t==='all'||q.type===t)&&(gd==='all'||q.grade===gd)&&(un==='all'||q.unit===un));const counts={easy:all.filter(x=>x.difficulty==='easy').length,medium:all.filter(x=>x.difficulty==='medium').length,hard:all.filter(x=>x.difficulty==='hard').length};$('#bankSummary').innerHTML=`<span class="summary-chip">الإجمالي ${all.length}</span><span class="summary-chip">🟢 سهل ${counts.easy}</span><span class="summary-chip">🟡 متوسط ${counts.medium}</span><span class="summary-chip">🔴 صعب ${counts.hard}</span><span class="summary-chip">ظاهر ${filtered.length}</span>`;$('#questionBank').innerHTML=filtered.map(q=>`<div class="bank-item"><div class="bank-tags"><span class="tag ${q.difficulty}">${difficultyName(q.difficulty)}</span><span class="tag">${typeName(q.type)}</span><span class="tag">${escapeHtml(q.grade||'—')}</span></div>${q.image?`<img class="bank-art" src="${escapeHtml(q.image)}" alt="رسم توضيحي للسؤال">`:''}<h4>${typeIcon(q.type)} ${escapeHtml(q.text)}</h4><p>${escapeHtml(q.subject||'عام')} • ${escapeHtml(q.unit||'عام')}</p>${q.source?`<small style="display:block;color:#8a8496;margin:-2px 0 9px">📘 ${escapeHtml(q.source)}${q.sourcePage?` • ص ${q.sourcePage}`:''}</small>`:''}<div class="card-actions"><button class="btn btn-soft" onclick="bankToBuilder('${q.id}')">استخدام</button><button class="btn btn-soft" onclick="pickBankMedia('${q.id}')">▧ صورة</button><button class="icon-btn danger" onclick="deleteBankQ('${q.id}')">✕</button></div></div>`).join('')||'<p>لا توجد أسئلة مطابقة.</p>'}
['bankSearch','bankDifficulty','bankType','bankGrade','bankUnit'].forEach(id=>$('#'+id).addEventListener(id==='bankSearch'?'input':'change',renderBank));
$('#bankGrade').addEventListener('change',()=>{const g=$('#bankGrade').value;const units=[...new Set(DB.bank.filter(q=>g==='all'||q.grade===g).map(q=>q.unit||'عام'))].sort();$('#bankUnit').innerHTML='<option value="all">كل الوحدات</option>'+units.map(u=>`<option value="${escapeHtml(u)}">${escapeHtml(u)}</option>`).join('');renderBank()});$('#bankGrade').dispatchEvent(new Event('change'));
window.pickBankMedia=id=>openMediaPicker(img=>{const b=DB.bank;const q=b.find(x=>x.id===id);if(q){q.image=img;DB.bank=b;renderBank();toast('تم ربط الصورة بالسؤال')}});
window.chooseFromMedia=id=>openMediaPicker(img=>{const q=builderQuestions.find(x=>x.id===id);if(q){q.image=img;renderQuestions();toast('تم اختيار الصورة للسؤال')}});
window.bankToBuilder=id=>{const q=clone(DB.bank.find(x=>x.id===id));if(!q)return;q.id=uid();builderQuestions.push(q);renderQuestions();go('builder');toast('تمت إضافة السؤال إلى الاختبار الحالي')};window.deleteBankQ=id=>{if(!confirm('حذف السؤال من بنك الأسئلة؟'))return;DB.bank=DB.bank.filter(x=>x.id!==id);renderBank();renderGenerator()};
$('#importFromQuizzes').onclick=()=>{let added=0;DB.quizzes.forEach(q=>added+=syncQuestionsToBank(q.questions,q));renderBank();toast(added?`تمت إضافة ${added} سؤال جديد`:'كل أسئلة الاختبارات موجودة مسبقًا')};
$('#openBankAdd').onclick=()=>openBankAdd();
function openBankAdd(){openModal(`<div class="overline">NEW QUESTION</div><h3>إضافة سؤال إلى البنك</h3><div class="modal-grid"><label>نوع السؤال<select id="baType"><option value="single">اختيار واحد</option><option value="multi">اختيارات متعددة</option><option value="tf">صح / خطأ</option><option value="short">إجابة قصيرة</option><option value="order">ترتيب</option><option value="match">مطابقة</option></select></label><label>الصعوبة<select id="baDifficulty"><option value="easy">سهل</option><option value="medium" selected>متوسط</option><option value="hard">صعب</option></select></label><label>المادة<input id="baSubject" value="المهارات الرقمية"></label><label>الصف<select id="baGrade"><option>السابع</option><option>الثامن</option><option>التاسع</option><option>العاشر</option><option>الحادي عشر</option><option>الثاني عشر</option></select></label><label>الوحدة / الموضوع<input id="baUnit" value="عام"></label><label>الوقت بالثواني<input id="baTime" type="number" value="20"></label></div><button type="button" class="btn btn-soft" style="margin-top:12px" id="baPickMedia">▧ اختر صورة من مكتبة الصور</button><div id="baPreviewMedia" style="margin-top:8px"></div><label style="display:block;margin-top:10px">🖼 صورة السؤال (اختيارية)<input id="baImage" type="file" accept="image/jpeg,image/png,image/webp,image/gif"><small>يمكنك اختيار رسم من الكتاب أو صورة توضيحية، وسيتم تصغيرها تلقائيًا قبل الحفظ.</small></label><label style="display:block;margin-top:10px">نص السؤال<textarea id="baText" style="width:100%;min-height:75px;border:1px solid #e8eaf1;border-radius:11px;padding:10px"></textarea></label><div id="baDynamic" style="margin-top:10px"></div><button class="btn btn-primary" id="saveBankQ" style="margin-top:12px">حفظ في البنك</button>`);const render=()=>{const t=$('#baType').value;let h='';if(t==='single'||t==='multi')h=`<label>الخيارات — كل خيار في سطر<textarea id="baLines" style="width:100%;min-height:100px"></textarea></label><label style="display:block;margin-top:7px">رقم/أرقام الإجابة الصحيحة (مثال 1 أو 1,3)<input id="baCorrect" placeholder="1"></label>`;if(t==='tf')h=`<label>الإجابة الصحيحة<select id="baTF"><option value="true">صح</option><option value="false">خطأ</option></select></label>`;if(t==='short')h=`<label>الإجابات المقبولة — كل إجابة في سطر<textarea id="baLines" style="width:100%;min-height:90px"></textarea></label>`;if(t==='order')h=`<label>الخطوات بالترتيب الصحيح — كل خطوة في سطر<textarea id="baLines" style="width:100%;min-height:110px"></textarea></label>`;if(t==='match')h=`<label>أزواج المطابقة — كل سطر بالشكل: العنصر | المطابقة<textarea id="baLines" placeholder="CPU | تنفيذ التعليمات" style="width:100%;min-height:110px"></textarea></label>`;$('#baDynamic').innerHTML=h};$('#baType').onchange=render;render();let baSelectedImage='';$('#baPickMedia').onclick=()=>openMediaPicker(url=>{baSelectedImage=url;$('#baPreviewMedia').innerHTML=`<img src="${escapeHtml(url)}" style="width:190px;max-height:140px;object-fit:contain;border-radius:14px" alt="معاينة">`});$('#saveBankQ').onclick=async()=>{try{const t=$('#baType').value,q=blankQuestion(t);q.text=$('#baText').value.trim();if(!q.text)return toast('اكتب نص السؤال');q.difficulty=$('#baDifficulty').value;q.subject=$('#baSubject').value.trim()||'عام';q.grade=$('#baGrade').value;q.unit=$('#baUnit').value.trim()||'عام';q.time=+$('#baTime').value||20;if(t==='single'||t==='multi'){q.options=$('#baLines').value.split(/\n/).map(x=>x.trim()).filter(Boolean);q.correct=$('#baCorrect').value.split(',').map(x=>+x.trim()-1).filter(x=>x>=0&&x<q.options.length);if(q.options.length<2||!q.correct.length)return toast('تحقق من الخيارات والإجابة الصحيحة')}if(t==='tf')q.correct=$('#baTF').value==='true';if(t==='short')q.answers=$('#baLines').value.split(/\n/).map(x=>x.trim()).filter(Boolean);if(t==='order')q.items=$('#baLines').value.split(/\n/).map(x=>x.trim()).filter(Boolean);if(t==='match')q.pairs=$('#baLines').value.split(/\n/).map(x=>x.split('|').map(y=>y.trim())).filter(x=>x.length>=2&&x[0]&&x[1]).map(x=>({left:x[0],right:x[1]}));if(baSelectedImage)q.image=baSelectedImage;if($('#baImage')?.files?.[0])q.image=await optimizeImage($('#baImage').files[0]);const e=validateQuestion(q);if(e)return toast(e);const b=DB.bank;if(b.some(x=>qSignature(x)===qSignature(q)))return toast('هذا السؤال موجود مسبقًا');b.push(q);DB.bank=b;closeModal();renderBank();renderGenerator();toast('تمت إضافة السؤال للبنك')}catch{toast('تعذر حفظ السؤال، تحقق من البيانات')}}}

// ---------- Solo game ----------
function renderPlaySelect(){const q=DB.quizzes;$('#playQuizSelect').innerHTML=q.map(x=>`<option value="${x.id}">${escapeHtml(x.title)}</option>`).join('');$('#playSetup').classList.remove('hidden');$('#gameArea').classList.add('hidden')}
$('#startQuiz').onclick=()=>{const quiz=DB.quizzes.find(x=>x.id===$('#playQuizSelect').value),name=$('#studentName').value.trim();if(!quiz)return toast('اختر اختبارًا');if(!name)return toast('اكتب اسم الطالب');startGame(quiz,name,$('#playMode').value,$('#studentTeam').value.trim())};
function prepareQuestions(quiz,mode){let qs=clone(quiz.questions);if(quiz.settings?.randomQuestions)qs=shuffle(qs);if(quiz.settings?.randomOptions){qs.forEach(q=>{if(q.type==='single'||q.type==='multi'){const paired=q.options.map((text,i)=>({text,correct:q.correct.includes(i)})),sh=shuffle(paired);q.options=sh.map(x=>x.text);q.correct=sh.map((x,i)=>x.correct?i:-1).filter(i=>i>=0)}})}if((mode==='boss'||quiz.settings?.bossEnabled)&&qs.length){qs[qs.length-1]._boss=true;qs[qs.length-1].points=(qs[qs.length-1].points||1000)*2}return qs}
function startGame(quiz,name,mode,team=''){const qs=prepareQuestions(quiz,mode),scored=qs.filter(q=>q.type!=='poll');game={quiz,name,team,mode,qs,index:0,score:0,maxScore:scored.reduce((a,q)=>a+(q.points||0),0),correct:0,scoredTotal:scored.length,started:Date.now(),answers:[],timer:null,timeLeft:0,selected:null};$('#playSetup').classList.add('hidden');$('#gameArea').classList.remove('hidden');renderGameQuestion()}
function renderGameQuestion(){clearInterval(game.timer);const q=game.qs[game.index];game.selected=q.type==='multi'?[]:null;game.timeLeft=game.mode==='focus'?9999:(q.time||20);const pct=(game.index/game.qs.length)*100;$('#gameArea').innerHTML=`<div class="game-top"><div><b>${escapeHtml(game.name)}</b><small>${game.team?' • '+escapeHtml(game.team):''} • ${game.index+1} من ${game.qs.length}</small></div><div class="timer" id="timerText">${game.mode==='focus'?'∞':game.timeLeft}</div></div><div class="game-progress"><div style="width:${pct}%"></div></div><div class="game-card ${q._boss?'boss':''}">${q._boss?'<div class="boss-banner">👑 سؤال الزعيم — النقاط مضاعفة</div>':''}${q.image?`<img class="question-image" src="${q.image}">`:''}<h3>${escapeHtml(q.text)}</h3>${gameAnswerUI(q)}<div id="feedbackBox"></div><div class="game-bottom"><span>${game.mode==='zen'?'وضع بدون ترتيب':`النقاط: <b>${Math.round(game.score)}</b>`}</span><button class="btn btn-primary" id="submitAnswer">${q.type==='poll'?'إرسال الرأي':'تأكيد الإجابة'}</button></div></div>`;$('#submitAnswer').onclick=submitGameAnswer;if(game.mode!=='focus'){game.timer=setInterval(()=>{game.timeLeft--;const el=$('#timerText');if(el)el.textContent=game.timeLeft;if(game.timeLeft<=0){clearInterval(game.timer);submitGameAnswer(true)}},1000)}setTimeout(enableDragOrder,50)}
function gameAnswerUI(q){if(q.type==='single'||q.type==='multi'||q.type==='poll')return `<div class="answers">${q.options.map((o,i)=>`<button class="answer-btn" onclick="selectAnswer(${i},this)">${escapeHtml(o)}</button>`).join('')}</div>`;if(q.type==='tf')return `<div class="answers"><button class="answer-btn" onclick="selectAnswer(true,this)">✅ صح</button><button class="answer-btn" onclick="selectAnswer(false,this)">❌ خطأ</button></div>`;if(q.type==='short')return `<div class="answers" style="grid-template-columns:1fr"><input id="shortGameAnswer" class="short-answer" placeholder="اكتب الإجابة هنا..."></div>`;if(q.type==='order'){const items=shuffle(q.items).map(text=>({text,key:uid()}));game.selected=items;return `<div class="order-list" id="orderList">${orderItemsHtml(items)}</div>`}if(q.type==='match'){const rights=shuffle(q.pairs.map(p=>p.right));game.selected={};return `<div class="match-grid">${q.pairs.map((p,i)=>`<div class="match-row"><div class="match-left">${escapeHtml(p.left)}</div><select onchange="setMatch(${i},this.value)"><option value="">اختر المطابقة...</option>${rights.map(r=>`<option value="${escapeHtml(r)}">${escapeHtml(r)}</option>`).join('')}</select></div>`).join('')}</div>`}return ''}
function orderItemsHtml(items){return items.map(it=>`<div class="order-item" draggable="true" data-key="${it.key}"><span>⠿ ${escapeHtml(it.text)}</span><button class="icon-btn" onclick="moveOrder('${it.key}',-1)">↑</button><button class="icon-btn" onclick="moveOrder('${it.key}',1)">↓</button></div>`).join('')}
function enableDragOrder(){const list=$('#orderList');if(!list)return;let dragged=null;list.querySelectorAll('.order-item').forEach(el=>{el.addEventListener('dragstart',()=>{dragged=el;el.classList.add('dragging')});el.addEventListener('dragend',()=>{el.classList.remove('dragging');const keys=[...list.querySelectorAll('.order-item')].map(x=>x.dataset.key);game.selected=keys.map(k=>game.selected.find(x=>x.key===k));dragged=null});el.addEventListener('dragover',e=>{e.preventDefault();if(!dragged||dragged===el)return;const rect=el.getBoundingClientRect();list.insertBefore(dragged,e.clientY<rect.top+rect.height/2?el:el.nextSibling)})})}
window.selectAnswer=(val,el)=>{const q=game.qs[game.index];if(q.type==='multi'){const i=game.selected.indexOf(val);if(i>=0){game.selected.splice(i,1);el.classList.remove('selected')}else{game.selected.push(val);el.classList.add('selected')}}else{game.selected=val;$$('.answer-btn').forEach(x=>x.classList.remove('selected'));el.classList.add('selected')}};
window.moveOrder=(key,dir)=>{const i=game.selected.findIndex(x=>x.key===key),n=i+dir;if(n<0||n>=game.selected.length)return;[game.selected[i],game.selected[n]]=[game.selected[n],game.selected[i]];$('#orderList').innerHTML=orderItemsHtml(game.selected);enableDragOrder()};window.setMatch=(i,v)=>{game.selected[i]=v};
function evaluateAnswer(q,ans){if(q.type==='single')return ans===q.correct[0];if(q.type==='multi')return [...(ans||[])].sort().join(',')===[...q.correct].sort().join(',');if(q.type==='tf')return ans===q.correct;if(q.type==='short')return q.answers.some(a=>normalize(a)===normalize(ans));if(q.type==='order')return ans.map(x=>x.text).join('|')===q.items.join('|');if(q.type==='match')return q.pairs.every((p,i)=>ans?.[i]===p.right);if(q.type==='poll')return null;return false}
function submitGameAnswer(timeout=false){if($('#submitAnswer')?.disabled)return;clearInterval(game.timer);const q=game.qs[game.index];let ans=game.selected;if(q.type==='short')ans=$('#shortGameAnswer').value.trim();if(!timeout&&q.type!=='short'&&q.type!=='order'&&q.type!=='match'&&ans===null)return toast('اختر إجابة أولًا');const correct=evaluateAnswer(q,ans);const speedRatio=game.mode==='focus'?1:Math.max(0,game.timeLeft/(q.time||20));const bonus=(game.quiz.settings?.speedBonus||game.mode==='speed')?(.6+.4*speedRatio):1;let earned=correct===true?Math.round((q.points||0)*bonus):0;if(game.mode==='zen')earned=0;game.score+=earned;if(correct===true)game.correct++;game.answers.push({qid:q.id,qtext:q.text,correct,earned,time:(q.time||20)-(game.mode==='focus'?(q.time||20):game.timeLeft)});$('#submitAnswer').disabled=true;const fb=$('#feedbackBox');fb.innerHTML=`<div class="feedback">${timeout?'⏱️ انتهى الوقت. ':''}${q.type==='poll'?'📊 تم تسجيل رأيك':correct?'✅ إجابة صحيحة':'❌ إجابة غير صحيحة'}${q.type==='poll'||game.mode==='zen'?'':` • +${earned} نقطة`}</div>`;if(game.quiz.settings?.showFeedback&&(q.type==='single'||q.type==='multi'))$$('.answer-btn').forEach((b,i)=>{if(q.correct.includes(i))b.classList.add('correct');else if(b.classList.contains('selected'))b.classList.add('wrong')});setTimeout(()=>{game.index++;if(game.index>=game.qs.length)finishGame();else renderGameQuestion()},900)}
function finishGame(){clearInterval(game.timer);const elapsed=Math.round((Date.now()-game.started)/1000),percent=game.scoredTotal?Math.round(game.correct/game.scoredTotal*100):100,result={id:uid(),student:game.name,team:game.team,quizId:game.quiz.id,quizTitle:game.quiz.title,score:Math.round(game.score),maxScore:game.maxScore,percent,correct:game.correct,total:game.scoredTotal,seconds:elapsed,date:Date.now(),mode:game.mode,answers:game.answers};const arr=DB.results;arr.push(result);DB.results=arr;$('#gameArea').innerHTML=`<div class="panel finish-card"><div class="score-ring" style="--score:${percent*3.6}deg"><b>${percent}%</b></div><h2>أحسنت يا ${escapeHtml(game.name)} 👏</h2><p>إجابات صحيحة: ${game.correct} من ${game.scoredTotal}</p>${game.mode==='zen'?'':'<h3>'+Math.round(game.score)+' نقطة</h3>'}<p>الوقت: ${formatTime(elapsed)}</p><div class="inline-actions" style="justify-content:center"><button class="btn btn-primary" onclick="restartCurrent()">طالب آخر</button><button class="btn btn-secondary" onclick="go('results')">عرض النتائج</button></div></div>`;renderDashboard()}
window.restartCurrent=()=>{$('#studentName').value='';renderPlaySelect()};

// ---------- Results ----------
function renderResults(){const r=DB.results,avg=r.length?Math.round(r.reduce((a,x)=>a+(x.percent||0),0)/r.length):0,best=r.length?Math.max(...r.map(x=>x.percent||0)):0,mastery=r.length?Math.round(r.filter(x=>(x.percent||0)>=70).length/r.length*100):0;$('#resultsSummary').innerHTML=`<div class="stat-card"><div><span>المحاولات</span><strong>${r.length}</strong></div></div><div class="stat-card"><div><span>متوسط الأداء</span><strong>${avg}%</strong></div></div><div class="stat-card"><div><span>أعلى نتيجة</span><strong>${best}%</strong></div></div><div class="stat-card"><div><span>إتقان 70%+</span><strong>${mastery}%</strong></div></div>`;$('#resultsTable').innerHTML=r.slice().reverse().map(x=>`<tr><td>${escapeHtml(x.student)}</td><td>${escapeHtml(x.quizTitle)}</td><td>${escapeHtml(x.team||'—')}</td><td>${x.score}/${x.maxScore}</td><td>${x.percent}%</td><td>${formatTime(x.seconds)}</td><td>${new Date(x.date).toLocaleString('ar-JO')}</td></tr>`).join('')||'<tr><td colspan="7">لا توجد نتائج بعد.</td></tr>';const qstats={};r.forEach(x=>(x.answers||[]).forEach(a=>{if(a.correct===null)return;const k=a.qtext||a.qid;qstats[k]??={wrong:0,total:0};qstats[k].total++;if(!a.correct)qstats[k].wrong++}));const hardest=Object.entries(qstats).sort((a,b)=>(b[1].wrong/b[1].total)-(a[1].wrong/a[1].total))[0];$('#hardestQuestion').textContent=hardest?hardest[0]:'—';$('#hardestRate').textContent=hardest?`${Math.round(hardest[1].wrong/hardest[1].total*100)}% أخطأوا فيه`:'لا توجد بيانات';const br=[...r].sort((a,b)=>(b.percent||0)-(a.percent||0))[0];$('#bestStudent').textContent=br?.student||'—';$('#bestStudentRate').textContent=br?`${br.percent}% في ${br.quizTitle}`:'لا توجد بيانات'}
$('#clearResults').onclick=()=>{if(confirm('مسح جميع النتائج؟')){DB.results=[];renderResults();renderDashboard()}};$('#exportResults').onclick=()=>{const rows=[['الطالب','الاختبار','الفريق','النقاط','الحد الأعلى','النسبة','الوقت بالثواني','التاريخ'],...DB.results.map(x=>[x.student,x.quizTitle,x.team||'',x.score,x.maxScore,x.percent,x.seconds,new Date(x.date).toLocaleString('ar-JO')])];const csv='\ufeff'+rows.map(row=>row.map(v=>'"'+String(v).replace(/"/g,'""')+'"').join(',')).join('\n');download('quiznova-results.csv',csv,'text/csv;charset=utf-8')};

// ---------- Live classroom: QR + PIN + teams + analytics ----------
async function checkServer(){
  if(!location.protocol.startsWith('http')){serverInfo=null;return false}
  try{const r=await fetch('/api/status',{cache:'no-store'});if(!r.ok)throw 0;serverInfo=await r.json();$('#serverBadge').textContent='● الصف المباشر جاهز';$('#serverBadge').classList.add('live');return true}
  catch{serverInfo=null;return false}
}
async function renderLiveLanding(){
  clearInterval(livePollTimer); const ok=await checkServer();
  $('#liveOffline').classList.toggle('hidden',ok); $('#liveSetup').classList.toggle('hidden',!ok); $('#liveHost').classList.add('hidden');
  if(ok){
    $('#liveQuizSelect').innerHTML=DB.quizzes.map(q=>`<option value="${q.id}">${escapeHtml(q.title)} — ${q.questions.length} سؤال</option>`).join('');
    $('#serverAddress').textContent=serverInfo.student_url||location.origin+'/student.html';
    const teamSel=$('#liveTeamCount'); const modeSel=$('#liveMode');
    $('#liveQuizSelect').onchange=()=>{const selected=DB.quizzes.find(x=>x.id===$('#liveQuizSelect').value);$('#liveSection').value=selected?.section||''};$('#liveQuizSelect').onchange();$('#liveBackground').value=DB.settings?.scene||'cartoon';
    const sync=()=>{teamSel.closest('label').style.opacity=modeSel.value==='teams'?'1':'.45';teamSel.disabled=modeSel.value!=='teams'};modeSel.onchange=sync;sync();
  }
}
$('#createLiveRoom').onclick=async()=>{
  const quiz=DB.quizzes.find(q=>q.id===$('#liveQuizSelect').value); if(!quiz)return toast('اختر اختبارًا أولًا');
  try{
    const payload={quiz,playType:$('#liveMode').value,gameMode:$('#liveGameMode').value,variantMode:$('#liveVariantMode').value,teamCount:+$('#liveTeamCount').value,section:$('#liveSection').value.trim(),background:$('#liveBackground').value,showFeedback:$('#liveShowFeedback').checked,powerups:$('#livePowerups').checked};
    const r=await fetch('/api/room/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}); const d=await r.json(); if(!d.ok)throw 0;
    liveRoom=d.code; liveHostToken=d.hostToken||''; liveStageToken=d.stageToken||''; liveSaved=false; liveAutoRevealIndex=-1; $('#liveSetup').classList.add('hidden'); $('#liveHost').classList.remove('hidden'); renderLiveHost(d,quiz); startLivePolling();
  }catch{toast('تعذر إنشاء الغرفة. تحقق من اتصال الخادم بالإنترنت ثم حاول مرة أخرى')}
};
function renderLiveHost(data,quiz){
  const join=data.join_url||`${data.student_url}?code=${encodeURIComponent(data.code)}`;
  $('#liveHost').innerHTML=`
  <div class="room-shell">
    <div class="sky-room-settings"><h3>⚙ إعدادات الاختبار</h3><div class="sky-setting"><span>نمط اللعب</span><b>${data.playType==='teams'?'👥 مجموعات':'👤 فردي'}</b></div><div class="sky-setting"><span>حماية من النقل</span><b>${data.variantMode==='models4'?'نماذج A/B/C/D':data.variantMode==='options'?'ترتيب خيارات مختلف':'موحّد'}</b></div><div class="sky-setting"><span>الاختبار</span><b>${escapeHtml(quiz.title)}</b></div><div class="sky-setting"><span>الشعبة</span><b>${escapeHtml($('#liveSection').value.trim()||'لم تُحدّد')}</b></div><div class="sky-setting"><span>الخلفية الرسمية</span><b>${$('#liveBackground').selectedOptions[0]?.textContent||'سماوية'}</b></div></div>
    <div class="room-code-card"><div class="sky-room-title">🎮 غرفة الألعاب — QuizNova Arena</div>
      <div class="host-join-grid">
        <div class="qr-wrap"><img id="roomQr" src="/api/qr?format=png&text=${encodeURIComponent(join)}" alt="QR دخول الطلاب" loading="eager"><div class="qr-fallback" id="qrFallback">تعذر إظهار الرمز. انسخ الرابط بالزر أدناه.</div></div>
        <div class="join-copy"><small>جاهز للدخول</small><div class="room-code">${escapeHtml(data.code)}</div><p>الطالب يمسح QR بالكاميرا أو يفتح الرابط ثم يكتب الرمز.</p><div class="security-badge">${data.variantMode==='models4'?'🔀 نماذج A/B/C/D':data.variantMode==='same'?'📺 نموذج موحّد':'🛡️ خيارات مختلفة لكل جهاز'}</div><b>${escapeHtml(join)}</b></div>
      </div>
      <div class="host-actions"><button class="btn btn-white" id="liveStartBtn">▶ ابدأ أول سؤال</button><button class="btn btn-glass" id="liveNextBtn">إظهار الترتيب 🏆</button><button class="btn btn-skip" id="liveSkipBtn" title="تخطّ السؤال فورًا، دون انتظار أي طالب">⏭ تخطّي السؤال</button><button class="btn btn-glass" id="openStageBtn">▣ شاشة العرض</button><button class="btn btn-glass" id="copyJoinBtn">نسخ الرابط</button><button class="btn btn-glass" id="liveEndBtn">إنهاء</button></div>
    </div>
    <div class="panel players-panel"><div class="panel-head"><div><div class="overline">LOBBY</div><h3>الطلاب المنضمون <span id="livePlayerCount">0</span></h3><p>${data.playType==='teams'?'سيتم توزيع الطلاب تلقائيًا على الفرق بالتساوي.':'اللعب فردي؛ لكل طالب ترتيبه ونقاطه.'}</p></div></div><div id="livePlayers" class="players-grid"></div></div>
  </div>
  <div class="live-game-grid">
    <div class="panel live-question-panel">
      <div class="live-question-header"><div><div class="overline">LIVE QUESTION</div><h3 id="liveQuestionTitle">بانتظار بدء اللعبة</h3></div><span class="pill" id="liveClock">⏱ --</span><span class="pill" id="liveAnswerCount">0 إجابة</span></div>
      <div id="liveQuestionBody"><div class="tip-box"><strong>🎮 ${escapeHtml(quiz.title)}</strong><p>ابدأ عندما يكتمل دخول الطلاب. يمكنك إبقاء رمز QR ظاهرًا حتى يدخل المتأخرون.</p></div></div>
    </div>
    <div class="panel"><div class="panel-head"><div><div class="overline">LEADERBOARD</div><h3 id="leaderTitle">الترتيب المباشر</h3></div></div><div id="liveLeaderboard" class="leaderboard"></div><div id="liveReactions" class="reaction-strip"></div></div>
  </div>`;
  const qrEl=$('#roomQr');let qrAttempt=0;
  qrEl.onerror=()=>{if(qrAttempt++===0){qrEl.src='/api/qr?format=svg&text='+encodeURIComponent(join)}else{qrEl.style.display='none';$('#qrFallback').style.display='block';toast('تعذر تحميل QR؛ رابط الدخول ورمز الغرفة متاحان')}};
  $('#liveStartBtn').onclick=()=>liveControl('start'); $('#liveNextBtn').onclick=()=>liveControl('next');$('#liveSkipBtn').onclick=()=>{if(confirm('تخطي السؤال الحالي والانتقال مباشرة إلى السؤال التالي؟'))liveControl('skip')}; $('#liveEndBtn').onclick=()=>liveControl('end');
  $('#copyJoinBtn').onclick=()=>navigator.clipboard?.writeText(join).then(()=>toast('تم نسخ رابط الدخول')).catch(()=>toast('انسخ الرابط الظاهر يدويًا')); $('#openStageBtn').onclick=()=>window.open('/stage.html?code='+encodeURIComponent(data.code)+'&stage='+encodeURIComponent(liveStageToken),'quiznova_stage','noopener');
}
async function liveControl(action){
  try{const r=await fetch('/api/room/control',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code:liveRoom,action,hostToken:liveHostToken})});const d=await r.json();if(!d.ok)throw 0;if(action==='end')toast('تم إنهاء الجلسة')}
  catch{toast('تعذر تنفيذ الأمر')}
}
function startLivePolling(){
  clearInterval(livePollTimer); const poll=async()=>{if(!liveRoom)return;try{const r=await fetch('/api/room/state?code='+encodeURIComponent(liveRoom)+'&host='+encodeURIComponent(liveHostToken),{cache:'no-store'});const d=await r.json();if(d.ok)updateLiveHost(d.room)}catch{}};poll();livePollTimer=setInterval(poll,650)
}
function renderPlayerCards(players){
  return players.map(p=>`<div class="player-chip"><div class="player-avatar"><img src="/assets/avatars/${/^\d{2}$/.test(p.avatar||'')?p.avatar:'01'}.svg" alt=""></div><div><strong>${escapeHtml(p.name)} ${p.model?`<span class="model-tag">${escapeHtml(p.model)}</span>`:''}</strong><small>${escapeHtml(p.team||'فردي')} • ${p.score} نقطة</small></div></div>`).join('')||'<p>بانتظار دخول الطلاب...</p>'
}
function renderLeaderboard(room){
  const isTeams=room.playType==='teams'; const leaders=isTeams?room.teams:room.leaders;
  $('#leaderTitle').textContent=isTeams?'ترتيب المجموعات':'الترتيب الفردي';
  return (leaders||[]).slice(0,12).map((p,i)=>`<div class="leader-row"><div class="leader-rank">${i+1}</div>${!isTeams?`<img class="sky-leader-avatar" src="/assets/avatars/${/^\d{2}$/.test(p.avatar||'')?p.avatar:'01'}.svg" alt="">`:''}<div><strong>${escapeHtml(p.name)}</strong><small>${isTeams?`${p.members||0} طلاب • ${p.correct||0} صحيحة`:escapeHtml(p.team||'')}</small></div><b>${p.score}</b></div>`).join('')||'<p>لا يوجد ترتيب بعد.</p>'
}
function renderQuestionStats(room){
  const q=room.question,st=room.stats||{};
  if(st.mixed){
    const cards=(st.models||[]).map(m=>`<div class="model-round-card"><div class="model-letter">${escapeHtml(m.model)}</div><div><b>نموذج ${escapeHtml(m.model)}</b><p>${escapeHtml(m.question)}</p><small>${m.answered}/${m.total} أجابوا • ${m.correct} صحيحة</small></div></div>`).join('');
    const good=(st.correctStudents||[]).map(escapeHtml).join('، ')||'—',bad=(st.wrongStudents||[]).map(escapeHtml).join('، ')||'—';
    return `<div class="mixed-round-banner"><span>🔀</span><div><b>الجولة ${room.index+1}: نماذج مختلفة</b><p>كل مجموعة نموذج ترى سؤالًا بترتيب مختلف؛ النتائج أدناه مجمعة للجولة.</p></div></div>
      <div class="live-kpis"><div class="live-kpi"><b>${st.answered||0}</b><span>أجابوا</span></div><div class="live-kpi good"><b>${st.correct||0}</b><span>صحيحة</span></div><div class="live-kpi bad"><b>${st.wrong||0}</b><span>خاطئة</span></div><div class="live-kpi wait"><b>${st.pending||0}</b><span>لم يجيبوا</span></div></div>
      <div class="model-round-grid">${cards}</div>
      <div class="student-lists"><div class="mini-list"><b>✅ صحيح في هذه الجولة</b><p>${good}</p></div><div class="mini-list"><b>❌ أخطأ في هذه الجولة</b><p>${bad}</p></div></div>`;
  }
  if(!q)return '<div class="tip-box"><strong>بانتظار السؤال</strong><p>اضغط «ابدأ أول سؤال» عندما يصبح الطلاب جاهزين.</p></div>';
  const bars=(st.distribution||[]).map(x=>{const max=Math.max(1,...(st.distribution||[]).map(y=>y.count||0));const w=Math.round((x.count||0)/max*100);return `<div class="answer-bar ${x.correct?'correct':''}"><label>${escapeHtml(x.label)}</label><div class="bar-track"><div class="bar-fill" style="width:${w}%"></div></div><b>${x.count}</b></div>`}).join('');
  const good=(st.correctStudents||[]).map(escapeHtml).join('، ')||'—'; const bad=(st.wrongStudents||[]).map(escapeHtml).join('، ')||'—';
  return `<div class="live-question-text">${escapeHtml(q.text)}</div>${q.image?`<img class="host-question-image" src="${escapeHtml(q.image)}" alt="صورة السؤال">`:''}
    <div class="live-kpis"><div class="live-kpi"><b>${st.answered||0}</b><span>أجابوا</span></div><div class="live-kpi good"><b>${st.correct||0}</b><span>صحيحة</span></div><div class="live-kpi bad"><b>${st.wrong||0}</b><span>خاطئة</span></div><div class="live-kpi wait"><b>${st.pending||0}</b><span>لم يجيبوا</span></div></div>
    ${bars?`<div class="answer-bars">${bars}</div>`:''}
    <div class="correct-answer-box"><b>الإجابة الصحيحة:</b> ${escapeHtml(room.correctAnswer||'—')} ${st.answered?`• دقة الإجابات الحالية ${st.accuracy||0}%`:''}</div>
    <div class="student-lists"><div class="mini-list"><b>✅ أجابوا بشكل صحيح</b><p>${good}</p></div><div class="mini-list"><b>❌ يحتاجون مراجعة هذا السؤال</b><p>${bad}</p></div></div>`;
}

function renderRoundResults(room){
  const isTeams=room.playType==='teams',leaders=isTeams?(room.teams||[]):(room.leaders||[]),st=room.stats||{},medals=['🥇','🥈','🥉'];
  const podium=leaders.slice(0,3).map((p,i)=>`<div class="round-podium-card p${i+1}"><div class="round-medal">${medals[i]}</div>${!isTeams?`<img class="sky-podium-avatar" src="/assets/avatars/${/^\d{2}$/.test(p.avatar||'')?p.avatar:'01'}.svg" alt="">`:''}<b>${escapeHtml(p.name)}</b><small>${isTeams?`${p.members||0} طلاب • `:''}${p.score} نقطة</small></div>`).join('');
  const rest=leaders.slice(3,8).map((p,i)=>`<div class="round-rank-row"><span>${i+4}</span><b>${escapeHtml(p.name)}</b><strong>${p.score}</strong></div>`).join('');
  return `<div class="round-results-hero"><div class="round-results-title"><span class="trophy-orb">🏆</span><div><div class="overline">ROUND RESULTS</div><h2>ترتيب الجولة ${room.index+1}</h2><p>${st.accuracy||0}% دقة • ${st.correct||0} صحيحة • ${st.wrong||0} خاطئة</p></div></div><div class="round-podium">${podium}</div>${rest?`<div class="round-rest">${rest}</div>`:''}<div class="next-round-note">الترتيب ظاهر الآن للطلاب وشاشة العرض. اضغط «السؤال التالي» للمتابعة.</div></div>`;
}

function renderFinal(room){
  const rows=room.report||[]; const top=room.playType==='teams'?(room.teams||[]):rows;
  const medals=['🥇','🥈','🥉'];
  const podium=top.slice(0,3).map((x,i)=>`<div class="podium-card ${i===0?'first':''}"><span>${medals[i]}</span><b>${escapeHtml(x.name)}</b><small>${x.score} نقطة${x.percent!=null?` • ${x.percent}%`:''}</small></div>`).join('');
  const table=rows.map((x,i)=>`<tr><td>${i+1}</td><td>${escapeHtml(x.name)}</td><td>${escapeHtml(x.team||'—')}</td><td>${x.correct}</td><td>${x.wrong}</td><td>${x.percent}%</td><td>${x.score}</td></tr>`).join('');
  const classGrade=(room.report?.length? Math.round(room.report.reduce((sum,p)=>sum+(p.percent||0),0)/room.report.length*10)/10:0);const sectionText=escapeHtml(room.section||'غير محددة');const qrows=(room.questionReport||[]).map((q,i)=>`<tr><td>${i+1}</td><td>${escapeHtml(q.text)}</td><td>${q.accuracy}%</td><td>${escapeHtml((q.wrongStudents||[]).join('، ')||'—')}</td></tr>`).join(''); return `<div class="overline">FINAL RESULTS</div><h2>انتهت اللعبة 🎉</h2><div class="class-summary"><span>الشعبة: ${sectionText}</span><span>تقييم الشعبة: ${classGrade} / 100</span><span>التاريخ: ${new Date(room.createdAt||Date.now()).toLocaleDateString('ar-JO')}</span></div><div class="final-podium">${podium}</div><div class="report-table"><table><thead><tr><th>#</th><th>الطالب</th><th>الفريق</th><th>صحيح</th><th>خطأ</th><th>الدقة</th><th>النقاط</th></tr></thead><tbody>${table}</tbody></table></div><div style="margin-top:18px" class="overline">تحليل الأسئلة</div><div class="report-table"><table><thead><tr><th>#</th><th>السؤال</th><th>الدقة</th><th>من أخطأ</th></tr></thead><tbody>${qrows}</tbody></table></div><div class="inline-actions" style="margin-top:12px"><button class="btn btn-primary" id="exportLiveReport">تنزيل تقرير Excel منسّق (.xlsx)</button></div>`;
}

function saveLiveSession(room){
  if(liveSaved||room.status!=='finished')return; liveSaved=true;
  const now=Date.now(), qReport=room.questionReport||[], total=room.total||qReport.length;
  const arr=DB.results;
  (room.report||[]).forEach(p=>arr.push({id:uid(),student:p.name,team:p.team||'',quizId:'live_'+liveRoom,quizTitle:'جلسة مباشرة '+liveRoom,score:p.score,maxScore:0,percent:p.percent,correct:p.correct,total,seconds:0,date:now,mode:'live',answers:qReport.map(q=>({qid:'live_q_'+q.index,qtext:q.text,correct:(q.correctStudents||[]).includes(p.name)?true:(q.wrongStudents||[]).includes(p.name)?false:null}))}));
  DB.results=arr; renderDashboard();
}
function liveReportCsv(room){
  if(!liveRoom||!liveHostToken)return toast('مفتاح الغرفة غير متاح');
  const url='/api/room/export.xlsx?code='+encodeURIComponent(liveRoom)+'&host='+encodeURIComponent(liveHostToken);
  const a=document.createElement('a');a.href=url;a.download='QuizNova_'+liveRoom+'_report.xlsx';document.body.appendChild(a);a.click();a.remove();
  toast('جارٍ تنزيل تقرير Excel الملوّن');
}

function updateLiveHost(room){
  if(!$('#livePlayers'))return;
  $('#livePlayerCount').textContent=room.players.length; $('#livePlayers').innerHTML=renderPlayerCards(room.players);
  $('#liveLeaderboard').innerHTML=renderLeaderboard(room);
  const nextBtn=$('#liveNextBtn'),startBtn=$('#liveStartBtn'),skipBtn=$('#liveSkipBtn'),clock=$('#liveClock');
  if(clock)clock.textContent=room.status==='question'?`⏱ ${Math.max(0,Math.ceil(((room.startedAt||0)+(room.roundDurationMs||20000)-Date.now())/1000))} ثانية`:room.status==='results'?'✓ انتهى السؤال':'—';
  if(skipBtn)skipBtn.classList.toggle('hidden',room.status!=='question');
  if(room.status==='lobby'){
    $('#liveQuestionTitle').textContent='بانتظار بدء اللعبة';$('#liveAnswerCount').textContent=`${room.players.length} لاعب`;
    if(nextBtn)nextBtn.textContent='إظهار الترتيب 🏆'; if(startBtn)startBtn.classList.remove('hidden'); return;
  }
  if(startBtn)startBtn.classList.add('hidden');
  if(room.status==='finished'){
    $('#liveQuestionTitle').textContent='النتائج النهائية';$('#liveAnswerCount').textContent='انتهى';$('#liveQuestionBody').innerHTML=renderFinal(room);
    if(nextBtn)nextBtn.classList.add('hidden');saveLiveSession(room);if($('#exportLiveReport'))$('#exportLiveReport').onclick=()=>liveReportCsv(room);return;
  }
  if(nextBtn)nextBtn.classList.remove('hidden');
  if(room.status==='results'){
    $('#liveQuestionTitle').textContent=`نتائج الجولة ${room.index+1}`;$('#liveAnswerCount').textContent='🏆 الترتيب';$('#liveQuestionBody').innerHTML=renderRoundResults(room);
    if(nextBtn)nextBtn.textContent=room.index+1>=room.total?'عرض النتائج النهائية 🎉':'السؤال التالي ⟵';
  }else{
    $('#liveQuestionTitle').textContent=room.variantMode==='models4'?`الجولة ${room.index+1} من ${room.total} — نماذج مختلفة`:`السؤال ${room.index+1} من ${room.total}`;
    $('#liveAnswerCount').textContent=`${room.stats?.answered||0} / ${room.players.length} أجابوا`; $('#liveQuestionBody').innerHTML=renderQuestionStats(room);
    if(nextBtn)nextBtn.textContent='إظهار الترتيب 🏆';
    // The server owns both the timer and the all-answered transition, even if this tab is closed.
  }
  const reacts=room.stats?.reactions||{}; $('#liveReactions').innerHTML=Object.entries(reacts).map(([e,n])=>`<span class="reaction-chip">${e} ${n}</span>`).join('');
}

// ---------- Settings ----------
function loadSettings(){const s=DB.settings;if(s.teacherName)$('#teacherName').value=s.teacherName;if(s.schoolName)$('#schoolName').value=s.schoolName;if(s.platformName)$('#platformName').value=s.platformName;applySettings();if($('#teacherBackground'))$('#teacherBackground').value=s.scene||'cartoon'}
function applySettings(){document.body.dataset.scene=DB.settings.scene||'cartoon';const teacher=$('#teacherName').value||'المعلم',platform=$('#platformName').value||'QuizNova';$('.teacher-card strong').textContent=teacher;$('.brand h1').textContent=platform;document.title=platform+' Arena'}
$('#saveSettings').onclick=()=>{DB.settings={teacherName:$('#teacherName').value,schoolName:$('#schoolName').value,platformName:$('#platformName').value,scene:$('#teacherBackground').value};applySettings();toast('تم حفظ الإعدادات')};$('#exportBackup').onclick=()=>download('quiznova-arena-backup.json',JSON.stringify({quizzes:DB.quizzes,bank:DB.bank,results:DB.results,settings:DB.settings,version:5},null,2));$('#importBackup').onclick=()=>$('#backupFile').click();$('#backupFile').onchange=e=>{const f=e.target.files[0];if(!f)return;const r=new FileReader();r.onload=()=>{try{const d=JSON.parse(r.result);if(!Array.isArray(d.quizzes)||!Array.isArray(d.results))throw 0;DB.quizzes=d.quizzes;DB.results=d.results;DB.bank=Array.isArray(d.bank)?d.bank:DB.bank;DB.settings=d.settings||{};loadSettings();renderDashboard();renderGenerator();toast('تمت استعادة النسخة الاحتياطية')}catch{toast('ملف النسخة غير صالح')}};r.readAsText(f);e.target.value=''};

resetBuilder();loadSettings();renderDashboard();renderGenerator();checkServer();
