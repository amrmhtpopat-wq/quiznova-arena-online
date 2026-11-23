"""TAG V5: responsive public entry, champion branding, back navigation and non-invasive lab coverage."""
import os,sys,json,tempfile,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
tmp=tempfile.TemporaryDirectory()
os.environ.pop("DATABASE_URL",None)
os.environ["QUIZNOVA_SQLITE_PATH"]=str(Path(tmp.name)/"v5-layout.sqlite")
os.environ["QUIZNOVA_CLOUD"]="1"
os.environ["QUIZNOVA_ALLOW_EPHEMERAL"]="yes"
import platform_store as store
import server
store.create_teacher("spatial-v5@example.org","StrongSpatialV5Pass123!","معلم الاختبار","مدرسة اختبار","المهارات الرقمية","boys")
http=server.ThreadingHTTPServer(("127.0.0.1",0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
BASE=f"http://127.0.0.1:{http.server_port}"
checks=0
def assert_in_bounds(page,selector,label,margin=3):
  bounds=page.locator(selector).first.bounding_box()
  assert bounds is not None,(label,"missing box")
  w=page.evaluate("window.innerWidth")
  assert bounds["width"]>16 and bounds["x"]>=-margin and bounds["x"]+bounds["width"]<=w+margin,(label,w,bounds)
def no_overflow(page,label,margin=5):
  dim=page.evaluate("""() => ({width:innerWidth,scroll:document.documentElement.scrollWidth,body:document.body.scrollWidth})""")
  assert dim["scroll"]<=dim["width"]+margin,(label,dim)
def asset_loaded(page,selector,label):
  page.locator(selector).first.wait_for(state="visible",timeout=15000)
  state=page.locator(selector).first.evaluate("""im => ({src:im.getAttribute('src'),w:im.naturalWidth,h:im.naturalHeight})""")
  assert state["w"]>50 and state["h"]>50,(label,state)
  return state
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
 for width,height in [(320,780),(390,844),(768,1024),(1024,768),(1366,768)]:
  ctx=browser.new_context(viewport={"width":width,"height":height},
       is_mobile=width<=440,has_touch=width<=440,service_workers="block")
  page=ctx.new_page()
  page.goto(BASE+"/",wait_until="domcontentloaded")
  page.locator("#studentWelcome").wait_for(state="visible")
  asset=asset_loaded(page,"#studentWelcome .bo-entry-logo img","public logo")
  assert "tag-spatial-identity-v3.webp" in asset["src"]
  for i in range(3):
   card=page.locator("#studentWelcome .bo-entry-option").nth(i)
   assert card.is_visible(),(width,"hidden activity",i)
   assert_in_bounds(page,f"#studentWelcome .bo-entry-option:nth-child({i+1})",f"entry card {width}/{i}")
   style=card.evaluate("""el => ({background:getComputedStyle(el).backgroundImage,
      color:getComputedStyle(el).color, title:getComputedStyle(el.querySelector('strong')).color})""")
   assert "linear-gradient" in style["background"] and "rgb(248, 251, 255)" not in style["background"],(width,"old bright tile",style)
   assert style["title"] in ["rgb(246, 252, 250)","rgb(245, 253, 249)","rgb(242, 252, 249)"],(width,"wrong heading palette",style)
  no_overflow(page,f"home {width}")
  print("HOME_PASS",width,flush=True);checks+=1
  if width in (390,1366):
   for mode in ["live","card","solo"]:
    page.goto(BASE+"/",wait_until="domcontentloaded")
    page.locator('#studentWelcome .bo-entry-option[href="/student.html?mode='+mode+'"]').click()
    page.wait_for_url("**/student.html?mode="+mode,timeout=12000)
    page.locator(".tag-back-nav").wait_for(state="visible",timeout=10000)
    assert_in_bounds(page,".tag-back-nav",f"student back {width}")
    page.locator(".tag-back-nav").click()
    page.wait_for_url(BASE+"/",timeout=12000)
    checks+=1
   # CHAMPION TAG requires an authenticated teacher; test branding only after
   # entering through the normal sign-in route (never bypass protected pages).
   page.goto(BASE+"/?teacher=1",wait_until="domcontentloaded")
   page.locator("#authWall").wait_for(state="visible",timeout=12000)
   page.locator("#email").fill("spatial-v5@example.org")
   page.locator("#password").fill("StrongSpatialV5Pass123!")
   page.locator("#authSubmit").click()
   page.locator("#workspace").wait_for(state="visible",timeout=15000)
   page.goto(BASE+"/champion.html",wait_until="domcontentloaded")
   asset=asset_loaded(page,"header.top .brand-img","champion logo")
   assert "tag-spatial-identity-v3.webp" in asset["src"]
   page.locator(".tag-back-nav").wait_for(state="visible")
   assert_in_bounds(page,"header.top .brand-img",f"champion brand {width}")
   assert_in_bounds(page,"header.top .tag-back-nav",f"champion back {width}")
   no_overflow(page,f"champion {width}",margin=10)
   checks+=1
   page.goto(BASE+"/champion-board.html",wait_until="domcontentloaded")
   asset=asset_loaded(page,"header.top .brand-img","champion board logo")
   assert "tag-spatial-identity-v3.webp" in asset["src"]
   page.locator(".tag-back-nav").wait_for(state="visible")
   assert_in_bounds(page,"header.top .tag-back-nav",f"champion board back {width}")
   checks+=1
  ctx.close()
 for path in ["about.html","for-teachers.html","app.html","admin.html",
              "tag-lab-home.html","tag-lab-books.html","tag-lab-create.html",
              "tag-lab-games.html","tag-lab-library.html","tag-lab-live.html",
              "tag-lab-mixer.html","tag-lab-students.html","game-lab-preview.html",
              "stage.html"]:
  ctx=browser.new_context(viewport={"width":390,"height":844},is_mobile=True,has_touch=True,service_workers="block")
  page=ctx.new_page()
  page.goto(BASE+"/"+path,wait_until="domcontentloaded",timeout=25000)
  button=page.locator(".tag-back-nav")
  button.wait_for(state="attached",timeout=15000)
  assert_in_bounds(page,".tag-back-nav","back "+path)
  if path in ("about.html","for-teachers.html","app.html"):
   no_overflow(page,path,margin=8)
  print("BACK_PASS",path,flush=True);checks+=1
  ctx.close()
 browser.close()
http.shutdown();http.server_close()
print("PASS TAG V5 responsive and back-nav check:",checks,"complete cases.")
