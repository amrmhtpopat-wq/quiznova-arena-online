/* BOOYAHJO V12.4 QA: fictional Latin-letter names. Character IDs and artwork unchanged. */
(function(){'use strict';
const names={"m01":"Zappo","m02":"Robix","m03":"Foxzo","m04":"Ninzo","m05":"Shieldox","m06":"Pixelo","m07":"Zoomix","m08":"Zoomix","n01":"Nomado","n02":"Sherixo","n03":"Gearix","n04":"Skyro","n05":"Striko","n06":"Falconix","n07":"Shadowix","n08":"Technox","b01":"Bolto","b02":"Springo","b03":"Bombo","b04":"Korko","b05":"Domo","b06":"Capto","b07":"Sparko","b08":"Hawko","b09":"Flashix","b10":"Zyko","b11":"Fizzio","b12":"Beardo","b13":"Bubbo","b14":"Turbo","b15":"Ziglo","b16":"Shuzo","g01":"Starla","g02":"Lunix","g03":"Foxyra","g04":"Jojo","g05":"Moonya","g06":"Rosix","g07":"Glimma","g08":"Sesma","g09":"Rubyx","g10":"Yoyo","g11":"Lamira","g12":"Tutto","g13":"Roro","g14":"Nuna","g15":"Gingya","g16":"Shusha"};
const roles={"n01":"Jordanian Heritage","n02":"Police","n03":"Engineer","n04":"Pilot","n05":"Football","n06":"Cadet","n07":"Ninja","n08":"Tech Hero"};
window.BOOYAH_AVATAR_NAMES=Object.freeze(names);
window.BOOYAH_AVATAR_ROLES=Object.freeze(roles);
window.booyahAvatarName=id=>names[id]||'Mystery Hero';
window.booyahAvatarLabel=id=>names[id]?(roles[id]?names[id]+' — '+roles[id]:names[id]):'Mystery Hero';
})();
