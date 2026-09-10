#!/usr/bin/env python3
"""SETTLE sidecar - one upstream feed in, two WebSocket streams out.

    uvicorn sidecar:app --reload --port 8000

    ws://localhost:8000/ws/naive             every word, the instant it appears
    ws://localhost:8000/ws/settled?tau=0.774  a word, held until stable for tau

Source is a committed JSONL run, replayed at the pace it was recorded -
not a live Speechmatics connection. CLAUDE.md rule 4 develops against
replayed JSONL for exactly this reason, and docs/SCOPE.md already treats a
replay-only sidecar as a complete, sanctioned outcome ("on video the
difference is invisible"). A live source is a real extension point (see
docs/TODO.md) but is not built here - it would need recorder.py's connection
logic pulled into something reusable, and that file's pacing loop is the one
thing in this project rule 2 says not to touch under time pressure.

Both streams read the SAME upstream feed (SETTLE_SOURCE, default below) -
one asyncio task owns it, matching CLAUDE.md rule 3's "one connection,
fanned out to two consumers" even in replay form. Word alignment reuses
analyzer.apply() - see docs/DOD.md S5. Do not write a second aligner here.
"""
import asyncio
import json
import os
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

import analyzer

SOURCE = os.environ.get("SETTLE_SOURCE", "runs/09_md1.0.jsonl")
TAU_DEFAULT = 0.774  # settling p95 at max_delay=1.0, see README results table

app = FastAPI()


class Hub:
    """Owns the single upstream feed; fans its per-message word lists out to
    every subscriber. Starts on the first subscriber, not at import time, so
    `uvicorn sidecar:app` doesn't replay a run nobody is watching.

    Every published event is kept in self.log for the current run. A new
    subscriber is handed the log so far before it starts waiting on live
    events - without this, two WebSocket clients connecting even a few
    milliseconds apart could see different prefixes of the run, which is
    exactly the byte-identical-input guarantee (docs/DOD.md S2) this class
    exists to provide. Relying on both clients happening to connect in the
    same event-loop tick would be a race, not a guarantee.
    """
    def __init__(self, source):
        self.source = source
        self.subscribers = []
        self.log = []
        self.task = None

    def subscribe(self):
        # A finished task means the previous replay ran to completion (its
        # last act is publishing {"done": True}) - a subscriber arriving
        # after that starts a fresh replay rather than waiting on a task
        # that will never publish again. Concurrent subscribers arriving
        # while a replay is still running share it, per CLAUDE.md rule 3.
        if self.task is None or self.task.done():
            self.subscribers = []
            self.log = []
            self.task = asyncio.create_task(self._run())
        q = asyncio.Queue()
        for event in self.log:
            q.put_nowait(event)
        self.subscribers.append(q)
        return q

    def unsubscribe(self, q):
        if q in self.subscribers:
            self.subscribers.remove(q)

    async def _publish(self, event):
        self.log.append(event)
        for q in self.subscribers:
            await q.put(event)

    async def _run(self):
        records = analyzer.load(self.source)
        t0 = None
        for rec in records:
            if rec["kind"] not in ("AddPartialTranscript", "AddTranscript"):
                continue
            rec_words = analyzer.words(rec["payload"])
            if not rec_words:
                continue
            if t0 is None:
                t0 = rec["t"]
            else:
                await asyncio.sleep(max(0.0, rec["t"] - t0))
                t0 = rec["t"]
            await self._publish({
                "words": rec_words,
                "final": rec["kind"] == "AddTranscript",
            })
        await self._publish({"done": True})


hub = Hub(SOURCE)


async def naive_stream(websocket):
    q = hub.subscribe()
    slots = []
    try:
        while True:
            event = await q.get()
            if event.get("done"):
                await websocket.send_json({"done": True})
                return
            slots, _touched, changed, _dropped = analyzer.apply(
                slots, event["words"], event["final"])
            for i in changed:
                slot = slots[i]
                await websocket.send_json({
                    "text": slot["text"], "start": slot["span"][0], "end": slot["span"][1],
                    "sent_at": time.time(),
                })
    finally:
        hub.unsubscribe(q)


async def settled_stream(websocket, tau):
    q = hub.subscribe()
    slots = []
    pending = {}  # slot index -> asyncio.Task, cancelled and replaced on every revision
    stats = {"released": 0, "retracted": 0}  # exposed for the S4 measurement below

    async def release(idx, text, start, end):
        await asyncio.sleep(tau)
        await websocket.send_json({
            "text": text, "start": start, "end": end, "sent_at": time.time(),
        })
        stats["released"] += 1
        pending.pop(idx, None)

    try:
        while True:
            event = await q.get()
            if event.get("done"):
                # Let anything already in flight land before closing out.
                if pending:
                    await asyncio.gather(*pending.values(), return_exceptions=True)
                await websocket.send_json({"done": True})
                return
            slots, _touched, changed, dropped = analyzer.apply(
                slots, event["words"], event["final"])
            # A slot the engine retracted can't be announced once it's
            # stable - it no longer exists. Cancel any release still
            # waiting out its tau for one of these. This doesn't make the
            # settled stream immune to retraction (a token can still be
            # *released* before the message that retracts it arrives -
            # measured honestly in docs/DOD.md S4, not hidden here), only
            # to the case where retraction beats the tau timer.
            for i in dropped:
                if i in pending:
                    pending.pop(i).cancel()
                    stats["retracted"] += 1
            for i in changed:
                if i in pending:
                    pending[i].cancel()
                slot = slots[i]
                pending[i] = asyncio.create_task(
                    release(i, slot["text"], slot["span"][0], slot["span"][1]))
    finally:
        hub.unsubscribe(q)
        for t in pending.values():
            t.cancel()


@app.websocket("/ws/naive")
async def ws_naive(websocket: WebSocket):
    await websocket.accept()
    try:
        await naive_stream(websocket)
    except WebSocketDisconnect:
        pass


@app.websocket("/ws/settled")
async def ws_settled(websocket: WebSocket, tau: float = TAU_DEFAULT):
    await websocket.accept()
    try:
        await settled_stream(websocket, tau)
    except WebSocketDisconnect:
        pass


@app.get("/")
async def index():
    return {"source": SOURCE, "tau_default": TAU_DEFAULT,
            "endpoints": ["/ws/naive", "/ws/settled?tau=<seconds>"]}



def simulate_settled(records, tau):
    """What the settled stream would announce, and when, for one committed
    run - the same hold-policy decision as settled_stream() above (schedule
    a release at last-change-time + tau, cancel and reschedule on any further
    change, cancel outright if the slot is retracted before the deadline),
    expressed as a pure function over logical message time instead of real
    asyncio.sleep. Used to measure S4/S7 across the whole corpus in seconds
    rather than real minutes; settled_stream() is the live version of the
    identical rule, not a second policy.

    A pending release becomes "due" only once a later message's arrival
    time reaches its deadline - the same race a real timer has against a
    same-instant retraction, just checked at message granularity rather than
    continuously. Fine for corpus-level percentiles; not a claim of
    millisecond timer precision.

    Returns [(release_t, text, start, end)], sorted by release_t, on the
    same wall clock as the run's own "t" field.
    """
    slots = []
    pending = {}  # slot index -> (deadline, text, start, end)
    released = []
    for rec in records:
        if rec["kind"] not in ("AddPartialTranscript", "AddTranscript"):
            continue
        rec_words = analyzer.words(rec["payload"])
        if not rec_words:
            continue
        t = rec["t"]
        due = [i for i, p in pending.items() if p[0] <= t]
        for i in due:
            released.append(pending.pop(i))
        slots, _touched, changed, dropped = analyzer.apply(
            slots, rec_words, rec["kind"] == "AddTranscript")
        for i in dropped:
            pending.pop(i, None)
        for i in changed:
            slot = slots[i]
            pending[i] = (t + tau, slot["text"], slot["span"][0], slot["span"][1])
    released.extend(pending.values())  # still waiting when the run ended - fires at its deadline
    return sorted(released)


def measure(paths, tau):
    """S4 (residual retraction rate) and S7 (added latency per released
    token) over a corpus, at one tau.

    A released token counts as retracted if no slot in the run's true final
    answer (analyzer.track()) overlaps its span by >=50% with matching text -
    the settled stream announced something that never became part of what
    actually happened, because retraction beat the tau timer (settled_stream
    cancels a pending release when it can - see its own comment - this counts
    the cases where it can't).

    Added latency, for a token that was NOT retracted, is (settled release
    time - naive's own first announcement of that exact text at that span) -
    how much later a settled-stream viewer saw it than a naive-stream viewer
    did.
    """
    total = 0
    retracted = 0
    added = []
    for path in paths:
        records = analyzer.load(path)
        truth = analyzer.track(records)
        released = simulate_settled(records, tau)

        naive_first = []  # (span, text, t) for every text a slot ever showed
        slots = []
        for rec in records:
            if rec["kind"] not in ("AddPartialTranscript", "AddTranscript"):
                continue
            rw = analyzer.words(rec["payload"])
            if not rw:
                continue
            slots, _touched, changed, _dropped = analyzer.apply(
                slots, rw, rec["kind"] == "AddTranscript")
            for i in changed:
                naive_first.append((slots[i]["span"], slots[i]["text"], rec["t"]))

        for release_t, text, start, end in released:
            total += 1
            best, score = None, 0.0
            for s in truth:
                sc = analyzer.overlap(s["span"], (start, end))
                if sc > score:
                    best, score = s, sc
            if best is None or score < 0.5 or best["text"] != text:
                retracted += 1
                continue
            cands = [t for span, txt, t in naive_first
                     if txt == text and analyzer.overlap(span, (start, end)) >= 0.5]
            if cands:
                added.append(release_t - min(cands))
    return total, retracted, added


if __name__ == "__main__":
    import glob
    import sys

    tau = float(sys.argv[1]) if len(sys.argv) > 1 else TAU_DEFAULT
    paths = sys.argv[2:] or sorted(glob.glob("runs/*.jsonl"))
    total, retracted, added = measure(paths, tau)
    print(f"tau={tau}s  runs={len(paths)}  tokens released={total}")
    print(f"residual retraction rate: {retracted}/{total} ({100*retracted/total:.1f}%)")
    if added:
        print(f"added latency  p50={analyzer.pct(added,50):.3f}s  "
              f"p95={analyzer.pct(added,95):.3f}s  max={max(added):.3f}s")
