#!/usr/bin/env python3
"""SETTLE analyzer - per-word settling time from a recorded run.

    python analyzer.py --inspect runs/call1_md1.0.jsonl   # dump one payload
    python analyzer.py runs/call1_md1.0.jsonl             # measure one run
    python analyzer.py runs/*.jsonl                       # compare runs

Definitions live in docs/METHOD.md. This module interprets; recorder.py does not.

! The payload reader below follows the documented Speechmatics results shape
! (results[].start_time / end_time / alternatives[0].content). Run --inspect
! against a real file and confirm before trusting any number this prints.
"""
import json
import sys
from collections import defaultdict


def load(path):
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def words(payload):
    """[(start_time, end_time, text)] for one transcript message."""
    out = []
    for item in payload.get("results", []):
        if item.get("type") not in (None, "word"):
            continue          # punctuation carries no independent timing
        alts = item.get("alternatives") or [{}]
        text = (alts[0].get("content") or "").strip()
        if text:
            out.append((item.get("start_time", 0.0),
                        item.get("end_time", 0.0), text))
    return out


def overlaps(a, b):
    """True when two audio intervals refer to the same spoken word.

    Overlap of at least half the shorter interval. Index matching is wrong
    here - words get inserted and deleted mid-revision, which is the whole
    phenomenon under study.
    """
    lo = max(a[0], b[0])
    hi = min(a[1], b[1])
    if hi <= lo:
        return False
    shorter = min(a[1] - a[0], b[1] - b[0])
    return shorter <= 0 or (hi - lo) >= 0.5 * shorter


def track(records):
    """Group every observation by the spoken word it refers to.

    Returns {slot_index: {"span": (start, end), "obs": [(t, text), ...]}}.
    """
    slots = []
    for rec in records:
        if rec["kind"] not in ("AddPartialTranscript", "AddTranscript"):
            continue
        for start, end, text in words(rec["payload"]):
            hit = next((s for s in slots if overlaps(s["span"], (start, end))), None)
            if hit is None:
                slots.append({"span": (start, end), "obs": [(rec["t"], text)]})
            else:
                hit["span"] = (min(hit["span"][0], start), max(hit["span"][1], end))
                hit["obs"].append((rec["t"], text))
    return {i: s for i, s in enumerate(slots)}


def settling(records):
    """[(final_text, emission_lag, settling_time, revisions)] for one run."""
    stats = []
    for slot in track(records).values():
        obs = slot["obs"]
        t_first = obs[0][0]
        t_last_change = t_first
        revisions = 1
        for i in range(1, len(obs)):
            if obs[i][1] != obs[i - 1][1]:
                t_last_change = obs[i][0]
                revisions += 1
        stats.append((obs[-1][1],
                      round(t_first - slot["span"][1], 3),
                      round(t_last_change - t_first, 3),
                      revisions))
    return stats


def pct(values, p):
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(round((p / 100) * (len(ordered) - 1))))
    return ordered[idx]


def report(path):
    records = load(path)
    md = next((r.get("max_delay") for r in records if r.get("max_delay")), "?")
    stats = settling(records)
    if not stats:
        print(f"{path}: no transcript messages found")
        return
    settle = [s[2] for s in stats]
    revised = [s for s in stats if s[3] > 1]
    print(f"\n{path}   max_delay={md}   words={len(stats)}")
    print(f"  settling  p50 {pct(settle,50):.3f}s   p95 {pct(settle,95):.3f}s"
          f"   p99 {pct(settle,99):.3f}s   max {max(settle):.3f}s")
    print(f"  revised   {len(revised)}/{len(stats)} words "
          f"({100*len(revised)/len(stats):.1f}%)")
    for text, lag, st, rev in sorted(stats, key=lambda s: -s[2])[:5]:
        print(f"    {text:<18} settling {st:>6.3f}s  revisions {rev}  lag {lag:>6.3f}s")


def inspect(path):
    for rec in load(path):
        if rec["kind"] == "AddPartialTranscript":
            print(json.dumps(rec["payload"], indent=2)[:2000])
            return
    print("no AddPartialTranscript in this run - partials may be disabled")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--inspect":
        inspect(args[1])
    else:
        for path in args:
            report(path)
