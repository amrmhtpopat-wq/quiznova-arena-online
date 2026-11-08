"""BOOYAHJO V12.7 SEO teachers page: real Chromium and isolated SQLite acceptance tests."""
import os
import sys
import tempfile
import threading
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
TMP=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(TMP.name)/'seo-landing.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import server

HTTP=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=HTTP.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(HTTP.server_port)
shots=ROOT/'browser-qa-artifacts'
shots.mkdir(exist_ok=True)

def get(path):
    with urllib.request.urlopen(base+path,timeout=15) as resp:
        assert resp.status==200,(path,resp.status)
        return resp.read().decode('utf8')

def assert_true(condition,description):
    if not condition:raise AssertionError(description)

class CrawlableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1=0;self.description=[];self.canonical=[];self.robots=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='h1':self.h1+=1
        if tag=='meta' and a.get('name')=='description':self.description.append(a.get('content',''))
        if tag=='meta' and a.get('name')=='robots':self.robots.append(a.get('content',''))
        if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a.get('href',''))

try:
    landing=get('/for-teachers.html')
    parser=CrawlableParser();parser.feed(landing)
    assert_true(parser.h1==1,'One semantic H1 required')
    assert_true(len(parser.description)==1 and 'اختبارات تفاعلية' in parser.description[0],
                'Unique Arabic teacher SEO description missing')
    assert_true(parser.canonical==['https://quiznova-arena-online.onrender.com/for-teachers.html'],
                'Absolute canonical broken')
    assert_true(len(parser.robots)==1 and 'index,follow' in parser.robots[0],
                'Teacher page wrongly blocked by robots')
    assert_true('application/ld+json' in landing and '"@type":"WebPage"' in landing,
                'Structured SEO metadata missing')
    assert_true('for-teachers-v127.css' in landing,'Standalone teacher landing style missing')
    sitemap=get('/sitemap.xml')
    root=ET.fromstring(sitemap)
    locs=[e.text for e in root.iter() if e.tag.endswith('loc')]
    assert_true(len(locs)==3,'Sitemap must list exactly three public pages: '+str(locs))
    assert_true('https://quiznova-arena-online.onrender.com/for-teachers.html' in locs,
                'Teacher guide absent from sitemap')
    assert_true('Disallow: /for-teachers.html' not in get('/robots.txt'),
                'Teacher guide must be crawlable')
    assert_true('/for-teachers.html' in get('/about.html'),'About page internal link missing')
    assert_true('/for-teachers.html' in get('/'),'Homepage internal link missing')
    assert_true('/for-teachers.html' in get('/visitor-tracker-v125.js'),
                'Teacher landing tracking route missing')
    assert_true(len(get('/for-teachers-v127.css'))>10000,'CSS asset empty')
    for n in ('m01','m02','m07'):
        assert_true('<svg' in get('/assets/avatars-game/'+n+'.svg'),'Mascot image unavailable: '+n)

    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True,args=['--no-sandbox'])
        for width,height in [(320,740),(360,780),(390,844),(430,932),(600,860),
                             (768,1024),(820,1180),(1024,768),(1366,820),(1920,1080)]:
            mobile=width<=600
            ctx=browser.new_context(viewport={'width':width,'height':height},
                is_mobile=mobile,has_touch=mobile)
            page=ctx.new_page()
            errors=[];failed_requests=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('response',lambda r:failed_requests.append(r.url)
                    if r.status>=400 and r.url.startswith(base) else None)
            res=page.goto(base+'/for-teachers.html',wait_until='networkidle',timeout=25000)
            assert_true(res.status==200,'Teacher landing HTTP failure')
            h1=page.locator('h1')
            assert_true(h1.count()==1 and h1.is_visible(),'Hero H1 missing at '+str(width))
            assert_true('تحدٍّ' in h1.inner_text(),'Arabic hero title missing')
            assert_true(page.locator('.feature-card').count()==6,
                        'Six real feature cards missing')
            assert_true(page.locator('.step-card').count()==3,'Three how-to steps missing')
            assert_true(page.locator('.faq-list details').count()==5,'FAQ missing')
            assert_true(page.locator('.mascots img').count()==3,'Game mascots missing')
            assert_true(page.locator('a[href="/?teacher=1"]').count()>=2,
                        'Teacher signup/login CTAs missing')
            page.locator('.faq-list summary').first.click()
            assert_true(page.locator('.faq-list details').first.get_attribute('open') is not None,
                        'FAQ expand does not work')
            page.locator('.faq-list summary').first.click()
            assert_true(page.locator('.faq-list details').first.get_attribute('open') is None,
                        'FAQ collapse does not work')
            layout=page.evaluate("""() => ({
              body:document.body.scrollWidth,
              root:document.documentElement.scrollWidth,
              width:innerWidth,
              boxes:Array.from(document.querySelectorAll('.site-header,.hero-layout,.quiz-demo,.features-grid,.steps-grid,.use-layout,.faq-layout,.closing-panel,.site-footer'))
                .map(e=>{const b=e.getBoundingClientRect();return {c:e.className,l:b.left,r:b.right,w:b.width}})
            })""")
            assert_true(layout['body']<=width+3 and layout['root']<=width+3,
                        'Horizontal overflow at '+str(width)+' '+str(layout))
            for item in layout['boxes']:
                assert_true(item['w']>0 and item['l']>=-3 and item['r']<=width+3,
                            'Main component is clipped at '+str(width)+': '+str(item))
            assert_true(not failed_requests,'Missing assets '+str(width)+': '+str(failed_requests))
            assert_true(not errors,'Browser script errors '+str(width)+': '+str(errors))
            if width in (320,390,768,1366):
                page.screenshot(path=str(shots/('teachers-seo-'+str(width)+'.png')),
                                full_page=True)
            ctx.close()
        browser.close()
    print('PASS: indexable Arabic SEO teacher page, 3-URL sitemap, links, assets, privacy-safe tracking, 10 responsive widths, FAQ and actual Chromium browser. No game UI changes.')
finally:
    HTTP.shutdown();HTTP.server_close();TMP.cleanup()
