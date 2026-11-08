"""V12.6: viewport-height projector regression with a read-only mock stage API."""
from __future__ import annotations
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SCENES = {
    "111111": "lobby",
    "222222": "question",
    "333333": "results",
    "444444": "teamresults",
    "555555": "finished",
    "666666": "longquestion",
    "777777": "private",
}
PLAYERS = [{"name": "طالب "+str(i), "score": 1100-i*90,
            "avatar": "b01", "team": "النمور" if i % 2 else "الصقور"}
           for i in range(1, 9)]
LEADERS = [{"name": p["name"], "score": p["score"]} for p in PLAYERS]
TEAMS = [{"name": "النمور", "score": 5800}, {"name": "الصقور", "score": 5400}]


def stage_room(code):
    scene = SCENES[code]
    group = scene == "teamresults"
    status = "question" if scene in ("question", "longquestion") else ("results" if scene in ("results", "teamresults", "private") else scene)
    return {
        "status": status, "background": "cartoon", "index": 1, "total": 8,
        "playType": "teams" if group else "individual",
        "players": PLAYERS, "teams": TEAMS, "leaders": LEADERS,
        "teamNames": ["النمور", "الصقور"], "showFeedback": scene != "private",
        "examMode": False, "roundDurationMs": 30000, "stats": {
            "accuracy": 82, "answered": 8, "correct": 6, "wrong": 2},
        "quizTitle": "تجربة عرض BOOYAHJO", "question": {
            "type": "single",
            "text": ("اختر الإجابة الصحيحة عن السؤال التعليمي التالي الذي يحتوي على تفاصيل كثيرة "
                     "ويحتاج إلى عرض واضح دون تحريك الصفحة داخل شاشة البروجيكتور. ") * (3 if scene == "longquestion" else 1),
            "options": ["وحدة المعالجة المركزية", "ذاكرة الوصول العشوائي",
                        "محرك الأقراص الصلبة", "اللوحة الأم"]},
        "explanation": "الإجابة الصحيحة تعتمد على وظيفة الوحدة."}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/room/state":
            code = parse_qs(parsed.query).get("code", [""])[0]
            if code not in SCENES:
                self.send_error(404)
                return
            raw = json.dumps({"ok": True, "room": stage_room(code)}, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if parsed.path == "/api/qr":
            raw = b'<svg xmlns="http://www.w3.org/2000/svg" width="180" height="180"><rect width="180" height="180" fill="white"/></svg>'
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        self.path = parsed.path
        super().do_GET()


def run():
    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=http.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:" + str(http.server_port)
    sizes = [(1366, 768), (1280, 720), (1920, 1080), (1024, 600), (390, 844)]
    screenshot_dir = ROOT / "browser-qa-artifacts"
    screenshot_dir.mkdir(exist_ok=True)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            try:
                for width, height in sizes:
                    page = browser.new_page(viewport={"width": width, "height": height})
                    try:
                        for code, scene in SCENES.items():
                            page.goto(f"{base}/stage.html?code={code}&stage=mock", wait_until="domcontentloaded")
                            expected = "results" if scene in ("teamresults", "private") else ("question" if scene == "longquestion" else scene)
                            page.wait_for_function("(status) => document.body.dataset.stageView === status", expected, timeout=8000)
                            page.wait_for_timeout(220)
                            sizes_seen = page.evaluate("""() => {
                                let wrap = document.querySelector('.stage-wrap');
                                let elements = ['.stage-head'];
                                if (document.body.dataset.stageView === 'question') elements.push('.question','.bo-stage-next-control','.live-bottom');
                                if (document.body.dataset.stageView === 'results') elements.push('.bo-result-title','.bo-result-grid','.bo-stage-next-control');
                                let rects = elements.map(sel => {
                                    let el = document.querySelector(sel), rect=el?.getBoundingClientRect();
                                    return {sel, bottom:rect?.bottom ?? -1,top:rect?.top ?? -1};
                                });
                                return {innerHeight:innerHeight, docHeight:document.documentElement.scrollHeight,
                                        bodyHeight:document.body.scrollHeight, stageScroll:wrap?.scrollHeight,
                                        stageClient:wrap?.clientHeight, rects,
                                        titleVisible:!!document.querySelector('.question h1') || document.body.dataset.stageView !== 'question',
                                        firstRankVisible:!!document.querySelector('.bo-result-row') || document.body.dataset.stageView !== 'results'};
                            }""")
                            errors = []
                            if sizes_seen["docHeight"] > height + 2 or sizes_seen["bodyHeight"] > height + 2: errors.append("whole-page overflow")
                            if sizes_seen["stageScroll"] > sizes_seen["stageClient"] + 2: errors.append("stage content overflow")
                            for rect in sizes_seen["rects"]:
                                if rect["top"] < -2 or rect["bottom"] > height + 2:
                                    errors.append(rect["sel"] + " out of viewport")
                            if not sizes_seen["titleVisible"] or not sizes_seen["firstRankVisible"]:
                                errors.append("missing key content")
                            if scene in ("results", "teamresults"):
                                visible_rank = page.locator(".bo-result-row").count()
                                if visible_rank != (2 if scene == "teamresults" else 5):
                                    errors.append(f"rank count {visible_rank}")
                            if errors:
                                page.screenshot(path=str(screenshot_dir / f"stage-v126-fail-{scene}-{width}x{height}.png"), full_page=True)
                                raise AssertionError(f"{scene} {width}x{height}: {errors}, {sizes_seen}")
                        print(f"PASS viewport {width}x{height}: lobby/question/results/team/finished/long/private")
                    finally:
                        page.close()
            finally:
                browser.close()
    finally:
        http.shutdown()
    print("PASS: projector viewport fit in 35 scenario/viewport combinations.")


if __name__ == "__main__":
    run()
