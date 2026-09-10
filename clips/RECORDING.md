# How to record

One command per clip. It records straight to the format `recorder.py` wants —
16 kHz mono PCM s16le — so there is no separate conversion step and `make prep`
has nothing to do for clips recorded this way.

```bash
ffmpeg -f avfoundation -i ":1" -ac 1 -ar 16000 -f s16le clips/01.pcm
```

`:1` selects "MacBook Pro Microphone" (device index 1 on this machine, checked
10 Sep 2026 — re-run `ffmpeg -f avfoundation -list_devices true -i ""` if it
ever looks wrong).

Steps, per clip:

1. Open `clips/SCRIPT.md`, find the clip number.
2. Run the command above with that number, e.g. `clips/02.pcm` for clip 02.
3. It starts recording immediately. Read the line.
4. Press `q` in the terminal to stop and close the file cleanly. (Ctrl-C also
   works but can truncate the last fraction of a second — prefer `q`.)
5. Move to the next clip.

If a take is bad, just re-run the same command — `ffmpeg -y` is not set on
purpose, so it will refuse to silently overwrite; delete the bad file first:
`rm clips/01.pcm` then re-record.

## After all ten

```bash
make sweepall     # warm-up run (discarded) + all ten clips × all four max_delay
make results      # the README table
```

`make prep` is only needed for clips brought in as `.m4a`/`.wav`/`.mp3` (e.g.
from a phone). Clips recorded with the command above are already the right
format and `make prep` will find nothing to do for them.
