# meal-planner

Weekly meal-plan pipeline: produces a 7-day dinner plan plus an
aisle-grouped shopping list, honoring household dietary rules, and improves
itself from ratings feedback.

## How it runs

```
Saturday  → preference poll goes out over chat (what to add/avoid this week)
Saturday  → agent builds plan + shopping list from config + feedback history
          → newsletter email; ratings/note feedback flows back via
            feedback_log.py into state/feedback.jsonl
```

The plan generation is done by the scheduled agent; this directory holds its
rules, recipe sources, and the feedback recorder.

## Files

| File | Purpose |
|---|---|
| `config.json` | The contract: household size, cooking effort, budget, plan shape (days, main+sides structure, protein rotation), and `diet_rules.avoid` — the hard exclusions (allergies, dislikes) every plan must respect. |
| `feedback_log.py` | Parses free-text feedback into `state/feedback.jsonl`. `--rating "Recipe" --score 4 [--notes ...]` or `--note "whole message"`. One JSON object per line; the planner reads this to stop repeating duds. |
| `sources.txt` | Recipe sites/sources the planner may draw from. |
| `state/last_plan.json` | Previous week's plan — used for cross-week variety checks. |

## Setup

1. Edit `config.json`: servings, budget, and especially `diet_rules.avoid`
   — write them as explicit, checkable rules ("no tree nuts; watch 'may
   contain' labels on packaged sauces"), not vibes.
2. Point the newsletter recipient at your own address (placeholder here).

## Gotchas

- Allergen rules are **hard constraints** — the plan is wrong if a single
  recipe violates one, even if everything else is great.
- Ratings accumulate; a recipe rated ≤2 a few times should stop rotating
  back in. `feedback_log.py` exists so even a cron job without heredoc
  access can record a rating.
