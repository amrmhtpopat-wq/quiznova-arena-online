"""TAG INDEPENDENT V1: opt-in HTTP surface isolation for the standalone LAB.

Safe by default: the existing official and QA services are unchanged unless
TAG_LAB_ONLY_MODE=1 is explicitly configured on a new service.
The only future external dependency is the student-card identity bridge.
"""
import os
from urllib.parse import urlparse

_ENABLED = {"1", "true", "yes", "on"}
_AUTH_PATHS = {
    "/api/auth/register", "/api/auth/login", "/api/auth/logout",
    "/api/auth/me", "/api/auth/password", "/api/auth/forgot",
    "/api/auth/reset", "/api/auth/reset-status",
}
_API_READ = {"/api/health", "/api/status", "/api/qr"}
_API_POST_BLOCKED = {
    "/api/game-lab/pro/assignments/save",  # wait for cross-site card binding
    "/api/game-lab/pro/card/catalog",       # must never look up isolated local student table
}

def enabled():
    return os.environ.get("TAG_LAB_ONLY_MODE", "").strip().lower() in _ENABLED

def allowed(method, path):
    """Constrain the independent LAB, without modifying existing services."""
    if not enabled():
        return True
    p = urlparse(path).path
    method = str(method).upper()
    if method in ("GET", "HEAD"):
        if p in ("", "/", "/favicon.ico", "/robots.txt"):
            return True
        if p.startswith("/api/"):
            return (p in _API_READ or p in _AUTH_PATHS or
                    p.startswith("/api/game-lab/"))
        if p.lower().endswith(".html"):
            return p.startswith("/tag-lab-") or p.startswith("/game-lab-")
        # The existing server's translate_path still disallows Python, env and DB files.
        return True
    if method == "POST":
        if p == "/api/tag-independent/card/verify":
            return True
        if p in _API_POST_BLOCKED:
            return False
        return p in _AUTH_PATHS or p.startswith("/api/game-lab/")
    return False

def reject(handler, method, path):
    """Return True after handling a request forbidden in standalone LAB mode."""
    if not enabled():
        return False
    p = urlparse(path).path
    if method.upper() in ("GET", "HEAD") and p in ("", "/"):
        handler.send_response(302)
        handler.send_header("Location", "/tag-lab-home.html")
        handler.send_header("Cache-Control", "no-store")
        handler.end_headers()
        return True
    if allowed(method, path):
        return False
    handler.send_json({"ok": False, "error": "not_available_on_tag_lab"}, 404)
    return True
