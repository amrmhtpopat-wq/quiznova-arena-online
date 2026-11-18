"""Chromium student photo questions stay on screen, with optional accessible zoom."""
import os,sys,tempfile,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
tmp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(tmp.name)/'tag-image-layout.sqlite')
os.environ['QUIZNOVA_CLOUD']='1';os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import server
http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(http.server_port)
pic='/assets/backgrounds/quiznova-learning.webp'
options=['المعلومة الأولى وهي مثال تعليمي واضح','الإجابة الثانية التي تشرح الفكرة باختصار',
         'الاختيار الثالث المتعلق بمفهوم الدرس','الإجابة الرابعة المقترحة في السؤال']
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
 for width,height in ((320,640),(390,844),(430,740),(820,600),(1366,768)):
  ctx=browser.new_context(viewport={'width':width,'height':height},service_workers='block')
  page=ctx.new_page()
  errors=[]
  page.on('pageerror',lambda exc:errors.append(str(exc)))
  page.goto(BASE+'/student.html',wait_until='domcontentloaded')
  for kind in ('live','solo'):
   page.evaluate("""({kind,pic,opts})=>{
     const live=document.getElementById('gameView'),solo=document.getElementById('soloView');
     const markup='<img class="question-image" src="'+pic+'" alt="صورة السؤال">'
       +'<h2>انظر إلى الصورة ثم اختر الخيار الصحيح الذي يعبّر عن الفكرة الأساسية في الدرس</h2>'
       +'<div class="answers">'+opts.map(o=>'<button class="answer">'+o+'</button>').join('')+'</div>';
     const smarkup='<img class="bo-solo-question-image" src="'+pic+'" alt="صورة السؤال">'
       +'<h2>انظر إلى الصورة ثم اختر الخيار الصحيح الذي يعبّر عن الفكرة الأساسية في الدرس</h2>'
       +'<div class="bo-solo-options">'+opts.map(o=>'<label class="bo-solo-choice"><input type="radio" name="test"><span>'+o+'</span></label>').join('')+'</div>'
       +'<button type="submit" class="bo-solo-submit">تأكيد الإجابة</button>';
     live.innerHTML='';live.classList.toggle('hidden',kind!=='live');
     solo.classList.toggle('hidden',kind!=='solo');
     if(kind==='live'){
       live.innerHTML='<div class="game-top"><div class="player-pill">طالب</div><div class="timer">20</div></div>'
         +'<div class="progress"></div><div class="question-card" data-type="single">'+markup+'</div>';
     }else{
       document.getElementById('soloPlayArea').innerHTML='<div class="bo-solo-progress-header">السؤال 1 من 4</div><form class="bo-solo-question">'+smarkup+'</form>';
     }
     document.body.dataset.boQuestion=kind;
   }""",{'kind':kind,'pic':pic,'opts':options})
   page.wait_for_timeout(200)
   target='#gameView .question-card' if kind=='live' else '#soloView .bo-solo-question'
   choice='.answers .answer' if kind=='live' else '.bo-solo-options .bo-solo-choice'
   image='.question-image' if kind=='live' else '.bo-solo-question-image'
   boxes=page.locator(target+' '+choice).evaluate_all("""els=>els.map(e=>{
     const r=e.getBoundingClientRect();return {top:r.top,bottom:r.bottom,height:r.height,left:r.left,right:r.right};
   })""")
   assert len(boxes)==4,(width,kind,boxes)
   assert all(b['height']>=20 and b['top']>=0 and b['bottom']<=height+2
              and b['left']>=-2 and b['right']<=width+2 for b in boxes),(width,kind,boxes)
   assert page.locator(target+' '+image).is_visible(),(width,kind,'image hidden')
   page.locator(target+' '+image).click()
   page.locator('.tag-question-image-modal[open]').wait_for(state='visible',timeout=3500)
   page.get_by_role('button',name='إغلاق الصورة').click()
   assert not page.locator('.tag-question-image-modal[open]').count(),(width,kind,'preview still open')
  assert not errors,(width,errors)
  ctx.close()
 browser.close()
http.shutdown();http.server_close()
print('PASS image, title and all four options fit without page scroll; picture zoom works at five viewport sizes.')
