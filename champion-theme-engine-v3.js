/* CHAMPION TAG V3 theme registry: no user HTML/URLs are interpolated into CSS. */
(function(){
 "use strict";
 const themes={
  gold:{name:"كأس العالم الذهبي",defaultBackground:"stadium"},
  neon:{name:"استاد المستقبل",defaultBackground:"arena"},
  esports:{name:"ساحة الأبطال الإلكترونية",defaultBackground:"grid"},
  broadcast:{name:"البث الرياضي الاحترافي",defaultBackground:"lights"}
 };
 const backgrounds={
  stadium:"ملعب كأس العالم",
  night:"استاد ليلي",
  lights:"أضواء البث",
  arena:"استاد النيون",
  grid:"الساحة الإلكترونية",
  minimal:"خلفية بسيطة"
 };
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
 window.TAGChampionTheme={themes,backgrounds,apply,syncButtons};
})();
