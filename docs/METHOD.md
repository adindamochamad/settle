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

Two implementation choices follow from that rule and are stated because they
change the numbers:

- An observation binds to the **best** overlapping word, not the first one that
  clears 50%. Adjacent short words (`is in`, `to two`) otherwise capture each
  other and their revisions get attributed to the wrong slot.
- A word's interval **follows its most recent observation**. The engine nudges
  timings slightly between revisions; taking the union of every interval seen
  instead lets one word grow until it swallows its neighbours.

## Two clocks

The recorder logs each message against both a **wall clock** (`t`, seconds since
the session opened) and an **audio clock** (`audio_pos`, seconds of audio sent
when the message arrived). They are not interchangeable and every quantity below
names the one it uses.

The wall clock leads the audio clock by the connection setup plus whatever
pacing drift has accumulated. A *duration* measured on the wall clock is
unaffected, because the offset cancels in the subtraction. A quantity that
compares a message against a position in the audio is not, and must use the
audio clock or it silently reports the TLS handshake as engine latency.

Two things make up that offset, and they are handled differently.

**Connection setup** — DNS, TLS and the `StartRecognition` round trip — is
reported, never corrected. It is real, it varies per run, and it is why emission
lag is computed on the audio clock: `audio_pos` starts at the first chunk, so
setup cannot leak into it.

**Pacing drift** is corrected at the source. The sender sleeps until an absolute
deadline, a fixed `CHUNK_MS` step from the first chunk, with the sleep clamped at
zero. Chunk *k* therefore never leaves before `t0 + k·CHUNK_MS`: the recorder
cannot run faster than real time, it only stops per-iteration overhead
accumulating. Measured on one 6.8 s clip: a plain fixed sleep drifts **+1.4%**,
deadline scheduling **+0.0%**. Uncorrected drift inflates every wall-clock
settling time by its own proportion, and grows with clip length.

Whatever drift remains is printed at the end of every run. Above 5% the run is
void — see `docs/DOD.md` R4.

## The quantities

For each word *w* in the final transcript, over one run:

| Quantity | Clock | Definition |
|---|---|---|
| **emission lag** | audio | `audio_pos_first(w) − end_time(w)` — how much further the audio had to run before any text for *w* appeared |
| **settling time** | wall | `t_last_change(w) − t_first(w)` — how long the text at that interval kept changing |
| **risk window** | wall | `t_final(w) − t_first(w)` — how long *w* was visible to a consumer while still revisable |
| **revision count** | — | number of distinct texts observed at that interval |
| **revised after final** | — | whether the text at that interval ever differed from what the first `AddTranscript` reported |

Emission lag can go **negative**, and that is a result rather than a fault.
`end_time(w)` is the word's interval as finally settled. The engine sometimes
publishes a hypothesis for an interval and then extends that interval as more
audio arrives, so the first text for *w* can appear while *w* is still being
spoken. Measured on a 6.8 s clip: 1 of 20 words, at −0.248 s — text first
appeared at `audio_pos` 0.512 s for a hypothesis spanning `(0.0, 0.2)`, which
settled as `(0.0, 0.76)`.

The analyzer reports these separately as **speculative** emissions. They matter
to the sidecar: a token can exist before the audio that decides it does.

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
- **Cold start.** The first session opened on a key emits its first text much
  later than subsequent ones: `audio_pos` 3.072 s on a cold session against
  0.512 s warm, on the same clip. Emission lag from a cold first run is not
  comparable to the rest. `make sweepall` discards a warm-up run before the
  corpus for this reason.
- **Small corpus.** 10 clips, ~2.0 minutes of audio, 303 final words, one
  speaker (the author), recorded 10 Sep 2026. Enough to establish the
  phenomenon and its shape against `max_delay`, not enough for a confidence
  interval. Reported as percentiles over words, with the word count always
  shown.
- **Two clips transcribed with heavy word error rate.** Clips 07 and 08 were
  written to probe homophone and self-correction pressure ("two two" vs "22",
  "nobody" vs "somebody") and instead produced substantial misrecognition
  unrelated to the targeted contrast — e.g. "vehicle" heard as "Fakel" and
  "Collection". Their settling and revision numbers are included in the pooled
  table because they are real engine behaviour, not excluded, but they should
  not be read as clean examples of the specific phenomenon they were designed
  to isolate. The D1 gate revision ("now" → "not", clip 08) came from this
  noisier pair, not from the cleaner clips.
- **One engine.** Only Speechmatics is measured. No claim is made about any
  other vendor; the harness is engine-agnostic but has not been run elsewhere.
- **Synthetic dispatch consumer.** The downstream cost of a retraction is
  modelled, not observed in a production system.
