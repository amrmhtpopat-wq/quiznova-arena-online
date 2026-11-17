"""TAG Student Verify V1 — PIN ownership and attempt concurrency protection.

* A unique CSPRNG six-digit PIN is issued separately from card ID / QR.
* One-time delivery to the authenticated teacher; PBKDF2-HMAC hashes only at rest.
* Five incorrect PIN entries lock the student for fifteen minutes, across workers.
* Disabled per teacher by default until *all* active student PINs are issued.
* All DB writes use platform_store's SQLite/Postgres parameterized SQL adapter.
"""
import hashlib
import hmac
import re
import secrets
import time

import platform_store as store

PIN_FORMAT = re.compile(r"^[0-9]{6}$")
PIN_ITERATIONS = 210_000
MAX_FAILURES = 5
LOCK_SECONDS = 15 * 60


def ensure_schema():
    store.exec_sql(
        "CREATE TABLE IF NOT EXISTS student_verify_settings ("
        "teacher_id TEXT PRIMARY KEY, enabled INTEGER NOT NULL DEFAULT 0)"
    )
    store.exec_sql(
        "CREATE TABLE IF NOT EXISTS student_verify_pins ("
        "student_id TEXT PRIMARY KEY, teacher_id TEXT NOT NULL,"
        "pin_hash TEXT NOT NULL, pin_salt TEXT NOT NULL,"
        "failed_count INTEGER NOT NULL DEFAULT 0,"
        "locked_until BIGINT NOT NULL DEFAULT 0, issued_at BIGINT NOT NULL)"
    )
    store.exec_sql(
        "CREATE INDEX IF NOT EXISTS idx_verify_pins_teacher "
        "ON student_verify_pins (teacher_id)"
    )


def hash_pin(pin, salt):
    return hashlib.pbkdf2_hmac(
        "sha256", pin.encode("ascii"), bytes.fromhex(salt), PIN_ITERATIONS
    ).hex()


def is_enabled(teacher_id):
    if not teacher_id:
        return False
    r = store.query(
        "SELECT enabled FROM student_verify_settings WHERE teacher_id=?",
        (teacher_id,),
    )
    return bool(r and int(r["enabled"]))


def status(teacher_id):
    r = store.query(
        "SELECT COUNT(*) AS total, "
        "COALESCE(SUM(CASE WHEN p.student_id IS NOT NULL THEN 1 ELSE 0 END),0) AS issued "
        "FROM students AS s LEFT JOIN student_verify_pins AS p "
        "ON p.student_id=s.id AND p.teacher_id=s.teacher_id "
        "WHERE s.teacher_id=? AND s.archived=0",
        (teacher_id,),
    )
    return {
        "enabled": is_enabled(teacher_id),
        "students": int(r["total"] or 0),
        "issued": int(r["issued"] or 0),
        "pinLength": 6,
        "approvalRequired": False,
        "concurrentAttemptsBlocked": True,
    }


def issue_pins(teacher_id, student_id=None, rotate=False):
    """Issue missing PINs once or replace ONE student's PIN.

    PINs are returned only in this authenticated response. Never include in
    list_students, QR, logs, public profiles or student catalog responses.
    """
    if rotate and not student_id:
        raise ValueError("student_required_for_rotation")
    if student_id and not re.fullmatch(r"[0-9a-f]{32}", str(student_id)):
        raise ValueError("invalid_student")
    issued = []
    with store.DB_LOCK:
        with store.db_connection() as con:
            cur = con.cursor()
            sql = ("SELECT s.id,s.name,s.class_name,s.card_code,p.student_id "
                   "FROM students AS s LEFT JOIN student_verify_pins AS p "
                   "ON p.student_id=s.id AND p.teacher_id=s.teacher_id "
                   "WHERE s.teacher_id=? AND s.archived=0")
            args = [teacher_id]
            if student_id:
                sql += " AND s.id=?"
                args.append(student_id)
            sql += " ORDER BY s.class_name,s.name"
            students = cur.execute(store.sql(sql), tuple(args)).fetchall()
            if student_id and not students:
                raise ValueError("student_not_found")
            for sid, name, section, card_code, existing in students:
                if existing and not rotate:
                    continue
                pin = f"{secrets.randbelow(1_000_000):06d}"
                salt = secrets.token_hex(16)
                hashed = hash_pin(pin, salt)
                stamp = int(time.time())
                if existing:
                    cur.execute(store.sql(
                        "UPDATE student_verify_pins "
                        "SET pin_hash=?,pin_salt=?,failed_count=0,locked_until=0,issued_at=? "
                        "WHERE student_id=? AND teacher_id=?"),
                        (hashed, salt, stamp, sid, teacher_id))
                    # PIN reset must also revoke existing unfinished attempts.
                    # Otherwise a stolen, previously verified bearer session token
                    # would remain valid after the teacher replaces its PIN.
                    active = cur.execute(store.sql(
                        "SELECT token_hash,payload FROM solo_sessions "
                        "WHERE teacher_id=? AND student_id=?"),
                        (teacher_id, sid)).fetchall()
                    for key, payload in active:
                        attempt = store.jload(payload, {})
                        if attempt and not attempt.get("finished"):
                            cur.execute(store.sql(
                                "DELETE FROM solo_sessions WHERE token_hash=? AND "
                                "teacher_id=? AND student_id=?"),
                                (key, teacher_id, sid))
                else:
                    cur.execute(store.sql(
                        "INSERT INTO student_verify_pins "
                        "(student_id,teacher_id,pin_hash,pin_salt,failed_count,locked_until,issued_at) "
                        "VALUES(?,?,?,?,0,0,?)"),
                        (sid, teacher_id, hashed, salt, stamp))
                issued.append({
                    "id": sid, "name": name, "className": section,
                    "cardCode": card_code, "pin": pin,
                })
    return issued


def set_enabled(teacher_id, enabled):
    """Fail closed if teacher requests protection before issuing all codes."""
    if type(enabled) is not bool:
        raise ValueError("invalid_verify_setting")
    if enabled:
        info = status(teacher_id)
        if not info["students"] or info["issued"] != info["students"]:
            raise ValueError("pin_not_ready")
    with store.DB_LOCK:
        with store.db_connection() as con:
            cur = con.cursor()
            if enabled:
                # A pre-PIN session must not retain its ability to answer or
                # block the student's first protected session after activation.
                sessions = cur.execute(store.sql(
                    "SELECT token_hash,payload FROM solo_sessions WHERE teacher_id=?"),
                    (teacher_id,)).fetchall()
                for key, payload in sessions:
                    old = store.jload(payload, {})
                    if old and not old.get("finished") and not old.get("pinVerified"):
                        cur.execute(store.sql(
                            "DELETE FROM solo_sessions WHERE teacher_id=? AND token_hash=?"),
                            (teacher_id, key))
            cur.execute(store.sql(
                "DELETE FROM student_verify_settings WHERE teacher_id=?"),
                (teacher_id,))
            cur.execute(store.sql(
                "INSERT INTO student_verify_settings(teacher_id,enabled) VALUES(?,?)"),
                (teacher_id, 1 if enabled else 0))
    return status(teacher_id)


def verify_in_transaction(cur, teacher_id, student_id, pin):
    """Called while caller holds the student row lock in the SAME transaction.

    Returns None on success, otherwise an error code. Never reveal the PIN.
    """
    settings = cur.execute(store.sql(
        "SELECT enabled FROM student_verify_settings WHERE teacher_id=?"),
        (teacher_id,)).fetchone()
    if not settings or not int(settings[0]):
        return None
    locking = " FOR UPDATE" if store.DATABASE_URL else ""
    rec = cur.execute(store.sql(
        "SELECT pin_hash,pin_salt,failed_count,locked_until "
        "FROM student_verify_pins WHERE teacher_id=? AND student_id=?" + locking),
        (teacher_id, student_id)).fetchone()
    if not rec:
        return "student_pin_not_issued"
    expected, salt, failures, locked_until = rec
    stamp = int(time.time())
    if int(locked_until) > stamp:
        return "student_pin_locked"
    value = str(pin or "")
    valid = bool(PIN_FORMAT.fullmatch(value))
    # Always hash even malformed input, to reduce timing distinctions.
    trial = value if valid else "000000"
    correct = hmac.compare_digest(hash_pin(trial, salt), expected) and valid
    if correct:
        if int(failures) or int(locked_until):
            cur.execute(store.sql(
                "UPDATE student_verify_pins SET failed_count=0,locked_until=0 "
                "WHERE student_id=? AND teacher_id=?"),
                (student_id, teacher_id))
        return None
    new_count = int(failures) + 1
    lock_now = new_count >= MAX_FAILURES
    cur.execute(store.sql(
        "UPDATE student_verify_pins SET failed_count=?,locked_until=? "
        "WHERE student_id=? AND teacher_id=?"),
        (0 if lock_now else new_count, stamp + LOCK_SECONDS if lock_now else 0,
         student_id, teacher_id))
    return "student_pin_locked" if lock_now else (
        "student_pin_required" if not value else "student_pin_invalid"
    )


def verify_student(student, pin):
    """Safe stand-alone check for live room admission (not quiz creation)."""
    if not student:
        return "invalid_card"
    with store.DB_LOCK:
        with store.db_connection() as con:
            cur = con.cursor()
            lock = " FOR UPDATE" if store.DATABASE_URL else ""
            exists = cur.execute(store.sql(
                "SELECT id FROM students WHERE id=? AND teacher_id=? AND archived=0" + lock),
                (student["id"], student["teacher_id"])).fetchone()
            if not exists:
                return "invalid_card"
            return verify_in_transaction(
                cur, student["teacher_id"], student["id"], pin
            )


def release_active_attempt(teacher_id, student_id):
    """Teacher-only recovery for a lost device; does not erase completed records."""
    if not re.fullmatch(r"[0-9a-f]{32}", str(student_id or "")):
        raise ValueError("invalid_student")
    import solo_api
    removed = 0
    with store.DB_LOCK:
        with store.db_connection() as con:
            cur = con.cursor()
            student = cur.execute(store.sql(
                "SELECT id FROM students WHERE id=? AND teacher_id=? AND archived=0"),
                (student_id, teacher_id)).fetchone()
            if not student:
                raise ValueError("student_not_found")
            rows = cur.execute(store.sql(
                "SELECT token_hash,payload FROM solo_sessions "
                "WHERE teacher_id=? AND student_id=?"),
                (teacher_id, student_id)).fetchall()
            for token_hash, payload in rows:
                state = store.jload(payload, {})
                if state and not state.get("finished"):
                    cur.execute(store.sql(
                        "DELETE FROM solo_sessions WHERE token_hash=? AND "
                        "teacher_id=? AND student_id=?"),
                        (token_hash, teacher_id, student_id))
                    removed += 1
    return {"revoked": removed, "studentId": student_id}
