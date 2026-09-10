# TODO

`docs/DOD.md` says what done means. This says what is left, in dependency order.
Codes in brackets are the DoD items a task closes. Every one of the 43 open DoD
items appears somewhere below; if a task is not here, it is not in scope.

Times are estimates for one person. If a day overruns, go to `docs/SCOPE.md` and
cut from the bottom — do not extend the day.

---

## Closed on D1 — Thu 10 Sep

Setup, recorder and analyzer are done and evidenced. 12 DoD items ticked.

- Environment: `.venv/`, websockets 17.1, fastapi 0.141.1 on Python 3.14.6.
  `additional_headers` confirmed present; `extra_headers` no longer exists in
  this version, so the CLAUDE.md fallback note is now a trap, not a rescue.
- Key live, `.env` git-ignored, never echoed. **[R5]**
- Recorder: bounded wait after `EndOfStream`, `Error` stops the sender,
  drift reported at the last chunk. Deadline pacing, drift +0.0%.
  **[R1, R2, R3, R4]**
- Analyzer: audio-clock emission lag, best-overlap binding, one observation per
  message per slot, post-final metric, speculative-emission metric, `--table`,
  non-zero exit on bad runs, determinism. **[A1–A8]**
- `docs/METHOD.md` extended: two clocks, alignment rules, five quantities,
  cold-start and speculative-emission findings.
- `LICENSE`, `make results`, SCOPE.md weekday labels corrected.

**What the 6.8 s smoke clip already showed.**

> ⚠️ These came from **macOS `say` TTS**, not from a recorded voice, on a
> throwaway clip that is not in `clips/` and whose run is not in `runs/`. They
> are shape, not evidence. **None of them may appear in the README, the website,
> the deck or the video.** Every published number comes from the corpus via
> `make results`. This table exists to tell you what to expect, and to be
> deleted once the real sweep replaces it.

| Finding (TTS, not evidence) | Number |
|---|---|
| Words revised, clean TTS audio | 3/20 (15.0%) |
| Text changed after `AddTranscript` | 0/20 (0.0%) |
| Risk window, first text → finalised | p95 1.398 s |
| Speculative emission — text before the word finished | 1/20, −0.248 s |
| Cold-start first emission vs warm | `audio_pos` 3.072 s vs 0.512 s |

If the corpus reproduces `after final = 0%`, that is the answer to the sweep's
headline question, and it moves the story: the danger is not that finals change,
it is how long a word sits visible and revisable before becoming one. That is the
**risk window**, and it is what the sidecar sells. Do not pre-write that
conclusion into the deck before the sweep says so.

---

## D1 — closed, Thu 10 Sep

Corpus recorded and swept: 10 clips, 40 runs (all four `max_delay` values),
zero failed runs, zero drift warnings. **[C1, C2, R7]**

**Gate D1 passed.** `runs/08_md1.0.jsonl`, span `(5.6, 5.76)`: a partial at
`audio_pos` 6.4s reads `"now"`; the `AddTranscript` at 6.784s reads `"not"`.
Same audio interval, different meaning. **[C3]**

README and `docs/METHOD.md` filled from `make results` — no longer `TBD`.
**[C4]** Headline: **0.0% of words changed after their `AddTranscript`**,
across 1,227 words at all four `max_delay` settings. Settling p99 scales
3.5x from `max_delay=0.7` to `4.0` (0.985s → 3.441s) — that scaling is the
sweep's actual result.

**Correctness fix, found while building the website (below): `analyzer.track()`
had no way to detect a word the engine hypothesised and then fully retracted
(not revised - deleted, with no replacement). Confirmed against
`metadata.transcript` on a real run (clip 09: a partial reads "Recording", the
next `AddTranscript` reports `""`). Fixed by dropping any unlocked slot once
processing's frontier has moved past its span without re-touching it. Word
counts dropped ~1-3% per bucket (phantom words removed); the 0.0%
after-final headline was unaffected. All numbers above are post-fix.

**Two things to fix, not blocking, before D4:**

- [ ] Clips 05 and 08 are 9.0s and 9.1s — short of the 20–60s target in
      `clips/SCRIPT.md`. Re-record both longer if there's time; not required,
      the corpus already clears C1's 8-clip minimum. **[C1 follow-up]**
- [x] Clips 07 and 08 transcribed with heavy WER on their targeted contrast —
      see `docs/METHOD.md` threats to validity. Neither is a clean demo
      candidate. Checked clip 01 (the clip designed for the flip): it never
      mis-hears `someone` as `no one` — no usable flip there either.
      **Best candidate found: clip 09, span (4.76, 4.96), `"trying"` →
      `"trapped"` at `audio_pos` 5.376s → 5.76s.** Not the scripted flip and
      not a clean transcript around it, but a real, dramatic, dispatch-relevant
      single-word revision — closest thing to the cold open PITCH.md wants.
      Confirm this is usable on video (zoom to the one word, not the full
      line) before locking it as the U3 demo clip.
- [x] Corpus committed: `8a62e5a`.
- [x] Public repo created and wired as origin: github.com/adindamochamad/settle
      **[X1]**

## D2 — Fri 11 Sep · Gate: the chart exists as an image file

The analyzer work planned for today is already done, so D2 is lighter than the
schedule assumed. Use the slack to start D3 early, not to polish.

**Sweep (~2 h, mostly waiting)**

- [x] Warm-up is built into `make sweepall` and its first run is discarded.
      Cold start measured 3.072 s to first text against 0.512 s warm — six
      times — and would otherwise skew emission lag.
- [x] `make sweepall` run on D1 — 40 runs, all committed.
- [x] No run had drift over 5% or an `Error` — nothing to discard.
- [x] Exercised the error path with a deliberately wrong key, 4 attempts.
      Found a real gap doing it: the server fails two different ways - a
      JSON `Error` message (handled), or a protocol-level WebSocket close
      that raised unhandled and wrote nothing to the run file at all.
      `recorder.py` restructured (connection lifecycle now wrapped in
      `try`/`except websockets.exceptions.ConnectionClosed`) so both paths
      log a clean Error record and exit 1. Re-verified a normal successful
      recording still works afterward. **[R6]**
- [x] Every surviving run committed. **[X3]**

**Chart — done, Thu 10 Sep**

- [x] `chart.py`, SVG from the standard library, no plotting dependency added.
      `make chart` regenerates `web/chart.svg` from `runs/` in one command.
      Embedded in README. **[G1, G2]**
- [x] p50 and p95 plotted against `max_delay`. p50 is flat at 0.000s at every
      setting (median word never revises); p95 is the curve that matters —
      0.721s → 2.796s, a 3.9x range. A risk-window series is still open, see
      below.
- [x] Axis units, per-point and total `n`, "wall clock" named on the y-axis
      and in the caption. **[G3]**
- [x] Checked at 800px and 390px (phone width) via `qlmanage` thumbnails —
      vector text stays sharp at both. **[G4]**
- [ ] Consider adding the risk window (first text → finalised) as a third
      series. It is the number the sidecar sells and isn't on the chart yet —
      not blocking, worth 15 minutes before D3.

**Numbers — done, Thu 10 Sep**

- [x] `make results` pasted into the README table. **[X2]**
- [x] `docs/METHOD.md` threats to validity updated to the actual corpus.
      **[C4]**
- [x] τ picked: 0.774s, settling p95 at `max_delay=1.0`. **[feeds S3]**

> **Abort check, D2 night.** No chart? `docs/SCOPE.md` says drop the sidecar and
> ship the instrument plus the curve. Decide tonight, not on D3.

## D3 — Sat 12 Sep · Gate: a public URL

**Build the static path first (~2 h).** It is the D4 abort path, so building it
as the primary means the fallback is already done and a live sidecar is upside
rather than risk. No backend, no key, nothing to fall over while a judge watches.

- [x] `web/` — three sections, static, replaying a committed run client-side:
      the flip, the curve, what settling time is. **[W2, W3]**
- [x] Every number on the page from `analyzer.py --table`. **[W4]**
- [x] Published to GitHub Pages, verified live via curl (not localhost).
      **Gate D3 passed.** **[W1]**
      **https://adindamochamad.github.io/settle/**
- [ ] W5 checked at 390px/800px via thumbnail rendering, not on an actual
      physical phone yet — open the live URL on a real phone once to confirm
      before D4.

**Found and fixed while testing the replay in a real browser:** `analyzer.py`
had no way to detect a word the engine hypothesised and then fully retracted
(deleted, not revised). Fixed in both `analyzer.py` and the site's JS port —
see the 10 Sep commit for the full story. All published numbers are post-fix.

**Sidecar — done, Thu 10 Sep**

- [x] Replaced the `NotImplementedError`. Hub owns one replay task, fanned out
      to `/ws/naive` and `/ws/settled` via per-subscriber queues, backfilled
      from a run log so a client connecting even slightly late still gets the
      full sequence - closes a real race, found by testing three demo runs in
      a row and the second one hanging. **[S2]** (S1 is scoped to replay only
      this pass - see the "not built" note below.)
- [x] Hold policy: release a token once unchanged for τ. Imports
      `analyzer.apply()` (built on `overlap()`); no second aligner. **[S5]**
- [x] τ settable via `?tau=` on connect; default 0.774s = settling p95 at
      `max_delay=1.0`, in README. **[S3]**
- [x] Speculative emission decision: no special-case handling added. τ is
      defined purely on text-stability (`t_last_change`, per docs/METHOD.md),
      and a word's span drifting while its text stays constant is, by that
      same definition, a settled word regardless of span movement - engineering
      around it would contradict the metric the sidecar is built to honor. The
      real risk this note was pointing at is retraction, not speculative
      emission, and that one IS handled (`settled_stream()` cancels a pending
      release the moment its slot is dropped) and measured (S4).
- [x] Replay source, from a committed run. **Live source not built this
      pass** - a deliberate scope call (see the open decision below), not an
      oversight. **[S6 partial]**
- [x] Residual retraction rate and added latency per token, measured over the
      corpus via `sidecar.py`'s own `simulate_settled()`/`measure()` (the
      identical policy, run at logical speed instead of real time) and
      `make measure`. 4.2% retraction / 0.774s p50 added latency at md=1.0
      (where τ was calibrated); 13.9% / varies across all four max_delay
      pooled - τ doesn't transfer across max_delay settings, see README.
      **[S4, S7]**
- [x] Speculative emission: decided no special handling - see the resolved
      item above, settling is text-only by definition.

**Consumers — done, Thu 10 Sep**

- [x] Replaced the `NotImplementedError`. `Consumer` class, shared
      `tier_for()`, append-only timestamped `.actions`. **[U1, U2, U4]**
- [x] Canonical demo clip locked: `runs/09_md1.0.jsonl`. A misheard partial
      ("working fire me") makes naive fire `ELEVATED - FIRE` - a false alarm -
      before correcting through `STANDARD` to the true `CRITICAL - RESCUE`;
      settled, τ=0.774s, only ever shows the correct tier. Verified
      reproducible across 4 separate live runs. In README. **[U3]**
- [x] `make demo` - no arguments, starts the sidecar, runs both consumers,
      tears it down. Tested from a cold start (port not already bound).

## D4 — Sun 13 Sep · Feature freeze 23:59

Nothing new starts today.

- [ ] Morning: finish D3 slippage only.
- [ ] Run the full demo three times cleanly, end to end. Three, not one.
- [ ] Walk `docs/DOD.md` top to bottom. Tick or formally cut every box. An
      untouched box is not a cut.
- [ ] Audit every number in README, website and deck against the evidence rule.
      Anything you cannot trace to a run file in under a minute gets deleted or
      reverts to `TBD`.
- [ ] `git log -p | grep -i` for the key — history, not just the tree. **[X5]**
- [ ] Clean-clone test in a fresh directory: install, `make analyze`, confirm the
      README table reproduces. **[X4]**
- [ ] Deck: PDF, ≤ 12 slides, charts reused as the same image files, no number
      absent from the README. **[P1, P2, P3]**
- [ ] Write the video script word for word. Improvising on D5 costs takes.
- [ ] **23:59 — freeze.** Bug fixes only after this.

## D5 — Mon 14 Sep · Every asset recorded

- [ ] Cold open first, while you are freshest. It decides whether the rest is
      watched.
- [ ] Screen recordings at the site's real resolution. No phone footage.
- [ ] The side-by-side block, 90 s or more, uncut. Do not shorten it to make room
      for anything else. **[V2]**
- [ ] Chart walkthrough with word counts visible on screen.
- [ ] Closing line: *the team that measured how long "final" isn't final.*
- [ ] Edit, caption, export MP4 under 5:00. **[V1, V3]**
- [ ] Play back on laptop speakers, and again muted with captions. Both.
      **[V3, V4]**
- [ ] **No footage may be left to shoot at the end of today.**

## D6 — Tue 15 – Wed 16 Sep · Submit

- [ ] Upload the video; open it in an incognito window. **[V5]**
- [ ] Fill all four lablab fields. **[Z1]**
- [ ] Open every link logged out: prototype URL, video, deck, repo. **[Z2]**
- [ ] Submit with 6 hours of buffer minimum. **[Z3]**
- [ ] Only then, if time remains, improve anything.

## Any time — the repo

- [x] Public GitHub repo created and pushed:
      github.com/adindamochamad/settle **[X1]**

---

## Open decisions

| # | Decision | Status |
|---|---|---|
| 1 | Chart library | Hand-rolled SVG from the stdlib. Keeps the three-dependency rule; SVG is what the site needs. matplotlib as a time-boxed fallback. |
| 2 | Public URL shape | Static GitHub Pages replaying a committed run. It is the abort path already — build it as the primary. |
| 3 | Pacing drift | **Settled 10 Sep: deadline scheduling.** The original recommendation here rested on a drift figure that turned out to be a measurement bug. Measured A/B: fixed sleep +1.4%, deadline +0.0%, and it cannot send faster than real time. |
| 4 | This file in the repo | `docs/DOD.md` is worth showing a judge. This file is internal; gitignore it if the repo should stay lean. |
| 5 | τ default | **Settled: 0.774s** — settling p95 at `max_delay=1.0`, from the real corpus. |
| 6 | Sidecar upstream source | **Settled 10 Sep: replay only.** Live would mean adding reusable connection logic to recorder.py mid-feature, risking the one file CLAUDE.md rule 2 protects most. `docs/SCOPE.md` already treats replay-only as complete, not a cut corner. Live is a real, scoped follow-up if time allows: pull `websockets.connect(...)` out of `record()` into something both files call, without touching the pacing loop. |
