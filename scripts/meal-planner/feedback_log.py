#!/usr/bin/env python3
"""Parse free-text feedback messages into state/feedback.jsonl.

Usage:
  feedback_log.py --rating "Recipe Name" --score 4 [--notes "extra tasty, will repeat"]
  feedback_log.py --note "whole text of the user's message"

Ratings 1-5. Appends JSON lines: {ts, type: rating|note, recipe?, rating?, notes}
The meal-planner scout job also appends directly via its own file tools;
this helper exists so the feedback-forwarding cron can parse structured ratings
without heredocs (cron_mode denies python -c / heredoc pipes).
"""
import argparse, json, os, sys
from datetime import datetime, timezone

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state", "feedback.jsonl")


def append(obj):
    obj["ts"] = datetime.now(timezone.utc).isoformat()
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    with open(PATH, "a") as f:
        f.write(json.dumps(obj) + "\n")
    print(f"logged: {obj}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rating", help="recipe name being rated")
    ap.add_argument("--score", type=int, help="1-5")
    ap.add_argument("--notes", default="")
    ap.add_argument("--note", help="free-text feedback, logged verbatim")
    a = ap.parse_args()
    if a.rating:
        score = a.score or 3
        if not 1 <= score <= 5:
            sys.exit("score must be 1-5")
        append({"type": "rating", "recipe": a.rating, "rating": score, "notes": a.notes})
    elif a.note:
        append({"type": "note", "notes": a.note})
    else:
        sys.exit("nothing to log")


if __name__ == "__main__":
    main()
