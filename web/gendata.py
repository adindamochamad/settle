#!/usr/bin/env python3
"""SETTLE site data - a compact replay stream for web/index.html.

    python web/gendata.py runs/09_md1.0.jsonl > web/data.json
    make site

Strips each record to only what the replay needs: timing and word-level
results. The raw payload carries engine-internal fields the page has no use
for. Source of truth is always the committed run; this is never hand-edited.
"""
import json
import sys

sys.path.insert(0, ".")
import analyzer


def compact(path):
    recs = analyzer.load(path)
    out = []
    for r in recs:
        if r["kind"] not in ("AddPartialTranscript", "AddTranscript"):
            continue
        words = [{"s": s, "e": e, "w": w} for s, e, w in analyzer.words(r["payload"])]
        if not words:
            continue
        out.append({
            "t": r["t"],
            "ap": r.get("audio_pos", r["t"]),
            "final": r["kind"] == "AddTranscript",
            "words": words,
        })
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    data = compact(sys.argv[1])
    if not data:
        print(f"{sys.argv[1]}: no transcript messages", file=sys.stderr)
        sys.exit(1)
    print(json.dumps({"source": sys.argv[1], "messages": data}))
