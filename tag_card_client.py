"""TAG Independent V1: private server-to-server student-card verification client.

The official site owns the physical card; LAB receives only an opaque cardRef.
Never put this secret in JavaScript or log raw QR/card values.
"""
import json
import os
import re
import urllib.error
import urllib.request

OFFICIAL_ENDPOINT = "https://quiznova-arena-online.onrender.com/api/tag-independent/card/resolve"
CARD_PATTERN = re.compile(r"^[A-Za-z0-9_-]{4,90}$")
REF_PATTERN = re.compile(r"^tg1_[0-9a-f]{40}$")

class CardBridgeUnavailable(Exception):
    pass

class CardNotFound(Exception):
    pass

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None

def configured():
    secret = os.getenv("TAG_CARD_BRIDGE_SECRET", "")
    return len(secret) >= 32

def verify(card):
    """Return opaque cardRef. Never return a student's name or official teacher ID."""
    if not isinstance(card,str) or not CARD_PATTERN.fullmatch(card.strip()):
        raise CardNotFound("invalid_card")
    secret = os.getenv("TAG_CARD_BRIDGE_SECRET", "")
    if len(secret) < 32:
        raise CardBridgeUnavailable("bridge_unconfigured")
    data = json.dumps({"card": card.strip()}, separators=(",",":")).encode()
    req = urllib.request.Request(
        OFFICIAL_ENDPOINT,
        data=data,
        method="POST",
        headers={
            "Authorization":"Bearer "+secret,
            "Content-Type":"application/json",
            "Accept":"application/json",
        },
    )
    opener=urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(req,timeout=5) as response:
            if response.status != 200:
                raise CardBridgeUnavailable("provider_unavailable")
            raw=response.read(2048)
            obj=json.loads(raw)
    except urllib.error.HTTPError as err:
        if err.code in (400,403,404):
            raise CardNotFound("invalid_card") from None
        raise CardBridgeUnavailable("provider_unavailable") from None
    except (urllib.error.URLError,TimeoutError,ValueError,UnicodeError,TypeError) as err:
        raise CardBridgeUnavailable("provider_unavailable") from None
    ref=obj.get("cardRef") if isinstance(obj,dict) and obj.get("ok") is True else None
    if obj.get("version") != 1 or not isinstance(ref,str) or not REF_PATTERN.fullmatch(ref):
        raise CardBridgeUnavailable("invalid_provider_response")
    return ref
