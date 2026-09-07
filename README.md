# public

Home for my automation scripts — the pipelines behind a few daily/weekly
personal newsletters and digests, run on my Ubuntu AI server via scheduled
jobs. Each pipeline lives in its own directory with its own README.

| Directory | What it does | Cadence |
|---|---|---|
| [`scripts/ai-newsletter/`](scripts/ai-newsletter/) | Watches ~14 tech/YouTube channels, transcripts new uploads, builds a daily AI news digest email | Daily |
| [`scripts/madison-events/`](scripts/madison-events/) | Scans local event listings within N miles of home and emails a weekend-ready roundup | Daily |
| [`scripts/meal-planner/`](scripts/meal-planner/) | Weekly meal plan + aisle-grouped shopping list, with dietary rules and rating feedback | Weekly |
| [`scripts/send_newsletter.py`](scripts/send_newsletter.py) | Shared SMTP helper used by all three pipelines | — |

## Conventions

- **Python 3, stdlib-first.** Few dependencies; where one is needed (e.g.
  `yt-dlp`) it's documented in the pipeline README.
- **Config over code.** Each pipeline reads a `config.json` next to its
  scripts. Copy the `*.example` files and fill in your own values.
- **State is a JSON file**, never a database — `state.json` per pipeline,
  safe to delete (the pipeline rebuilds it, just without dedupe history).
- All emails render as a dark-theme HTML newsletter with a plain-text twin.

## Security notes

Everything here has been scrubbed of credentials and personal data:
SMTP settings ship as `smtp.env.example`, addresses/coordinates are
placeholders. Do not commit a real `smtp.env`.
