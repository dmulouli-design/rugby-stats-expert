"""Read-only connection to public Rugby-Data GitHub metadata.
Public repository does NOT establish redistribution rights. No copying into player dataset.
"""
import json
import urllib.request
from urllib.parse import quote

BASE = "https://api.github.com/repos/transientlunatic/Rugby-Data"
ALLOWED_DIRS = {"json", "yaml"}
MAX_BYTES = 2_000_000

def request_json(url, opener=urllib.request.urlopen):
    if not url.startswith(BASE + "/"):
        raise ValueError("Source URL not allowlisted")
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "RugbyStatsExpert/0.7"})
    with opener(req, timeout=12) as response:
        if int(response.headers.get("Content-Length", "0")) > MAX_BYTES:
            raise ValueError("Source response too large")
        payload = response.read(MAX_BYTES + 1)
        if len(payload) > MAX_BYTES:
            raise ValueError("Source response too large")
    return json.loads(payload)

def source_status(fetch=request_json):
    repo = fetch(BASE)
    license_obj = repo.get("license") or {}
    return {"source": repo.get("html_url", "https://github.com/transientlunatic/Rugby-Data"),
            "updated_at": repo.get("pushed_at"), "license_spdx": license_obj.get("spdx_id") or "UNVERIFIED",
            "redistribution_approved": False,
            "message": "Verify dataset and upstream feed licensing before redistribution."}

def browse(path="json", fetch=request_json):
    parts = path.strip("/").split("/")
    if not parts or parts[0] not in ALLOWED_DIRS or len(parts) > 6 or any(p in ("", ".", "..") for p in parts):
        raise ValueError("Only json/ and yaml/ paths are permitted")
    url = BASE + "/contents/" + "/".join(quote(p, safe="") for p in parts)
    data = fetch(url)
    if not isinstance(data, list):
        raise ValueError("Expected a directory")
    return [{"name": e.get("name"), "path": e.get("path"), "type": e.get("type"), "url": e.get("html_url")}
            for e in data if e.get("type") in ("file", "dir")][:200]
