#!/usr/bin/env python3
"""Fetch a YouTube transcript as timestamped plain text.

Usage: fetch_transcript.py <video_id_or_URL> [--lang en]
Strategy: 1) yt-dlp auto-captions (works from datacenter IPs), 2) youtube-transcript-api.
Prints JSON: {video_id, title, source, text, ok} — text lines prefixed [MM:SS].
"""
import json, os, re, subprocess, sys, tempfile

YTDLP = os.path.expanduser("~/.venvs/yt/bin/yt-dlp")


def vid_from(arg):
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([\w-]{11})", arg)
    return m.group(1) if m else arg.strip()


def _ts_secs(stamp):
    g = [int(x) for x in re.split(r"[:.]", stamp)[:3]]
    return g[0] * 3600 + g[1] * 60 + g[2] if len(g) == 3 else g[0] * 60 + g[1]


def _strip_overlap(prev_words, text, max_w=14):
    """Return the part of `text` that doesn't repeat the tail of prev cue(s)."""
    if not prev_words:
        return text
    w = text.split()
    k = min(max_w, len(prev_words), len(w))
    for n in range(k, 2, -1):
        if w[:n] == prev_words[-n:]:
            return " ".join(w[n:])
    return text


def vtt_to_lines(vtt):
    """Parse VTT cue blocks -> deduped '[MM:SS] text' lines."""
    out, prev_words = [], []
    blocks = re.split(r"\n\s*\n", vtt)
    for b in blocks:
        m = re.search(r"(\d+:\d+(?::\d+)?)[.,]\d+\s*-->", b)
        if not m:
            continue
        secs = _ts_secs(m.group(1))
        txt_lines = []
        for ln in b.splitlines():
            ln = ln.strip()
            if not ln or "-->" in ln or ln.startswith(("WEBVTT", "Kind:", "Language:", "NOTE", "{")):
                continue
            ln = re.sub(r"<[^>]+>", "", ln)
            ln = re.sub(r"\\c[^}]*\}?", "", ln)
            ln = re.sub(r">>", "", ln).strip()
            if ln:
                txt_lines.append(ln)
        text = _strip_overlap(prev_words, " ".join(txt_lines))
        text = re.sub(r"\s*\[music\]\s*", " ", text).strip()
        if not text:
            continue
        out.append(f"[{secs // 60:02d}:{secs % 60:02d}] {text}")
        prev_words = (prev_words + text.split())[-30:]
    return "\n".join(out)


def via_ytdlp(vid, lang):
    with tempfile.TemporaryDirectory() as td:
        cmd = [YTDLP, "--skip-download", "--no-warnings", "--write-auto-subs",
               "--sub-langs", f"{lang}.*,.*-orig", "--sub-format", "vtt",
               "-o", os.path.join(td, "sub.%(ext)s"), f"https://www.youtube.com/watch?v={vid}"]
        subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        for f in sorted(os.listdir(td)):
            if f.endswith(".vtt"):
                with open(os.path.join(td, f), encoding="utf-8", errors="replace") as fh:
                    txt = vtt_to_lines(fh.read())
                    if txt:
                        return txt
    return None


def via_api(vid, lang):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        tl = YouTubeTranscriptApi().fetch(vid, languages=[lang])
        return "\n".join(f"[{int(s.start) // 60:02d}:{int(s.start) % 60:02d}] {s.text}" for s in tl)
    except Exception:
        return None


def title_of(vid):
    try:
        r = subprocess.run([YTDLP, "--no-warnings", "--skip-download", "--print", "%(title)s",
                            f"https://www.youtube.com/watch?v={vid}"],
                           capture_output=True, text=True, timeout=60)
        return r.stdout.strip()
    except Exception:
        return ""


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: fetch_transcript.py <video_id_or_URL> [--lang en]")
    vid = vid_from(sys.argv[1])
    lang = "en"
    if "--lang" in sys.argv:
        lang = sys.argv[sys.argv.index("--lang") + 1]
    text = via_ytdlp(vid, lang)
    source = "ytdlp-auto-subs"
    if not text:
        text = via_api(vid, lang)
        source = "transcript-api"
    print(json.dumps({"video_id": vid, "title": title_of(vid), "source": source,
                      "text": text or "", "ok": bool(text)}))


if __name__ == "__main__":
    main()
