"""TAG Spatial V4: physical geometry, direct navigation and studio sidebar audit."""
import json,os,sys,tempfile,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
tmp=tempfile.TemporaryDirectory()
os.environ.pop("DATABASE_URL",None)
os.environ["QUIZNOVA_SQLITE_PATH"]=str(Path(tmp.name)/"spatial-v4.sqlite")
os.environ["QUIZNOVA_CLOUD"]="1"
os.environ["QUIZNOVA_ALLOW_EPHEMERAL"]="yes"
import platform_store as store
import server
store.create_teacher("spatial-v4@example.org","SpatialStrongPass123!","معلم الاختبار","مدرسة تجريبية","المهارات الرقمية","boys")
http=server.ThreadingHTTPServer(("127.0.0.1",0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
BASE="http://127.0.0.1:"+str(http.server_port)
seen=[]
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
    for width,height in ((390,844),(768,1024),(1366,768)):
        ctx=browser.new_context(viewport={"width":width,"height":height},
                is_mobile=width<600,has_touch=width<600,service_workers="block")
        page=ctx.new_page()
        page.on("pageerror",lambda err:seen.append(str(err)))
        page.goto(BASE+"/?teacher=1",wait_until="domcontentloaded")
        page.locator("#email").fill("spatial-v4@example.org")
        page.locator("#password").fill("SpatialStrongPass123!")
        page.locator("#authSubmit").click()
        page.locator("#workspace").wait_for(state="visible",timeout=15000)
        page.locator("#panel-home .tag-spatial-native-host").wait_for(state="visible",timeout=12000)
        page.wait_for_function("""() => Boolean(document.querySelector(".tag-spatial-native-host")?.shadowRoot?.getElementById("tag-v3-tools"))""",timeout=8000)
        dims=page.evaluate("""() => {
           const rect=s=>{const e=document.querySelector(s);if(!e)return null;
            const r=e.getBoundingClientRect(),c=getComputedStyle(e);
            return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),
                 d:c.display,v:c.visibility,z:c.zIndex,overflow:c.overflow};};
           const host=document.querySelector(".tag-spatial-native-host"),sh=host.shadowRoot;
           const hr=sh.querySelector(".header").getBoundingClientRect();
           const shell=sh.querySelector(".shell").getBoundingClientRect();
           const menu=document.querySelector("#workspace>.sidebar");
           return {viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,
            workspace:rect("#workspace"),main:rect("#workspace>.main"),
            topbar:rect("#workspace>.main>.topbar"),panel:rect("#panel-home"),
            legacyHero:rect("#panel-home>.hero"),nativeHost:rect(".tag-spatial-native-host"),
            spatialHeader:{x:Math.round(hr.x),y:Math.round(hr.y),w:Math.round(hr.width),h:Math.round(hr.height)},
            spatialShell:{x:Math.round(shell.x),y:Math.round(shell.y),w:Math.round(shell.width),h:Math.round(shell.height)},
            sidebar:rect("#workspace>.sidebar"),teacherMenu:menu?.getBoundingClientRect().toJSON()};}""")
        print("PORTAL_GEOMETRY "+json.dumps({"width":width,"geo":dims},ensure_ascii=False),flush=True)
        assert dims["scrollWidth"]<=width+5,("portal_overflow",width,dims)
        assert dims["spatialHeader"]["w"]>100 and dims["spatialHeader"]["h"]>=40,("header_missing",width)
        assert dims["spatialHeader"]["y"]<150,("EXCESSIVE_TOP_GAP",width,dims)
        assert not page.locator("#panel-home>.hero").is_visible(),("OLD_HERO_FLASH",width,dims)
        assert not page.locator("#workspace>.sidebar").is_visible(),("OLD_SIDEBAR_ON_HOME",width,dims)
        assert dims["main"]["w"]>=width-3,("LANDING_NOT_FULL_WIDTH",width,dims)
        host=page.locator(".tag-spatial-native-host")
        host.locator('[data-tool="create"]').first.click()
        page.wait_for_url("**/studio.html#builder",timeout=14000)
        page.locator("#view-builder.active").wait_for(state="visible",timeout=15000)
        studio=page.evaluate("""() => {
         const sb=document.querySelector("#sidebar"),nav=sb.querySelector("nav"),
          groups=[...sb.querySelectorAll(".tag-studio-nav-group")];
         const rect=e=>{const r=e.getBoundingClientRect();return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)]};
         return {viewport:innerWidth,scroll:document.documentElement.scrollWidth,sidebar:rect(sb),
          sidebarStyle:[getComputedStyle(sb).display,getComputedStyle(sb).position,
            getComputedStyle(sb).overflowY],scrollHeight:sb.scrollHeight,clientHeight:sb.clientHeight,
          nav:rect(nav),groupRects:groups.map(rect),groupDisplays:groups.map(e=>getComputedStyle(e).display),
          main:rect(document.querySelector("#app>.main"))}; }""")
        print("STUDIO_GEOMETRY "+json.dumps({"width":width,"geo":studio},ensure_ascii=False),flush=True)
        assert studio["scroll"]<=width+5,("studio_overflow",width,studio)
        assert len(studio["groupRects"])==4 and all(r[3]>20 for r in studio["groupRects"]),("sidebar_hidden",width,studio)
        if width>=1025:
            assert studio["sidebar"][2]>=240 and studio["nav"][2]>=210,("sidebar_clipped",width,studio)
            assert studio["sidebar"][3]>=height*0.93,("SIDEBAR_ONLY_LOGO_VISIBLE",width,studio)
            assert all(r[0]>=studio["sidebar"][0]-2 and r[0]+r[2]<=studio["sidebar"][0]+studio["sidebar"][2]+2 for r in studio["groupRects"]),("menu_horizontal_clip",width,studio)
        ctx.close()
    browser.close()
http.shutdown();http.server_close()
assert not seen,seen
print("PASS TAG Spatial V4: dashboard layout, direct navigation, 3D scene and studio sidebar geometry.")
