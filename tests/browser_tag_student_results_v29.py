"""TAG V29 regression: the teacher/projector owns standings; the student sees only their own result."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'student.js').read_text(encoding='utf-8')
a=source.index('function showRoundLeaderboard(r){')
b=source.index('\nsetCodeFromUrl();',a)
student_functions=source[a:b]
assert 'r.leaders' not in student_functions, 'Student screens must not read class rankings.'
assert '<div class="leaderboard">' not in student_functions, 'No public standing board on a student device.'
assert 'tag28-person-body' not in (ROOT/'tag-stage-worldcup-v28.js').read_text(encoding='utf-8')

with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
 page=browser.new_page()
 errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content('<!doctype html><html lang="ar" dir="rtl"><body><div id="gameView"></div></body></html>')
 prelude="""const session={name:'محمد',avatar:'b07',team:'',model:'',lastResultView:-1,timer:0,poll:0};
 const $=s=>document.querySelector(s);
 const esc=v=>String(v??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
 const teamRosterHtml=()=>'';const avatarPath=id=>'/assets/avatars3d/'+id+'.webp';
 const confetti=()=>{};"""
 page.add_script_tag(content=prelude+student_functions)
 common={'playerScore':2220,'leaders':[{'name':'أحمد','score':2450},{'name':'محمد','score':2220},{'name':'عمر','score':1980}],
         'examMode':False,'showFeedback':True,'index':2}
 page.evaluate('r=>showRoundLeaderboard(r)',common)
 assert page.locator('.round-score').is_visible()
 assert page.locator('.leaderboard,.leader,.rank').count()==0
 assert 'أحمد' not in page.locator('#gameView').inner_text()
 assert 'المركز' not in page.locator('#gameView').inner_text()
 finish={**common,'xpGain':60,'xp':160,'level':2,
         'xpBreakdown':{'total':60,'correct':30,'fastest':10,'completion':10,'firstPlace':10},
         'progress':{'title':'متمكن','percent':35,'xpToNext':140}}
 page.evaluate('r=>showFinish(r)',finish)
 assert page.locator('.finish-card').is_visible()
 assert page.locator('.finish-original-avatar img').get_attribute('src')=='/assets/avatars3d/b07.webp'
 assert page.locator('.leaderboard,.leader,.rank,.v104-student-medal').count()==0
 assert 'أحمد' not in page.locator('#gameView').inner_text()
 assert 'المركز الأول' not in page.locator('#gameView').inner_text()
 assert '2220' in page.locator('#gameView').inner_text()
 assert not errors,errors
 print('PASS TAG V29 student: original avatar, private personal scores/XP, no live or final ranking')
 page.close()
 browser.close()
