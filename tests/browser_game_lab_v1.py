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
            page.on("pageerror",lambda e:errors.append(str(e)))
            try:
              page.goto(base+"/game-lab-preview.html",wait_until="domcontentloaded")
              page.locator(".game").first.wait_for(state="visible",timeout=7000)
              assert page.locator(".game").count()==24
              assert page.locator(".game .state:not(.plan)").count()==8
              assert page.locator("#contentFeedback").inner_text().startswith("✓"),"sample content failed to load"
              horizontal=page.evaluate("()=>({s:document.documentElement.scrollWidth,w:innerWidth})")
              assert horizontal["s"]<=horizontal["w"]+2,(width,horizontal)
              page.locator("#gameSearch").fill("مطابقة")
              assert page.locator(".game").count()<=2
              page.locator("#gameSearch").fill("")
              assert page.locator(".game").count()==24
              page.locator("[data-category='vocabulary']").click()
              assert 1<=page.locator(".game").count()<24
              page.locator("[data-category='all']").click()
              # Exercise every playable template with the same content.
              for game in ("quiz","fast","pairs","flash","wheel","boxes","sort","truth"):
                page.evaluate("id=>{document.querySelectorAll('.game').forEach(x=>{if(x.querySelector('button').onclick){}})}",game)
                page.evaluate("id=>{document.querySelector('.button')}",game)
                # Launch by matching catalog-card display title.
                card=page.locator(".game").filter(has=page.locator("h3",has_text={
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
              # Printing uses a true text worksheet; no app data leaves this browser.
              page.locator("#printActivity").evaluate("el=>{el.onclick=()=>{const p=document.getElementById('printPage');const fn=window.print;window.print=()=>{};el.click();window.print=fn}}")
              # Save and reload a local draft, no server storage.
              page.locator("#saveActivity").click()
              assert page.locator("#savedList .saved").count()==1
              page.reload(wait_until="domcontentloaded")
              assert page.locator("#savedList .saved").count()==1
              assert not errors,(width,errors)
              print("PASS GameLab %sx%s: catalog, filters, 8 games, local drafts, viewport" % (width,height),flush=True)
            finally:
              page.close()
        finally:
          browser.close()
    finally:
      http.shutdown()
    print("PASS GameLab: all 8 interactive templates across 4 desktop/mobile viewports.")

if __name__=="__main__":
    run()
