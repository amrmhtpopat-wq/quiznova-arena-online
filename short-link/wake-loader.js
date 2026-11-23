/* TAG static splash: an image decode verifies the live backend without requiring CORS.
   Does not replace Render's own interstitial on direct backend links. */
(function(){
 "use strict";
 const target=window.TAG_ENTRY_TARGET;
 const go=window.TAG_ENTRY_GO;
 const base="https://quiznova-arena-online.onrender.com";
 if(typeof target!=="string"||!target.startsWith(base+"/")||typeof go!=="function")return;
 const status=document.getElementById("wakeStatus");
 const retry=document.getElementById("wakeRetry");
 if(!status||!retry)return;
 let began=Date.now(),attempt=0,finished=false;
 const maxWindow=95000;
 function ping(){
  if(finished)return;
  attempt++;
  status.textContent=attempt===1?"نجهّز المنصة ونتحقق من اتصال الخادم…":"ما زلنا نجهّز المنصة، سيتم تحويلك تلقائيًا عند جاهزيتها…";
  const probe=new Image();
  let settled=false;
  const timer=setTimeout(()=>settle(false),12000);
  function settle(ok){
   if(settled||finished)return;
   settled=true;
   clearTimeout(timer);
   probe.onload=probe.onerror=null;
   if(ok&&probe.naturalWidth>0){
    finished=true;
    status.textContent="المنصة جاهزة! جارٍ فتحها…";
    setTimeout(go,280);
    return;
   }
   if(Date.now()-began>=maxWindow){
    status.textContent="تأخر تجهيز الخادم. اضغط إعادة المحاولة وسنفتح الصفحة تلقائيًا بعد جاهزيتها.";
    retry.hidden=false;
    return;
   }
   setTimeout(ping,2600);
  }
  probe.onload=()=>settle(true);
  probe.onerror=()=>settle(false);
  probe.src=base+"/assets/brand/tag-favicon-v24.png?wake="+Date.now()+"-"+attempt;
 }
 retry.addEventListener("click",()=>{began=Date.now();attempt=0;retry.hidden=true;ping();});
 ping();
})();
