/* Read-only audience projection of CHAMPION TAG eliminations. */
(function(){
"use strict";
const $=id=>document.getElementById(id);
const esc=window.TAGChampionBracket.escape;
const params=new URLSearchParams(location.search),id=params.get('id')||'';
let previous='',initialLoaded=false,knownChampion='';
async function refresh(){
 if(!/^[a-f0-9]{32}$/.test(id)){
  $('boardBracket').textContent='رابط البطولة غير صحيح. افتح شاشة العرض من حساب المعلم.';return
 }
 try{
  const resp=await fetch('/api/champion/public?id='+encodeURIComponent(id),{cache:'no-store'});
  if(!resp.ok)throw Error('unavailable');
  const data=await resp.json();if(!data.ok||!data.tournament)throw Error('unavailable');
  const t=data.tournament,stamp=JSON.stringify(t);
  if(stamp!==previous){previous=stamp;
   const celebrate=initialLoaded&&Boolean(t.champion)&&t.champion!==knownChampion;
   $('boardTitle').innerHTML='بطولة <em>'+esc(t.title)+'</em>';
   $('boardInfo').textContent=t.champion?'👑 بطل البطولة: '+t.champion:'شاهد جدول تصفيات '+(t.kind==='students'?'الطلاب':t.kind==='classes'?'الشعب':'الفرق')+' حتى المباراة النهائية.';
   window.TAGChampionTheme.apply(t.theme,t.background);
   $('boardBracket').innerHTML=window.TAGChampionBracket.render(t,false);
   window.TAGChampionBracket.afterRender($('boardBracket'));
   window.TAGChampionCeremony?.update(t,{autoplay:celebrate});
   knownChampion=t.champion||'';initialLoaded=true;
  }
  $('boardStatus').textContent='تحديث تلقائي كل 8 ثوانٍ • آخر تحقق '+new Date().toLocaleTimeString('ar-JO');
 }catch(e){
  $('boardStatus').textContent='تعذّر تحديث النتائج مؤقتًا. سيحاول النظام إعادة الاتصال.';
 }
}
$('boardFullscreen').addEventListener('click',async()=>{
 try{if(!document.fullscreenElement)await document.documentElement.requestFullscreen();else await document.exitFullscreen()}
 catch{$('boardStatus').textContent='تعذّر تشغيل ملء الشاشة. استخدم F11 على الكمبيوتر.'}
});
$('boardRefresh').addEventListener('click',()=>void refresh());
void refresh();setInterval(()=>{if(!document.hidden)void refresh()},8000);
})();
