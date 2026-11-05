import os, tempfile, unittest, uuid
from pathlib import Path

tmp=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(tmp.name)/'unit-tests.sqlite')
import platform_store as store
store.init()
import platform_security as sec

class QuizNovaSecurityTests(unittest.TestCase):
    def setUp(self):
        name=uuid.uuid4().hex[:10]
        self.email=name+'@school.example'
        self.password='TeacherPass#123'
        account=store.create_teacher(self.email,self.password,'Example Teacher','مدرسة بنين','المهارات الرقمية','boys')
        self.teacher=account['teacher']['id']
        self.token=account['token']

    def test_authentication_and_school_avatar_policy(self):
        self.assertEqual(store.teacher_for_token(self.token)['id'],self.teacher)
        self.assertEqual(len(store.avatar_pool('boys')),32)
        self.assertEqual(len(store.avatar_pool('girls')),16)
        self.assertEqual(len(store.avatar_pool('mixed')),48)

    def test_optimistic_sync(self):
        self.assertEqual(sec.snapshot_with_revision(self.teacher)['revision'],0)
        result=sec.save_patch(self.teacher,{'quizzes':[{'title':'one'}]},0)
        self.assertEqual(result['revision'],1)
        with self.assertRaisesRegex(ValueError,'revision_conflict'):
            sec.save_patch(self.teacher,{'quizzes':[]},0)
        self.assertEqual(len(sec.snapshot_with_revision(self.teacher)['data']['quizzes']),1)

    def test_backups_restore_and_recovery_point(self):
        sec.save_patch(self.teacher,{'bank':[{'question':'example'}]},0)
        safe=sec.create_backup(self.teacher)
        sec.save_patch(self.teacher,{'bank':[]},1)
        with self.assertRaisesRegex(ValueError,'wrong_credentials'):
            sec.restore_backup(self.teacher,safe['id'],'wrong')
        done=sec.restore_backup(self.teacher,safe['id'],self.password)
        self.assertTrue(done['recovery_backup_id'])
        self.assertEqual(len(sec.snapshot_with_revision(self.teacher)['data']['bank']),1)

    def test_tenant_isolation(self):
        b=sec.create_backup(self.teacher)
        other=store.create_teacher(uuid.uuid4().hex+'@school.example','TeacherPass#123','Second','مدرسة مختلطة','رياضيات','mixed')['teacher']['id']
        self.assertEqual(sec.list_backups(other),[])
        with self.assertRaisesRegex(ValueError,'backup_not_found'):
            sec.download_backup(other,b['id'])

    def test_change_password_expires_old_sessions(self):
        sec.change_password(self.teacher,self.password,'NewPass#123456')
        self.assertIsNone(store.teacher_for_token(self.token))
        self.assertEqual(store.login(self.email,'NewPass#123456')['teacher']['id'],self.teacher)

    def test_password_reset_requires_configured_mail(self):
        for v in ('SMTP_HOST','SMTP_USER','SMTP_PASSWORD','SMTP_FROM'):
            os.environ.pop(v,None)
        with self.assertRaisesRegex(ValueError,'email_not_configured'):
            sec.request_password_reset(self.email)

if __name__=='__main__':
    unittest.main()
