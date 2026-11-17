"""TAG Independent V1 - card-only identity provider for the separate TAG LAB.

Disabled unless a strong server-side TAG_CARD_BRIDGE_SECRET is configured.
No student name, teacher account, grades, scores, or QR value leaves this API.
Requests are server-to-server only; no CORS header is granted to browsers.
This module is developed on a non-deployed official-site branch.
"""
import hashlib
import hmac
import os
import re
import threading
import time
import platform_store as store

_PATH = "/api/tag-independent/card/resolve"
_ALLOWED_CARD = re.compile(r"^[A-Za-z0-9_-]{4,90}$")
_LOCK = threading.RLock()
_ATTEMPTS = {}

def _limited(ip):
    now = time.monotonic()
    with _LOCK:
        recent = [t for t in _ATTEMPTS.get(ip, ()) if now-t < 60]
        if len(recent) >= 60:
            _ATTEMPTS[ip] = recent
            return True
        _ATTEMPTS[ip] = recent + [now]
        if len(_ATTEMPTS)>2000:
            _ATTEMPTS.clear()
        return False

def _identity(secret, student_id):
    message = ("tag-independent-v1:student:" + str(student_id)).encode()
    return "tg1_" + hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()[:40]

def handle_post(handler, url, data):
    if url.path != _PATH:
        return False
    secret = os.getenv("TAG_CARD_BRIDGE_SECRET", "")
    if len(secret) < 32:
        handler.send_json({"ok":False,"error":"bridge_disabled"},503)
        return True
    received = handler.headers.get("Authorization", "")
    expected = "Bearer " + secret
    if not hmac.compare_digest(received, expected):
        handler.send_json({"ok":False,"error":"unauthorized"},401)
        return True
    if _limited(handler.client_address[0]):
        handler.send_json({"ok":False,"error":"rate_limited"},429)
        return True
    card = data.get("card") if isinstance(data,dict) else None
    if not isinstance(card,str) or not _ALLOWED_CARD.fullmatch(card.strip()):
        handler.send_json({"ok":False,"error":"invalid_card"},403)
        return True
    # Source of truth: official TAG student-card table, including prior card aliases.
    student = store.student_profile_by_card(card.strip())
    if student is None:
        handler.send_json({"ok":False,"error":"invalid_card"},403)
        return True
    handler.send_json({"ok":True,"version":1,"cardRef":_identity(secret,student["id"])})
    return True
