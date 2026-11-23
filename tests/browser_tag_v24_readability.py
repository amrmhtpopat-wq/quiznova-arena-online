"""TAG V24 actual-browser UI readability and responsive interaction across 320–1366 px.
Local disposable teacher database. No production accounts or student records used.
"""
import os,sys,tempfile,threading,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
tmp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(tmp.name)/'tag-v24-ui.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
import server
teacher=store.create_teacher('tag-v24-qa@example.org','TAGV24SafeTestStrong123!',
 'معلم الفحص','مدرسة فحص تجريبية','المهارات الرقمية','boys')
http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(http.server_port)
Path('artifacts/tag-v24').mkdir(parents=True,exist_ok=True)
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
 for width,height in ((320,700),(390,844),(768,1024),(1024,768),(1366,850)):
  ctx=browser.new_context(viewport={'width':width,'height':height},
    is_mobile=width<=430,has_touch=width<=430,service_workers='block')
  ctx.add_init_script('localStorage.setItem("qn9_teacher_token",'+json.dumps(teacher['token'])+');')
  page=ctx.new_page()
  errors=[]
  page.on('pageerror',lambda err:errors.append(str(err)))
  page.goto(BASE+'/studio.html#bank',wait_until='domcontentloaded',timeout=30000)
  page.locator('#view-bank.active').wait_for(state='visible',timeout=30000)
  page.locator('#questionBank .jordan-bank-item').first.wait_for(state='visible',timeout=20000)
  assert page.locator('#view-bank .tag24-filter').count()==7
  bank=page.evaluate("""() => {
   let el=document.querySelector('.jordan-bank-item');
   let font=node=>parseFloat(getComputedStyle(node).fontSize);
   let rect=node=>{let r=node.getBoundingClientRect();return {left:r.left,right:r.right,width:r.width}};
   return {viewport:innerWidth,scroll:document.documentElement.scrollWidth,
    questionSize:font(el.querySelector('h4')),metaSize:font(el.querySelector('p')),
    tagSize:font(el.querySelector('.bank-tags .tag')),sourceSize:font(el.querySelector('.jordan-source-label')),
    titleColor:getComputedStyle(el.querySelector('h4')).color,
    card:rect(el),search:rect(document.getElementById('bankSearch'))};
  }""")
  print('TAG_V24_BANK',width,json.dumps(bank,ensure_ascii=False),flush=True)
  assert bank['scroll']<=width+5,('Bank horizontal overflow',width,bank)
  assert bank['questionSize']>=15 and bank['metaSize']>=12 and bank['tagSize']>=11,('Tiny bank text',width,bank)
  assert bank['sourceSize']>=11,('Tiny source label',width,bank)
  assert bank['card']['left']>=-4 and bank['card']['right']<=width+4,('Card clipping',width,bank)
  assert bank['search']['left']>=-4 and bank['search']['right']<=width+4,('Filter clipping',width,bank)
  assert bank['titleColor'].startswith('rgb(')
  rgb=[int(x.strip()) for x in bank['titleColor'][4:-1].split(',')[:3]]
  assert min(rgb)>=180,('Bank font dark on dark background',width,bank)
  page.locator('#bankSearch').fill('فحص-بحث-غير-موجود-2026')
  page.locator('#view-bank .jordan-no-questions').wait_for(state='visible',timeout=4000)
  page.locator('#bankSearch').fill('')
  page.locator('#questionBank .jordan-bank-item').first.wait_for(state='visible',timeout=5000)
  page.screenshot(path=f'artifacts/tag-v24/bank-{width}.png',full_page=False)
  page.evaluate("go('generator')")
  page.locator('#view-generator.active').wait_for(state='visible',timeout=15000)
  generator=page.evaluate("""() => {
   const font=node=>parseFloat(getComputedStyle(node).fontSize);
   const rect=node=>{const r=node.getBoundingClientRect();return {left:r.left,right:r.right,width:r.width}};
   return {viewport:innerWidth,scroll:document.documentElement.scrollWidth,
    intro:font(document.querySelector('#tag24GeneratorTitle')),
    title:font(document.querySelector('#tagBookMakerTitle')),
    label:font(document.querySelector('#view-generator .tag-book-field label')),
    type:font(document.querySelector('#view-generator .type-pick b')),
    aiButton:rect(document.getElementById('tagBookAi')),
    bookPanel:rect(document.getElementById('tagBookMaker')),
    generatorPanel:rect(document.querySelector('#view-generator .generator-panel'))};
  }""")
  print('TAG_V24_GENERATOR',width,json.dumps(generator,ensure_ascii=False),flush=True)
  assert generator['scroll']<=width+5,('Generator horizontal overflow',width,generator)
  assert generator['title']>=20 and generator['label']>=13 and generator['type']>=11,('Tiny generator labels',width,generator)
  for part in ('aiButton','bookPanel','generatorPanel'):
   assert generator[part]['left']>=-4 and generator[part]['right']<=width+4,(width,part,generator)
  page.locator('#tagBookTopic').fill('اختبار الصف السابع')
  assert page.locator('#tagBookTopic').input_value()=='اختبار الصف السابع'
  page.screenshot(path=f'artifacts/tag-v24/generator-{width}.png',full_page=False)
  assert not errors,('JS errors',width,errors)
  ctx.close()
 browser.close()
http.shutdown();http.server_close()
print('PASS TAG V24 bank and generator: 320,390,768,1024,1366px')
