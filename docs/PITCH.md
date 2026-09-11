# Pitch video — 5 minutes, async

The remote track is judged on video. The first ten seconds decide whether the
rest is watched. No team introduction, no title card, no "hi, we are".

| Time | Content |
|---|---|
| 0:00–0:12 | **Cold open.** The locked demo clip plays (`runs/09_md1.0.jsonl` — see README "The demo"). A partial misheard as `working fire me` fires `ELEVATED - FIRE` on the naive console — a false alarm. Freeze on it, already sent, before the correction lands. |
| 0:12–0:40 | The gap: vendors publish WER and latency. Nobody publishes settling time. State the thesis in one sentence. |
| 0:40–1:10 | What settling time is — the control-theory step response and its tolerance band, 30 seconds, visual. |
| 1:10–2:50 | **The side-by-side demo, full run.** The largest block. Do not shorten this to make room for anything else. |
| 2:50–3:50 | The instrument: the measured curve, settling time against `max_delay`, real numbers with word counts shown. |
| 3:50–4:30 | The sidecar: one connection in, two streams out, how it drops into an existing pipeline. |
| 4:30–5:00 | Where it goes next. Close on the line below. |

**Closing line, for the judges' deliberation:**

> The team that measured how long "final" isn't final.

## Recording notes

- Shoot every take on D5. Re-shooting on D6 is how submissions get missed.
- Screen recordings at the site's real resolution; no phone-camera footage.
- Captions throughout — judges may watch muted.
- Run the demo three times cleanly before recording it once.

## Script

Word for word, per block. Every number here is re-verified against `runs/`
as of 11 Sep 2026 — re-check with `make results` and `make measure` before
recording if any run file changes after this is written. Screen directions
in *italics*, spoken lines plain.

### 0:00–0:12 — Cold open

*No narration. No title card. Screen recording of the live console
(consumers.py output, or a UI built on it) playing `runs/09_md1.0.jsonl`
through the sidecar. Let the audio play under it.*

*On screen, in order: naive console shows `"...working fire me"` then locks
red on `ELEVATED - FIRE`. Freeze the frame there for a full second.*

Caption overlay only: **"This is a real dispatch console. It just called in
a fire that isn't happening."**

*Hard cut to black.*

### 0:12–0:40 — The gap

**Every speech-to-text vendor publishes two numbers. Word error rate — was
the final text right. Latency — how fast did it arrive. Neither one
describes the seconds in between, where the text is visible, sounds
plausible, and is still changing. Nobody publishes that number. We call it
settling time. This is SETTLE.**

*Screen: title card, first and only one. "SETTLE" over the tagline.*

### 0:40–1:10 — What settling time is

**A word appears the moment the engine has a guess. That guess isn't always
the last one. Settling time is how long it keeps changing after it first
shows up. Hold it for a fixed window after its last change — we call that
window tau — and you know it's done moving.**

*Screen: the step-response diagram from web/index.html section 3 — word
spoken, first text, last change, finalised, the risk-window band.*

### 1:10–2:50 — The side-by-side demo, full run, uncut

*Screen: `web/console.html`, opened in a browser against a running
`make sidecar`/`make demo` - naive left, settled right, same clip playing on
both from the same upstream feed, the divider between them lighting up red
on DIVERGED. Let it run start to finish - this block is the demo, not a
summary of it. Minimal narration, three cues only, timed to the clip's own
real timestamps:*

**(≈0:03 into the clip) Same audio, both sides, right now.**

**(≈0:04, when naive fires ELEVATED - FIRE) Naive just dispatched a fire
response. Watch the right side.**

**(silence — let the settled side sit on "STANDARD" through the correction,
then land on CRITICAL - RESCUE once "trapped" locks in)**

**(clip ends) The settled side never saw the false alarm. Same input. One
extra second of patience.**

### 2:50–3:50 — The instrument: the measured curve

**Ten clips, one speaker, swept across four settings of the engine's own
max_delay control — 0.7 to 4 seconds. Settling time's 99th percentile runs
from 0.985 seconds at the tightest setting to 3.441 seconds at the loosest —
3.5 times longer. Every point on this curve is a committed recording; you
can check it yourself.**

*Screen: `web/chart.svg`, p50 flat at the bottom, p95 climbing. Zoom on the
`n=` labels — real word counts, not smoothed.*

**And the headline the documentation never answers: once Speechmatics calls
a word final, does it ever change again? Across 1,227 words, zero times.
Final really is final. The danger isn't that finals lie — it's how long a
word sits in the open, looking final, before it actually is one.**

### 3:50–4:30 — The sidecar

**SETTLE holds a word for tau — here, 0.774 seconds, the corpus's own 95th
percentile — before releasing it once. One upstream connection, two
consumers, byte-identical input. At the setting tau was calibrated for,
95.8% of what it releases matches what the engine eventually decided.
Naively, 33 to 45 percent of words get revised at least once before that —
use tau from the wrong max_delay setting, and the miss rate climbs, because
settling itself takes longer than tau accounts for. The dial has to match
its regime.**

*Screen: the sidecar architecture — one feed in, `/ws/naive` and
`/ws/settled` out — then the residual-retraction numbers on screen as text,
sourced from `make measure`.*

### 4:30–5:00 — Where it goes next

**Every place an agent or a pipeline acts on live transcription has this
same gap — voice assistants, meeting bots, call centers. SETTLE is the
instrument that measures it, and the sidecar that buys it back.**

*Screen: fade to the closing line, held for the last 3 seconds, no
voiceover under it.*

> **The team that measured how long "final" isn't final.**
