# SETTLE — project context

Read this before touching anything in this repo.

## What this is

A hackathon submission for the **AI Infra Summit Hackathon** (lablab.ai × Kisaco
Research), Speechmatics sponsor track. Online build window: **10–16 September
2026**. Solo developer. First-ever hackathon submission.

**Thesis, in one sentence:**
> Streaming ASR tells you what it heard. Nothing tells you when it stopped changing.

SETTLE is two things shipped together:

1. **An instrument** that measures *settling time* — how long a word keeps being
   revised after it first appears — a number no ASR vendor publishes.
2. **A sidecar** that holds tokens until they settle, so downstream consumers
   never act on text that is about to be retracted.

The demo domain is emergency dispatch, because a retraction there is
catastrophic rather than annoying: a partial says `no one is trapped inside`,
the final says `someone is trapped inside`, and a naive consumer has already
downgraded the response tier.

## Non-negotiable rules

1. **Never invent a number.** Every latency, percentile, or rate that appears in
   the README, the website, the deck, or the video must trace back to a real
   file in `runs/`. The judges are infrastructure engineers at Intel, Qualcomm
   and Speechmatics. A fabricated benchmark is the one mistake this project
   cannot survive. If a number is not measured yet, write `TBD`, not a guess.
2. **Do not remove the realtime pacing** in `recorder.py`
   (`await asyncio.sleep(CHUNK_MS / 1000)`). Sending the audio file faster than
   real time destroys every timing measurement the project is built on.
3. **One ASR connection, fanned out to two consumers.** Never open two sessions
   for the side-by-side demo. The free tier allows 2 concurrent realtime
   sessions, and more importantly a single stream is the only honest comparison.
4. **Develop against replayed JSONL, not the live API.** Record once, iterate
   offline. API credit is not the constraint; wasting a day on flaky network is.
5. **Feature freeze is 13 September, 23:59.** After that: bug fixes only.
6. **Word confidence on partials is meaningless** — Speechmatics documents this
   explicitly. Stability must be derived from revision history. Any code that
   reads `confidence` off an `AddPartialTranscript` is wrong.

## Scope

**In scope — four components, nothing else:**

| File | Role |
|---|---|
| `recorder.py` | Connect to Speechmatics realtime, log every message with arrival timestamp to JSONL |
| `analyzer.py` | Compute per-word settling time from a JSONL run |
| `sidecar.py` | FastAPI WebSocket proxy: one ASR connection in, settled + naive streams out |
| `consumers.py` | Two mock dispatch consumers that act on the two streams |

**Explicitly out of scope.** Do not build these, do not suggest them:
user accounts, a database, multi-language support, speaker diarization,
translation, an LLM anywhere in the pipeline, a CLI framework, Docker,
Kubernetes manifests, CI, unit-test coverage targets, a design system,
authentication, rate limiting, or a settings page.

## Data contract

`recorder.py` writes one JSON object per line to `runs/<clip>_md<delay>.jsonl`:

```json
{
  "t": 2.1043,              // seconds since session start, arrival wall-clock
  "audio_pos": 2.048,       // seconds of audio sent when this arrived
  "kind": "AddPartialTranscript",
  "max_delay": 1.0,
  "payload": { ... }        // the raw Speechmatics message, unmodified
}
```

`payload` is never trimmed or normalised at record time. The recorder is an
instrument; it observes and does not interpret. All interpretation lives in
`analyzer.py`.

## Definitions

See `docs/METHOD.md` for the full measurement definition. Summary:

- **settling time** of a word — elapsed time between the first message that
  reported text at that audio interval and the last message that changed it.
- **tolerance band** — a word is *settled at τ* once its text has not changed
  for τ seconds. τ is the tunable dial the sidecar exposes.
- **emission lag** — time between the end of the spoken word and the first time
  any text for it appeared.

Words are matched across revisions by **audio-interval overlap**, never by index
in the results array. Index matching breaks the moment a word is inserted or
deleted mid-revision, which is exactly the case this project studies.

## Environment

- Python 3.11+, `websockets>=14` (if `additional_headers` raises, the installed
  version predates 14 — use `extra_headers`)
- `SPEECHMATICS_API_KEY` in the environment; see `.env.example`
- Realtime endpoint: `wss://eu.rt.speechmatics.com/v2`
- Audio in: raw 16 kHz mono PCM s16le

## Code style

Plain, boring Python. Standard library plus the three dependencies. No classes
where a function works. No abstraction layer that exists for a second
implementation that will never be written. This code will be read by judges who
have five minutes — favour obviousness over cleverness.

## Deliverables (lablab)

1. Working prototype at a public URL
2. Pitch video, MP4, ≤ 5 minutes
3. Slide deck, PDF
4. Public GitHub repository

If time runs out, sacrifice from the bottom: video > numbers > sidecar >
website. See `docs/SCOPE.md` for the abort rules.
