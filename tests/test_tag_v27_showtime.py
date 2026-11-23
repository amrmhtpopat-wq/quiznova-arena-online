"""TAG V27 release: safe source wiring, scoreboard, character assets and branded wake paths."""
import subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
read=lambda name:(ROOT/name).read_text(encoding='utf-8')

class ShowTimeRelease(unittest.TestCase):
 def test_projector_showtime_without_exam_leaks(self):
  html=read('stage.html')
  self.assertIn('/tag-live-showtime-v27.js?v=27.0',html)
  self.assertIn('/tag-live-showtime-v27.css?v=27.0',html)
  self.assertIn('stage.js?v=27.0',html)
  src=read('stage.js')
  self.assertIn("window.TagLiveShow?.remember(r,'stage')",src)
  self.assertIn('stageRoundSignature',src)
  self.assertIn("TagLiveShow.round(r,document.getElementById('tagV27RoundStage'),'stage')",src)
  self.assertIn("r.status==='results'&&(r.examMode||!r.showFeedback)",src)
  self.assertIn('TagLiveShow?.podiumMarkup(ranked',src)
  self.assertIn('TagLiveShow.celebrate',src)
 def test_teacher_showtime_polls_do_not_restart_animations(self):
  html=read('studio.html')
  self.assertIn('/tag-live-showtime-v27.js?v=27.0',html)
  self.assertIn('/tag-live-showtime-v27.css?v=27.0',html)
  self.assertIn('app.js?v=27.0',read('studio-auth.js'))
  src=read('app.js')
  self.assertIn("room.status==='results'&&!room.examMode&&room.showFeedback!==false",src)
  self.assertIn("TagLiveShow.round(room,roundBody.querySelector('#tagV27RoundHost'),'host'",src)
  self.assertIn('dataset.tagV27ViewKey!==roundKey',src)
  self.assertIn('dataset.tagV27ViewKey!==finalKey',src)
  self.assertIn('podiumMarkup(top',src)
  self.assertIn('renderLeaderboard(room)',src)
 def test_reveal_uses_real_server_scores_and_teacher_owned_avatar(self):
  src=read('tag-live-showtime-v27.js')
  self.assertIn("room.playType==='teams'?(room.teams||[]):(room.leaders||[])",src)
  self.assertIn('for(let index=all.length-1;index>=0;index--)',src)
  self.assertIn('Math.max(0,Math.round(Number(n)||0))',src)
  self.assertIn('window.matchMedia',src)
  self.assertIn("const cards=[3,2,1]",src)
  self.assertIn("avatarPath(p.avatar)",src)
  self.assertNotIn('localStorage',src)
  self.assertNotIn('fetch(',src)
 def test_branded_first_party_wake_routes_preserve_old_qr(self):
  subprocess.run(['python','tools/build_teachgame_unified.py'],cwd=ROOT,check=True,timeout=25,capture_output=True)
  out=ROOT/'short-link-unified'
  for slug,destination in [('teacher','/portal.html'),('student','/student.html'),('studio','/studio.html'),
                           ('tag-lab','/tag-lab-home.html'),('champion','/champion.html'),('stage','/stage.html')]:
   with self.subTest(slug=slug):
    html=(out/slug/'index.html').read_text(encoding='utf8')
    self.assertIn('TAG_ENTRY_TARGET="https://teachgame.onrender.com'+destination,html)
    self.assertIn('wake-loader.js',html)
    self.assertNotIn('فتح الصفحة مباشرة',html)
  home=(out/'index.html').read_text(encoding='utf8')
  self.assertIn('href="/tag-lab/"',home)
  self.assertIn('href="/student/"',home)
  self.assertIn('href="/teacher/"',home)
  self.assertNotIn('href="https://quiznova-arena-online.onrender.com',home)
  self.assertFalse((out/'student.html').exists())
  self.assertTrue((out/'assets/brand/tag-favicon-v24.png').is_file())
if __name__=='__main__':unittest.main()
