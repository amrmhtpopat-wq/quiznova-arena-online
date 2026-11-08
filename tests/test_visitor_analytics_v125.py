"""BOOYAHJO visitor counter V12.5: real HTTP, SQLite/Neon-compatible upserts and owner-only read."""
import hashlib
import json
import os
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

from cryptography.fernet import Fernet

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
TEMP=tempfile.TemporaryDirectory()
os.environ.pop('DATABASE_URL',None)
os.environ['QUIZNOVA_SQLITE_PATH']=str(Path(TEMP.name)/'visitors.sqlite')
os.environ['QUIZNOVA_CLOUD']='1'
os.environ['QUIZNOVA_ALLOW_EPHEMERAL']='yes'
os.environ['BOOYAH_ADMIN_SETUP_KEY']='isolated-test-visitors-owner-setup-super-long'
os.environ['BOOYAH_ADMIN_TOTP_KEY']=Fernet.generate_key().decode('ascii')
import server
import platform_store as store
import visitor_analytics as visitor
import admin_api

HTTP=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
threading.Thread(target=HTTP.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:'+str(HTTP.server_port)
JAR=CookieJar()
CLIENT=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(JAR))

def request(path,payload=None,headers=None):
    req=urllib.request.Request(BASE+path,
        data=json.dumps(payload).encode('utf8') if payload is not None else None,
        headers={'Content-Type':'application/json','X-BOOYAH-Admin':'1',**(headers or {})})
    try:
        with CLIENT.open(req,timeout=15) as r:return r.status,json.load(r)
    except urllib.error.HTTPError as err:return err.code,json.load(err)

class VisitorCounterTests(unittest.TestCase):
    def test_01_visitor_total_day_sessions_and_pageviews(self):
        self.assertEqual(visitor.summary()['total'],0)
        first='a'*32; second='b'*32
        for identifier,page in [(first,'home'),(first,'student'),(second,'home')]:
            status,response=request('/api/visitors/track',{'id':identifier,'page':page})
            self.assertEqual((status,response['ok']),(200,True))
        stats=visitor.summary()
        self.assertEqual([stats[k] for k in ('total','today','last7Days','visits','pageviews')],
                         [2,2,2,2,3],stats)
        self.assertEqual(stats['timezone'],'Asia/Amman')
        self.assertIsNotNone(stats['since'])
        digest=hashlib.sha256(('booyahjo-anonymous-v1:'+first).encode()).hexdigest()
        self.assertNotEqual(digest,first)
        raw=store.query('SELECT * FROM site_visitors WHERE visitor_hash=?',(digest,))
        self.assertEqual(raw['pageviews'],2)
        store.exec_sql('UPDATE site_visitors SET last_seen=? WHERE visitor_hash=?',
                       (int(time.time())-visitor.SESSION_SECONDS-10,digest))
        day=visitor._day(int(time.time()))
        store.exec_sql('UPDATE site_visit_days SET last_seen=? WHERE visitor_hash=? AND day_amman=?',
                       (int(time.time())-visitor.SESSION_SECONDS-10,digest,day))
        status,response=request('/api/visitors/track',{'id':first,'page':'studio'})
        self.assertEqual(status,200,response)
        stats=visitor.summary()
        self.assertEqual([stats[k] for k in ('total','today','visits','pageviews')],[2,2,3,4])
        # No stored address, student or teacher identity.
        columns=set(raw)
        self.assertEqual(columns,{'visitor_hash','first_seen','last_seen','visits','pageviews'})

    def test_02_reject_invalid_and_cross_site_and_keep_totals_unchanged(self):
        original=visitor.summary()
        attempts=[
            ({'id':'not-a-real-id','page':'home'},None,400),
            ({'id':'b'*32,'page':'admin'},None,400),
            ({'id':'c'*32,'page':'home'},{'Origin':'https://evil.example'},403),
            ({'id':'c'*32,'page':'home'},{'Sec-Fetch-Site':'cross-site'},403)
        ]
        for payload,headers,expected in attempts:
            status,response=request('/api/visitors/track',payload,headers)
            self.assertEqual(status,expected,response)
        self.assertEqual(visitor.summary(),original)
        status,response=request('/api/admin/summary')
        self.assertEqual(status,401,response)

    def test_03_owner_authenticated_summary_and_no_public_read(self):
        status,created=request('/api/admin/setup',{
            'setupKey':os.environ['BOOYAH_ADMIN_SETUP_KEY'],
            'name':'مدير الزيارات','email':'owner-visitors@example.org',
            'password':'OwnerVisitorTestingPassword2026!'})
        self.assertEqual(status,200,created)
        secret=created['secret']
        status,ready=request('/api/admin/activate',{
            'setupKey':os.environ['BOOYAH_ADMIN_SETUP_KEY'],
            'email':'owner-visitors@example.org','otp':admin_api.totp(secret)})
        self.assertEqual(status,200,ready)
        status,logged=request('/api/admin/login',{
            'email':'owner-visitors@example.org',
            'password':'OwnerVisitorTestingPassword2026!','otp':admin_api.totp(secret)})
        self.assertEqual(status,200,logged)
        status,result=request('/api/admin/summary')
        self.assertEqual(status,200,result)
        self.assertEqual(result['summary']['visitors']['total'],2)
        self.assertEqual(result['summary']['visitors']['visits'],3)
        self.assertEqual(result['summary']['visitors']['pageviews'],4)
        self.assertNotIn('visitor_hash',json.dumps(result))
        self.assertNotIn('owner-visitors@example.org',json.dumps(result))
        # Counts remain across independent calls, not lost after a request.
        self.assertEqual(visitor.summary()['total'],2)

if __name__=='__main__':
    try:unittest.main()
    finally:HTTP.shutdown();HTTP.server_close()
