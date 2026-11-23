"""Build the public TAG static gateway for one-origin routing on Render.

Render's static site serves existing files before applying rewrite rules.
Only retain the static landing, branding, SEO and cold-start *directory*
handoffs; HTML pages at the root are served via backend proxy instead.
Neither the dynamic server, database, student QR/PIN, nor auth is modified.
"""
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
import re, shutil

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'short-link'
OUT=ROOT/'short-link-unified'
PUBLIC='https://teachgame.onrender.com'
LEGACY='https://quiznova-arena-online.onrender.com'
if not (SRC/'index.html').is_file(): raise SystemExit('missing static landing')
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(SRC,OUT)
# Preserve / as fast, indexable static landing. Remove any collision with a
# real backend HTML page, which must be served via Render rewrites instead.
for p in OUT.glob('*.html'):
    if p.name!='index.html':
        p.unlink()
def first_party(url):
    if not url.startswith(LEGACY):return url
    parsed=urlsplit(url)
    path=parsed.path
    if path in ('','/','/index.html'):
        path='/portal.html'
    return urlunsplit(('https','teachgame.onrender.com',path,parsed.query,parsed.fragment))
# Cold-start entry pages still work and ping the existing backend while Render
# boots, but navigate to the public origin (and never reveal the old host).
for p in OUT.rglob('index.html'):
    if p.parent==OUT:continue
    html=p.read_text(encoding='utf8')
    html=re.sub(r'window\.TAG_ENTRY_TARGET="([^"]+)"',
        lambda m:'window.TAG_ENTRY_TARGET="'+first_party(m.group(1))+'"',html)
    # Existing noscript fallback must also stay under public origin.
    html=re.sub(r'(<meta http-equiv="refresh" content="0;url=)([^"]+)',
        lambda m:m.group(1)+first_party(m.group(2)),html)
    html=html.replace(LEGACY,PUBLIC)
    p.write_text(html,encoding='utf8')
# The indexable root is kept as a branded landing instead of redirecting to
# a server that might be asleep. First-party links target the proxied routes.
home=OUT/'index.html'
s=home.read_text(encoding='utf8')
s=s.replace('https://quiznova-arena-online.onrender.com/student.html','https://teachgame.onrender.com/student.html')
s=s.replace('https://quiznova-arena-online.onrender.com/','https://teachgame.onrender.com/portal.html')
home.write_text(s,encoding='utf8')
# Backend probe remains on legacy backend, which is a health-check upstream
# (not user navigation). The validated destination is now first-party.
loader=OUT/'wake-loader.js'
if loader.exists():
    s=loader.read_text(encoding='utf8')
    old='const base="https://quiznova-arena-online.onrender.com";'
    assert old in s,'wake loader contract changed'
    s=s.replace(old,old+'\n const publicBase="https://teachgame.onrender.com";')
    s=s.replace('!target.startsWith(base+"/")','!target.startsWith(publicBase+"/")')
    loader.write_text(s,encoding='utf8')
print('TAG unified static gateway prepared:',OUT)
