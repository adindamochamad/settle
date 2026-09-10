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
across 1,314 words at all four `max_delay` settings. Settling p99 scales
3.4x from `max_delay=0.7` to `4.0` (1.023s → 3.441s) — that scaling is the
sweep's actual result.

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
- [ ] Commit the corpus. Not yet done — ask before it happens.

## D2 — Fri 11 Sep · Gate: the chart exists as an image file

The analyzer work planned for today is already done, so D2 is lighter than the
schedule assumed. Use the slack to start D3 early, not to polish.

**Sweep (~2 h, mostly waiting)**

- [x] Warm-up is built into `make sweepall` and its first run is discarded.
      Cold start measured 3.072 s to first text against 0.512 s warm — six
      times — and would otherwise skew emission lag.
- [ ] `make sweepall` if not already run on D1. Sequential by design — the free
      tier allows two concurrent sessions and there is no reason to spend them.
- [ ] Discard and re-record any run with drift over 5%, or with `Error` in it.
- [ ] Exercise the error path once on purpose — run with a deliberately wrong
      key and confirm the `Error` is in the JSONL and the exit code is 1. It has
      never actually fired. **[R6]**
- [ ] Commit every surviving run. They are the evidence, not build output.
      **[X3]**

**Chart (~90 min)**

- [ ] `chart.py`, SVG from the standard library — keeps the three-dependency
      rule, and SVG is what the website wants anyway. matplotlib only as a
      time-boxed fallback. **[G1, G2]**
- [ ] Plot settling p50 and p95 against `max_delay`. Consider a second series
      for the risk window; that is the number the sidecar argument rests on.
      **[G1]**
- [ ] Axis units, `n` on the figure, clock named in the caption. **[G3]**
- [ ] Check at 1080p and at phone width. **[G4]**

**Numbers (~30 min)**

- [ ] `make results` → paste into the README table. Never type it. **[X2]**
- [ ] Update METHOD.md threats to validity with the corpus as recorded: clip
      count, total audio minutes, total words, one speaker. **[C4]**
- [ ] Pick τ from the measured distribution and write down the percentile.
      Settling p95 is the defensible default. **[feeds S3]**

> **Abort check, D2 night.** No chart? `docs/SCOPE.md` says drop the sidecar and
> ship the instrument plus the curve. Decide tonight, not on D3.

## D3 — Sat 12 Sep · Gate: a public URL

**Build the static path first (~2 h).** It is the D4 abort path, so building it
as the primary means the fallback is already done and a live sidecar is upside
rather than risk. No backend, no key, nothing to fall over while a judge watches.

- [ ] `web/` — three sections, static, replaying a committed run client-side:
      the flip, the curve, what settling time is. Not four sections. **[W2, W3]**
- [ ] Every number on the page from `analyzer.py --table`. **[W4]**
- [ ] Publish to GitHub Pages. Open it from a phone on mobile data — not
      localhost, not this machine. **Gate D3.** **[W1, W5]**

**Sidecar (~3 h)**

- [ ] Replace the `NotImplementedError`. One upstream connection, fanned out to
      `/ws/naive` and `/ws/settled`, byte-identical input to both. **[S1, S2]**
- [ ] Hold policy: release a token once its text has been unchanged for τ.
      Import `analyzer.overlaps()`; a second aligner is a failure. **[S5]**
- [ ] τ settable at connect time, default from D2's measurement, percentile
      recorded in the README. **[S3]**
- [ ] Handle speculative emission: a word's interval can still be growing when
      its text looks stable. Releasing on a span that is still extending is the
      one way this policy can be wrong on its own terms. Decide the rule and
      write it down.
- [ ] JSONL replay source alongside the live source. **[S6]**
- [ ] Measure residual retraction rate and added latency per token over the
      corpus. Report both even if the retraction rate is not zero. **[S4, S7]**

**Consumers (~90 min)**

- [ ] Replace the `NotImplementedError`. One keyword tiering function, two
      streams, irreversible time-stamped actions. **[U1, U2, U4]**
- [ ] Lock the canonical demo clip — naive fires the wrong tier, settled does
      not, every run. Record its name in the README. **[U3]**
- [ ] `make demo` reproduces it without arguments.

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

## Any time — the repo (~20 min, do it before D6)

- [ ] Create the public GitHub repo and push. There is still no remote. Doing
      this on D6 is how a broken repo link gets submitted. **[X1]**

---

## Open decisions

| # | Decision | Status |
|---|---|---|
| 1 | Chart library | Hand-rolled SVG from the stdlib. Keeps the three-dependency rule; SVG is what the site needs. matplotlib as a time-boxed fallback. |
| 2 | Public URL shape | Static GitHub Pages replaying a committed run. It is the abort path already — build it as the primary. |
| 3 | Pacing drift | **Settled 10 Sep: deadline scheduling.** The original recommendation here rested on a drift figure that turned out to be a measurement bug. Measured A/B: fixed sleep +1.4%, deadline +0.0%, and it cannot send faster than real time. |
| 4 | This file in the repo | `docs/DOD.md` is worth showing a judge. This file is internal; gitignore it if the repo should stay lean. |
| 5 | τ default | Open until D2. Settling p95 is the defensible choice; the number itself comes from the corpus, not from the smoke clip. |
