/* TAG question illustrations: optional large preview without moving answer choices. */
(function(){
  "use strict";
  const selector="#gameView .question-image, #soloPlayArea .bo-solo-question-image";
  let modal=null,source=null;
  function openPreview(img){
    if(typeof HTMLDialogElement==="undefined")return;
    if(!modal){
      modal=document.createElement("dialog");
      modal.className="tag-question-image-modal";
      modal.setAttribute("aria-label","تكبير صورة السؤال");
      const close=document.createElement("button");
      close.type="button";close.textContent="إغلاق الصورة ×";
      close.addEventListener("click",()=>modal.close());
      const picture=document.createElement("img");
      picture.alt="صورة السؤال بالحجم الكبير";
      modal.append(close,picture);
      modal.addEventListener("click",e=>{if(e.target===modal)modal.close()});
      modal.addEventListener("close",()=>{if(source&&source.isConnected)source.focus();source=null});
      document.body.append(modal);
    }
    source=img;
    modal.querySelector("img").src=img.currentSrc||img.src;
    modal.showModal();
    modal.querySelector("button").focus();
  }
  function prepare(){
    document.querySelectorAll(selector).forEach(img=>{
      if(img.dataset.tagPreviewReady)return;
      img.dataset.tagPreviewReady="1";
      img.setAttribute("tabindex","0");
      img.setAttribute("role","button");
      img.setAttribute("aria-label","تكبير صورة السؤال");
    });
  }
  document.addEventListener("click",e=>{
    const img=e.target.closest?.(selector);
    if(img)openPreview(img);
  });
  document.addEventListener("keydown",e=>{
    if(e.key!=="Enter"&&e.key!==" ")return;
    const img=e.target.closest?.(selector);
    if(img){e.preventDefault();openPreview(img)}
  });
  const live=document.getElementById("gameView");
  const solo=document.getElementById("soloPlayArea");
  if(live)new MutationObserver(prepare).observe(live,{childList:true,subtree:true});
  if(solo)new MutationObserver(prepare).observe(solo,{childList:true,subtree:true});
  prepare();
})();
