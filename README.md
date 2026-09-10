# SETTLE

**Streaming ASR tells you what it heard. Nothing tells you when it stopped changing.**

Speechmatics track · AI Infra Summit Hackathon 2026

---

Streaming speech recognition emits partial hypotheses that get revised. A word
appears, looks settled, and is rewritten 800 ms later. Anything downstream that
acts on the stream — an agent, a command handler, a dispatch console — has
already acted.

Vendors publish word error rate and latency. Both describe endpoints. Neither
describes the interval in between, where the text is visible, plausible, and
still moving. That interval has no published number.

SETTLE measures it, then holds it.

## Two parts

**The instrument.** Streams a fixed clip at real-time pace, records every
inbound message with its arrival timestamp, and computes per-word **settling
time** — how long a word kept being revised after it first appeared. Every clip
is swept across `max_delay` ∈ {0.7, 1.0, 2.0, 4.0} to answer a question the
documentation does not: *does a transcript marked final actually stop changing?*

**The sidecar.** A WebSocket proxy that holds a token until its text has been
stable for τ seconds, then releases it. One upstream connection, two downstream
streams — naive and settled — so the difference is visible on identical input.

τ is a dial, not a switch. It buys correctness with latency, and the instrument
is what tells you the exchange rate.

## Results

Measured on this repository's runs. See `docs/METHOD.md` for definitions and
stated threats to validity.

| `max_delay` | words | settling p50 | settling p99 | words revised |
|---|---|---|---|---|
| 0.7 | TBD | TBD | TBD | TBD |
| 1.0 | TBD | TBD | TBD | TBD |
| 2.0 | TBD | TBD | TBD | TBD |
| 4.0 | TBD | TBD | TBD | TBD |

Numbers are filled in from `runs/` only. Nothing in this table is estimated.

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env          # add your Speechmatics key
export SPEECHMATICS_API_KEY=...

ffmpeg -i clips/call1.m4a -ac 1 -ar 16000 -f s16le clips/call1.pcm

make record CLIP=call1 MD=1.0     # one run
make sweep  CLIP=call1            # all four max_delay values
make analyze                      # settling time across every run
```

`python analyzer.py --inspect runs/<file>.jsonl` dumps a raw payload if you want
to check the reader against the wire format yourself.

## Layout

```
recorder.py    instrument — observes, never interprets
analyzer.py    settling time, emission lag, revision counts
sidecar.py     WebSocket proxy with the settle policy
consumers.py   naive vs settled dispatch mocks
docs/METHOD.md how the measurement works, and where it is weak
docs/SCOPE.md  timeline, gates, abort rules
docs/PITCH.md  video structure
runs/          recorded sessions — the evidence, kept in the repo
```

## Why the demo is a dispatch call

A retraction has to cost something before the problem is legible. In a note-taking
app a revised word is a typo. In emergency dispatch, a partial reading
`no one is trapped inside` that resolves to `someone is trapped inside` has
already downgraded the response tier by the time it is corrected.

All audio is recorded by the author for this project. No real emergency calls
were used.
