#!/usr/bin/env python3
from __future__ import annotations
import json, re
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN = Path("/opt/lara/app/google_youtube_token.json")
OUT = Path("/tmp/factbook-links/data/archive.json")
CUTOFF = "2026-10-01T00:00:00Z"
LIMIT = 30

def seconds(value: str) -> int:
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", value or "")
    if not m:
        return 0
    h, mi, s = (int(x or 0) for x in m.groups())
    return h * 3600 + mi * 60 + s

def slugify(title: str, video_id: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    base = (base[:46].rstrip("-") or "video")
    return f"{base}-{video_id[:6].lower()}"

creds = Credentials.from_authorized_user_file(str(TOKEN))
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    TOKEN.write_text(creds.to_json(), encoding="utf-8")
yt = build("youtube", "v3", credentials=creds, cache_discovery=False)

channel = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]
uploads = channel["contentDetails"]["relatedPlaylists"]["uploads"]
ids = []
page = None
while len(ids) < 120:
    r = yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50, pageToken=page).execute()
    ids.extend(x["contentDetails"]["videoId"] for x in r.get("items", []))
    page = r.get("nextPageToken")
    if not page:
        break

videos = []
for i in range(0, len(ids), 50):
    r = yt.videos().list(part="snippet,status,contentDetails,localizations", id=",".join(ids[i:i+50])).execute()
    for x in r.get("items", []):
        if x.get("status", {}).get("privacyStatus") != "public":
            continue
        if seconds(x.get("contentDetails", {}).get("duration")) < 240:
            continue
        published = x.get("snippet", {}).get("publishedAt", "")
        if published < CUTOFF:
            continue
        loc = x.get("localizations") or {}
        title = x.get("snippet", {}).get("title", "")
        ar = (loc.get("ar") or {}).get("title") or title
        vid = x["id"]
        videos.append({
            "video_id": vid,
            "slug": "deepwater" if vid == "jyhvZ3bOKhM" else slugify(title, vid),
            "title": title,
            "title_ar": ar,
            "description_ar": f"{ar}. شاهد الفيديو كاملًا على YouTube.",
            "published_at": published,
            "duration": x.get("contentDetails", {}).get("duration", "")
        })

videos.sort(key=lambda v: v["published_at"], reverse=True)
videos = videos[:LIMIT]
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"count": len(videos), "videos": videos}, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"count": len(videos), "first": videos[:5]}, ensure_ascii=False))
