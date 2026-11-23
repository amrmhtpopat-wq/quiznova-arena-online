"""TAG PWA V1: isolated installability, icon, MIME and offline privacy contract tests."""
import json
import os
import struct
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
temp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(temp.name)/'tag-pwa-qa.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import server

http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(http.server_port)


def get(path):
    req=urllib.request.Request(BASE+path)
    try:
        with urllib.request.urlopen(req,timeout=12) as resp:
            return resp.status,resp.headers,resp.read()
    except urllib.error.HTTPError as e:
        return e.code,e.headers,e.read()


class PWASafeInstallContract(unittest.TestCase):
    def test_manifest_correct_mime_scope_and_entry(self):
        status,headers,data=get('/manifest.webmanifest')
        self.assertEqual(status,200)
        self.assertIn('application/manifest+json',headers['Content-Type'])
        self.assertIn('no-cache',headers['Cache-Control'])
        m=json.loads(data)
        self.assertEqual(m['short_name'],'TAG')
        self.assertEqual(m['id'],'/app.html')
        self.assertEqual(m['start_url'],'/app/')
        self.assertEqual(m['scope'],'/')
        self.assertEqual(m['display'],'standalone')
        self.assertFalse(m.get('prefer_related_applications',False))
        self.assertIn('ar',m['lang'])
        self.assertEqual(len(m['shortcuts']),2)
        self.assertEqual({shortcut['short_name'] for shortcut in m['shortcuts']},{'الطالب','المعلم'})
        self.assertEqual({shortcut['url'] for shortcut in m['shortcuts']},{'/student/','/teacher/'})
        self.assertNotIn('TAG LAB',[shortcut['name'] for shortcut in m['shortcuts']])

    def test_real_pngs_are_square_not_svg_renamed(self):
        manifest=json.loads(get('/manifest.webmanifest')[2])
        icons=[x for x in manifest['icons'] if x['type']=='image/png']
        self.assertGreaterEqual(len(icons),3)
        for item in icons:
            with self.subTest(src=item['src']):
                status,headers,png=get(item['src'])
                self.assertEqual(status,200)
                self.assertIn('image/png',headers['Content-Type'])
                self.assertEqual(png[:8],bytes([137,80,78,71,13,10,26,10]))
                self.assertEqual(png[12:16],b'IHDR')
                width,height=struct.unpack('>II',png[16:24])
                expected=int(item['sizes'].split('x')[0])
                self.assertEqual((width,height),(expected,expected))
                self.assertGreater(len(png),700)
        status,_,apple=get('/assets/pwa/tag-apple-180.png')
        self.assertEqual(status,200)
        self.assertEqual(struct.unpack('>II',apple[16:24]),(180,180))

    def test_install_files_available_and_no_personal_information_cached(self):
        for path in ('/app.html','/pwa-offline.html','/sw.js','/tag-pwa-v1.js'):
            with self.subTest(path=path):
                status,_,content=get(path)
                self.assertEqual(status,200)
                self.assertTrue(content)
        status,headers,data=get('/sw.js')
        self.assertIn('no-cache',headers['Cache-Control'])
        worker=data.decode('utf-8')
        self.assertIn("req.mode!=='navigate'",worker)
        self.assertIn("url.pathname.startsWith('/api/')",worker)
        self.assertIn("event.respondWith(fetch(req).catch(",worker)
        self.assertIn('PUBLIC_ASSETS',worker)
        self.assertNotIn('cache.put(req',worker)
        self.assertNotIn("cache.add('/student.html')",worker)
        self.assertNotIn('skipWaiting()',worker)

    def test_important_portals_link_manifest_but_maintain_card_and_pin(self):
        for path in ('/','/student.html','/studio.html','/tag-lab-home.html',
                     '/champion.html','/game-lab-play.html','/game-lab-live.html'):
            status,_,page=get(path)
            with self.subTest(path=path):
                self.assertEqual(status,200)
                self.assertIn(b'\"/manifest.webmanifest\"',page)
                self.assertIn(b'/tag-pwa-v1.js',page)
        student=get('/student.html')[2].decode('utf-8')
        self.assertIn('id="liveStudentPin"',student)
        self.assertIn('id="soloPinCode"',student)
        self.assertIn('id="cardCode"',student)
        portal=get('/')[2].decode('utf-8')
        self.assertIn('id="studentVerifyPanel"',portal)
        self.assertIn('/tag-lab-home.html',portal)
        self.assertNotIn('الحصة التفاعلية وخلط الألعاب',portal)
        self.assertIn('href="/app.html"',portal)

    def test_private_files_and_api_do_not_become_static_assets(self):
        for path in ('/platform_store.py','/.env','/data/students.db'):
            with self.subTest(path=path):
                status,_,_=get(path)
                self.assertEqual(status,404)
        status,headers,_=get('/api/card/profile?card=NOT-A-STUDENT')
        self.assertEqual(status,404)
        self.assertIn('no-store',headers['Cache-Control'])


if __name__=='__main__':
    unittest.main()
