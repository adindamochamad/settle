# How settling time is measured

This document exists so a judge can check the number instead of trusting it.

## The gap

ASR vendors publish two numbers: **word error rate** (was the final text right?)
and **latency** (how fast did text arrive?). Both describe endpoints. Neither
describes the interval in between, where the text is visible, plausible, and
still changing.

For anything that *acts* on a stream — an agent, a command handler, a dispatch
system — that interval is the only one that matters. It has no published number.
We call it **settling time**, after the control-theory quantity: the time a step
response takes to enter and remain within a tolerance band around its final
value.

## What the recorder captures

`recorder.py` streams a fixed audio file to Speechmatics at real-time pace and
appends every inbound message to JSONL with the wall-clock offset at which it
arrived. It stores the raw payload without modification. It makes no
interpretation, so a disagreement about method can always be re-settled against
the same recordings.

Real-time pacing is load-bearing. Sending the file as fast as the socket allows
would compress the revision behaviour we are trying to observe and produce
numbers that describe nothing.

## Aligning words across revisions

A partial transcript is not an append-only prefix. Words are inserted, deleted
and rewritten mid-stream, so the *n*-th word of one revision is frequently not
the *n*-th word of the next.

Words are therefore matched by **audio-interval overlap**. Two observed words
refer to the same spoken word when their `[start_time, end_time]` intervals
overlap by at least 50% of the shorter interval. Index-based matching is wrong
here in exactly the cases the project studies.

## The three quantities

For each word *w* in the final transcript, over one run:

| Quantity | Definition |
|---|---|
| **emission lag** | `t_first(w) − end_time(w)` — how long after the word was spoken before any text for it appeared |
| **settling time** | `t_last_change(w) − t_first(w)` — how long the text at that interval kept changing |
| **revision count** | number of distinct texts observed at that interval |

`t_first(w)` is the arrival time of the first message reporting text at *w*'s
interval. `t_last_change(w)` is the arrival time of the last message at which
that text differed from the message before it. A word never revised has a
settling time of zero.

**Settled at tolerance τ**: *w* is settled at time `t_last_change(w) + τ`. τ is
the dial the sidecar exposes. Holding a token for τ trades τ seconds of latency
for the retraction risk that remains after it.

## The sweep

`max_delay` (0.7–4 s) is Speechmatics' own control over when a final is emitted.
Every clip is recorded at `max_delay` ∈ {0.7, 1.0, 2.0, 4.0} so settling time can
be plotted against it.

The question the sweep answers, which is not answered anywhere in the
documentation:

> **Does a transcript marked final at `max_delay = 4` actually stop changing?**

Both possible answers are useful. If finals are still revised, the sweep has
measured a real gap in a real product. If they are not, the sweep produces a
data-backed tuning recommendation and bounds the region where a sidecar is
needed at all.

## Threats to validity

Stated up front rather than waiting to be asked.

- **Single speaker, single accent.** All clips are one voice. Settling behaviour
  almost certainly varies with speaker, accent and noise profile; the absolute
  numbers here describe this speaker only. The *shape* against `max_delay` is
  the transferable result.
- **Small corpus.** Roughly ten clips. Enough to establish the phenomenon, not
  enough for a confidence interval. Reported as percentiles over words, with the
  word count always shown.
- **One engine.** Only Speechmatics is measured. No claim is made about any
  other vendor; the harness is engine-agnostic but has not been run elsewhere.
- **Synthetic dispatch consumer.** The downstream cost of a retraction is
  modelled, not observed in a production system.
