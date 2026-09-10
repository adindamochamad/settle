#!/usr/bin/env python3
"""SETTLE recorder - capture every ASR message with its arrival timestamp.

    export SPEECHMATICS_API_KEY=...
    python recorder.py clips/call1.pcm runs/call1_md1.jsonl 1.0

Audio must be raw 16 kHz mono PCM s16le:
    ffmpeg -i clips/call1.m4a -ac 1 -ar 16000 -f s16le clips/call1.pcm
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import websockets

URL = "wss://eu.rt.speechmatics.com/v2"
SR = 16_000
CHUNK_MS = 128
CHUNK = SR * 2 * CHUNK_MS // 1000  # 16-bit mono
GRACE = 30.0                       # seconds to wait for EndOfTranscript


async def record(pcm_path, out_path, max_delay=1.0, language="en"):
    key = os.environ["SPEECHMATICS_API_KEY"]
    audio = Path(pcm_path).read_bytes()
    clip_len = len(audio) / (SR * 2)
    started = time.perf_counter()
    audio_started = None
    send_finished = None
    seq = 0
    failed = None

    with open(out_path, "w") as out:
        def log(kind, payload):
            out.write(json.dumps({
                "t": round(time.perf_counter() - started, 4),
                "audio_pos": round(seq * CHUNK_MS / 1000, 4),
                "kind": kind,
                "max_delay": max_delay,
                "payload": payload,
            }) + "\n")
            out.flush()

        async with websockets.connect(
            URL,
            additional_headers={"Authorization": f"Bearer {key}"},
            max_size=None,
        ) as ws:
            await ws.send(json.dumps({
                "message": "StartRecognition",
                "audio_format": {
                    "type": "raw", "encoding": "pcm_s16le", "sample_rate": SR,
                },
                "transcription_config": {
                    "language": language,
                    "enable_partials": True,
                    "max_delay": max_delay,
                },
            }))

            done = asyncio.Event()

            async def send_audio():
                nonlocal seq, audio_started, send_finished
                off = 0
                audio_started = time.perf_counter()
                nxt = audio_started
                while off < len(audio) and not done.is_set():
                    await ws.send(audio[off:off + CHUNK])
                    off += CHUNK
                    seq += 1
                    # Realtime pacing. Do NOT remove: blasting the file at once
                    # destroys every timing measurement this project depends on.
                    #
                    # Deadlines are fixed CHUNK_MS steps from the first chunk and
                    # the sleep is clamped at zero, so chunk k never leaves before
                    # t0 + k*CHUNK_MS: this cannot run faster than real time, it
                    # only stops ws.send() latency accumulating into drift. A
                    # Measured A/B on one 6.8s clip: plain sleep(CHUNK_MS/1000)
                    # drifts +1.4%, this loop +0.0%. Drift inflates every
                    # wall-clock settling time by its own proportion and grows
                    # with clip length. See docs/METHOD.md, "Two clocks".
                    nxt += CHUNK_MS / 1000
                    await asyncio.sleep(max(0.0, nxt - time.perf_counter()))
                # Stamped here, before EndOfStream: everything after this is
                # waiting for the server, which is not pacing drift.
                send_finished = time.perf_counter()
                if not done.is_set():
                    await ws.send(json.dumps({
                        "message": "EndOfStream", "last_seq_no": seq,
                    }))

            async def receive():
                nonlocal failed
                async for raw in ws:
                    if isinstance(raw, bytes):
                        continue
                    msg = json.loads(raw)
                    kind = msg.get("message")
                    if kind == "AudioAdded":
                        continue
                    log(kind, msg)
                    if kind == "Error":
                        # Recorded, not swallowed: a failed run must look failed.
                        failed = msg.get("reason") or msg.get("type") or "Error"
                        done.set()
                        return
                    if kind == "EndOfTranscript":
                        done.set()
                        return

            try:
                await asyncio.wait_for(
                    asyncio.gather(send_audio(), receive()),
                    timeout=clip_len + GRACE,
                )
            except TimeoutError:
                # Without this a server that never sends EndOfTranscript hangs
                # the run forever, and `make sweep` along with it.
                failed = f"no EndOfTranscript within {clip_len + GRACE:.0f}s"
                done.set()

    # Instrument self-check. Pacing drift is reported, never compensated:
    # compensating means touching the sleep above. A run whose drift exceeds
    # 5% of the clip is void - see docs/DOD.md R4.
    sent = seq * CHUNK_MS / 1000
    drift = (send_finished - audio_started - sent) if send_finished else 0.0
    pct = 100 * drift / clip_len if clip_len else 0.0
    print(f"{out_path}  clip {clip_len:.1f}s  sent {sent:.1f}s  "
          f"drift {drift:+.2f}s ({pct:+.1f}%)", file=sys.stderr)
    if abs(pct) > 5:
        print("  WARNING: drift over 5% - this run is void, record it again",
              file=sys.stderr)
    if failed:
        print(f"  FAILED: {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    pcm, out = sys.argv[1], sys.argv[2]
    delay = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    sys.exit(asyncio.run(record(pcm, out, delay)))
