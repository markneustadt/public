# ai-newsletter

Daily "AI News & Walkthroughs" digest: watches a list of YouTube channels,
picks up **new uploads and shorts (livestreams excluded)**, fetches
transcripts, and assembles a dark-theme HTML newsletter delivered by email.

## How it runs

```
check_channels.py  →  new_videos.json   (which videos are new since yesterday)
fetch_transcript.py →  spool/transcripts/<id>.txt   (timestamped text per video)
   [an AI agent writes the digest from those transcripts]
send_email.py      →  SMTP relay → inbox
```

The middle "write the digest" step is done by the scheduled agent, not a
script — these scripts handle everything deterministic.

## Files

| File | Purpose |
|---|---|
| `check_channels.py` | Lists new uploads across tracked channels via `yt-dlp` (queries the `/videos` and `/shorts` playlist tabs, never `/streams`). Dedupes against `state.json`. Exit 0 even on partial failures; per-channel errors land in `"errors"`. |
| `fetch_transcript.py` | One video (ID or URL) → timestamped plain text. Tries yt-dlp auto-captions first (works from datacenter IPs), falls back to `youtube-transcript-api`. |
| `model_fit.py` | Estimator: given params/quant bits/context, does a model fit in this GPU/RAM, and roughly how fast would it decode? Backs the "can it run on my hardware" segment. Machine specs live in `config.json`. |
| `send_email.py` | Sends the newsletter over SMTP. Reads creds from `smtp.env` next to the script (or `EMAIL_*` env vars). |
| `config.json` | Channel handle → display-name map, lookback window, caps, hardware specs, email settings. |
| `channels.txt` | The tracked channel handles. |
| `smtp.env.example` | Template — copy to `smtp.env` and fill in. |

## Setup

```bash
cp smtp.env.example smtp.env   # and edit
pip install yt-dlp youtube-transcript-api   # or a venv, e.g. ~/.venvs/yt
python3 check_channels.py --dry-run         # smoke test
```

## Gotchas

- `check_channels.py` hardcodes the yt-dlp path (`~/.venvs/yt/bin/yt-dlp`) —
  adjust to your install.
- Deleting `state.json` makes every video "new" again — first run will be big.
- Shorts are capped separately from regular uploads (`shorts_per_channel`).
