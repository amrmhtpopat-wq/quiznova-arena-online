"""TAG student: server-verified speed champion and feedback secrecy."""
import unittest
import sys
import tempfile,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
temp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(temp.name)/'tag-feedback-check.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
import server

class SpeedChampion(unittest.TestCase):
 def room(self, first=1900, second=2700, same_question=True):
  return {'players':{
   'a':{'id':'a','answers':{'0':{'correct':True,'elapsedMs':first,'questionIndex':0}}},
   'b':{'id':'b','answers':{'0':{'correct':True,'elapsedMs':second,'questionIndex':0 if same_question else 2}}}
  }}
 def test_fastest_real_server_time(self):
  r=self.room()
  self.assertTrue(server.round_speed_champion(r,0,'a'))
  self.assertFalse(server.round_speed_champion(r,0,'b'))
 def test_tied_answers_are_not_claimed_as_winners(self):
  r=self.room(1000,1000)
  self.assertFalse(server.round_speed_champion(r,0,'a'))
  self.assertFalse(server.round_speed_champion(r,0,'b'))
 def test_single_student_or_different_question_is_not_crowned(self):
  r=self.room(same_question=False)
  self.assertFalse(server.round_speed_champion(r,0,'a'))
  del r['players']['b']
  self.assertFalse(server.round_speed_champion(r,0,'a'))
 def test_only_correct_answers_qualify(self):
  r=self.room()
  r['players']['a']['answers']['0']['correct']=False
  self.assertFalse(server.round_speed_champion(r,0,'a'))
  self.assertFalse(server.round_speed_champion(r,0,'b'))
 def test_hidden_feedback_must_not_disclose_speed(self):
  s=(ROOT/'server.py').read_text(encoding='utf-8')
  self.assertIn("room['status']=='results' and room.get('showFeedback',True) and not room.get('examMode')",s)
  js=(ROOT/'student.js').read_text(encoding='utf-8')
  self.assertIn('r.speedChampion&&r.showFeedback',js)
  self.assertIn('reveal&&res?.correct===true',js)
  self.assertIn('examMode?',js)
  solo=(ROOT/'solo-student-v120.js').read_text(encoding='utf-8')
  self.assertIn('tag-solo-celebrate',solo)
if __name__=='__main__':unittest.main()
