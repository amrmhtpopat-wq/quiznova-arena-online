/* TeachGame V10.2 — lightweight accessibility and status cleanup.
 * Status remains in normal document flow; no toast, sticky bar or overlay.
 */
(()=>{
 'use strict';
 const D=document,overlay=D.getElementById('playOverlay'),status=D.getElementById('playStatus');
 if(!overlay||!status)return;
 const clean=()=>{
  // Earlier versions add a mascot to the header or a background emoji stamp.
  // Remove them once, without touching game-specific interactive illustrations.
  overlay.querySelector('.playhead>.v101-buddy')?.remove();
  overlay.querySelectorAll('#playBody>.v101-scene-token').forEach(el=>el.remove());
  const hasMessage=Boolean(status.textContent.trim());
  if(status.getAttribute('aria-hidden')!==(hasMessage?'false':'true'))
   status.setAttribute('aria-hidden',hasMessage?'false':'true');
 };
 status.setAttribute('role','status');
 status.setAttribute('aria-live','polite');
 status.setAttribute('aria-atomic','true');
 let scheduled=false;
 const refresh=()=>{
  if(scheduled)return;
  scheduled=true;
  requestAnimationFrame(()=>{scheduled=false;clean()});
 };
 const observer=new MutationObserver(refresh);
 observer.observe(status,{childList:true,characterData:true,subtree:true});
 observer.observe(overlay,{attributes:true,attributeFilter:['hidden']});
 clean();
})();