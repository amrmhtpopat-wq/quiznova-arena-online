"""Browser contract for Book Engine V2: inline evidence counts and source-scoped retry.

The model API is intercepted by Playwright; no external API key and no real
Gemini cost. Authentication, editor and navigation use a local test server.
"""
import os,sys,json,tempfile,threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
temp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ.pop('GEMINI_API_KEY',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(temp.name)/'tag-book-ai-v2.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
import server
teacher=store.create_teacher('tag-ai-v2-test@example.org','TAGV2SamplePass123!',
 'معلم تجريبي','مدرسة تجريبية','المهارات الرقمية','boys')
http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(http.server_port)
received=[]
rows=[
 {'q':'ما الفكرة الأساسية المتعلقة بالأمن الرقمي في هذا المقطع؟',
  'a':'حماية البيانات الشخصية','g':'الأمن الرقمي','sourcePage':2,
  'sourceQuote':'حماية البيانات الشخصية من الوصول غير المصرح به ضرورة أساسية.',
  'sourceQuoteVerified':True,'questionType':'mcq','difficulty':'easy',
  'choices':['إهمال الخصوصية','حماية البيانات الشخصية','نشر كلمات المرور','تجاهل التحديثات']},
 {'q':'هل تساعد كلمة المرور القوية على حماية الحسابات؟',
  'a':'صح','g':'الأمن الرقمي','sourcePage':3,
  'sourceQuote':'كلمات المرور القوية تساعد على حماية الحسابات من الوصول غير المصرح به.',
  'sourceQuoteVerified':True,'questionType':'true_false','difficulty':'easy','choices':['صح','خطأ']},
 {'q':'اذكر إجراء يساعد على الحفاظ على سلامة الحساب الشخصي.',
  'a':'تفعيل المصادقة الثنائية','g':'الأمن الرقمي','sourcePage':4,
  'sourceQuote':'تفعيل المصادقة الثنائية يضيف طبقة حماية إضافية للحساب.',
  'sourceQuoteVerified':True,'questionType':'short','difficulty':'medium','choices':[]}
]
alternative={**rows[0], 'q':'كيف تساعد قواعد الخصوصية الرقمية على حماية المستخدم؟'}
pages={'ok':True,'pages':[{'p':i,'preview':'محتوى دراسي نصي واضح في صفحة '+str(i)} for i in range(1,9)]}
books={'ok':True,'aiEnabled':True,'books':[{'id':'v2-book-sample','name':'كتاب الأمن الرقمي.txt',
                  'pageCount':8,'kind':'txt','createdAt':0}]}
mock_generation={
 'ok':True,'mode':'ai','rows':rows,'count':3,'sourcePages':4,
 'warning':'3 من 4 أسئلة مرتبطة بمصادر دقيقة، راجعها قبل الحفظ.',
 'generationStats':{'requested':4,'providerCalls':2,'proposed':6,
   'rejected':3,'sections':1,'coverage':{'coveredPages':3,'extractablePages':4},
   'teacherReviewRequired':True}
}
mock_retry={
 'ok':True,'mode':'ai','rows':[alternative],'count':1,'sourcePages':1,
 'warning':'تم توليد سؤال بديل من الصفحة نفسها.',
 'generationStats':{'requested':1,'providerCalls':1,'proposed':2,'rejected':1,
  'sections':1,'coverage':{'coveredPages':1,'extractablePages':1}}
}

with sync_playwright() as play:
 browser=play.chromium.launch(headless=True,args=['--no-sandbox'])
 for width in (390,1366):
  ctx=browser.new_context(viewport={'width':width,'height':844},
                          is_mobile=width<600,has_touch=width<600,
                          service_workers='block')
  ctx.add_init_script('localStorage.setItem("qn9_teacher_token",'+json.dumps(teacher['token'])+');')
  page=ctx.new_page()
  page.on('pageerror',lambda err:received.append('PAGE_ERROR '+str(err)))
  page.route('**/api/game-lab/pro/books',lambda route:route.fulfill(json=books))
  page.route('**/api/game-lab/pro/books/pages?*',lambda route:route.fulfill(json=pages))
  def generate_route(route):
   data=route.request.post_data_json
   received.append({'kind':'generate','data':data})
   route.fulfill(json=mock_generation)
  def retry_route(route):
   data=route.request.post_data_json
   received.append({'kind':'retry','data':data})
   route.fulfill(json=mock_retry)
  page.route('**/api/game-lab/pro/books/ai',generate_route)
  page.route('**/api/game-lab/pro/books/ai/retry',retry_route)
  page.goto(BASE+'/studio.html#generator',wait_until='domcontentloaded',timeout=27000)
  page.wait_for_function("document.getElementById('tagBookAi') && !document.getElementById('tagBookAi').disabled",timeout=20000)
  page.locator('#tagBookGrade').select_option(label='التاسع')
  page.locator('#tagBookStart').fill('1')
  page.locator('#tagBookEnd').fill('4')
  page.locator('#tagBookCount').fill('4')
  page.locator('#tagBookQuestionMix').select_option('mcq')
  previous_calls=len([x for x in received if isinstance(x,dict) and x.get('kind')=='generate'])
  page.locator('#tagBookAi').click()
  assert 'يجب الموافقة' in page.locator('#tagBookStatus').inner_text()
  assert len([x for x in received if isinstance(x,dict) and x.get('kind')=='generate'])==previous_calls
  page.locator('#tagBookAiConsent').check()
  saved_before=page.evaluate('DB.quizzes.length')
  page.locator('#tagBookAi').click()
  page.locator('.tag-book-question').first.wait_for(state='visible',timeout=7000)
  assert page.locator('.tag-book-question').count()==3
  assert page.locator('.tag-book-retry').count()==3
  stats=page.locator('#tagBookEngineStats').inner_text()
  for expected in ('المطلوب 4','المقبول 3','المستبعد 3','صفحات مغطاة 3 من 4','طلبات AI المستخدمة 2'):
   assert expected in stats,(width,expected,stats)
  assert page.evaluate('DB.quizzes.length')==saved_before,'Preview must not auto-publish'
  page.locator('.tag-book-retry').first.click()
  page.wait_for_function("document.querySelector('.tag-book-question strong').textContent.includes('قواعد الخصوصية')",timeout=7000)
  retries=[x for x in received if isinstance(x,dict) and x.get('kind')=='retry']
  assert retries,(width,'Missing retry request')
  sent=retries[-1]['data']
  assert sent['retryPage']==2 and sent['retryQuestion']==rows[0]['q']
  assert rows[1]['q'] in sent['excludeQuestions']
  assert page.locator('.tag-book-question').count()==3,'Retry must not discard the other questions'
  assert page.evaluate('DB.quizzes.length')==saved_before
  assert page.locator('#tagBookResults').is_visible()
  ctx.close()
 browser.close()
http.shutdown();http.server_close()
assert not any(isinstance(x,str) and x.startswith('PAGE_ERROR') for x in received),received
print('PASS Book Engine V2: explicit consent, selected question types, audit report, page-bound retry and no auto-publish on phone/desktop')
