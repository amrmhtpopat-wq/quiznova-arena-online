"""Chromium: validate mascot artwork, 9 unique cards, QR images and A4 print styling."""
import os,sys,tempfile,threading,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright

temp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(temp.name)/'badge.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import platform_store as store
store.init()
import server
account=store.create_teacher('badj-'+uuid.uuid4().hex+'@example.org',
  'SuperTestPassword123!','Teacher','مدرسة تجريبية للبنين','المهارات الرقمية','boys')
teacher=account['teacher']
student_rows=[
 {'name':f'طالب اختبار {index}','className':'التاسع ب','avatar':f'm{index:02}'}
 for index in range(1,9)
]
student_rows.append({'name':'طالب إضافي','className':'السابع أ','avatar':'b01'})
students=store.add_students(teacher['id'],student_rows)
assert len(students)==9
site=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=site.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(site.server_port)
dest=Path('browser-qa-artifacts')
dest.mkdir(exist_ok=True)

def images_load(page, selector):
  return page.locator(selector).evaluate_all(
    '(items)=>items.every(im=>im.complete && im.naturalWidth>0)')

with sync_playwright() as playwright:
  browser=playwright.chromium.launch(headless=True,args=['--no-sandbox'])
  for width,height,mobile in ((1366,768,False),(390,844,True)):
    ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=mobile,has_touch=mobile)
    ctx.add_init_script("localStorage.setItem('qn9_teacher_token',"+repr(account['token'])+");")
    page=ctx.new_page()
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(base+'/',wait_until='domcontentloaded',timeout=30000)
    page.locator('button.nav[data-panel="students"]').wait_for(state='visible',timeout=15000)
    page.locator('button.nav[data-panel="students"]').click()
    page.locator('.bo-student-id').first.wait_for(state='visible',timeout=12000)
    assert page.locator('.bo-student-id').count()==9
    codes=page.locator('.bo-badge-access-id').all_text_contents()
    assert len(set(codes))==9
    assert all(c.strip()!='BADJ-TH42' for c in codes)
    assert page.locator('.bo-badge-edition').first.inner_text()=='BADJ-TH42'
    assert page.locator('.bo-badge-student-name').first.inner_text()=='طالب اختبار 1'
    page.eval_on_selector_all('.bo-student-id img','images=>images.forEach(img=>img.loading="eager")')
    page.wait_for_function(
      'Array.from(document.querySelectorAll(".bo-badge-qr img,.bo-badge-avatar img")).every(img=>img.complete && img.naturalWidth>0)',
      timeout=15000
    )
    assert images_load(page,'.bo-badge-qr img')
    assert images_load(page,'.bo-badge-avatar img')
    card_img=page.locator('.bo-student-id').nth(7).locator('.bo-badge-avatar img')
    assert card_img.get_attribute('src').endswith('/m07.svg'),card_img.get_attribute('src')
    page.screenshot(path=str(dest/('badj-cards-mobile.png' if mobile else 'badj-cards-desktop.png')),full_page=True)

    page.locator('button.nav[data-panel="school"]').click()
    gallery=page.locator('#schoolAvatarGallery .bo-mascot-option')
    gallery.first.wait_for(state='visible',timeout=8000)
    selected=page.locator('#newStudentAvatar option').all_text_contents()
    for name in ('شرارة','روبوك','فوكسو','نينزو','درعو','بيكسو','زومي'):
      assert name in selected,(name,selected)
    assert 'شخصية شبابية' not in selected
    page.eval_on_selector_all('#schoolAvatarGallery .bo-mascot-option img',
        'imgs=>imgs.forEach(img=>img.loading="eager")')
    page.wait_for_function(
        'Array.from(document.querySelectorAll("#schoolAvatarGallery .bo-mascot-option img")).every(img=>img.complete && img.naturalWidth>0)',
        timeout=20000)
    assert images_load(page,'#schoolAvatarGallery .bo-mascot-option img')

    page.emulate_media(media='print')
    printed=page.locator('#studentsBoard').evaluate(
      'el=>getComputedStyle(el).gridTemplateColumns.split(" ").filter(Boolean).length')
    assert printed==2,printed
    card_height=page.locator('.bo-student-id').first.evaluate('el=>el.getBoundingClientRect().height')
    assert 220<=card_height<=255,card_height
    page.emulate_media(media='screen')
    assert not errors,errors
    ctx.close()

    student_ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=mobile,has_touch=mobile)
    student_page=student_ctx.new_page()
    student_page.goto(base+'/student.html',wait_until='domcontentloaded',timeout=30000)
    student_page.locator('#avatarPicker .avatar-choice').first.wait_for(state='visible',timeout=10000)
    names=student_page.locator('#avatarPicker .bo-avatar-name').all_text_contents()
    assert names[:7]==['شرارة','روبوك','فوكسو','نينزو','درعو','بيكسو','زومي'],names
    student_page.eval_on_selector_all('#avatarPicker img',
        'imgs=>imgs.forEach(img=>img.loading="eager")')
    student_page.wait_for_function(
        'Array.from(document.querySelectorAll("#avatarPicker img")).every(img=>img.complete && img.naturalWidth>0)',
        timeout=20000)
    assert images_load(student_page,'#avatarPicker img')
    student_page.locator('[data-avatar="m06"]').click()
    assert 'selected' in student_page.locator('[data-avatar="m06"]').get_attribute('class')
    student_page.screenshot(path=str(dest/('mascots-mobile.png' if mobile else 'mascots-desktop.png')),full_page=True)
    student_ctx.close()
  browser.close()
site.shutdown();site.server_close()
print('PASS: 7 named mascots, unique QR/student card codes, A4 two-column print and mobile/desktop images.')
