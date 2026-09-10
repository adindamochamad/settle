#!/usr/bin/env python3
"""SETTLE analyzer - per-word settling time from a recorded run.

    python analyzer.py --inspect runs/call1_md1.0.jsonl   # dump one payload
    python analyzer.py runs/call1_md1.0.jsonl             # measure one run
    python analyzer.py runs/*.jsonl                       # compare runs
    python analyzer.py --table runs/*.jsonl               # the README table

Definitions live in docs/METHOD.md. This module interprets; recorder.py does not.

! The payload reader below follows the documented Speechmatics results shape
! (results[].start_time / end_time / alternatives[0].content). Run --inspect
! against a real file and confirm before trusting any number this prints.
! That check is docs/DOD.md A1, and it is blocking.
"""
import json
import sys
from collections import defaultdict

PARTIAL = "AddPartialTranscript"
FINAL = "AddTranscript"


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


def overlap(a, b):
    """Fraction of the shorter interval that two audio intervals share."""
    lo = max(a[0], b[0])
    hi = min(a[1], b[1])
    if hi <= lo:
        return 0.0
    shorter = min(a[1] - a[0], b[1] - b[0])
    if shorter <= 0:
        return 0.0
    return (hi - lo) / shorter


def overlaps(a, b):
    """True when two audio intervals refer to the same spoken word.

    Overlap of at least half the shorter interval. Index matching is wrong
    here - words get inserted and deleted mid-revision, which is the whole
    phenomenon under study. This is the single alignment rule in the project;
    sidecar.py imports it rather than growing a second one.
    """
    return overlap(a, b) >= 0.5


def apply(slots, rec_words, is_final):
    """Update slots with one message's words - the one alignment step.

    Returns (slots, touched, changed, dropped): touched is every slot index
    matched or created by this message; changed is the subset whose text is
    new or different from before this call; dropped is the *pre-call*
    indices retracted this call (see below) - a caller holding index-keyed
    state (sidecar.py's pending release timers) needs the old numbering to
    know what to cancel, since the returned slots are already renumbered.
    track() (batch, a whole run) and sidecar.py (streaming, live or
    replayed) both call this, so there is exactly one implementation of
    "which word is this, did it change, was it retracted" - not two.
    sidecar.py must not grow a second aligner; see docs/DOD.md S5.

    A word is bound to its *best* overlapping slot, not the first one that
    clears the threshold - adjacent short words otherwise capture each other.
    A slot's span follows the most recent observation, because the engine
    nudges word timings between revisions; unioning the spans instead lets one
    slot grow until it swallows its neighbours.

    One message contributes at most one observation per slot. Without that,
    two neighbouring words in the same message can both bind to it and the
    second reads as an instant revision of the first - a revision count of 2
    with a settling time of 0.

    Retraction: the engine sometimes drops a word it had hypothesised, with
    no replacement - not a revision to different text, a deletion. A trailing
    AddTranscript with zero words is the clearest case (confirmed against
    metadata.transcript on a real run: it reports "", not a shorter string).
    There is no direct signal for this in results[], so it is inferred: once
    processing's frontier (the earliest start_time in a message's words) has
    moved past a slot's span and that slot was never part of any AddTranscript,
    it will not be mentioned again - drop it. A slot already finalised is
    never dropped; the corpus shows finals do not retract (see README).
    """
    used = set()
    changed = set()
    for start, end, text in rec_words:
        best, score = None, 0.0
        for i, slot in enumerate(slots):
            if i in used:
                continue
            sc = overlap(slot["span"], (start, end))
            if sc > score:
                best, score = i, sc
        if best is None or score < 0.5:
            slots.append({"span": (start, end), "text": text, "locked": is_final})
            used.add(len(slots) - 1)
            changed.add(len(slots) - 1)
        else:
            if slots[best]["text"] != text:
                changed.add(best)
            slots[best]["span"] = (start, end)
            slots[best]["text"] = text
            if is_final:
                slots[best]["locked"] = True
            used.add(best)

    touched = used
    dropped = set()
    if rec_words:
        frontier = min(s for s, _, _ in rec_words)
        keep = [i for i, s in enumerate(slots)
                if i in used or s["locked"] or s["span"][1] > frontier]
        if len(keep) != len(slots):
            dropped = set(range(len(slots))) - set(keep)
            new_index = {old_i: new_i for new_i, old_i in enumerate(keep)}
            slots = [slots[i] for i in keep]
            touched = {new_index[i] for i in touched if i in new_index}
            changed = {new_index[i] for i in changed if i in new_index}
    return slots, touched, changed, dropped


def track(records):
    """Group every observation by the spoken word it refers to, over a whole
    run - the offline/batch use of apply(). See apply()'s docstring for the
    alignment rule itself.

    Returns [{"span": (start, end), "text": str, "locked": bool,
    "obs": [(t, audio_pos, text, is_final)]}]. "obs" is the arrival history
    settling() needs (t_first, t_last_change, first-final timestamp); it gets
    one entry per message that touches a slot, matching every message
    apply() bound a word to for that slot - not just the ones that changed
    its text, since a slot's first *final* matters even when its text was
    already stable.
    """
    slots = []
    for rec in records:
        if rec["kind"] not in (PARTIAL, FINAL):
            continue
        is_final = rec["kind"] == FINAL
        rec_words = words(rec["payload"])
        slots, touched, _changed, _dropped = apply(slots, rec_words, is_final)
        for i in touched:
            slots[i].setdefault("obs", []).append(
                (rec["t"], rec.get("audio_pos", rec["t"]), slots[i]["text"], is_final))
    return slots


def settling(records):
    """One dict per spoken word in one run. See docs/METHOD.md."""
    stats = []
    for slot in track(records):
        obs = slot["obs"]
        t_first, pos_first = obs[0][0], obs[0][1]
        t_last_change = t_first
        revisions = 1
        for i in range(1, len(obs)):
            if obs[i][2] != obs[i - 1][2]:
                t_last_change = obs[i][0]
                revisions += 1

        # The headline question in docs/METHOD.md: once a word is reported in
        # an AddTranscript, does its text ever change again?
        idx = next((i for i, o in enumerate(obs) if o[3]), None)
        if idx is None:
            t_final, after_final = None, False
        else:
            t_final = obs[idx][0]
            after_final = any(o[2] != obs[idx][2] for o in obs[idx + 1:])

        stats.append({
            "text": obs[-1][2],
            # Emission lag is on the audio clock: how much audio had been sent
            # when this text first appeared. Using wall-clock `t` here would
            # fold in TLS setup and pacing drift, which are not the engine.
            # It goes negative when the engine emitted a hypothesis before the
            # word it later settled on had finished - see docs/METHOD.md.
            "emission": round(pos_first - slot["span"][1], 3),
            "settling": round(t_last_change - t_first, 3),
            "risk": round(t_final - t_first, 3) if t_final is not None else None,
            "revisions": revisions,
            "after_final": after_final,
            "finalised": t_final is not None,
        })
    return stats


def pct(values, p):
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(round((p / 100) * (len(ordered) - 1))))
    return ordered[idx]


def offset(records):
    """Wall clock minus audio clock at the end of a run.

    Connection setup plus accumulated pacing drift. Reported, never corrected -
    see docs/DOD.md R4.
    """
    if not records:
        return 0.0
    last = records[-1]
    return round(last["t"] - last.get("audio_pos", last["t"]), 3)


def read(path):
    """(records, stats) or an explanation on stderr. Never returns junk."""
    try:
        records = load(path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"{path}: unreadable - {exc}", file=sys.stderr)
        return None, None
    if not records:
        print(f"{path}: empty run", file=sys.stderr)
        return None, None
    stats = settling(records)
    if not stats:
        kinds = sorted({r.get("kind") for r in records})
        print(f"{path}: no transcript messages found - kinds present: "
              f"{', '.join(k for k in kinds if k)}", file=sys.stderr)
        return None, None
    return records, stats


def report(path):
    records, stats = read(path)
    if stats is None:
        return False
    md = next((r.get("max_delay") for r in records if r.get("max_delay")), "?")
    settle = [s["settling"] for s in stats]
    emission = [s["emission"] for s in stats]
    risk = [s["risk"] for s in stats if s["risk"] is not None]
    revised = [s for s in stats if s["revisions"] > 1]
    late = [s for s in stats if s["after_final"]]
    n = len(stats)

    print(f"\n{path}   max_delay={md}   words={n}   "
          f"wall-audio offset {offset(records):+.3f}s")
    print(f"  settling     p50 {pct(settle,50):.3f}s  p95 {pct(settle,95):.3f}s"
          f"  p99 {pct(settle,99):.3f}s  max {max(settle):.3f}s   [wall clock]")
    if risk:
        print(f"  risk window  p50 {pct(risk,50):.3f}s  p95 {pct(risk,95):.3f}s"
              f"  max {max(risk):.3f}s"
              f"   [first text -> finalised, {len(risk)}/{n} words]")
    print(f"  emission lag p50 {pct(emission,50):.3f}s  "
          f"p95 {pct(emission,95):.3f}s   [audio clock]")
    spec = sum(1 for e in emission if e < 0)
    if spec:
        # Not an error. A negative emission lag means text for this interval
        # appeared while the word was still being spoken: the engine published
        # a hypothesis, then extended the word's end_time past the point where
        # the audio stood when it did so.
        print(f"  speculative  {spec}/{n} words ({100*spec/n:.1f}%)"
              f"   <- text emitted before the word finished")
    print(f"  revised      {len(revised)}/{n} words ({100*len(revised)/n:.1f}%)")
    print(f"  after final  {len(late)}/{n} words ({100*len(late)/n:.1f}%)"
          f"   <- does 'final' stop changing?")
    for s in sorted(stats, key=lambda s: -s["settling"])[:5]:
        print(f"    {s['text']:<18} settling {s['settling']:>6.3f}s  "
              f"revisions {s['revisions']}  lag {s['emission']:>6.3f}s")
    return True


def table(paths):
    """The README results table, emitted from runs/ so it is never typed."""
    pooled = defaultdict(list)
    for path in paths:
        records, stats = read(path)
        if stats is None:
            continue
        md = next((r.get("max_delay") for r in records if r.get("max_delay")), None)
        pooled[md].extend(stats)
    if not pooled:
        print("no usable runs", file=sys.stderr)
        return False
    print("| `max_delay` | words | settling p50 | settling p99 | "
          "words revised | revised after final |")
    print("|---|---|---|---|---|---|")
    for md in sorted(pooled, key=lambda m: (m is None, m)):
        stats = pooled[md]
        settle = [s["settling"] for s in stats]
        n = len(stats)
        rev = sum(1 for s in stats if s["revisions"] > 1)
        late = sum(1 for s in stats if s["after_final"])
        print(f"| {md} | {n} | {pct(settle,50):.3f}s | {pct(settle,99):.3f}s | "
              f"{100*rev/n:.1f}% | {100*late/n:.1f}% |")
    return True


def inspect(path):
    for rec in load(path):
        if rec["kind"] == PARTIAL:
            print(json.dumps(rec["payload"], indent=2)[:2000])
            return True
    print("no AddPartialTranscript in this run - partials may be disabled",
          file=sys.stderr)
    return False


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    if args[0] == "--inspect":
        sys.exit(0 if inspect(args[1]) else 1)
    if args[0] == "--table":
        sys.exit(0 if table(args[1:]) else 1)
    ok = [report(p) for p in args]
    sys.exit(0 if all(ok) and ok else 1)
