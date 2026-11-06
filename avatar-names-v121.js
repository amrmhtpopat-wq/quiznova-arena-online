/* One shared naming catalogue for every teacher and student character. Visual assets are unchanged. */
(function(){
 'use strict';
 const names={
   m01:'شرارة',m02:'روبوك',m03:'فوكسو',m04:'نينزو',m05:'درعو',m06:'بيكسو',m07:'زومي',m08:'زومي',
   n01:'نشمي',n02:'هيبة',n03:'باني',n04:'طيّار',n05:'هدّاف',n06:'صقر',n07:'ظل',n08:'نبض',
   b01:'برق',b02:'مهند',b03:'ليث',b04:'يزن',b05:'فارس',b06:'كابتن',b07:'سند',b08:'شاهين',
   b09:'سيف',b10:'زيكو',b11:'رامي',b12:'شهم',b13:'أمير',b14:'عاصم',b15:'غيث',b16:'أسد',
   g01:'نجمة',g02:'لؤلؤة',g03:'ليان',g04:'جود',g05:'قمر',g06:'وردة',g07:'بريق',g08:'سما',
   g09:'رُبى',g10:'يارا',g11:'لمى',g12:'تالا',g13:'رنا',g14:'ندى',g15:'جنى',g16:'شهد'
 };
 const roles={
   n01:'التراث الأردني',n02:'الشرطة',n03:'الهندسة',n04:'الطيران',
   n05:'كرة القدم',n06:'العسكرية',n07:'النينجا',n08:'التقنية'
 };
 window.BOOYAH_AVATAR_NAMES=Object.freeze(names);
 window.BOOYAH_AVATAR_ROLES=Object.freeze(roles);
 window.booyahAvatarName=id=>names[id]||'بطل التحدي';
 window.booyahAvatarLabel=id=>names[id]?(roles[id]?names[id]+' — '+roles[id]:names[id]):'شخصية اللعبة';
})();
