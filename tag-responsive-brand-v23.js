/* TAG V23: navigation + new student badge mark, visual only. Keep IDs, QR and PIN unchanged. */
(()=>{'use strict';
const name=(location.pathname.split('/').pop()||'index.html').toLowerCase();
if(/^(tag-lab|game-lab|tag-independent)/.test(name))return;
const ROOT=location.hostname==='teachgame.onrender.com'?'/portal.html?teacher=1':'/?teacher=1';
function installBack(){
 if(document.querySelector('.tag23-back'))return;
 if(name==='index.html'&&!location.search&&!location.hash)return;
 const b=document.createElement('button');b.type='button';b.className='tag23-back';
 b.setAttribute('aria-label','العودة للصفحة السابقة');b.title='رجوع';
 b.innerHTML='<span aria-hidden="true">➜</span><span class="tag23-back-label">رجوع</span>';
 b.addEventListener('click',()=>{
  const sameOrigin=(()=>{try{return !!document.referrer&&new URL(document.referrer).origin===location.origin}catch{return false}})();
  if(sameOrigin&&history.length>1)history.back();else location.assign(name==='student.html'||name==='index.html'?'/':ROOT);
 });
 document.body.appendChild(b);
}
const mark='/assets/brand/tag-spatial-identity-v3.webp';
function updateBadgeLogos(root){
 if(!root||typeof root.querySelectorAll!=='function')return;
 root.querySelectorAll('.bo-student-id .tag-card-logo,.bo-student-id .bo-badge-brand img').forEach(img=>{
  if(img.dataset.tag23Updated)return;
  img.dataset.tag23Updated='1';
  if(!img.getAttribute('src')?.includes('tag-spatial-identity-v3.webp'))img.src=mark;
  img.alt='شعار TEACH AND GAME – TAG';
 });
}
function start(){
 installBack();
 const board=document.getElementById('studentsBoard');
 if(board){
  updateBadgeLogos(board);
  new MutationObserver(()=>updateBadgeLogos(board)).observe(board,{childList:true,subtree:true});
 }
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();