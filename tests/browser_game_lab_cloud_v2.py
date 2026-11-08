"""Game Lab V2 real Chromium: teacher login, cloud save/publish, card attempt and reports."""
from __future__ import annotations
import json,os,tempfile,threading,uuid
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright
TMP=tempfile.TemporaryDirectory()
os.environ.pop("DATABASE_URL",None)
os.environ["QUIZNOVA_SQLITE_PATH"]=str(Path(TMP.name)/"lab-browser.sqlite")
os.environ["QUIZNOVA_CLOUD"]="1"
os.environ["QUIZNOVA_ALLOW_EPHEMERAL"]="yes"
import platform_store as db
db.init()
import server
email="gamelab-"+uuid.uuid4().hex+"@example.org"
password="VerySecureQATeacherPassword123!"
teacher=db.create_teacher(email,password,"Game Lab QA Teacher","مدرسة تجريبية","المهارات الرقمية")
student=db.add_students(teacher["teacher"]["id"],[{"name":"طالب تجربة Game Lab","className":"السابع أ","avatar":"m01"}])[0]
http=ThreadingHTTPServer(("127.0.0.1",0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
base="http://127.0.0.1:"+str(http.server_port)
try:
 with sync_playwright() as playwright:
  browser=playwright.chromium.launch(headless=True,args=["--no-sandbox"])
  try:
   teacher_ctx=browser.new_context(viewport={"width":1280,"height":800})
   teacher_page=teacher_ctx.new_page()
   errors=[]
   teacher_page.on("pageerror",lambda e:errors.append("teacher:"+str(e)))
   teacher_page.goto(base+"/game-lab-preview.html",wait_until="domcontentloaded")
   teacher_page.locator("#cloudEmail").fill(email)
   teacher_page.locator("#cloudPassword").fill(password)
   teacher_page.locator("#cloudSignIn").click()
   teacher_page.locator("#cloudWorkspace").wait_for(state="visible",timeout=13000)
   teacher_page.locator("#cloudMode").select_option("quiz")
   teacher_page.locator("#cloudMaxAttempts").select_option("2")
   teacher_page.locator("#cloudSave").click()
   teacher_page.locator("#cloudList .cloud-activity").first.wait_for(timeout=10000)
   assert teacher_page.locator("#cloudList .cloud-activity").count()==1
   teacher_page.locator("#cloudList .cloud-activity button").filter(has_text="نشر").click()
   teacher_page.locator("#cloudShare").wait_for(state="visible",timeout=10000)
   link=teacher_page.locator("#cloudLink").input_value()
   assert link.startswith(base+"/game-lab-play.html?game="),link
   assert teacher_page.locator("#cloudQR").get_attribute("src").startswith("/api/qr?")
   player_ctx=browser.new_context(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
   student_page=player_ctx.new_page()
   student_page.on("pageerror",lambda e:errors.append("student:"+str(e)))
   student_page.goto(link,wait_until="domcontentloaded")
   student_page.locator("#activityTitle").wait_for(timeout=12000)
   assert "مكونات الحاسوب" in student_page.locator("#activityTitle").inner_text()
   student_page.locator("#studentCard").fill(student["cardCode"])
   student_page.locator("#startBtn").click()
   student_page.locator("#questionText").wait_for(state="visible",timeout=12000)
   question_answers=["CPU","RAM","اللوحة الأم","SSD","لوحة المفاتيح","الشاشة","الفأرة","السماعات"]
   for i,answer in enumerate(question_answers):
    assert student_page.locator("#questionText").inner_text()
    student_page.locator("#choices .choice").filter(has_text=answer).first.click()
    student_page.locator("#nextBtn").wait_for(state="visible",timeout=12000)
    student_page.locator("#nextBtn").click()
   student_page.locator("#finishPanel").wait_for(state="visible",timeout=10000)
   assert "800" in student_page.locator("#finishScore").inner_text()
   assert "90" in student_page.locator("#earnedXp").inner_text()
   player_ctx.close()
   teacher_page.locator("#cloudList .cloud-activity button").filter(has_text="النتائج").click()
   teacher_page.locator("#cloudReport").wait_for(state="visible",timeout=12000)
   assert teacher_page.locator("#cloudResults tbody tr").count()==1
   assert student["name"] in teacher_page.locator("#cloudResults").inner_text()
   assert not errors,errors
   teacher_ctx.close()
   print("PASS: authenticated teacher save/publish/QR and card-based student results and XP.",flush=True)
  finally:
   browser.close()
finally:
 http.shutdown()
 http.server_close()
 TMP.cleanup()
