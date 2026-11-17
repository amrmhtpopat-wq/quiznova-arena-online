/* CHAMPION TAG V3 theme registry: no user HTML/URLs are interpolated into CSS. */
(function(){
 "use strict";
 const themes={
  gold:{name:"كأس العالم الذهبي",defaultBackground:"daylight"},
  neon:{name:"استاد المستقبل",defaultBackground:"neon"},
  esports:{name:"ساحة الأبطال الإلكترونية",defaultBackground:"neon"},
  broadcast:{name:"البث الرياضي الاحترافي",defaultBackground:"elegant"}
 };
 const backgrounds={
  // Legacy assets stay valid for previously saved tournaments.
  stadium:"ملعب كأس العالم (قديم)",night:"استاد ليلي (قديم)",lights:"أضواء البث (قديم)",
  arena:"استاد النيون (قديم)",grid:"الساحة الإلكترونية (قديم)",minimal:"خلفية بسيطة (قديم)",
  daylight:"ملعب كأس العالم",finals:"استاد النهائي الذهبي",
  royal:"منصة التتويج الملكية",celebration:"أضواء الاحتفال",hall:"قاعة الأبطال",
  neon:"موجات النيون",trophy:"الكأس الرسمية",elegant:"الخلفية الفاخرة البسيطة"
 };
 const visibleBackgrounds=Object.freeze(["daylight","finals","royal","celebration","hall","neon","trophy","elegant"]);
 const permitted=(obj,value,fallback)=>Object.prototype.hasOwnProperty.call(obj,value)?value:fallback;
 function apply(theme,background){
  const t=permitted(themes,theme,"gold");
  const b=permitted(backgrounds,background,themes[t].defaultBackground);
  document.body.dataset.championTheme=t;
  document.body.dataset.championBg=b;
  return {theme:t,background:b};
 }
 function syncButtons(container,attr,selected){
  if(!container)return;
  container.querySelectorAll('['+attr+']').forEach(button=>{
   const yes=button.getAttribute(attr)===selected;
   button.classList.toggle('is-selected',yes);
   button.setAttribute('aria-pressed',String(yes));
  });
 }
 window.TAGChampionTheme={themes,backgrounds,visibleBackgrounds,apply,syncButtons};
})();
