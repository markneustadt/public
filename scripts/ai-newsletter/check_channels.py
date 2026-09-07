#!/usr/bin/env python3
"""List NEW uploads (videos + shorts, NOT livestreams) across tracked channels.

Usage:  check_channels.py            # print JSON of new items, update state.json
        check_channels.py --dry-run  # don't touch state.json

State: state.json {"seen": {"<video_id>": first_seen_iso}} — deduped by id.
For each channel we pull the flat /videos and /shorts playlist tabs via yt-dlp
(the /streams tab is deliberately never queried, so live content is excluded).
Exit code 0 even on partial failures; per-channel errors appear in "errors".
"""
import concurrent.futures as cf
import datetime as dt
import json
import os
import subprocess
import sys

YTDLP = os.path.expanduser("~/.venvs/yt/bin/yt-dlp")
DIR = os.path.dirname(os.path.abspath(__file__))


def load():
    with open(os.path.join(DIR, "channels.txt")) as f:
        handles = [l.split("#")[0].strip() for l in f if l.split("#")[0].strip()]
    with open(os.path.join(DIR, "config.json")) as f:
        cfg = json.load(f)
    state_path = os.path.join(DIR, "state.json")
    state = {}
    if os.path.exists(state_path):
        with open(state_path) as f:
            state = json.load(f)
    return handles, cfg, state


def fetch_tab(handle, tab, limit):
    url = f"https://www.youtube.com/{handle}/{tab}"
    cmd = [
        YTDLP, "--flat-playlist", "--no-warnings", "--ignore-errors",
        "--playlist-end", str(limit),
        "--print", "%(id)s\t%(title)s\t%(duration)s\t%(timestamp)s\t%(view_count)s",
        url,
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    items = []
    for line in out.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 4 or not parts[0]:
            continue
        vid, title = parts[0], parts[1]
        try:
            dur = float(parts[2]) if parts[2] not in ("NA", "") else None
        except ValueError:
            dur = None
        try:
            ts = float(parts[3]) if parts[3] not in ("NA", "") else None
        except ValueError:
            ts = None
        views = None
        if len(parts) > 4 and parts[4] not in ("NA", ""):
            try:
                views = int(parts[4])
            except ValueError:
                pass
        items.append({
            "id": vid, "title": title, "tab": tab, "duration_s": dur,
            "ts": ts, "views": views,
            "url": f"https://youtu.be/{vid}",
        })
    return items


def main():
    dry = "--dry-run" in sys.argv
    handles, cfg, state = load()
    seen = state.setdefault("seen", {})
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=cfg.get("lookback_days", 4))
    cutoff_ts = cutoff.timestamp()
    limit = cfg.get("max_videos_per_channel", 12)
    short_limit = cfg.get("shorts_per_channel", 6)
    vod_min = cfg.get("livestream_vod_min_duration", 5400)

    jobs = [(h, tab, short_limit if tab == "shorts" else limit) for h in handles for tab in ("videos", "shorts")]
    errors, new = [], []
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(fetch_tab, h, t, lim): (h, t) for h, t, lim in jobs}
        for fut in cf.as_completed(futs):
            h, t = futs[fut]
            try:
                for it in fut.result():
                    title_l = (it["title"] or "").lower()
                    if it["ts"] is not None and it["ts"] < cutoff_ts:
                        continue
                    if it["id"] in seen:
                        continue
                    # heuristically drop long livestream rebroadcasts
                    if (it["duration_s"] or 0) >= vod_min or "live" in title_l.split() or "stream" in title_l.split():
                        continue
                    it["channel_handle"] = h.lstrip("@")
                    it["channel"] = cfg["channel_names"].get(it["channel_handle"], h.lstrip("@"))
                    new.append(it)
            except Exception as e:
                errors.append(f"{h}/{t}: {type(e).__name__}: {e}")

    new.sort(key=lambda x: x["ts"] or 0, reverse=True)
    if not dry:
        now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        for it in new:
            seen[it["id"]] = now
        if len(seen) > 800:  # cap: drop oldest
            for k in sorted(seen, key=seen.get)[: len(seen) - 800]:
                del seen[k]
        with open(os.path.join(DIR, "state.json"), "w") as f:
            json.dump(state, f)

    print(json.dumps({
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "channels_checked": len(handles),
        "new_count": len(new),
        "new_videos": new,
        "errors": errors,
    }, indent=2))


if __name__ == "__main__":
    main()
