"""Chromium regression for BOOYAHJO Game Lab isolated QA preview."""
from __future__ import annotations
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]

def run():
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,directory=str(ROOT),**kwargs)
        def log_message(self,*args):
            pass
    http=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    Thread(target=http.serve_forever,daemon=True).start()
    base="http://127.0.0.1:"+str(http.server_port)
    try:
      with sync_playwright() as runner:
        browser=runner.chromium.launch(headless=True,args=["--no-sandbox"])
        try:
          for width,height in ((1440,900),(1280,720),(390,844),(360,740)):
            page=browser.new_page(viewport={"width":width,"height":height})
            errors=[]
            page.on("pageerror",lambda e:errors.append(str(e)+" STACK "+str(e.stack)))
            try:
              page.goto(base+"/game-lab-preview.html",wait_until="domcontentloaded")
              page.locator(".game").first.wait_for(state="visible",timeout=7000)
              assert page.locator("#gameGrid .game").count()==24
              assert page.locator("#gameGrid .game .state:not(.plan)").count()==24
              assert page.locator("#contentFeedback").inner_text().startswith("✓"),"sample content failed to load"
              horizontal=page.evaluate("()=>({s:document.documentElement.scrollWidth,w:innerWidth})")
              assert horizontal["s"]<=horizontal["w"]+2,(width,horizontal)
              page.locator("#gameSearch").fill("مطابقة")
              assert page.locator("#gameGrid .game").count()<=2
              page.locator("#gameSearch").fill("")
              assert page.locator("#gameGrid .game").count()==24
              page.locator("[data-category='vocabulary']").click()
              assert 1<=page.locator("#gameGrid .game").count()<24
              page.locator("[data-category='all']").click()
              # Exercise every playable template with the same content.
              for game in ("quiz","fast","pairs","flash","wheel","boxes","sort","truth"):
                # Launch by matching catalog-card display title.
                card=page.locator("#gameGrid .game").filter(has=page.locator("h3",has_text={
                  "quiz":"تحدي الاختيار","fast":"سباق الوقت","pairs":"توصيل الأزواج",
                  "flash":"بطاقات الذاكرة","wheel":"عجلة الحظ","boxes":"الصناديق الغامضة",
                  "sort":"فرز وتصنيف","truth":"صح أم خطأ؟"}[game])).first
                card.locator("button").click()
                page.locator("#playOverlay").wait_for(state="visible",timeout=7000)
                assert page.locator("#playBody").inner_text().strip(),game
                if game in ("quiz","fast"):
                  page.locator("#answers .choice").first.click()
                  assert page.locator("#nextWrap button").count()==1
                elif game=="pairs":
                  assert page.locator("#matchLeft button").count()>0
                  assert page.locator("#matchRight button").count()>0
                elif game=="flash":
                  before=page.locator("#flipCard").inner_text()
                  page.locator("#flipCard").click()
                  assert page.locator("#flipCard").inner_text()!=before
                elif game=="wheel":
                  page.locator("#wheelArea button").click()
                  page.wait_for_timeout(3150)
                  assert page.locator("#wheelReveal h3").count()==1
                elif game=="boxes":
                  page.locator(".mystery").first.click()
                  assert page.locator(".mystery.open").count()==1
                elif game=="sort":
                  page.locator("#sortChoices button").first.click()
                  assert page.locator("#sortNext button").count()==1
                elif game=="truth":
                  page.locator("#truthActions button").first.click()
                  assert page.locator("#truthNext button").count()==1
                page.locator("#closePlay").click()
                assert page.locator("#playOverlay").is_hidden()
              # All sixteen new minigames render original interactive controls.
              catalog_extra={
                'crossword':('الكلمات المتقاطعة','.extra-cross-letter'),
                'wordsearch':('البحث عن الكلمات','.extra-word-letter'),
                'anagram':('ترتيب الحروف','.extra-letter'),
                'order':('الترتيب المنطقي','.extra-order-line'),
                'maze':('متاهة المعرفة','#mazeChoices .choice'),
                'balloons':('فرقعة البالونات','.extra-balloon'),
                'memory':('تذكّر الصورة','.extra-memory-card'),
                'hidden':('الصورة المخفية','.extra-hidden-tile'),
                'cloze':('أكمل الفراغ','#clozeChoices .choice'),
                'diagram':('تسمية الرسم','#diagramChoices .choice'),
                'board':('لوحة النقاط','.extra-score-team'),
                'teams':('معركة الفرق','#teamsOptions .choice'),
                'survey':('استفتاء الصف','.extra-survey-row'),
                'exit':('بطاقة الخروج','#exitResponse'),
                'story':('اختر مسارك','#storyPaths .choice'),
                'bingo':('بينغو المصطلحات','.extra-bingo-cell')}
              for gid,(title,selector) in catalog_extra.items():
                card=page.locator('#gameGrid .game').filter(has=page.locator('h3',has_text=title)).first
                card.locator('button').click()
                page.locator('#playOverlay').wait_for(state='visible',timeout=7000)
                if page.locator(selector).count()<1:
                  page.screenshot(path=str(ROOT/'browser-qa-artifacts'/('gamelab-broken-'+gid+'-'+str(width)+'.png')),full_page=True)
                  raise AssertionError(f'{gid} failed to show {selector}')
                # Enter a sample interaction into the playable template.
                if gid=='anagram':page.locator('.extra-letter:not([disabled])').first.click()
                if gid=='memory':page.locator('.extra-memory-card').first.click()
                if gid=='hidden':page.locator('.extra-hidden-tile').first.click()
                if gid=='order':page.locator('.extra-order-line .button').first.click()
                if gid=='maze':page.locator('#mazeChoices button').first.click()
                if gid=='balloons':page.locator('.extra-balloon').first.click(force=True)
                if gid=='survey':page.locator('.extra-survey-row .button').first.click()
                if gid=='exit':page.locator('#exitResponse').fill('إجابة تجريبية')
                if gid=='story':page.locator('#storyPaths .choice').first.click()
                if gid=='bingo':page.locator('#bingoControls .button').first.click()
                assert not errors,(gid,width,errors)
                page.locator('#closePlay').click()
                assert page.locator('#playOverlay').is_hidden()
              # Game Mixer: three playable stages and a single classroom recap.
              if width==1440:
                for select in ('mixerOne','mixerTwo','mixerThree'):
                  page.locator('#'+select).select_option('board')
                page.locator('#mixerStart').click()
                page.locator('#playOverlay').wait_for(state='visible')
                for stage in range(3):
                  page.locator('#boardControls button').filter(has_text='إنهاء').click()
                  assert not errors,('mixer stage',stage,errors)
                  if stage<2:
                    page.locator('#endButtons button').filter(has_text='الانتقال').click()
                  else:
                    page.locator('#endButtons button').filter(has_text='ملخص الحصة').click()
                assert 'اكتملت رحلة Game Mixer' in page.locator('#playBody').inner_text()
                page.locator('#closePlay').click()
              # Printing uses a true text worksheet; no app data leaves this browser.
              page.evaluate("() => {window.print=()=>{}}")
              page.locator("#printActivity").click()
              assert page.locator("#printPage .print-q").count()==8
              # Save and reload a local draft, no server storage.
              page.locator("#saveActivity").click()
              assert page.locator("#savedList .saved").count()==1
              page.reload(wait_until="domcontentloaded")
              assert page.locator("#savedList .saved").count()==1
              assert not errors,(width,errors)
              print("PASS GameLab %sx%s: catalog, filters, 24 games, local drafts, viewport" % (width,height),flush=True)
            finally:
              page.close()
        finally:
          browser.close()
    finally:
      http.shutdown()
    print("PASS GameLab: all 24 interactive templates across 4 desktop/mobile viewports.")

if __name__=="__main__":
    run()
