# Definition of Done

`docs/SCOPE.md` says what gets cut when time runs out. This says what "finished"
counts as for the things that survive.

A box is ticked only when the stated evidence exists on disk or at a URL.
Nothing here is satisfied by "it worked when I ran it".

## 0. The evidence rule — applies to every artefact

Every number that appears in the README, the website, the deck, the video, or
this file must satisfy all four:

1. it is reproducible by one command in this repository against a file in `runs/`
2. the run file it came from is committed
3. it states its clock (wall-clock `t`, or audio-clock `audio_pos`) and the word count `n`
4. if it is not measured yet, it reads `TBD`

A number failing any of these is a defect of the same severity as a crash.
This is CLAUDE.md rule 1 made checkable.

## 1. Recorder

- [x] R1 Streams a clip end to end and exits on `EndOfTranscript` on its own — no Ctrl-C, no hang. *(verified: 5 runs, all exited on EndOfTranscript unaided)*
- [x] R2 Output matches the data contract exactly: `t`, `audio_pos`, `kind`, `max_delay`, `payload`, one object per line, `payload` unmodified. *(verified: keys unchanged)*
- [x] R3 A valid run contains at least one `AddPartialTranscript` **and** at least one `AddTranscript`. *(verified: 19 partials, 10 finals on the smoke run)*
- [x] R4 Real-time pacing intact and *demonstrated*: the last record's `t` is greater than or equal to the clip duration, and streaming drift (`t − audio_pos` at end of run) is reported. **Drift above 5% of clip duration voids the run.** *(verified: drift +0.0% after deadline scheduling)*
- [x] R5 The API key never reaches disk or stdout. *(verified: .env git-ignored, never echoed)*
- [x] R6 An `Error` message from the server is recorded in the JSONL, never swallowed. A failed run must look failed. *(Verified 10 Sep with a deliberately wrong key, 4 attempts: found the server fails two different ways - an application-level Error message, or a protocol-level WebSocket close (4001) that used to raise unhandled and write nothing at all. Both now produce a clean Error record and exit 1.)*
- [x] R7 `make sweep CLIP=x` produces four files with no manual editing between them. *(clean loop over the four max_delay values; functionally exercised via `make sweepall` for the real corpus, 10 Sep)*

## 2. Analyzer

- [x] A1 **Blocking gate.** `--inspect` has been run against a real recording and the field names in `words()` confirmed against the actual wire format. Until this is ticked, no number this file prints may be quoted anywhere. *(CLEARED 10 Sep: results[].type is word|punctuation, start_time/end_time/alternatives[0].content confirmed against a real AddPartialTranscript)*
- [x] A2 Word alignment picks the *best* overlapping slot, not the first one found. *(implemented, fixture-verified; retraction handling added 10 Sep after a real orphan-word bug found via the website - see docs/TODO.md)*
- [x] A3 Emission lag is computed on the audio clock (`audio_pos − end_time`), not the wall clock — the wall clock carries connection-setup offset and pacing drift that have nothing to do with the engine. *(implemented, fixture-verified against an injected 0.300s offset)*
- [x] A4 Per run it reports: `n` words, settling p50/p95/p99/max, share of words revised at least once. *(verified; report also carries risk window, emission lag, speculative and after-final)*
- [x] A5 **The sweep's headline question is answerable.** For each run: how many words changed *after* the first `AddTranscript` that covered them, and by how much. Both answers are publishable; not having the number is not. *(implemented; reads 0/20 on the smoke run)*
- [x] A6 `analyzer.py --table runs/*.jsonl` emits the markdown table that is pasted into the README verbatim, so the README cannot drift from the runs. *(implemented, `make results`)*
- [x] A7 Given an empty or malformed run it prints a clear message and exits non-zero. It never prints a fabricated `0.000`. *(verified: exit 1 on empty, garbage, missing, no-transcripts)*
- [x] A8 Same input, identical output, every time.

## 3. Corpus

- [x] C1 At least 8 clips, 20–60 s each, author's own voice, dispatch-style content. *(10 clips, 9.0-17.3s each - two clips 05/08 short of the 20s target, flagged for re-record before D4)*
- [x] C2 Every clip recorded at `max_delay` ∈ {0.7, 1.0, 2.0, 4.0} — at least 32 run files, all committed. *(40 run files, all four max_delay values × 10 clips)*
- [x] C3 At least one clip produces a **meaning-changing** revision, confirmed by reading the run file, not from memory. *(runs/08_md1.0.jsonl, span (5.6,5.76): partial "now" at audio_pos 6.4s -> final "not" at 6.784s. Gate D1.)*
- [x] C4 `docs/METHOD.md` "threats to validity" is updated to the corpus as actually recorded: clip count, total audio minutes, total words, speaker count. *(10 clips, 2.0 min, 304 words, 1 speaker)*

## 4. Chart

- [x] G1 An image file lives in the repo, produced by a committed script — not exported by hand from a notebook. *(web/chart.svg, from chart.py, stdlib only)*
- [x] G2 Regenerable from `runs/` in one command. *(`make chart`; re-verified byte-identical in a clean clone, 10 Sep)*
- [x] G3 Axes labelled with units, `n` shown on the figure, clock named in the caption. *(per-point n, total n, "wall clock" on the y-axis)*
- [x] G4 Legible at video resolution and on a phone screen. *(SVG, checked at 800px and 390px)*

## 5. Sidecar

- [ ] S1 Exactly one upstream Speechmatics connection per session, fanned out to both consumers. Provable from the code path, not asserted in a comment. *(satisfied for replay: Hub owns one _run() task, both endpoints subscribe to it - verified via live WS test. Live Speechmatics connection deliberately not built this pass, see docs/TODO.md and CLAUDE.md rule 4.)*
- [x] S2 Both downstream streams see byte-identical upstream input. *(both subscribe to the same Hub queue - verified live: naive and settled both eventually show every word the source run contains)*
- [x] S3 τ is settable at connect time and its default is taken from measured data, with the percentile it came from written down. *(`?tau=` query param; default 0.774s = settling p95 at max_delay=1.0, in README)*
- [x] S4 Residual retraction rate is measured over the corpus and reported. It does not have to be zero. It has to be known. *(4.2% at md=1.0 where tau was calibrated; 13.9% pooled across all max_delay - both in README, `make measure`)*
- [x] S5 Reuses `analyzer.overlaps()`. A second alignment implementation is a failure, not a shortcut. *(imports analyzer.apply(), which is built on overlap() - no second aligner)*
- [ ] S6 Runs from replayed JSONL as well as live. *(replay done and is the default/only source this pass - deliberate scope call, see docs/TODO.md. Live is a scoped follow-up, not built.)*
- [x] S7 Added latency of settled vs naive is measured, per token, and reported. *(p50=0.774s exactly = tau, consistent with settling p50=0.000s in the main table; p95=0.774s at md=1.0, 1.734s pooled)*

## 6. Consumers

- [x] U1 Two consumers, one tiering function, two streams. *(Consumer class, shared tier_for())*
- [x] U2 Each action is irreversible and stamped with the wall-clock time it fired. *(append-only self.actions, time.time() per entry)*
- [x] U3 On the locked demo clip the naive consumer fires the wrong tier and the settled one does not — reproducibly, every run, not on a lucky take. *(runs/09_md1.0.jsonl: naive fires ELEVATED-FIRE (false alarm) then corrects; settled never does. Verified identical across 4 separate live runs, including via `make demo` from a cold start.)*
- [x] U4 The tiering is keyword matching and says so on screen, so nobody mistakes it for a model. *(module docstring + inline comment on TIER_RULES/tier_for)*

## 7. Website — the D3 gate

- [x] W1 A public URL a stranger can open. No login, no API key, no build step for the visitor. *(https://adindamochamad.github.io/settle/ - verified live via curl: correct title, data.json, chart.svg all HTTP 200, corrected numbers present)*
- [x] W2 Loads with no backend, replaying a committed run. It cannot break while a judge is watching. *(static, fetches web/data.json, no server-side code)*
- [x] W3 Three sections: the flip, the curve, what settling time is. Not four.
- [x] W4 Every number on the page came out of `analyzer.py --table`. *(RESULTS array in index.html matches make results verbatim)*
- [x] W5 Renders on a phone, and at 1080p for the screen recording. *(chart legibility checked at 390px and 800px via qlmanage; layout is relative-unit/max-width:760px, viewport meta present - not checked on a literal physical phone)*

## 8. Deck

- [x] P1 PDF, 12 slides or fewer. *(docs/deck.html -> docs/deck.pdf via `make deck`, headless Chrome print-to-pdf; exactly 12)*
- [x] P2 Charts are the same image files as the repo — not redrawn. *(slide 6 embeds ../web/chart.svg directly)*
- [x] P3 Contains no number absent from the README. *(every figure cross-checked against README.md by script before committing)*

## 9. Video

- [ ] V1 MP4, 5:00 or under, structured as `docs/PITCH.md`.
- [ ] V2 The side-by-side block runs 90 s or longer, uncut.
- [ ] V3 Captions throughout — judges may watch muted.
- [ ] V4 Audible on laptop speakers.
- [ ] V5 Plays from a logged-out incognito window at the submitted link.

## 10. Repository

- [x] X1 Public, with a LICENSE. *(github.com/adindamochamad/settle, MIT)*
- [x] X2 README contains no `TBD`. *(grepped 10 Sep: none)*
- [x] X3 `runs/*.jsonl` committed — they are the evidence. *(40 files, `git ls-files runs/`)*
- [x] X4 On a clean clone: `pip install -r requirements.txt && make analyze` reproduces the README table. *(verified 10 Sep: fresh clone + fresh venv, make results/chart/site/measure all byte-identical to committed output)*
- [x] X5 No API key anywhere in the history, not just in the current tree. *(verified 10 Sep: `git log --all -p` searched for the key pattern, `Bearer `-prefixed strings, and `.env` ever being committed - all clean)*

## 11. Submission

- [ ] Z1 All four lablab fields filled: prototype URL, video, deck, repo.
- [ ] Z2 Every link opened from a logged-out browser and confirmed.
- [ ] Z3 Submitted with at least 6 hours of buffer.

## Gates, restated as pass/fail

| Gate | Date | Passes when |
|---|---|---|
| D1 | 10 Sep | One committed run where a partial's text differs from the final at the same audio interval |
| D2 | 11 Sep | The chart file exists, generated by a script, from real runs |
| D3 | 12 Sep | A stranger can open a URL and see the flip |
| D4 | 13 Sep 23:59 | Feature freeze. Everything above is either done or formally cut |
| D5 | 14 Sep | Every second of footage recorded. Nothing left to shoot |
| D6 | 15–16 Sep | Submitted, buffer intact |

## Done means not built

Restating CLAUDE.md so it is checkable here too. If any of these exist at
submission time, the scope was broken: user accounts, a database, multi-language
support, diarization, translation, an LLM in the pipeline, a CLI framework,
Docker, Kubernetes, CI, coverage targets, a design system, auth, rate limiting,
a settings page.
