#!/usr/bin/env python3
"""SETTLE sidecar - D3. Not built yet; this pins the interface.

One Speechmatics connection in, two streams out:

    ASR ---> sidecar ---+--> /ws/naive     emits every partial immediately
                        |
                        +--> /ws/settled   holds a token until its text has
                                           been stable for `tau` seconds

The free tier allows 2 concurrent realtime sessions, and a single upstream
connection is also the only honest basis for the comparison - both consumers
must see byte-identical input.

    uvicorn sidecar:app --reload --port 8000

Settle policy reuses the alignment in analyzer.overlaps(); do not write a
second implementation of it.
"""
raise NotImplementedError("D3 - see docs/SCOPE.md before starting")
