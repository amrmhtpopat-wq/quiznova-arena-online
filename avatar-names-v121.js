/* One shared naming catalogue for every teacher and student character. Visual assets are unchanged. */
(function(){
 'use strict';
 const names={
   m01:'شرارة',m02:'روبوك',m03:'فوكسو',m04:'نينزو',m05:'درعو',m06:'بيكسو',m07:'زومي',m08:'زومي',
   n01:'نشمي',n02:'درعوش',n03:'مسمارو',n04:'نفّاث',n05:'هدّاف',n06:'صقّور',n07:'شبحو',n08:'تكّو',
   b01:'برقو',b02:'زنبرك',b03:'بومبو',b04:'كركور',b05:'دومو',b06:'كابتنو',b07:'شرشور',b08:'شاهينو',
   b09:'وميضو',b10:'زيكو',b11:'فرفور',b12:'دبدوب',b13:'بوبو',b14:'تربو',b15:'زغلو',b16:'شوشو',
   g01:'نجّومة',g02:'لولو',g03:'فوفو',g04:'جوجو',g05:'قمّورة',g06:'روزو',g07:'بريقا',g08:'سمسمة',
   g09:'روبي',g10:'يويو',g11:'لامي',g12:'توتو',g13:'رورو',g14:'نونو',g15:'جينجو',g16:'شوشة'
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
