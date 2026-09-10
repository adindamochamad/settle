#!/usr/bin/env python3
"""SETTLE consumers - two mock dispatch consumers reading the sidecar's two
streams, tiering on keywords alone.

    uvicorn sidecar:app --port 8000 &
    python consumers.py
    # or: make demo

Each consumer keeps its own reconstructed line (released words, sorted by
audio position - the same left-to-right reassembly web/index.html does) and
re-tiers on every update. The naive consumer acts on every word the instant
the engine says it; the settled consumer only sees a word once the sidecar
has held it for tau. Both log every tier CHANGE, timestamped, the moment it
happens - once logged, that entry is never edited, matching what a real
dispatch console would already have sent.

Tiering is deliberately trivial: keyword match against the reconstructed
line, first rule that hits wins, no model anywhere. The point of the demo is
the retraction, not the classifier - see docs/DOD.md U4.
"""
import asyncio
import json
import sys
import time

import websockets

TIER_RULES = [
    (("trapped", "entrapped"), "CRITICAL - RESCUE"),
    (("not breathing", "unresponsive", "no pulse"), "CRITICAL - MEDICAL"),
    (("fire", "smoke", "alarm"), "ELEVATED - FIRE"),
    ((), "STANDARD"),  # default: always matches, must stay last
]


def tier_for(line):
    """Keyword match only - see the module docstring and docs/DOD.md U4."""
    for keywords, name in TIER_RULES:
        if not keywords or any(k in line for k in keywords):
            return name
    return "STANDARD"


class Consumer:
    """One dispatch console, reading one of the sidecar's two streams."""

    def __init__(self, label):
        self.label = label
        self.slots = []  # [(start, end, text)], kept sorted for left-to-right reassembly
        self.tier = None
        self.actions = []  # [(wall_clock_t, tier, line)] - append-only, never edited

    def line(self):
        return " ".join(text for _, _, text in sorted(self.slots))

    def apply(self, event):
        span = (event["start"], event["end"])
        for i, (s, e, _t) in enumerate(self.slots):
            if (s, e) == span:
                self.slots[i] = (*span, event["text"])
                break
        else:
            self.slots.append((*span, event["text"]))
        line = self.line()
        new_tier = tier_for(line)
        if new_tier != self.tier:
            self.tier = new_tier
            self.actions.append((time.time(), new_tier, line))
            print(f"[{self.label:<7}] {new_tier:<20} <- {line!r}")


async def run_consumer(uri, label):
    c = Consumer(label)
    async with websockets.connect(uri) as ws:
        async for raw in ws:
            event = json.loads(raw)
            if event.get("done"):
                break
            c.apply(event)
    return c


async def main(sidecar="ws://localhost:8000", tau=None):
    settled_uri = f"{sidecar}/ws/settled" + (f"?tau={tau}" if tau else "")
    naive, settled = await asyncio.gather(
        run_consumer(f"{sidecar}/ws/naive", "naive"),
        run_consumer(settled_uri, "settled"),
    )

    print()
    print(f"naive final tier:   {naive.tier}")
    print(f"settled final tier: {settled.tier}")

    naive_tiers = {t for _, t, _ in naive.actions}
    settled_tiers = {t for _, t, _ in settled.actions}
    wrong = naive_tiers - settled_tiers
    if wrong:
        print(f"\nnaive fired a tier settled never did: {sorted(wrong)}")
        print("this is the demo: naive acted on a hypothesis the engine")
        print("went on to retract before the settled stream ever saw it.")
        return 0
    print("\nno tier divergence on this run - naive and settled agreed "
          "throughout. Not every clip produces one; see docs/METHOD.md.")
    return 1


if __name__ == "__main__":
    sidecar = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8000"
    sys.exit(asyncio.run(main(sidecar)))
