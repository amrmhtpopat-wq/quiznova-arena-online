/* BOOYAHJO GAME LAB V2 — sixteen original, working offline classroom minigames.
 * These teacher-preview games use the same reusable lesson rows.
 * No tracking, external dependencies, or student grades in this module.
 */
(function(){'use strict';
let ctx=null,mode='',rows=[],score=0,index=0,cleanups=[];
const $=s=>document.querySelector(s);
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function mix(src){const a=[...src];for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]}return a}
function removeSpaces(v){return Array.from(String(v||'').replace(/[\s\-_.,،.؟!?]/g,''))}
function button(t,fn,cl='button alt'){const b=document.createElement('button');b.className=cl;b.type='button';b.textContent=t;b.onclick=fn;return b}
function finish(){ctx.finish(score)}
function advance(){index++;if(index>=Math.min(rows.length,8))finish();else renderMode()}
function root(html){ctx.container(html);ctx.status('')}
function feedback(text){ctx.status(text)}
function count(text){ctx.updateCounter(text)}
function choicesFor(row,n=4){const wrong=mix([...new Set(rows.map(x=>x.a).filter(x=>x!==row.a))]).slice(0,n-1);return mix([row.a,...wrong])}
function popupNext(host,fn=advance,lab='السؤال التالي ⟵'){host.append(button(lab,fn,'button'))}
function clear(){cleanups.forEach(fn=>{try{fn()}catch(_){}});cleanups=[]}
function playAnagram(){
 if(index>=Math.min(rows.length,8))return finish();const row=rows[index],answer=removeSpaces(row.a);let picked=[],letters=mix(answer.map((letter,i)=>({letter,i})));count((index+1)+' / '+Math.min(rows.length,8));
 root('<div class="playcard"><h3>🔤 رتّب الحروف لتكوين الإجابة</h3><p>'+esc(row.q)+'</p><div class="extra-slots" id="letterAnswer">اختر الحروف بالترتيب</div><div class="extra-letter-pool" id="letterPool"></div><div class="buttons extra-center" id="extraActions"></div></div>');
 const refresh=()=>{const target=$('#letterAnswer');target.textContent=picked.map(x=>x.letter).join('')||'اختر الحروف بالترتيب';const pool=$('#letterPool');pool.replaceChildren();letters.forEach(item=>{const b=button(item.letter,()=>{picked.push(item);refresh()},'extra-letter');b.disabled=picked.some(x=>x.i===item.i);pool.append(b)})};
 const actions=$('#extraActions');actions.append(button('↺ إعادة',()=>{picked=[];refresh()},'button alt'));
 actions.append(button('تحقق ✓',()=>{if(picked.map(x=>x.letter).join('')===answer.join('')){score+=100;feedback('✅ ترتيب صحيح • +100');actions.replaceChildren();popupNext(actions)}else feedback('حاول مرة أخرى، أو اضغط إعادة لإعادة ترتيب الحروف')},'button'));refresh();
}
function playOrder(){
 const items=rows.slice(0,Math.min(rows.length,7));if(index>0)return finish();let list=mix(items.map((x,i)=>({id:i,text:x.q})));count('رتّب '+items.length+' خطوات');
 root('<div class="playcard"><h3>🪜 الترتيب المنطقي</h3><p>رتّب الخطوات التالية حسب ترتيبها الأصلي في محتوى الدرس باستخدام الأسهم، ثم تحقّق.</p><div id="orderList" class="extra-order"></div><div class="buttons extra-center" id="orderActions"></div></div>');
 const paint=()=>{const host=$('#orderList');host.replaceChildren();list.forEach((x,i)=>{const line=document.createElement('div');line.className='extra-order-line';const b=document.createElement('b');b.textContent=(i+1)+' . '+x.text;const actions=document.createElement('div');actions.className='buttons';actions.append(button('↑',()=>{if(i>0){[list[i-1],list[i]]=[list[i],list[i-1]];paint()}},'button alt small'),button('↓',()=>{if(i<list.length-1){[list[i],list[i+1]]=[list[i+1],list[i]];paint()}},'button alt small'));line.append(b,actions);host.append(line)})};
 $('#orderActions').append(button('✅ تحقق من الترتيب',()=>{const right=list.every((x,i)=>x.id===i);if(right){score=100;feedback('ممتاز! رتبت الخطوات بشكل صحيح');$('#orderActions').replaceChildren(button('🏆 إنهاء',finish,'button'))}else feedback('الترتيب غير صحيح بعد. حاول تبديل بعض الخطوات.')}));paint();
}
function playMaze(){
 if(index>=Math.min(rows.length,8))return finish();const row=rows[index],options=choicesFor(row);count('المستوى '+(index+1)+' / '+Math.min(rows.length,8));
 root('<div class="playcard"><div class="extra-maze-path" id="mazePath">'+rows.slice(0,8).map((x,i)=>'<span class="'+(i<index?'done':i===index?'active':'')+'">'+(i+1)+'</span>').join('<i>←</i>')+'</div><h3>🌀 متاهة المعرفة</h3><p>'+esc(row.q)+'</p></div><div class="playchoices" id="mazeChoices"></div><div class="buttons extra-center" id="mazeNext"></div>');
 options.forEach(t=>$('#mazeChoices').append(button('🚪 '+t,()=>{if($('#mazeNext').children.length)return;const right=t===row.a;if(right){score+=100;feedback('✅ وجدت المخرج! +100')}else feedback('حاول مرة أخرى في المحطة التالية. الإجابة الصحيحة: '+row.a);$('#mazeChoices').querySelectorAll('button').forEach(b=>b.disabled=true);popupNext($('#mazeNext'))},'choice')));
}
function playBalloons(){
 if(index>=Math.min(rows.length,8))return finish();const row=rows[index];count((index+1)+' / '+Math.min(rows.length,8));root('<div class="playcard"><h3>🎈 فرقعة بالونات الإجابات</h3><p>'+esc(row.q)+'</p></div><div class="extra-balloons" id="balloons"></div><div class="buttons extra-center" id="balloonNext"></div>');
 choicesFor(row).forEach((t,i)=>{const b=button(t,()=>{if($('#balloonNext').children.length)return;if(t===row.a){score+=100;b.classList.add('popped');feedback('🎉 بالون صحيح! +100')}else{b.classList.add('wrong');feedback('الإجابة الصحيحة: '+row.a)}$('#balloons').querySelectorAll('button').forEach(x=>x.disabled=true);popupNext($('#balloonNext'))},'extra-balloon');b.style.setProperty('--float-delay',(i*.18)+'s');$('#balloons').append(b)});
}
function playMemory(){
 const cards=mix(rows.slice(0,Math.min(rows.length,6)).flatMap((r,i)=>[{id:i,v:r.q,side:'q'},{id:i,v:r.a,side:'a'}]));let revealed=[],solved=new Set(),locked=false;count('0 / '+cards.length/2);
 root('<div class="playcard"><h3>🧠 ذاكرة الأزواج</h3><p>اكشف بطاقتين، وحاول مطابقة السؤال بإجابته.</p><div class="extra-memory" id="memoryGrid"></div><div class="buttons extra-center" id="memoryDone"></div></div>');
 const paint=()=>{const host=$('#memoryGrid');host.replaceChildren();cards.forEach((c,i)=>{const show=solved.has(c.id)||revealed.includes(i);const b=button(show?c.v:'❓',()=>{if(locked||solved.has(c.id)||revealed.includes(i))return;revealed.push(i);paint();if(revealed.length===2){locked=true;const a=cards[revealed[0]],b=cards[revealed[1]];if(a.id===b.id&&a.side!==b.side){solved.add(a.id);score+=50;feedback('✅ زوج صحيح +50');revealed=[];locked=false;count(solved.size+' / '+cards.length/2);paint();if(solved.size===cards.length/2)popupNext($('#memoryDone'),finish,'🏆 إنهاء اللعبة')}else{feedback('لم تتطابق البطاقتان');const t=setTimeout(()=>{revealed=[];locked=false;paint()},850);cleanups.push(()=>clearTimeout(t))}}},'extra-memory-card'+(show?' showing':'')+(solved.has(c.id)?' solved':''));host.append(b)})};paint();
}
function playHidden(){
 const image=window.BOOYAH_GAME_LAB_IMAGE||'/assets/backgrounds/quiznova-learning.webp';if(index>=Math.min(rows.length,8))return finish();const row=rows[index],tiles=16,uncovered=new Set();count((index+1)+' / '+Math.min(rows.length,8));
 root('<div class="playcard"><h3>🖼️ الصورة المخفية</h3><p>اكشف المربعات، ثم حاول الإجابة عن السؤال: '+esc(row.q)+'</p><div class="extra-hidden" id="hiddenImage" style="background-image:url(&quot;'+esc(image)+'&quot;)"></div><div class="buttons extra-center" id="hiddenActions"></div></div>');
 const host=$('#hiddenImage');for(let i=0;i<tiles;i++){const b=button('?',()=>{uncovered.add(i);b.classList.add('revealed');b.disabled=true;feedback('تم كشف '+uncovered.size+' من '+tiles+' مربعات')},'extra-hidden-tile');host.append(b)}
 $('#hiddenActions').append(button('👀 كشف الإجابة',()=>{score+=Math.max(10,100-uncovered.size*5);feedback('💡 الإجابة: '+row.a);host.querySelectorAll('button').forEach(b=>{b.classList.add('revealed');b.disabled=true});$('#hiddenActions').replaceChildren();popupNext($('#hiddenActions'))},'button'));
}
function playCloze(){
 if(index>=Math.min(rows.length,8))return finish();const row=rows[index],text=row.q.includes('___')?row.q:row.q+' : ______';count((index+1)+' / '+Math.min(rows.length,8));
 root('<div class="playcard"><h3>✍️ أكمل الفراغ</h3><p class="extra-gap">'+esc(text).replace(/___+/g,'<span>.................</span>')+'</p></div><div class="playchoices" id="clozeChoices"></div><div class="buttons extra-center" id="clozeNext"></div>');
 choicesFor(row).forEach(answer=>$('#clozeChoices').append(button(answer,()=>{if($('#clozeNext').children.length)return;const yes=answer===row.a;if(yes)score+=100;feedback(yes?'✅ إجابة صحيحة +100':'الإجابة الصحيحة: '+row.a);$('#clozeChoices').querySelectorAll('button').forEach(x=>x.disabled=true);popupNext($('#clozeNext'))},'choice')));
}
function playDiagram(){
 const image=window.BOOYAH_GAME_LAB_IMAGE||'/assets/backgrounds/quiznova-learning.webp';const items=rows.slice(0,Math.min(rows.length,6));const row=items[index];if(!row)return finish();count('تسمية '+(index+1)+' / '+items.length);
 root('<div class="playcard"><h3>📍 تسمية الرسم</h3><p>اختر التسمية الصحيحة لموقع الرقم '+(index+1)+'؛ يمكنك رفع صورة الدرس من صانع الأنشطة.</p><div class="extra-diagram" id="diagramImage" style="background-image:url(&quot;'+esc(image)+'&quot;)"><span class="extra-diagram-mark" style="left:'+(18+(index%3)*28)+'%;top:'+(28+Math.floor(index/3)*35)+'%">'+(index+1)+'</span></div><p>'+esc(row.q)+'</p></div><div class="playchoices" id="diagramChoices"></div><div class="buttons extra-center" id="diagramNext"></div>');
 choicesFor(row).forEach(a=>$('#diagramChoices').append(button(a,()=>{if($('#diagramNext').children.length)return;const yes=a===row.a;if(yes)score+=100;feedback(yes?'✅ تسمية صحيحة +100':'التسمية الصحيحة: '+row.a);$('#diagramChoices').querySelectorAll('button').forEach(b=>b.disabled=true);popupNext($('#diagramNext'),()=>{index++;if(index>=items.length)finish();else playDiagram()})},'choice')));
}
function playBoard(){
 let teams=[{name:'الفريق الأزرق',score:0},{name:'الفريق الذهبي',score:0},{name:'الفريق الأخضر',score:0}];let card=0;count('لوحة نقاط حرة');
 root('<div class="playcard"><h3>📈 لوحة نقاط المجموعات</h3><p>أضف النقاط أو اطرحها أثناء المناقشة. يمكن للمعلم تعديل أسماء الفرق.</p><div class="extra-score-teams" id="scoreTeams"></div><div class="extra-board-prompt" id="boardPrompt"></div><div class="buttons extra-center" id="boardControls"></div></div>');
 const paint=()=>{const host=$('#scoreTeams');host.replaceChildren();teams.forEach((t,i)=>{const div=document.createElement('div');div.className='extra-score-team';const field=document.createElement('input');field.maxLength=32;field.value=t.name;field.setAttribute('aria-label','اسم الفريق');field.onchange=()=>{t.name=field.value.slice(0,32)};const points=document.createElement('strong');points.textContent=t.score+' ⭐';div.append(field,points,button('＋ 10',()=>{t.score+=10;paint()},'button small'),button('− 10',()=>{t.score=Math.max(0,t.score-10);paint()},'button alt small'));host.append(div)});$('#boardPrompt').textContent='💬 سؤال المناقشة: '+rows[card%rows.length].q};
 const action=$('#boardControls');action.append(button('🎲 سؤال جديد',()=>{card++;paint()},'button'),button('↺ تصفير',()=>{if(confirm('تصفير نقاط العرض؟')){teams.forEach(t=>t.score=0);paint()}},'button alt'),button('🏆 إنهاء',()=>{score=Math.max(...teams.map(t=>t.score));finish()},'button gold'));paint();
}
function playTeams(){
 const totals=[0,0];let team=0;count('⚔️ الفريق الأول ضد الثاني');
 const draw=()=>{if(index>=Math.min(rows.length,8)){score=Math.max(...totals);return finish()}const row=rows[index];root('<div class="playinfo"><span>السؤال '+(index+1)+'</span><b>🔵 '+totals[0]+' — 🟡 '+totals[1]+'</b></div><div class="playcard"><h3>⚔️ دور الفريق '+(team===0?'الأزرق 🔵':'الذهبي 🟡')+'</h3><p>'+esc(row.q)+'</p></div><div class="playchoices" id="teamsOptions"></div><div class="buttons extra-center" id="teamsNext"></div>');choicesFor(row).forEach(a=>$('#teamsOptions').append(button(a,()=>{if($('#teamsNext').children.length)return;const yes=a===row.a;if(yes){totals[team]+=100;score=Math.max(...totals)}feedback(yes?'🎉 +100 للفريق '+(team===0?'الأزرق':'الذهبي'):'الإجابة الصحيحة: '+row.a);$('#teamsOptions').querySelectorAll('button').forEach(b=>b.disabled=true);popupNext($('#teamsNext'),()=>{index++;team=1-team;draw()})},'choice')))};draw();
}
function playSurvey(){
 const options=[...new Set(rows.map(r=>r.a))].slice(0,7),counts=options.map(()=>0);count('0 صوت');root('<div class="playcard"><h3>🗳️ استفتاء الصف</h3><p>سجّل أصوات الطلاب من الشاشة، وستظهر النسب فورًا.</p><div id="surveyBars" class="extra-survey"></div><div class="buttons extra-center" id="surveyControls"></div></div>');
 const paint=()=>{const host=$('#surveyBars');host.replaceChildren();const total=counts.reduce((a,b)=>a+b,0);options.forEach((opt,i)=>{const wrap=document.createElement('div');wrap.className='extra-survey-row';const label=document.createElement('span');label.textContent=opt;const graph=document.createElement('div');graph.className='extra-survey-track';const fill=document.createElement('i');fill.style.width=(total?Math.round(counts[i]*100/total):0)+'%';graph.append(fill);const n=document.createElement('b');n.textContent=counts[i];wrap.append(label,graph,n,button('＋',()=>{counts[i]++;count(counts.reduce((x,y)=>x+y,0)+' صوت');paint()},'button small'));host.append(wrap)})};
 $('#surveyControls').append(button('↺ تصفير الأصوات',()=>{counts.fill(0);count('0 صوت');paint()},'button alt'),button('إنهاء',()=>{score=counts.reduce((a,b)=>a+b,0);finish()},'button'));paint();
}
function playExit(){
 const items=rows.slice(0,Math.min(4,rows.length)),feedbacks=[];count('بطاقة خروج 1 / '+items.length);
 const draw=()=>{const row=items[index];if(!row){score=feedbacks.length*25;return finish()}root('<div class="playcard"><h3>🎟️ بطاقة الخروج</h3><p>'+esc(row.q)+'</p><textarea id="exitResponse" placeholder="اكتب إجابة الطالب هنا..." rows="4" maxlength="500" style="width:100%"></textarea><div class="buttons extra-center" id="exitButtons"></div></div>');$('#exitButtons').append(button('✓ حفظ الإجابة والمتابعة',()=>{const answer=$('#exitResponse').value.trim();if(answer.length<2){feedback('اكتب إجابة قصيرة أولًا');return}feedbacks.push(answer);index++;count('بطاقة خروج '+Math.min(index+1,items.length)+' / '+items.length);draw()},'button'))};draw();
}
function playStory(){
 const length=Math.min(rows.length,7);
 const draw=()=>{if(index>=length)return finish();const row=rows[index];count('المرحلة '+(index+1)+' / '+length);root('<div class="playcard"><div style="font-size:3.2rem">🧭</div><h3>قصة تفاعلية: اختر مسارك</h3><p>أمامك تحدٍّ جديد في رحلة المعرفة. لاتخاذ القرار الصحيح أجب عن السؤال:</p><h3>'+esc(row.q)+'</h3></div><div class="playchoices" id="storyPaths"></div><div id="storyResult" class="playcard hide"></div><div class="buttons extra-center" id="storyNav"></div>');choicesFor(row).forEach(a=>$('#storyPaths').append(button('🧭 '+a,()=>{if($('#storyNav').children.length)return;const correct=a===row.a;if(correct)score+=100;$('#storyPaths').querySelectorAll('button').forEach(b=>b.disabled=true);const panel=$('#storyResult');panel.classList.remove('hide');panel.textContent=correct?'🎉 فتحت المسار الصحيح وتقدّمت في الرحلة!':'🌀 دخلت مسارًا جانبيًا، وتعلمت أن الإجابة الصحيحة هي: '+row.a;popupNext($('#storyNav'),()=>{index++;draw()},index+1===length?'نهاية الرحلة 🏆':'المرحلة التالية ⟵')},'choice')))};draw();
}
function playBingo(){
 const unique=[...new Set(rows.map(r=>r.a))],values=mix(Array.from({length:16},(_,i)=>unique[i%unique.length]||'مفهوم '+i));let called=[],marks=new Set();count('🔲 بينغو 4 × 4');
 root('<div class="playcard"><h3>🔲 بينغو المصطلحات</h3><p>اضغط «اسحب بطاقة» ثم حدّد المصطلح على الشبكة. اربح عند إكمال صف أو عمود أو قطر.</p><div class="extra-bingo" id="bingoGrid"></div><div class="extra-bingo-draw" id="bingoCall">جاهز للسحب</div><div class="buttons extra-center" id="bingoControls"></div></div>');
 const hasLine=()=>{const lines=[];for(let y=0;y<4;y++)lines.push([0,1,2,3].map(x=>y*4+x));for(let x=0;x<4;x++)lines.push([0,1,2,3].map(y=>y*4+x));lines.push([0,5,10,15],[3,6,9,12]);return lines.some(line=>line.every(i=>marks.has(i)))};
 const paint=()=>{const host=$('#bingoGrid');host.replaceChildren();values.forEach((v,i)=>{const b=button(v,()=>{if(!called.includes(v)){feedback('انتظر ظهور المصطلح أولًا');return}marks.add(i);paint();if(hasLine()){score=250;feedback('🎉 بينغو! اكتمل خط صحيح.');$('#bingoControls').replaceChildren(button('🏆 إنهاء',finish,'button'))}},'extra-bingo-cell'+(marks.has(i)?' marked':''));host.append(b)})};
 $('#bingoControls').append(button('🎲 اسحب بطاقة',()=>{const available=unique.filter(x=>!called.includes(x));if(!available.length){feedback('جميع المصطلحات ظهرت. يمكنك إنهاء اللعبة.');return}const picked=mix(available)[0];called.push(picked);$('#bingoCall').textContent='🔊 '+picked;feedback('ابحث عن المصطلح في شبكة بينغو!')},'button'),button('إنهاء',finish,'button alt'));paint();
}
function playCrossword(){
 const size=13,grid=Array.from({length:size},()=>Array(size).fill(null)),words=rows.slice(0,12).map((r,i)=>({...r,letters:removeSpaces(r.a),i})).filter(r=>r.letters.length>=2&&r.letters.length<=10),placed=[];
 const first=words.shift();if(!first){root('<div class="playcard">أضف إجابات قصيرة من حرفين إلى عشرة حروف لهذه اللعبة.</div>');return}
 function place(word,r,c,vertical){for(let i=0;i<word.letters.length;i++){const y=r+(vertical?i:0),x=c+(vertical?0:i);if(y<0||x<0||y>=size||x>=size||grid[y][x]&&grid[y][x]!==word.letters[i])return false}
 for(let i=0;i<word.letters.length;i++){grid[r+(vertical?i:0)][c+(vertical?0:i)]=word.letters[i]}placed.push({word,r,c,vertical});return true}
 place(first,6,Math.max(0,Math.floor((size-first.letters.length)/2)),false);
 for(const word of words){let done=false;for(const p of [...placed]){if(done)break;for(let i=0;i<word.letters.length&&!done;i++){for(let j=0;j<p.word.letters.length&&!done;j++){if(word.letters[i]!==p.word.letters[j])continue;const vert=!p.vertical,y=p.r+(p.vertical?j:0)-(vert?i:0),x=p.c+(p.vertical?0:j)-(vert?0:i);if(place(word,y,x,vert))done=true}}}}
 if(placed.length<4){for(const word of words){if(placed.some(p=>p.word===word))continue;for(let y=0;y<size&&!placed.some(p=>p.word===word);y+=2){place(word,y,0,false)}}}
 count(placed.length+' كلمات');root('<div class="playcard"><h3>🔠 الكلمات المتقاطعة</h3><p>املأ الحروف حسب تعريفات الدرس ثم اضغط تحقق.</p><div class="extra-crossword" id="crossGrid"></div><div class="extra-clues" id="crossClues"></div><div class="buttons extra-center" id="crossActions"></div></div>');
 const host=$('#crossGrid');host.style.gridTemplateColumns='repeat('+size+',minmax(0,1fr))';const fields=[];for(let y=0;y<size;y++)for(let x=0;x<size;x++){const ch=grid[y][x];if(!ch){const blank=document.createElement('span');blank.className='extra-cross-blank';host.append(blank);continue}const input=document.createElement('input');input.className='extra-cross-letter';input.maxLength=1;input.autocomplete='off';input.setAttribute('aria-label','حرف في السطر '+(y+1)+' والعمود '+(x+1));input.dataset.solution=ch;input.dir='rtl';fields.push(input);host.append(input)}
 const clues=$('#crossClues');placed.forEach((p,i)=>{const div=document.createElement('div');div.textContent=(i+1)+' . '+p.word.q+' ('+(p.vertical?'عمودي':'أفقي')+')';clues.append(div)});
 $('#crossActions').append(button('✅ تحقق من الحل',()=>{const correct=fields.filter(f=>f.value.trim().toLocaleLowerCase()===f.dataset.solution.toLocaleLowerCase()).length;if(correct===fields.length){score=placed.length*100;feedback('🎉 أحسنت! كل الكلمات صحيحة');$('#crossActions').replaceChildren(button('🏆 إنهاء',finish,'button'))}else feedback('الصحيح: '+correct+' من '+fields.length+' حرفًا، واصل المحاولة.')},'button'),button('💡 تلميح حرف',()=>{const pending=fields.filter(f=>f.value.trim()!==f.dataset.solution);if(pending.length){const f=pending[0];f.value=f.dataset.solution;f.classList.add('hinted')}}));
}
function playWordsearch(){
 const size=12,grid=Array.from({length:size},()=>Array(size).fill('')),words=[...new Set(rows.map(r=>removeSpaces(r.a).join('')))].filter(w=>Array.from(w).length>=2&&Array.from(w).length<=size).slice(0,8),placed=[],dirs=[[0,1],[1,0],[1,1],[-1,1],[0,-1],[1,-1]];const randomLetters=Array.from(new Set(words.join('')))||['ب','و','ي','ا'];
 for(const word of words){const letters=Array.from(word);for(let retry=0;retry<140;retry++){const [dy,dx]=mix(dirs)[0],y=Math.floor(Math.random()*size),x=Math.floor(Math.random()*size);if(letters.some((l,i)=>{const yy=y+dy*i,xx=x+dx*i;return yy<0||xx<0||yy>=size||xx>=size||(grid[yy][xx]&&grid[yy][xx]!==l)}))continue;letters.forEach((l,i)=>{grid[y+dy*i][x+dx*i]=l});placed.push({word,y,x,dy,dx});break}}
 if(!placed.length){root('<div class="playcard">استخدم إجابات قصيرة لتجربة شبكة البحث عن الكلمات.</div>');return}
 for(let y=0;y<size;y++)for(let x=0;x<size;x++){if(!grid[y][x])grid[y][x]=randomLetters[Math.floor(Math.random()*randomLetters.length)]||'أ'}
 const found=new Set();let origin=null;count('0 / '+placed.length);
 root('<div class="playcard"><h3>🔍 البحث عن الكلمات</h3><p>اختر حرف البداية ثم حرف النهاية للكلمة (أفقيًا أو عموديًا أو قطريًا).</p><div class="extra-wordsearch" id="searchGrid"></div><div class="extra-word-list" id="searchWords"></div><div class="buttons extra-center" id="searchActions"></div></div>');
 const target=$('#searchGrid');target.style.gridTemplateColumns='repeat('+size+',minmax(0,1fr))';
 const cells=[];for(let y=0;y<size;y++)for(let x=0;x<size;x++){const b=button(grid[y][x],()=>{if(!origin){origin={x,y};b.classList.add('started');return}const targetWord=placed.find(w=>!found.has(w.word)&&((w.x===origin.x&&w.y===origin.y&&w.x+w.dx*(Array.from(w.word).length-1)===x&&w.y+w.dy*(Array.from(w.word).length-1)===y)||(w.x===x&&w.y===y&&w.x+w.dx*(Array.from(w.word).length-1)===origin.x&&w.y+w.dy*(Array.from(w.word).length-1)===origin.y)));target.querySelectorAll('.started').forEach(c=>c.classList.remove('started'));origin=null;if(targetWord){found.add(targetWord.word);for(let i=0;i<Array.from(targetWord.word).length;i++){cells[(targetWord.y+targetWord.dy*i)*size+targetWord.x+targetWord.dx*i].classList.add('found')}count(found.size+' / '+placed.length);feedback('✅ وجدت كلمة: '+targetWord.word);renderWords();if(found.size===placed.length){score=placed.length*100;$('#searchActions').replaceChildren(button('🏆 إنهاء',finish,'button'))}}else feedback('حاول اختيار أول حرف وآخر حرف من الكلمة')},'extra-word-letter');target.append(b);cells.push(b)}
 const renderWords=()=>{$('#searchWords').replaceChildren();placed.forEach(w=>{const chip=document.createElement('span');chip.className='extra-word-chip'+(found.has(w.word)?' found':'');chip.textContent=w.word;$('#searchWords').append(chip)})};renderWords();$('#searchActions').append(button('💡 تلميح',()=>{const w=placed.find(x=>!found.has(x.word));if(w)cells[w.y*size+w.x].classList.add('started')},'button alt'));
}
const handlers={anagram:playAnagram,order:playOrder,maze:playMaze,balloons:playBalloons,memory:playMemory,hidden:playHidden,cloze:playCloze,diagram:playDiagram,board:playBoard,teams:playTeams,survey:playSurvey,exit:playExit,story:playStory,bingo:playBingo,crossword:playCrossword,wordsearch:playWordsearch};
window.BOOYAH_EXTRA={render:(id,context)=>{if(!handlers[id])return false;clear();ctx=context;mode=id;rows=context.rows;score=0;index=0;handlers[id]();return true},stop:clear,ids:Object.keys(handlers)};
})();
