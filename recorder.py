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


async def record(pcm_path, out_path, max_delay=1.0, language="en"):
    key = os.environ["SPEECHMATICS_API_KEY"]
    audio = Path(pcm_path).read_bytes()
    started = time.perf_counter()
    seq = 0

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

            async def send_audio():
                nonlocal seq
                off = 0
                while off < len(audio):
                    await ws.send(audio[off:off + CHUNK])
                    off += CHUNK
                    seq += 1
                    # Realtime pacing. Do NOT remove: blasting the file at once
                    # destroys every timing measurement this project depends on.
                    await asyncio.sleep(CHUNK_MS / 1000)
                await ws.send(json.dumps({
                    "message": "EndOfStream", "last_seq_no": seq,
                }))

            async def receive():
                async for raw in ws:
                    if isinstance(raw, bytes):
                        continue
                    msg = json.loads(raw)
                    kind = msg.get("message")
                    if kind == "AudioAdded":
                        continue
                    log(kind, msg)
                    if kind in ("EndOfTranscript", "Error"):
                        return

            await asyncio.gather(send_audio(), receive())


if __name__ == "__main__":
    pcm, out = sys.argv[1], sys.argv[2]
    delay = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    asyncio.run(record(pcm, out, delay))
