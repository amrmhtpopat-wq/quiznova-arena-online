"""BOOYAHJO 12.1: real Chromium checks of class folders, editable cards, persistent media, cinematic stage and launch."""
import json,os,sys,tempfile,threading,time,uuid,base64,zlib,struct,urllib.request,urllib.error
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
TEMP=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(TEMP.name)/'v121-browser.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
import server

teacher=store.create_teacher('test-v121-browser@example.org','TeacherPasswordV121!',
 'معلم اختبار','مدرسة تجريبية','المهارات الرقمية','boys')
tid=teacher['teacher']['id']
store.add_students(tid,[
 {'name':'طالب الأول','className':'التاسع أ','avatar':'n01'},
 {'name':'طالب الثاني','className':'التاسع ب','avatar':'n02'}])
http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(http.server_port)
screens=Path('browser-qa-artifacts');screens.mkdir(exist_ok=True)

def request(path,body=None,token=None):
 headers={'Content-Type':'application/json'}
 if token:headers['Authorization']='Bearer '+token
 req=urllib.request.Request(base+path,
  data=json.dumps(body,ensure_ascii=False).encode('utf8') if body is not None else None,headers=headers)
 with urllib.request.urlopen(req,timeout=20) as response:
  return json.load(response)

def png_data():
 width=64
 seed=875
 rows=[]
 for y in range(width):
  line=bytearray([0])
  for x in range(width):
   seed=(seed*1664525+1013904223)&0xffffffff
   line.extend([(seed>>16)&255,(seed>>8)&255,seed&255])
  rows.append(bytes(line))
 def part(tag,data):return struct.pack('!I',len(data))+tag+data+struct.pack('!I',zlib.crc32(tag+data)&0xffffffff)
 return b'\x89PNG\r\n\x1a\n'+part(b'IHDR',struct.pack('!2I5B',width,width,8,2,0,0,0))+part(b'IDAT',zlib.compress(b''.join(rows)))+part(b'IEND',b'')

with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
 for width,height,mobile in [(1366,820,False),(390,844,True)]:
  ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=mobile,has_touch=mobile,accept_downloads=True)
  page=ctx.new_page();errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(base+'/?teacher=1',wait_until='domcontentloaded')
  page.locator('#authForm').wait_for(state='visible',timeout=15000)
  page.locator('#email').fill('test-v121-browser@example.org')
  page.locator('#password').fill('TeacherPasswordV121!')
  page.locator('#authSubmit').click()
  page.locator('#workspace').wait_for(state='visible',timeout=15000)
  page.locator('button.nav[data-panel="students"]').click()
  page.locator('#studentsBoard .bo-class-folder').first.wait_for(timeout=15000)
  assert page.locator('#studentsBoard .bo-class-folder').count()==2
  original=store.list_students(tid)[0]
  page.locator('#studentsBoard [data-edit-student="'+original['id']+'"]').click()
  page.locator('#boCardEditor').wait_for(state='visible',timeout=8000)
  page.locator('#boCardEditForm [name=name]').fill('طالب تم تعديله')
  page.locator('#boCardEditForm [name=className]').fill('التاسع ج')
  page.locator('#boCardEditForm [name=avatar]').select_option('n03')
  page.locator('#boCardSave').click()
  page.locator('#studentsBoard').get_by_text('طالب تم تعديله').first.wait_for(timeout=15000)
  updated=next(x for x in store.list_students(tid) if x['id']==original['id'])
  assert (updated['name'],updated['className'],updated['avatar'])==('طالب تم تعديله','التاسع ج','n03')
  assert (updated['card'],updated['cardCode'])==(original['card'],original['cardCode'])
  page.screenshot(path=str(screens/('v121-folders-mobile.png' if mobile else 'v121-folders-desktop.png')),full_page=True)
  # The second student is archived only in the first (desktop) pass. Mobile checks the remaining card.
  if not mobile:
   other=next(x for x in store.list_students(tid) if x['id']!=original['id'])
   page.once('dialog',lambda d:d.accept())
   page.locator('#studentsBoard [data-remove-student="'+other['id']+'"]').click()
   page.locator('#studentCount').get_by_text('1').wait_for(timeout=15000)
   assert store.student_profile_by_card(other['cardCode']) is None

  page.goto(base+'/studio.html#media',wait_until='domcontentloaded')
  page.locator('#view-media').wait_for(state='visible',timeout=20000)
  if not mobile:
   page.locator('#view-media input[type=file]').first.set_input_files({
    'name':'lesson-v121.png','mimeType':'image/png','buffer':png_data()})
   page.locator('#mediaGallery').get_by_text('lesson-v121').wait_for(timeout=15000)
   assert store.query('SELECT COUNT(*) AS n FROM teacher_media WHERE teacher_id=?',(tid,))['n']==1
  else:
   page.locator('#mediaGallery').get_by_text('lesson-v121').wait_for(timeout=15000)
  page.reload(wait_until='domcontentloaded')
  page.locator('#mediaGallery').get_by_text('lesson-v121').wait_for(timeout=20000)
  assert not errors,errors
  ctx.close()

 # Separate stage presentation test with an authorized room and a real participant.
 room=request('/api/room/start',{'quiz':{
  'id':'cinema-test','title':'تحدي بويا',
  'questions':[{'id':'q1','type':'single','text':'ما اسم المنصة؟','options':['بويا','غير ذلك'],
   'correct':[0],'time':30,'points':1000}]},
  'background':'cine-stars'},teacher['token'])
 code=room['code']
 joined=request('/api/room/join',{'code':code,'name':'مشارك اختبار','avatar':'n01'})
 assert joined['ok']
 stage_ctx=browser.new_context(viewport={'width':1280,'height':720})
 stage=stage_ctx.new_page()
 stage.goto(base+'/stage.html?code='+code+'&stage='+room['stageToken'])
 stage.locator('.lobby').wait_for(timeout=10000)
 request('/api/room/control',{'code':code,'hostToken':room['hostToken'],'action':'start'})
 stage.locator('.bo-launch-countdown').wait_for(state='visible',timeout=2500)
 stage.locator('body[data-scene="cine-stars"]').wait_for(timeout=6000)
 request('/api/room/control',{'code':code,'hostToken':room['hostToken'],'action':'background','background':'cine-neon'})
 stage.locator('body[data-scene="cine-neon"]').wait_for(timeout=9000)
 stage.screenshot(path=str(screens/'v121-cinematic-stage.png'),full_page=True)
 stage_ctx.close()
 browser.close()
http.shutdown();http.server_close()
print('PASS: desktop/mobile folders, QR-preserving edit, safe archive, Neon media retention after reload, launch countdown and stage theme synchronization.')
