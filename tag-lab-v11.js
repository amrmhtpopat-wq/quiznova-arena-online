/* TAG LAB V11: safe identity and teacher-first entry enhancements. */
(()=>{'use strict';
const d=document;
const note=d.createElement('p');
note.id='tagLabStartNote';note.setAttribute('role','note');
note.textContent='لإنشاء نشاط لمبحثك، ابدأ بأسئلة فارغة. ولتجربة طريقة اللعب أولًا اضغط «استعادة المثال»، ثم اختر أي لعبة.';
const builder=d.getElementById('builder');const form=d.getElementById('activityData');
if(builder&&form){const header=builder.querySelector('.section-head');header?.insertAdjacentElement('afterend',note);}
d.querySelectorAll('img.tag-lab-logo').forEach(img=>img.addEventListener('error',()=>{img.hidden=true;const alt=img.nextElementSibling;if(alt)alt.style.display='block'}));
})();
