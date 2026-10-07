#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/archive.json"
LEDGER = ROOT / "data/distribution-ledger.json"
BASE = "https://ramialmasri5.github.io/factbook-links"
TZ = ZoneInfo("Asia/Beirut")
PAGES = ("Rami Almasri", "Rami Almasri Plus")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def video_complete(entry: dict) -> bool:
    fb = entry.get("facebook") or {}
    return all((fb.get(page) or {}).get("status") == "PASS" for page in PAGES)


def resolve_slot(force_slot: str | None = None) -> str | None:
    if force_slot:
        return force_slot
    now = datetime.now(TZ)
    if now.hour == 10:
        return "morning"
    if now.hour == 20:
        return "evening"
    return None


def slot_done_today(ledger: dict, slot: str) -> bool:
    today = datetime.now(TZ).date().isoformat()
    for run in ledger.get("runs", []):
        if run.get("date") != today or run.get("slot") != slot:
            continue
        result = run.get("result") or {}
        if result and all(v == "PASS" for v in result.values()):
            return True
    return False


def pick_next(archive: dict, ledger: dict) -> dict | None:
    entries = ledger.get("videos") or {}
    for video in archive.get("videos", []):
        if video_complete(entries.get(video["video_id"]) or {}):
            continue
        return video
    return None


def publish_one(page: str, message: str, link: str) -> dict:
    cmd = [
        sys.executable,
        str(ROOT / "tools/meta_social.py"),
        "publish",
        "--page", page,
        "--message", message,
        "--link", link,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    payload = None
    for line in reversed((proc.stdout or "").splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
            break
        except json.JSONDecodeError:
            continue
    if proc.returncode != 0 or not isinstance(payload, dict):
        return {
            "status": "FAIL",
            "error": (proc.stderr or proc.stdout or f"exit_{proc.returncode}").strip()[-3000:],
            "published_at": datetime.now(TZ).isoformat(timespec="seconds"),
        }
    rb = payload.get("readback") or {}
    return {
        "status": payload.get("status"),
        "post_id": payload.get("post_id"),
        "permalink": rb.get("permalink_url"),
        "link_verified": payload.get("link_verified"),
        "published_at": datetime.now(TZ).isoformat(timespec="seconds"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slot", choices=["morning", "evening"])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    archive = load_json(ARCHIVE)
    ledger = load_json(LEDGER)
    slot = resolve_slot(args.slot)

    if not slot:
        print(json.dumps({"status": "PASS", "reason": "outside_beirut_slot"}, ensure_ascii=False))
        return 0

    if slot_done_today(ledger, slot):
        print(json.dumps({"status": "PASS", "reason": "slot_already_done", "slot": slot}, ensure_ascii=False))
        return 0

    video = pick_next(archive, ledger)
    if not video:
        print(json.dumps({"status": "PASS", "reason": "archive_exhausted"}, ensure_ascii=False))
        return 0

    link = f"{BASE}/{video['slug']}/"
    message = f"{video.get('title_ar') or video['title']}\nشاهد الفيديو كاملًا على يوتيوب 👇"

    if args.dry_run:
        print(json.dumps({
            "status": "PASS",
            "reason": "dry_run",
            "slot": slot,
            "video_id": video["video_id"],
            "title": video["title"],
            "link": link,
            "pages": list(PAGES),
        }, ensure_ascii=False))
        return 0

    if not os.getenv("META_ACCESS_TOKEN", "").strip():
        print(json.dumps({
            "status": "PASS",
            "reason": "meta_secret_not_configured",
            "slot": slot,
            "next_video_id": video["video_id"],
        }, ensure_ascii=False))
        return 0

    entries = ledger.setdefault("videos", {})
    entry = entries.setdefault(video["video_id"], {
        "slug": video["slug"],
        "deeplink_url": link,
        "facebook": {},
        "archive_complete": False,
    })
    entry.setdefault("facebook", {})
    result = {}

    for page in PAGES:
        existing = entry["facebook"].get(page) or {}
        if existing.get("status") == "PASS":
            result[page] = "PASS"
            continue
        published = publish_one(page, message, link)
        entry["facebook"][page] = published
        result[page] = published.get("status")
        entry["archive_complete"] = video_complete(entry)
        entry["updated_at"] = datetime.now(TZ).isoformat(timespec="seconds")
        save_json(LEDGER, ledger)

    entry["archive_complete"] = video_complete(entry)
    ledger.setdefault("runs", []).append({
        "date": datetime.now(TZ).date().isoformat(),
        "at": datetime.now(TZ).isoformat(timespec="seconds"),
        "slot": slot,
        "video_id": video["video_id"],
        "deeplink": link,
        "result": result,
    })
    ledger["runs"] = ledger["runs"][-200:]
    save_json(LEDGER, ledger)

    overall = "PASS" if entry["archive_complete"] else "PARTIAL"
    print(json.dumps({
        "status": overall,
        "slot": slot,
        "video_id": video["video_id"],
        "link": link,
        "result": result,
    }, ensure_ascii=False))
    return 0 if overall == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
