"""TAG Studio book-to-quiz: browser upload, page provenance, draft save, isolation."""
import os,sys,tempfile,threading,json
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
tmp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ.pop('GEMINI_API_KEY',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(tmp.name)/'studio-book-v1.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
import server
teacher=store.create_teacher('book-to-quiz-v1@example.org','TAGBookToQuizStrong123!',
 'معلم كتاب','مدرسة تجريبية','الثقافة المالية','mixed')
other=store.create_teacher('book-to-quiz-other@example.org','TAGBookOtherStrong123!',
 'معلم آخر','مدرسة أخرى','اللغة الإنجليزية','mixed')
http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(http.server_port)
# Actual question+answer pairs in a teacher's own material. No external AI needed.
questions=[
 ('ما المقصود بالادخار في الموازنة الشخصية؟','الاحتفاظ بجزء من الدخل لاستخدامه لاحقا'),
 ('لماذا تساعد الميزانية الأسرية على التخطيط؟','لأنها تنظم الدخل والمصروفات'),
 ('كيف يمكن تقليل النفقات غير الضرورية؟','بالمقارنة بين الاحتياجات والرغبات'),
 ('ما المقصود بصندوق الطوارئ المالي؟','مبلغ يخصص لتغطية النفقات غير المتوقعة'),
 ('كيف يحدد الطالب أولويات الشراء؟','بتقديم الحاجات الأساسية على الرغبات'),
]
body=('\n\n'.join('سؤال: '+q+'\nجواب: '+a for q,a in questions)+'\n').encode('utf-8')
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
 for width in (390,1366):
  context=browser.new_context(viewport={'width':width,'height':844},is_mobile=width<600,
    has_touch=width<600,service_workers='block')
  context.add_init_script('localStorage.setItem("qn9_teacher_token",'+json.dumps(teacher['token'])+');')
  page=context.new_page();errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(BASE+'/studio.html#generator',wait_until='domcontentloaded',timeout=30000)
  page.wait_for_function("typeof window.TAG_ACCEPT_BOOK_ROWS==='function' && !!document.getElementById('tagBookAi')",timeout=22000)
  assert page.locator('#tagBookMaker').is_visible(),width
  assert page.locator('#tagBookAi').is_disabled(),'AI provider unavailable locally; never simulate AI'
  assert page.locator('#tagBookExtract').is_enabled()
  assert page.locator('#tagBookGrade option').count()==12
  if width==390:
   page.locator('#tagBookFile').set_input_files({'name':'finance.txt','mimeType':'text/plain','buffer':body})
   page.locator('#tagBookUpload').click()
   page.wait_for_function("document.getElementById('tagBookSelect').options.length>1",timeout=28000)
   page.wait_for_function("document.getElementById('tagBookUpload').disabled===false",timeout=16000)
  book_id=page.locator('#tagBookSelect').input_value()
  assert book_id and len(book_id)>20,(width,book_id)
  page.locator('#tagBookGrade').select_option(label='التاسع')
  page.locator('#tagBookStart').fill('1')
  page.locator('#tagBookEnd').fill('1')
  page.locator('#tagBookCount').fill('4')
  page.locator('#tagBookTopic').fill('الوحدة الثانية: الميزانية')
  page.locator('#tagBookExtract').click()
  page.locator('#tagBookQuestions .tag-book-question').first.wait_for(state='visible',timeout=18000)
  assert page.locator('#tagBookQuestions .tag-book-question').count()==4,width
  assert 'صفحة 1' in page.locator('#tagBookQuestions .tag-book-evidence summary').first.inner_text()
  assert page.locator('#tagBookResults').is_visible()
  assert page.locator('#tagBookResults').bounding_box()['width']<=width+2
  page.locator('#tagBookToggleAll').click()
  assert page.locator('#tagBookQuestions .tag-book-pick:checked').count()==4
  assert page.evaluate('DB.quizzes.length')==0,'Suggestions must not save themselves'
  page.locator('#tagBookApply').click()
  page.locator('#view-builder.active').wait_for(state='visible',timeout=10000)
  assert page.evaluate('builderQuestions.length')==4
  assert page.locator('#quizSubject').input_value()=='الثقافة المالية'
  assert page.locator('#quizGrade').input_value()=='التاسع'
  source=page.locator('.tag-book-editor-source').first
  assert source.is_visible()
  assert 'صفحة 1' in source.inner_text()
  assert page.evaluate('builderQuestions.every(q=>q.reviewStatus==="teacher_review_required" && q.sourcePage===1)')
  assert page.evaluate('DB.quizzes.length')==0
  if width==390:
   page.locator('#saveQuiz').click()
   page.locator('#view-library.active').wait_for(state='visible',timeout=18000)
   assert page.evaluate('DB.quizzes.length')==1
   assert page.evaluate('DB.quizzes[0].questions.length')==4
  assert not errors,(width,errors)
  context.close()
 # Verify book confidentiality across different teacher accounts.
 def fetch(path,token):
  req=Request(BASE+path,headers={'Authorization':'Bearer '+token})
  try:
   with urlopen(req,timeout=15) as response:return response.status,json.load(response)
  except HTTPError as exc:return exc.code,json.load(exc)
 code,own=fetch('/api/game-lab/pro/books',teacher['token'])
 assert code==200 and len(own['books'])==1,(code,own)
 book_id=own['books'][0]['id']
 code,foreign=fetch('/api/game-lab/pro/books',other['token'])
 assert code==200 and not foreign['books'],'Other teacher must not see book'
 code,rejected=fetch('/api/game-lab/pro/books/pages?id='+book_id,other['token'])
 assert code!=200 and rejected['ok'] is False,'Cross-teacher page access must fail'
 browser.close()
http.shutdown();http.server_close()
print('PASS TAG book upload, source-backed extraction, phone/desktop draft import, manual save and teacher isolation.')
