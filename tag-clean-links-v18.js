/* TAG V18: remove referral tracking from address bar; preserve student card, room, teacher and session parameters. */
(function(){
 "use strict";
 try{
  const url=new URL(location.href);
  let dirty=false;
  for(const [key,val] of [...url.searchParams.entries()]){
   if(/^utm_/i.test(key)||/^(fbclid|gclid|mc_cid|mc_eid)$/i.test(key)||
      (/^(source|ref|referrer)$/i.test(key)&&/^(chatgpt(\.com)?|openai(\.com)?)$/i.test(val))){
      url.searchParams.delete(key);dirty=true;
   }
  }
  if(dirty)history.replaceState(history.state,"",url.pathname+url.search+url.hash);
 }catch(_err){ /* This is visual URL hygiene; never interrupt app initialization. */ }
})();
