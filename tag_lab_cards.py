"""TAG INDEPENDENT V1 — LAB-local student roster and game assignment.

No official teacher/student records or raw QR tokens are copied.
The only permitted cross-platform operation is card verification, by a private
server-to-server client. PINs are six randomly generated digits, slow-hashed.
This feature is enabled exclusively on a dedicated LAB-only service.
"""
from __future__ import annotations
import hashlib
import hmac
import re
import secrets
import time
import uuid
from urllib.parse import parse_qs
import platform_store as db
import platform_api as auth
import game_lab_api as games
import solo_api
import tag_card_client as bridge
import tag_independent_mode as mode

TEACHER_GET = {"/api/tag-independent/teacher/cards",
               "/api/tag-independent/teacher/assignments"}
TEACHER_POST = {"/api/tag-independent/teacher/cards/enroll",
                "/api/tag-independent/teacher/cards/update",
                "/api/tag-independent/teacher/cards/reset-pin",
                "/api/tag-independent/teacher/assign"}
STUDENT_POST = {"/api/tag-independent/student/login",
                "/api/tag-independent/student/catalog",
                "/api/tag-independent/student/logout"}
PIN_RE = re.compile(r"^[0-9]{6}$")
TOKEN_RE = re.compile(r"^[A-Za-z0-9_\-]{30,150}$")
MAX_STUDENTS_PER_TEACHER = 600
SESSION_TTL = 45 * 60
ACTIVE_RUN_TTL = 60 * 60

def now():
    return int(time.time())

def err(h, code, status=400):
    h.send_json({"ok":False,"error":code},status)
    return True

def text(value, maximum):
    return str(value or "").strip()[:maximum]

def phash(value):
    return hashlib.sha256(value.encode("ascii")).hexdigest()

def pin_hash(pin, salt_hex):
    return hashlib.pbkdf2_hmac("sha256",pin.encode("ascii"),
                              bytes.fromhex(salt_hex),210_000).hex()

def new_pin():
    return f"{secrets.randbelow(1_000_000):06d}"

def new_pin_pair():
    pin = new_pin()
    salt = secrets.token_hex(16)
    return pin, salt, pin_hash(pin,salt)

def check_pin(pin, row):
    if not isinstance(pin,str) or not PIN_RE.fullmatch(pin):
        return False
    return hmac.compare_digest(pin_hash(pin,row["pin_salt"]),
                               row["pin_digest"])

def init():
    if not mode.enabled():
        return
    for statement in (
      "CREATE TABLE IF NOT EXISTS tag_lab_card_roster ("
      "id TEXT PRIMARY KEY,teacher_id TEXT NOT NULL,card_ref TEXT NOT NULL UNIQUE,"
      "label TEXT NOT NULL,class_name TEXT NOT NULL,pin_salt TEXT NOT NULL,"
      "pin_digest TEXT NOT NULL,created_at BIGINT NOT NULL)",
      "CREATE INDEX IF NOT EXISTS ix_taglab_card_teacher "
      "ON tag_lab_card_roster(teacher_id,class_name)",
      "CREATE TABLE IF NOT EXISTS tag_lab_card_assignments ("
      "id TEXT PRIMARY KEY,teacher_id TEXT NOT NULL,activity_id TEXT NOT NULL,"
      "target_type TEXT NOT NULL,target_value TEXT NOT NULL,created_at BIGINT NOT NULL)",
      "CREATE UNIQUE INDEX IF NOT EXISTS ix_taglab_card_assignment_unique "
      "ON tag_lab_card_assignments(teacher_id,activity_id,target_type,target_value)",
      "CREATE TABLE IF NOT EXISTS tag_lab_card_sessions ("
      "token_hash TEXT PRIMARY KEY,roster_id TEXT NOT NULL UNIQUE,expires_at BIGINT NOT NULL)",
    ):
        db.exec_sql(statement)

def roster_row(tid, rid):
    return db.query("SELECT id,teacher_id,label,class_name,card_ref,pin_salt,pin_digest "
                    "FROM tag_lab_card_roster WHERE id=? AND teacher_id=?",(rid,tid))

def public_card(row):
    return {"id":row["id"],"label":row["label"],"className":row["class_name"]}

def cards(tid):
    records=db.query("SELECT id,label,class_name FROM tag_lab_card_roster "
                     "WHERE teacher_id=? ORDER BY class_name,label",(tid,),True)
    return [public_card(r) for r in records]

def enroll(tid,data):
    card=data.get("card")
    if not isinstance(card,str) or not card.strip() or len(card)>150:
        raise ValueError("invalid_card")
    label=text(data.get("label"),70)
    group=text(data.get("className"),70)
    if len(label)<2 or not group:
        raise ValueError("label_and_class_required")
    # Verification happens before DB write. No raw card or QR URL is stored.
    ref=bridge.verify(card)
    pin,salt,digest=new_pin_pair()
    rid=uuid.uuid4().hex
    timestamp=now()
    with db.DB_LOCK:
        with db.db_connection() as con:
            cur=con.cursor()
            cur.execute(db.sql("SELECT id FROM tag_lab_card_roster WHERE card_ref=?"),(ref,))
            if cur.fetchone():
                raise ValueError("card_already_enrolled")
            cur.execute(db.sql("SELECT COUNT(*) FROM tag_lab_card_roster WHERE teacher_id=?"),(tid,))
            if int(cur.fetchone()[0])>=MAX_STUDENTS_PER_TEACHER:
                raise ValueError("card_limit_reached")
            cur.execute(db.sql("INSERT INTO tag_lab_card_roster "
                 "(id,teacher_id,card_ref,label,class_name,pin_salt,pin_digest,created_at) "
                 "VALUES(?,?,?,?,?,?,?,?)"),
                 (rid,tid,ref,label,group,salt,digest,timestamp))
    return {"card":{"id":rid,"label":label,"className":group},
            "pin":pin,"pinShownOnce":True}

def update_card(tid,data):
    rid=text(data.get("id"),50)
    row=roster_row(tid,rid)
    if not row: raise ValueError("card_not_found")
    label=text(data.get("label"),70)
    group=text(data.get("className"),70)
    if len(label)<2 or not group:
        raise ValueError("label_and_class_required")
    with db.DB_LOCK:
        db.exec_sql("UPDATE tag_lab_card_roster SET label=?,class_name=? WHERE id=? "
                    "AND teacher_id=?",(label,group,rid,tid))
    return {"card":{"id":rid,"label":label,"className":group}}

def reset_pin(tid,data):
    rid=text(data.get("id"),50)
    if not roster_row(tid,rid):raise ValueError("card_not_found")
    pin,salt,digest=new_pin_pair()
    with db.DB_LOCK:
        with db.db_connection() as con:
            cur=con.cursor()
            cur.execute(db.sql("UPDATE tag_lab_card_roster SET pin_salt=?,pin_digest=? "
                               "WHERE id=? AND teacher_id=?"),(salt,digest,rid,tid))
            cur.execute(db.sql("DELETE FROM tag_lab_card_sessions WHERE roster_id=?"),(rid,))
    return {"pin":pin,"pinShownOnce":True}

def assignments(tid,aid):
    if not games.owner_row(tid,aid):
        raise ValueError("activity_not_found")
    rows=db.query("SELECT target_type,target_value FROM tag_lab_card_assignments "
                  "WHERE activity_id=? AND teacher_id=? ORDER BY created_at DESC",
                  (aid,tid),True)
    return [{"type":r["target_type"],"value":r["target_value"]} for r in rows]

def assign(tid,data):
    aid=text(data.get("activityId"),60)
    activity=games.owner_row(tid,aid)
    if not activity:raise ValueError("activity_not_found")
    if not activity["published"]:raise ValueError("publish_first")
    targets=data.get("targets")
    if not isinstance(targets,list) or len(targets)>80:
        raise ValueError("invalid_targets")
    members=cards(tid)
    student_ids={r["id"] for r in members}
    classes={r["className"] for r in members}
    accepted=set()
    for t in targets:
        if not isinstance(t,dict):raise ValueError("invalid_targets")
        typ=text(t.get("type"),12)
        val=text(t.get("value"),75)
        if typ=="all":
            val="*"
        elif typ=="class":
            if val not in classes:raise ValueError("class_not_found")
        elif typ=="student":
            if val not in student_ids:raise ValueError("student_not_found")
        else:
            raise ValueError("invalid_target_type")
        accepted.add((typ,val))
    with db.DB_LOCK:
        with db.db_connection() as con:
            cur=con.cursor()
            cur.execute(db.sql("DELETE FROM tag_lab_card_assignments "
                               "WHERE activity_id=? AND teacher_id=?"),(aid,tid))
            for typ,val in accepted:
                cur.execute(db.sql("INSERT INTO tag_lab_card_assignments "
                    "(id,teacher_id,activity_id,target_type,target_value,created_at) "
                    "VALUES(?,?,?,?,?,?)"),(uuid.uuid4().hex,tid,aid,typ,val,now()))
    return {"activityId":aid,"targets":[{"type":t,"value":v} for t,v in sorted(accepted)]}

def session(token):
    if not isinstance(token,str) or not TOKEN_RE.fullmatch(token):
        return None
    record=db.query(
       "SELECT s.token_hash,s.roster_id,s.expires_at,r.teacher_id,r.label,"
       "r.class_name FROM tag_lab_card_sessions s JOIN tag_lab_card_roster r "
       "ON r.id=s.roster_id WHERE s.token_hash=?",(phash(token),))
    return record if record and int(record["expires_at"])>now() else None

def catalog(row):
    tid=row["teacher_id"]
    rid=row["roster_id"] if "roster_id" in row else row["id"]
    group=row["class_name"]
    items=db.query(
        "SELECT a.id,a.title,a.subject,a.grade,a.mode,a.public_code,a.payload,"
        "a.max_attempts FROM game_lab_activities a "
        "JOIN tag_lab_card_assignments x ON x.activity_id=a.id "
        "AND x.teacher_id=a.teacher_id WHERE a.teacher_id=? AND "
        "a.published=1 AND a.archived=0 AND "
        "(x.target_type='all' OR (x.target_type='class' AND x.target_value=?) "
        "OR (x.target_type='student' AND x.target_value=?)) "
        "GROUP BY a.id ORDER BY a.updated_at DESC LIMIT 100",
        (tid,group,rid),True)
    count=db.query("SELECT activity_id,COUNT(*) AS n FROM game_lab_runs "
                   "WHERE teacher_id=? AND student_id=? GROUP BY activity_id",
                   (tid,rid),True)
    used={r["activity_id"]:int(r["n"]) for r in count}
    result=[]
    for a in items:
        item=games.participant_view(a)
        item.update({"id":a["id"],"code":a["public_code"],
                     "attemptsUsed":used.get(a["id"],0),
                     "remaining":max(0,int(a["max_attempts"])-used.get(a["id"],0))})
        result.append(item)
    return result

def card_login(h,data):
    card=data.get("card")
    pin=data.get("pin")
    if not isinstance(card,str) or len(card)>150 or not PIN_RE.fullmatch(str(pin or "")):
        return err(h,"invalid_credentials",403)
    if solo_api.limited(h,card.strip() or "card_login"):
        return err(h,"rate_limited",429)
    try:
        ref=bridge.verify(card)
    except bridge.CardNotFound:
        return err(h,"invalid_credentials",403)
    except bridge.CardBridgeUnavailable:
        return err(h,"card_bridge_unavailable",503)
    row=db.query("SELECT * FROM tag_lab_card_roster WHERE card_ref=?",(ref,))
    if not row or not check_pin(pin,row):
        return err(h,"invalid_credentials",403)
    token=secrets.token_urlsafe(36)
    with db.DB_LOCK:
        with db.db_connection() as con:
            cur=con.cursor()
            if db.DATABASE_URL:
                cur.execute(db.sql("SELECT id FROM tag_lab_card_roster WHERE id=? FOR UPDATE"),(row["id"],))
            cur.execute(db.sql("SELECT expires_at FROM tag_lab_card_sessions WHERE roster_id=?"),(row["id"],))
            old=cur.fetchone()
            if old and int(old[0])>now():
                return err(h,"session_already_active",409)
            if old:
                cur.execute(db.sql("DELETE FROM tag_lab_card_sessions WHERE roster_id=?"),(row["id"],))
            cur.execute(db.sql("INSERT INTO tag_lab_card_sessions "
                               "(token_hash,roster_id,expires_at) VALUES(?,?,?)"),
                        (phash(token),row["id"],now()+SESSION_TTL))
    profile={"roster_id":row["id"],"teacher_id":row["teacher_id"],
             "class_name":row["class_name"],"label":row["label"]}
    h.send_json({"ok":True,"session":token,"expiresIn":SESSION_TTL,
                 "student":{"label":row["label"],"className":row["class_name"]},
                 "activities":catalog(profile)})
    return True

def student_catalog(h,data):
    row=session(data.get("session"))
    if not row:return err(h,"invalid_session",403)
    h.send_json({"ok":True,"student":{"label":row["label"],"className":row["class_name"]},
                 "activities":catalog(row)})
    return True

def student_logout(h,data):
    token=data.get("session")
    if not session(token):return err(h,"invalid_session",403)
    db.exec_sql("DELETE FROM tag_lab_card_sessions WHERE token_hash=?",(phash(token),))
    h.send_json({"ok":True})
    return True

def start_game(a,data,h):
    """Authenticated LAB card game start; no official students/XP writes."""
    row=session(data.get("cardSession"))
    if not row:return err(h,"card_session_required",403)
    if row["teacher_id"]!=a["teacher_id"]:
        return err(h,"not_assigned_to_card",403)
    aid=a["id"];rid=row["roster_id"];tid=row["teacher_id"]
    payload=db.jload(a["payload"],{})
    questions=payload.get("rows",[])
    if not questions:return err(h,"empty_activity",409)
    token=secrets.token_urlsafe(36)
    key=games.hashed(token)
    with db.DB_LOCK:
        with db.db_connection() as con:
            cur=con.cursor()
            if db.DATABASE_URL:
                cur.execute(db.sql("SELECT id FROM tag_lab_card_roster WHERE id=? FOR UPDATE"),(rid,))
                if not cur.fetchone():return err(h,"invalid_card",403)
            cur.execute(db.sql(
                "SELECT 1 FROM tag_lab_card_assignments WHERE teacher_id=? AND activity_id=? "
                "AND (target_type='all' OR (target_type='class' AND target_value=?) "
                "OR (target_type='student' AND target_value=?)) LIMIT 1"),
                (tid,aid,row["class_name"],rid))
            if not cur.fetchone():return err(h,"not_assigned_to_card",403)
            cur.execute(db.sql("SELECT COUNT(*) FROM game_lab_runs "
                               "WHERE activity_id=? AND teacher_id=? AND student_id=?"),
                        (aid,tid,rid))
            if int(cur.fetchone()[0])>=int(a["max_attempts"]):
                return err(h,"attempt_limit",403)
            cur.execute(db.sql("SELECT 1 FROM game_lab_runs WHERE student_id=? AND "
                               "teacher_id=? AND finished_at=0 AND updated_at>? LIMIT 1"),
                        (rid,tid,now()-ACTIVE_RUN_TTL))
            if cur.fetchone():return err(h,"another_attempt_active",409)
            state={"rows":questions,"title":a["title"],"mode":a["mode"],
                   "duration":payload.get("time",25),"index":0,"score":0,
                   "correct":0,"finished":False,"xpGain":0,"guest":False,
                   "studentName":row["label"],"className":row["class_name"],
                   "sourceGroup":payload.get("sourceGroup") or aid,
                   "imageUrl":("/api/game-lab/pro/image?id="+str(payload.get("imageId"))+
                     "&code="+str(a["public_code"])) if payload.get("imageId") else ""}
            timestamp=now()
            cur.execute(db.sql("INSERT INTO game_lab_runs "
              "(token_hash,activity_id,teacher_id,student_id,student_name,class_name,"
              "state,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)"),
              (key,aid,tid,rid,row["label"],row["class_name"],db.jdump(state),
               timestamp,timestamp))
    h.send_json({"ok":True,"token":token,"state":games.state_view(state,key)})
    return True

def handle_get(h,url):
    if not mode.enabled() or url.path not in TEACHER_GET:return False
    t=auth.authorized(h)
    if not t:return True
    tid=t["id"]
    try:
        if url.path.endswith("/cards"):
            h.send_json({"ok":True,"cards":cards(tid)})
        else:
            aid=(parse_qs(url.query).get("activityId") or [""])[0]
            h.send_json({"ok":True,"targets":assignments(tid,aid)})
    except ValueError as exc:return err(h,str(exc),400)
    return True

def handle_post(h,url,data):
    if not mode.enabled():return False
    path=url.path
    if path not in TEACHER_POST and path not in STUDENT_POST:return False
    if not isinstance(data,dict):return err(h,"invalid_request")
    if path in STUDENT_POST:
        if path.endswith("/login"):return card_login(h,data)
        if path.endswith("/catalog"):return student_catalog(h,data)
        return student_logout(h,data)
    t=auth.authorized(h)
    if not t:return True
    try:
        if path.endswith("/cards/enroll"):result=enroll(t["id"],data)
        elif path.endswith("/cards/update"):result=update_card(t["id"],data)
        elif path.endswith("/cards/reset-pin"):result=reset_pin(t["id"],data)
        else:result=assign(t["id"],data)
        h.send_json({"ok":True,**result})
    except bridge.CardNotFound:return err(h,"invalid_card",403)
    except bridge.CardBridgeUnavailable:return err(h,"card_bridge_unavailable",503)
    except ValueError as exc:return err(h,str(exc),400)
    except Exception as exc:
        h.log_message("LAB cards error: %s",type(exc).__name__)
        return err(h,"server_error",500)
    return True
