/* TAG PWA V1: network-first navigations, strictly no cached accounts or exam data. */
'use strict';
const CACHE_NAME='tag-pwa-public-shell-v1';
const OFFLINE_URL='/pwa-offline.html';
const PUBLIC_ASSETS=[OFFLINE_URL,'/assets/pwa/tag-192.png','/assets/pwa/tag-512.png','/assets/pwa/tag-maskable-512.png'];
self.addEventListener('install',event=>{
 event.waitUntil(caches.open(CACHE_NAME).then(cache=>cache.addAll(PUBLIC_ASSETS)));
 // Do not skipWaiting: an exam already in progress must not be interrupted.
});
self.addEventListener('activate',event=>{
 event.waitUntil((async()=>{
  const keys=await caches.keys();
  await Promise.all(keys.filter(key=>key.startsWith('tag-pwa-public-shell-')&&key!==CACHE_NAME).map(key=>caches.delete(key)));
  await self.clients.claim();
 })());
});
self.addEventListener('fetch',event=>{
 const req=event.request;
 if(req.method!=='GET'||req.mode!=='navigate')return;
 const url=new URL(req.url);
 if(url.origin!==self.location.origin||url.pathname.startsWith('/api/'))return;
 // Authentication, cards, quizzes, results and PINs are ALWAYS requested live.
 // The only cached HTML is a generic, non-personal offline explanation.
 event.respondWith(fetch(req).catch(async()=>{
  const cached=await caches.match(OFFLINE_URL);
  return cached||new Response('TAG needs an internet connection.',{status:503,headers:{'Content-Type':'text/plain; charset=utf-8'}});
 }));
});
