/* V5 QA Game Lab: illustrated cards + simple, synchronized question forms.
   Preserve all original game functions, APIs and cloud/student data paths. */
(()=>{
"use strict";
const doc=document,$=id=>doc.getElementById(id);
const cats={
  quiz:"assessment",fast:"assessment",truth:"assessment",exit:"classroom",survey:"classroom",
  wheel:"chance",boxes:"chance",balloons:"chance",hidden:"chance",bingo:"chance",
  pairs:"memory",flash:"memory",memory:"memory",anagram:"memory",wordsearch:"memory",crossword:"memory",
  sort:"logic",order:"logic",maze:"logic",cloze:"logic",diagram:"logic",story:"logic",
  board:"classroom",teams:"classroom"
};
const arts={
  quiz:"quiz",fast:"quiz",truth:"quiz",exit:"quiz",survey:"score",board:"score",teams:"score",
  wheel:"wheel",boxes:"boxes",balloons:"cards",hidden:"cards",bingo:"cards",
  pairs:"cards",flash:"cards",memory:"cards",anagram:"letters",wordsearch:"grid",crossword:"grid",
  sort:"path",order:"path",maze:"path",cloze:"letters",diagram:"grid",story:"path"
};
function artwork(mode){
 const box=doc.createElement("div");box.className="v5-art";
 const f=cats[mode];box.dataset.family=f==="chance"?"chance":f==="memory"?"memory":f==="logic"?"logic":f==="classroom"?"class":"challenge";
 box.setAttribute("aria-hidden","true");
 const type=arts[mode];
 if(type==="wheel")box.innerHTML='<span class="v5-wheel-tip">▼</span><span class="v5-wheel"></span>';
 else if(type==="boxes")box.innerHTML='<span class="v5-art-grid"><span>?</span><span>1</span><span>★</span><span>4</span><span>?</span><span>6</span></span>';
 else if(type==="cards")box.innerHTML='<span class="v5-art-grid v5-cards"><span>🧩</span><span>?</span><span>◆</span><span>?</span><span>★</span><span>◆</span></span>';
 else if(type==="grid")box.innerHTML='<span class="v5-art-grid v5-cards"><span>أ</span><span>ب</span><span>ج</span><span>س</span><span>ي</span><span>ن</span></span>';
 else if(type==="path"||type==="letters")box.innerHTML=type==="path"?'<span class="v5-path"><span>1</span><span>2</span><span>3</span></span>':'<span class="v5-path"><span>أ</span><span>ب</span><span>ج</span></span>';
 else if(type==="score")box.innerHTML='<span class="v5-art-grid v5-cards"><span>🏆</span><span>10</span><span>20</span><span>30</span><span>⭐</span><span>50</span></span>';
 else box.innerHTML='<span class="v5-board"><strong>اختر الإجابة</strong><span class="v5-line"></span><span class="v5-line"></span><span class="v5-line"></span><span class="v5-line"></span></span>';
 box.insertAdjacentHTML("beforeend",'<span class="v5-number">★</span>');
 return box;
}
function decorate(){
 const grid=$("gameGrid");if(!grid)return;
 grid.querySelectorAll(".game[data-game-mode]").forEach(card=>{
  if(card.dataset.v5Enhanced==="1")return;
  const mode=card.dataset.gameMode,figure=card.querySelector(".figure");
  if(!figure||!Object.prototype.hasOwnProperty.call(arts,mode))return;
  figure.prepend(artwork(mode));card.dataset.v5Enhanced="1";
 });
}
function parsed(text){
 return String(text||"").split(/\r?\n/).map(s=>s.trim()).filter(Boolean).slice(0,80).map(line=>{
  const c=line.split("|").map(x=>x.trim());
  return {q:c[0]||"",a:c[1]||"",g:c[2]||"عام",page:c[3]||""};
 });
}
const normalize=x=>String(x||"").replace(/\|/g," / ").replace(/\r?\n/g," ").trim();
const esc=x=>String(x??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function start(){
 const builder=$("builder"),raw=$("activityData"),grid=$("gameGrid");
 if(!builder||!raw||!grid)return;
 doc.body.classList.add("game-lab-v5");decorate();
 new MutationObserver(decorate).observe(grid,{childList:true});
 const oldField=raw.closest(".field"),block=oldField&&oldField.parentNode;
 if(!block)return;
 const guide=doc.createElement("div");guide.className="v5-guide";
 guide.innerHTML='<div class="v5-guide-item"><b>1</b> اختر قالب اللعبة</div><div class="v5-guide-item"><b>2</b> اكتب الأسئلة</div><div class="v5-guide-item"><b>3</b> جرّب ثم احفظ</div>';
 builder.querySelector(".layout2")?.before(guide);
 const area=doc.createElement("section");area.id="v5QuickEditor";area.className="v5-simple-editor";
 area.innerHTML='<div class="v5-simple-head"><h4>✏️ محرر الأسئلة السهل</h4><span id="v5Count" class="pill">0 سؤال</span></div><p>كل سؤال وإجابته في خانات واضحة. لن تحتاج إلى كتابة رموز أو فواصل.</p><div id="v5QuestionList" class="v5-question-list"></div><div class="v5-simple-actions"><button type="button" id="v5Add" class="v5-add">＋ إضافة سؤال</button><button type="button" id="v5Refresh" class="v5-secondary">↻ جلب الأسئلة من الكتاب أو النص</button></div><small id="v5EditorStatus" role="status" aria-live="polite">أدخل أربعة أسئلة على الأقل، بحد أقصى 80 سؤالًا.</small>';
 const bulk=doc.createElement("details");bulk.id="v5BulkBox";
 bulk.innerHTML="<summary>⌨️ تحرير جماعي أو لصق الأسئلة (اختياري)</summary>";
 block.insertBefore(bulk,oldField);
 bulk.appendChild(oldField);bulk.before(area);
 const list=$("v5QuestionList"),count=$("v5Count"),status=$("v5EditorStatus");
 let rows=parsed(raw.value),lastRaw=raw.value;
 function say(t,warning=false){status.textContent=t;status.style.color=warning?"#ac2547":"#285c51"}
 function serialize(){
  return rows.map(r=>{
   const q=normalize(r.q),a=normalize(r.a),g=normalize(r.g)||"عام",page=normalize(r.page);
   if(!q&&!a)return "";
   return [q,a,g,...(page?[page]:[])].join(" | ");
  }).filter(Boolean).join("\n");
 }
 function sync(){
  raw.value=serialize();lastRaw=raw.value;count.textContent=rows.length+" سؤال";
 }
 function rowElement(row,i){
  const el=doc.createElement("article");el.className="v5-question";el.dataset.index=i;
  el.innerHTML='<div class="v5-question-head"><span>السؤال '+(i+1)+'</span><div class="v5-simple-actions"><button type="button" class="v5-remove" data-remove="'+i+'">حذف</button></div></div><div class="v5-question-fields"><label>نص السؤال<input name="q" maxlength="200" placeholder="مثال: ما وظيفة RAM؟" value="'+esc(row.q)+'"></label><label>الإجابة الصحيحة<input name="a" maxlength="100" placeholder="مثال: تخزين البيانات مؤقتًا" value="'+esc(row.a)+'"></label></div><div class="v5-question-fields"><label>المجموعة<input name="g" maxlength="60" value="'+esc(row.g)+'" placeholder="مثال: مكوّنات الحاسوب"></label><label>رقم صفحة الكتاب (اختياري)<input name="page" inputmode="numeric" maxlength="3" value="'+esc(row.page)+'" placeholder="مثال: 15"></label></div>';
  return el;
 }
 function paint(){list.replaceChildren(...rows.map(rowElement));count.textContent=rows.length+" سؤال"}
 function refreshFromRaw(){if(raw.value===lastRaw)return;rows=parsed(raw.value);lastRaw=raw.value;paint();say("تم استيراد الأسئلة إلى المحرر السهل.")}
 function validate(){
  if(raw.value!==lastRaw)refreshFromRaw();
  if(rows.length<4){say("أضف أربعة أسئلة على الأقل قبل تطبيق النشاط.",true);return false}
  for(let i=0;i<rows.length;i++){
   const r=rows[i];if(!normalize(r.q)||!normalize(r.a)){say("أكمل السؤال والإجابة رقم "+(i+1)+".",true);return false}
   if(normalize(r.page)&&(!/^\d+$/.test(normalize(r.page))||Number(r.page)<1||Number(r.page)>350)){say("رقم الصفحة في السؤال "+(i+1)+" غير صحيح.",true);return false}
  }
  return true;
 }
 paint();
 list.addEventListener("input",e=>{
  const input=e.target.closest("input[name]"),parent=input?.closest(".v5-question");
  if(!input||!parent)return;const i=Number(parent.dataset.index);
  if(!rows[i]||!["q","a","g","page"].includes(input.name))return;
  rows[i][input.name]=input.value;sync();say("✓ حُدّث المحتوى. اضغط تطبيق المحتوى للمعاينة.");
 });
 list.addEventListener("click",e=>{
  const btn=e.target.closest("[data-remove]");if(!btn)return;
  if(rows.length<2)return say("أبقِ سؤالًا واحدًا على الأقل.",true);
  rows.splice(Number(btn.dataset.remove),1);sync();paint();say("تم حذف السؤال.");
 });
 $("v5Add").addEventListener("click",()=>{
  if(rows.length>=80)return say("وصلت إلى الحد الأقصى: 80 سؤالًا.",true);
  rows.push({q:"",a:"",g:"عام",page:""});sync();paint();
  list.lastElementChild?.querySelector('input[name="q"]')?.focus({preventScroll:true});
  list.lastElementChild?.scrollIntoView({block:"nearest"});
 });
 $("v5Refresh").addEventListener("click",()=>{
  rows=parsed(raw.value);lastRaw=raw.value;paint();say("تم تحديث الأسئلة من النص أو الكتاب.");
 });
 raw.addEventListener("input",()=>{rows=parsed(raw.value);lastRaw=raw.value;paint();say("تمت قراءة الأسئلة من النص.")});
 area.addEventListener("focusin",()=>refreshFromRaw());
 // Some existing book-generation buttons set textarea.value without emitting input.
 doc.addEventListener("click",e=>{
  if(e.target.closest("#labBookGenerate,#cloudUseQuiz,#loadGrade7Pilot,#restoreExample"))setTimeout(refreshFromRaw,120);
 },true);
 doc.addEventListener("click",e=>{
  const btn=e.target.closest("button");if(!btn)return;
  if(!["applyContent","saveActivity","v4TrySelected","v4SaveSelected","quickPlay","cloudSave"].includes(btn.id))return;
  if(!validate()){
   e.preventDefault();e.stopImmediatePropagation();
   area.scrollIntoView({behavior:"smooth",block:"center"});
  }
 },true);
 $("v4ChosenTemplate")?.classList.add("v5-selected-template");
}
if(doc.readyState==="loading")doc.addEventListener("DOMContentLoaded",start,{once:true});
else start();
})();
