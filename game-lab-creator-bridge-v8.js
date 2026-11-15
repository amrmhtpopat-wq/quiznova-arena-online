/* TeachGame V8: connect the dedicated creator to the ORIGINAL working Game Lab engine.
 * Same-origin sessionStorage only; no student or cloud API calls during preview.
 */
(()=>{
'use strict';
const key='tg_game_lab_creator_preview_v8';
function boot(){
 const query=new URLSearchParams(location.search);
 if(query.get('creatorPreview')!=='1')return;
 let p;try{p=JSON.parse(sessionStorage.getItem(key)||'null')}catch(_){return}
 if(!p||Date.now()-Number(p.createdAt)>15*60*1000||!p.activity||!Array.isArray(p.activity.rows)||p.activity.rows.length<4||p.activity.rows.length>80)return;
 const mode=query.get('mode');
 if(mode!==p.mode||!/^[a-z]{3,16}$/.test(mode))return;
 const d=p.activity;
 const byId=id=>document.getElementById(id);
 const field=(id,value)=>{const el=byId(id);if(el&&value!==undefined&&value!==null)el.value=String(value)};
 field('activityTitle',d.title);field('subject',d.subject);field('grade',d.grade);field('roundTime',d.time);
 field('activityData',d.rows.map(r=>(String(r.q||'').replace(/\|/g,' / '))+' | '+String(r.a||'').replace(/\|/g,' / ')+' | '+String(r.g||'عام').replace(/\|/g,' / ')).join('\n'));
 // Option rows are passed only to the teacher-preview engine. No persisted data is altered.
 window.TG_CREATOR_PREVIEW_ROWS=d.rows.map(r=>({
  q:String(r.q||'').trim().slice(0,200),a:String(r.a||'').trim().slice(0,100),
  g:String(r.g||'عام').trim().slice(0,60),
  choices:Array.isArray(r.choices)?r.choices.map(x=>String(x).trim().slice(0,100)).filter(Boolean).slice(0,4):undefined,
  explanation:String(r.explanation||'').slice(0,240),markerX:Number(r.markerX??50),markerY:Number(r.markerY??50)
 }));
 window.TG_CREATOR_PREVIEW_TEAM_NAMES=Array.isArray(d.teamNames)?d.teamNames.slice(0,3):[];
 const previewImage=sessionStorage.getItem('tg_game_lab_v9_preview_image')||'';
 if(/^data:image\/(png|jpeg|webp);base64,/.test(previewImage)&&previewImage.length<2100000){
  window.BOOYAH_GAME_LAB_IMAGE=previewImage;
 }
 byId('applyContent')?.click();
 let attempts=0;
 const launch=()=>{
  attempts++;
  let target=document.querySelector('#gameGrid .game[data-game-mode="'+mode+'"] .button:not(.v4-use-template)');
  if(!target&&attempts===1){
   field('gameSearch','');field('gradeFilter','all');
   document.querySelector('#filterBar [data-category="all"]')?.click();
  }
  target=document.querySelector('#gameGrid .game[data-game-mode="'+mode+'"] .button:not(.v4-use-template)');
  if(target){target.click();return}
  if(attempts<12)setTimeout(launch,60);
  else{
   const msg=byId('contentFeedback');
   if(msg)msg.textContent='تعذر فتح القالب المختار. عُد إلى المحرر وجرّب مرة أخرى.';
  }
 };
 setTimeout(launch,100);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
