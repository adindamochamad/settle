# Handoff — read this first

Written 12 Sep 2026 for a fresh agent (or human) picking this up with zero
memory of how it got here. Everything below is self-contained; you should
not need this conversation's history to act correctly.

## What this is, in one breath

SETTLE — a hackathon submission (AI Infra Summit Hackathon, Speechmatics
track). Thesis: streaming ASR tells you what it heard, nothing tells you
when it stopped changing. The repo measures that gap ("settling time") and
ships a sidecar that holds tokens until they're stable. Full brief in
`CLAUDE.md` at the repo root — read that before touching anything; it has
non-negotiable rules, not suggestions.

## Where the real status lives

Don't trust a summary (including this one) over the source. Before doing
anything:

- `docs/DOD.md` — Definition of Done, one checkbox per requirement, each
  ticked box has a dated evidence note. **45/55 ticked as of this writing.**
- `docs/TODO.md` — day-by-day narrative of what happened and why, including
  every bug found and fixed. Long, but it's the record of *why* things are
  built the way they are.

Run `grep -c '^- \[x\]' docs/DOD.md` and `grep -c '^- \[ \]' docs/DOD.md`
to get the current true count — if it doesn't match "45/55", time has
passed and something changed; read `git log` to see what.

## Non-negotiable rules (from CLAUDE.md — do not relax these)

1. **Never invent a number.** Every latency/percentile/rate in README, the
   site, or the deck must trace to a committed file in `runs/`, or read
   `TBD`. This has already bitten this project once — a placeholder "800 ms"
   sat in the README for most of the build before an audit caught it. Before
   writing any number into a doc, re-derive it fresh (`make results`,
   `make measure`) and cross-check, don't copy from memory or a prior chat.
2. **Do not touch the pacing loop in `recorder.py`**
   (the deadline-scheduled `await asyncio.sleep(...)` in `send_audio()`).
   Every timing measurement in the project depends on it. If a task needs
   logic that currently lives in `recorder.py`, prefer extracting a small,
   reusable piece rather than editing the pacing path itself.
3. **One upstream connection, fanned out to two consumers** — never two
   separate sessions for naive/settled. The free tier allows 2 concurrent
   sessions; more importantly, a single stream is the only honest basis for
   the naive-vs-settled comparison.
4. **Develop against replayed JSONL, not the live API**, unless a task
   specifically calls for live. Record once, iterate offline.
5. Scope is closed: no user accounts, database, multi-language, diarization,
   translation, an LLM anywhere in the pipeline, CLI framework, Docker,
   Kubernetes, CI, coverage targets, design system, auth, rate limiting, or
   settings page. If you find yourself building one of these, stop.

## What's already done — don't re-do it, don't casually touch it

Every file below is built, tested (often against real recorded data or a
live WebSocket connection, not just "it parses"), and has a paper trail in
`docs/TODO.md` if you want the reasoning:

- `recorder.py`, `analyzer.py` — the instrument. 40 committed runs in
  `runs/`, corpus of 10 clips.
- `chart.py` → `web/chart.svg` — the measured curve, regenerates via
  `make chart`.
- `web/index.html` + `web/data.json` — the public static site, live at
  https://adindamochamad.github.io/settle/. Deployed via GitHub Pages,
  source = repo root, branch `main`.
- `sidecar.py`, `consumers.py` — the hold-policy sidecar and the two mock
  dispatch consumers. `make demo` reproduces the naive/settled divergence
  end to end, no arguments.
- `web/console.html` — a visual dispatch console (naive left, settled
  right) for recording the demo. Connects live to `sidecar.py` over
  WebSocket at `ws://localhost:8000`. **Local only, not part of the
  deployed site** — a page served over HTTPS can't open a plain `ws://`
  connection, so this one only works opened directly / via a local server
  against a running sidecar.
- `docs/deck.html` → `docs/deck.pdf` — 12-slide pitch deck. `make deck`
  regenerates the PDF via headless Chrome print-to-pdf.
- `docs/PITCH.md` — the video script, word for word, with screen
  directions, already pointing at the real (not aspirational) demo.

If you're asked to "improve" or "polish" any of the above, re-read the
relevant section of `docs/TODO.md` first — several design choices look
arbitrary but were arrived at after ruling something else out.

## What's genuinely left

### Optional, code-buildable: live Speechmatics connection for the sidecar

`docs/DOD.md` items **S1** and **S6** are open. Right now `sidecar.py` only
replays a committed `runs/*.jsonl` file — it cannot connect to Speechmatics
live. This was a deliberate scope cut (see rule 2 above): building it means
extracting `recorder.py`'s `websockets.connect(...)` + `StartRecognition`
handshake into something both `recorder.py` and `sidecar.py` can call,
**without** touching the pacing loop. `docs/SCOPE.md` explicitly treats a
replay-only sidecar as a complete, acceptable outcome — this is upside, not
a blocker.

If asked to build it:
1. Extract connection setup from `recorder.py`'s `record()` into a small
   reusable async generator (e.g. `connect_speechmatics(key, max_delay) ->
   yields raw messages`), used by both files. Do not change what
   `recorder.py` writes to its JSONL or how it paces audio.
2. Add a live source path to `sidecar.py`'s `Hub`, selected by an env var
   or startup flag, alongside the existing replay path — replay stays the
   default.
3. Re-run the full existing test suite before calling it done: fixture
   regression (`analyzer.py` against the scratch fixture), `make results`
   unchanged, `make demo` still reproduces the U3 divergence, and a live
   WebSocket smoke test against both `/ws/naive` and `/ws/settled`.

### Not code — do not attempt to automate

- **V1–V5** (video): recording, editing, exporting the 5-minute MP4 per
  `docs/PITCH.md`. This needs a human with a microphone and a screen
  recorder. An agent should not try to synthesize this.
- **Z1–Z3** (submission): filling the lablab.ai form and submitting. Needs
  the user's own account/access.

## Known gotchas — save yourself the time this session lost

- **qlmanage (`qlmanage -t -s N -o /tmp file.html`) is unreliable for
  fixed-width, print-oriented layouts.** It silently clips content past
  some internal viewport width — reproducibly, regardless of CSS fixes.
  Wasted real time on this chasing a phantom "missing table column" bug in
  `docs/deck.html` before testing the actual target pipeline. It's fine for
  fluid/responsive pages (`web/index.html`, `web/console.html`) but **do
  not use it to verify anything with a fixed pixel width meant for print or
  export** — use the real pipeline instead:
  `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless
  --disable-gpu --no-sandbox --print-to-pdf=out.pdf --print-to-pdf-no-header
  --no-pdf-header-footer file:///path/to/file.html`, then read the PDF
  directly.
- **Screenshotting a live browser window on this machine is risky.**
  `screencapture` grabbed the wrong browser (Brave, showing the user's
  personal history/bookmarks) twice this session despite checking which app
  was frontmost first. If you need to see a live, interactive page (not a
  static file), prefer: (a) a Node harness that loads the page's actual
  `<script>` content and drives it with fake WebSocket/DOM stubs against
  real recorded data, or (b) ask the user to look themselves and describe
  what they see, rather than repeated screen capture attempts.
- **A batch find/replace loop that asserts each match can silently drop
  every edit if one assertion in the middle throws** (the exception aborts
  before the file write at the end runs). This cost real accuracy earlier —
  several DoD checkboxes were reported ticked when the underlying edit had
  never actually landed. After any multi-item batch edit, re-read the file
  and grep for each expected change individually before reporting a count
  or percentage as fact.
- **`websockets` >= 14 uses `additional_headers=`, not `extra_headers=`.**
  `recorder.py` already has this right; don't "fix" it back.
- macOS has no `timeout` command by default — don't rely on it in scripts
  run here.

## How to verify you haven't broken anything

```bash
make results     # must match the table already in README.md exactly
make measure     # must match the sidecar table already in README.md
make demo        # naive must fire ELEVATED - FIRE, settled must not
```

If any of these produce different numbers than what's already committed in
`README.md`, stop and reconcile before doing anything else — either the
repo drifted (investigate why) or your change broke something.

## Everything else

Full method, definitions, and threats to validity: `docs/METHOD.md`.
Timeline and abort rules: `docs/SCOPE.md`. If in doubt about whether a
change is in scope, that file's abort-rule ladder is the tie-breaker.
