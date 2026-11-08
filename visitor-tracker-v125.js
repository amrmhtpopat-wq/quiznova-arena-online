/* BOOYAHJO 12.5 — non-blocking, anonymous visitor counting.
   Browser identity is random; no IP, student names or login credentials sent. */
(()=>{
  'use strict';
  const pages={'/':'home','/index.html':'home','/student.html':'student',
    '/studio.html':'studio','/stage.html':'stage','/about.html':'about','/for-teachers.html':'about','/privacy.html':'privacy'};
  const page=pages[location.pathname];
  if(!page)return;
  let id='';
  try {
    id=localStorage.getItem('booyahjo_visitor_v1')||'';
    if(!/^[a-f0-9]{32}$/.test(id)) {
      const random=new Uint8Array(16);
      crypto.getRandomValues(random);
      id=Array.from(random,x=>x.toString(16).padStart(2,'0')).join('');
      localStorage.setItem('booyahjo_visitor_v1',id);
    }
  }catch(_error){
    /* Storage unavailable: use a nonidentifying, short-lived browser identity. */
    try {
      const random=new Uint8Array(16);
      crypto.getRandomValues(random);
      id=Array.from(random,x=>x.toString(16).padStart(2,'0')).join('');
    }catch(_ignored){return}
  }
  const payload=JSON.stringify({id,page});
  try {
    /* fire-and-forget: a slow API never delays page rendering or student gameplay */
    if(navigator.sendBeacon && navigator.sendBeacon(
      '/api/visitors/track',new Blob([payload],{type:'application/json'})))return;
    fetch('/api/visitors/track',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:payload,keepalive:true,credentials:'omit'
    }).catch(()=>{});
  }catch(_ignored){}
})();