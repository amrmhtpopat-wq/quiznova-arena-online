/* TAG Home Mobile V5 — delegate to the existing teacher actions.
   No writes, API requests, or desktop behavior are introduced here. */
(function(){
  "use strict";
  document.addEventListener("click",function(event){
    const action=event.target.closest("[data-tag-v5-action]");
    if(!action || !window.matchMedia("(max-width:650px)").matches)return;
    const kind=action.getAttribute("data-tag-v5-action");
    const existing=kind==="backup" ? document.getElementById("downloadBackup")
      : kind==="refresh" ? document.getElementById("refresh") : null;
    if(!existing)return;
    event.preventDefault();
    existing.click();
  });
})();
