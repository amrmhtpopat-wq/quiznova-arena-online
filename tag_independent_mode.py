"""TAG INDEPENDENT V1: opt-in HTTP surface isolation for the standalone LAB.

Safe by default: the existing official and QA services are unchanged unless
TAG_LAB_ONLY_MODE=1 is explicitly configured on a new service.
The only future external dependency is the student-card identity bridge.
"""
import os
from urllib.parse import urlparse, parse_qsl, urlencode

_ENABLED = {"1", "true", "yes", "on"}

# Public TAG LAB page URLs. Legacy URLs continue to redirect so existing
# student QR codes and saved teacher links are not broken.
LEGACY_PAGE_REDIRECTS = {
    "/index.html": "/tag-lab-login.html",
    "/studio.html": "/tag-lab-create.html",
    "/teacher-hub-preview.html": "/tag-lab-library.html",
    "/student.html": "/tag-lab-student.html",
    "/game-lab-play.html": "/tag-lab-play.html",
    "/game-lab-card.html": "/tag-lab-card.html",
    "/game-lab-preview.html": "/tag-lab-preview.html",
}
# Use the original engine files on this branch without duplicating their
# logic. The visible address bar always shows the TAG LAB canonical route.
CANONICAL_STATIC_ALIASES = {
    "/tag-lab-play.html": "/game-lab-play.html",
    "/tag-lab-card.html": "/game-lab-card.html",
    "/tag-lab-preview.html": "/game-lab-preview.html",
}


def static_alias(path):
    """Resolve TAG LAB canonical filenames to existing static pages."""
    if not enabled():
        return path
    return CANONICAL_STATIC_ALIASES.get(path, path)

_AUTH_GET_PATHS = {"/api/auth/me", "/api/auth/reset-status"}
_AUTH_POST_PATHS = {
    "/api/auth/register", "/api/auth/login", "/api/auth/logout",
    "/api/auth/password", "/api/auth/forgot", "/api/auth/reset",
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
    # Deprecated QA student/live pages must never send independent LAB users to TAG.
    if p in ("/tag-lab-live.html", "/tag-lab-students.html"):
        return False
    # The obsolete pro/card APIs still depend on a legacy local student table.
    # Dedicated LAB live routes use only LAB-local card sessions or guest names.
    if p.startswith("/api/game-lab/pro/assignments"):
        return False
    if method in ("GET", "HEAD"):
        if p in ("", "/", "/favicon.ico", "/robots.txt"):
            return True
        if p.startswith("/api/"):
            return (p in _API_READ or p in _AUTH_GET_PATHS or
                    p.startswith("/api/tag-independent/teacher/") or
                    p.startswith("/api/game-lab/"))
        if p.lower().endswith(".html"):
            return p.startswith("/tag-lab-") or p.startswith("/game-lab-")
        # The existing server's translate_path still disallows Python, env and DB files.
        return True
    if method == "POST":
        if p in _API_POST_BLOCKED:
            return False
        return (p in _AUTH_POST_PATHS or
                p.startswith("/api/tag-independent/teacher/") or
                p.startswith("/api/tag-independent/student/") or
                p.startswith("/api/game-lab/"))
    return False

def reject(handler, method, path):
    """Return True after handling a request forbidden in standalone LAB mode."""
    if not enabled():
        return False
    parsed = urlparse(path)
    p = parsed.path
    if method.upper() in ("GET", "HEAD") and p in LEGACY_PAGE_REDIRECTS:
        canonical = LEGACY_PAGE_REDIRECTS[p]
        # Never reflect arbitrary raw input in a response header.
        query = urlencode(parse_qsl(parsed.query, keep_blank_values=True))
        handler.send_response(302)
        handler.send_header("Location", canonical + ("?" + query if query else ""))
        handler.send_header("Cache-Control", "no-store")
        handler.end_headers()
        return True
    if method.upper() in ("GET", "HEAD") and p in ("", "/"):
        handler.send_response(302)
        handler.send_header("Location", "/tag-lab-login.html")
        handler.send_header("Cache-Control", "no-store")
        handler.end_headers()
        return True
    if allowed(method, path):
        return False
    handler.send_json({"ok": False, "error": "not_available_on_tag_lab"}, 404)
    return True
