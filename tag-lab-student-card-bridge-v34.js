/* Shared official TAG / TAG LAB student card on the SAME origin and teacher database.
 * Never put card credentials into URLs, logs, query strings or network analytics.
 */
(()=>{'use strict';
const modes=document.getElementById('studentModes');if(!modes)return;
const parent=document.getElementById('cardProfile')?.parentElement||modes.parentElement;
const a=document.createElement('a');a.id='tagLabStudentGames';a.href='/game-lab-card.html?open=1';
a.textContent='🎮 ألعاب TAG LAB باستخدام بطاقة الطالب نفسها';
a.setAttribute('aria-label','فتح الألعاب التعليمية المرتبطة ببطاقة الطالب الحالية');
a.style.cssText='display:inline-flex;justify-content:center;align-items:center;gap:8px;margin:11px 0;padding:12px 16px;min-height:44px;border-radius:12px;background:#0b5e9e;border:1px solid #64a8d5;color:#fff;font:800 14px/1.5 Tahoma,Arial,sans-serif;text-decoration:none';
const note=document.createElement('p');note.style.cssText='font-size:12px;color:#5c7789;margin:5px 0';
note.textContent='نفس بطاقة الطالب ونفس حساب المعلم — لا حاجة لبطاقة جديدة.';
a.addEventListener('click',event=>{
 const main=document.getElementById('cardCode')?.value.trim()||'';
 const solo=document.getElementById('soloCardCode')?.value.trim()||'';
 // For the card/solo view, prefer whichever card the student entered.
 const selected=document.querySelector('[data-student-mode].is-active')?.dataset.studentMode;
 const card=(selected==='solo'?(solo||main):(main||solo));
 if(card){sessionStorage.setItem('booyah_lab_card_code',card)}
 else{
  // Let the dedicated TAG LAB card page accept it, without assuming success.
  sessionStorage.removeItem('booyah_lab_card_code')
 }
});
parent.append(a,note);
})();
