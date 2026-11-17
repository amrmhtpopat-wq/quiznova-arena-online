/* TAG LAB V11: safe identity and teacher-first entry enhancements. */
(()=>{'use strict';
const d=document;
d.querySelectorAll('img.tag-lab-logo').forEach(img=>img.addEventListener('error',()=>{img.hidden=true;const alt=img.nextElementSibling;if(alt)alt.style.display='block'}));
})();
