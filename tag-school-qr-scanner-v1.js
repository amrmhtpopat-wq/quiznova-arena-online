/* TAG school QR bridge v1
 * Decode existing school attendance QR LOCALLY in the browser: G9A-001, G8B-004, G7C-021.
 * The printed QR never changes. A successful read opens the card's published quizzes.
 * jsQR (Apache-2.0) is vendored under /vendor; no images or camera frames are uploaded.
 */
(()=>{
'use strict';
const by=id=>document.getElementById(id);
const video=by('scanVideo'),canvas=by('scanCanvas'),shell=by('scanShell');
const status=by('scanStatus'),startButton=by('startScan'),stopButton=by('stopScan');
const file=by('scanFile'),manual=by('manualCode'),ctx=canvas.getContext('2d',{willReadFrequently:true});
let stream=null,animation=0,lastFrame=0,scanning=false,busy=false,runId=0;
const schoolId=/^G[789][ABC]-\d{3}$/;
function say(message,kind='info'){status.textContent=message;status.dataset.kind=kind}
function extractSchoolId(raw){
 const clean=String(raw||'').trim().replace(/[\u200E\u200F\u202A-\u202E]/g,'');
 let text=clean.toUpperCase();
 if(schoolId.test(text))return text;
 // Optional: recognize a TAG-generated URL if someone scans it inside our camera tool.
 try{
  const url=new URL(clean);
  if(!['quiznova-arena-online.onrender.com','teachgame.onrender.com',location.hostname].includes(url.hostname.toLowerCase()))return '';
  text=String(url.searchParams.get('card')||'').toUpperCase();
  return schoolId.test(text)?text:'';
 }catch{return ''}
}
function stop(){
 scanning=false;runId++;
 if(animation)cancelAnimationFrame(animation);
 animation=0;lastFrame=0;
 const active=stream;stream=null;
 if(active)active.getTracks().forEach(track=>track.stop());
 try{video.pause();video.srcObject=null}catch{}
 shell.classList.remove('active');startButton.disabled=false;stopButton.disabled=true
}
async function accept(raw){
 if(busy)return;
 const card=extractSchoolId(raw);
 if(!card){say('هذا QR ليس من بطاقات الصف السابع أو الثامن أو التاسع. تأكد من البطاقة ثم أعد المحاولة.','error');return}
 busy=true;stop();manual.value=card;startButton.disabled=true;
 say('تمت قراءة البطاقة '+card+'، نتحقق من الاختبارات المخصصة لك…');
 try{
  const response=await fetch('/api/student/solo/catalog',{
   method:'POST',cache:'no-store',credentials:'same-origin',
   headers:{'Content-Type':'application/json'},
   body:JSON.stringify({card})
  });
  const data=await response.json().catch(()=>({}));
  if(!response.ok||!data.ok){
   say(data.error==='invalid_card'?'هذه البطاقة غير مفعّلة في TAG. راجع معلمك.':'تعذر التحقق من البطاقة الآن. أعد المحاولة.','error');
   return;
  }
  const name=String(data.student?.name||'الطالب');
  say('أهلًا '+name+'! تم التعرف على شعبتك، وفتح صفحة الاختبارات الآن…','success');
  // Keep the original card ID out of the browser history and URL.
  try{
   sessionStorage.setItem('tag_school_card_pending',card);
   location.assign('/student.html?mode=card');
  }catch{
   // Session storage may be blocked in private browsing; fall back to the public
   // printed school ID only. Never put TAG's private card_token in the URL.
   location.assign('/student.html?mode=card&card='+encodeURIComponent(card));
  }
 }catch{say('تعذر الاتصال بمنصة TAG. افحص الإنترنت وحاول مرة أخرى.','error')}
 finally{busy=false;startButton.disabled=false}
}
function decode(imageData){
 if(typeof window.jsQR!=='function')throw new Error('decoder_missing');
 const result=window.jsQR(imageData.data,imageData.width,imageData.height,{inversionAttempts:'attemptBoth'});
 return result?.data||''
}
function loop(now,id){
 if(!scanning||id!==runId||busy)return;
 animation=requestAnimationFrame(t=>loop(t,id));
 if(now-lastFrame<155||video.readyState<2||!video.videoWidth)return;
 lastFrame=now;
 const scale=Math.min(1,850/video.videoWidth);
 const w=Math.max(16,Math.round(video.videoWidth*scale));
 const h=Math.max(16,Math.round(video.videoHeight*scale));
 canvas.width=w;canvas.height=h;
 try{
  ctx.drawImage(video,0,0,w,h);
  const decoded=decode(ctx.getImageData(0,0,w,h));
  if(decoded){const card=extractSchoolId(decoded);if(card){void accept(card)}else say('تمت قراءة QR لكن ليس رمز بطاقة مدرستك للصفوف 7–9.','error')}
 }catch(error){stop();say(error.message==='decoder_missing'?'تعذّر تهيئة قارئ QR. جرّب إدخال الرقم يدويًا.':'حدث خطأ في قراءة الكاميرا. استخدم صورة QR أو الرمز المكتوب.','error')}
}
async function start(){
 if(busy||scanning)return;
 if(typeof window.jsQR!=='function'){say('قارئ QR لم يُحمّل؛ جرّب تحديث الصفحة أو كتابة رقم البطاقة.','error');return}
 if(!navigator.mediaDevices?.getUserMedia){say('المتصفح لا يدعم فتح الكاميرا هنا. استخدم اختيار صورة QR أو أدخل الرمز.','error');return}
 startButton.disabled=true;say('اسمح باستخدام الكاميرا ثم وجّهها إلى رمز البطاقة.');
 try{
  const got=await navigator.mediaDevices.getUserMedia({audio:false,video:{facingMode:{ideal:'environment'},width:{ideal:1280},height:{ideal:720}}});
  if(busy){got.getTracks().forEach(t=>t.stop());return}
  stream=got;video.srcObject=got;await video.play();
  scanning=true;stopButton.disabled=false;shell.classList.add('active');say('ضع رمز QR داخل المربع الأخضر، وسيتم فتح اختباراتك تلقائيًا.');
  const id=++runId;animation=requestAnimationFrame(t=>loop(t,id))
 }catch(error){
  stop();say(error?.name==='NotAllowedError'?'لم يتم السماح للكاميرا. فعّل إذن الكاميرا للمتصفح أو اختر صورة QR.':'لم يتم فتح الكاميرا. استخدم صورة للرمز أو اكتب الرقم.','error')
 }
}
async function decodeFile(selected){
 if(!selected)return;
 if(selected.size>12*1024*1024){say('الصورة كبيرة جدًا. اختر صورة أصغر من 12 ميغابايت.','error');return}
 stop();say('جارٍ قراءة رمز QR من الصورة…');
 const url=URL.createObjectURL(selected);const img=new Image();
 try{
  await new Promise((resolve,reject)=>{img.onload=resolve;img.onerror=reject;img.src=url});
  const factor=Math.min(1,1800/Math.max(img.naturalWidth,img.naturalHeight));
  const w=Math.max(16,Math.round(img.naturalWidth*factor)),h=Math.max(16,Math.round(img.naturalHeight*factor));
  canvas.width=w;canvas.height=h;ctx.drawImage(img,0,0,w,h);
  const raw=decode(ctx.getImageData(0,0,w,h));
  if(raw)await accept(raw);else say('لم يظهر رمز QR واضح في هذه الصورة. حاول تصوير الرمز عن قرب بإضاءة جيدة.','error');
 }catch{say('تعذّر قراءة الصورة. تأكد أنها صورة واضحة لرمز QR.','error')}
 finally{URL.revokeObjectURL(url);file.value=''}
}
startButton.addEventListener('click',()=>{void start()});
stopButton.addEventListener('click',()=>{stop();say('تم إيقاف الكاميرا. يمكنك بدء المسح مجددًا.')});
file.addEventListener('change',()=>{void decodeFile(file.files?.[0])});
by('manualForm').addEventListener('submit',event=>{event.preventDefault();void accept(manual.value)});
document.addEventListener('visibilitychange',()=>{if(document.hidden&&scanning){stop();say('توقف المسح عند مغادرة الصفحة؛ اضغط بدء المسح للمتابعة.')}});
window.addEventListener('pagehide',stop);
})();
