#!/usr/bin/env python3
"""SETTLE chart - settling time vs max_delay, as a standalone SVG.

    python chart.py runs/*.jsonl > web/chart.svg
    make chart

Hand-rolled, stdlib only. This is the one number-bearing image in the repo;
every point on it must trace to analyzer.settling() over a committed run, per
docs/DOD.md's evidence rule. No plotting library, no exported-by-hand image.
"""
import sys
from collections import defaultdict

import analyzer

W, H = 720, 480
PAD_L, PAD_R, PAD_T, PAD_B = 70, 30, 40, 100
PLOT_W, PLOT_H = W - PAD_L - PAD_R, H - PAD_T - PAD_B

BG = "#0b0f14"
GRID = "#26313d"
AXIS = "#5b6b7a"
TEXT = "#c9d4de"
P50 = "#4fd1c5"
P95 = "#f2a65a"


def collect(paths):
    """{max_delay: [settling_time, ...]} pooled across every clip."""
    by_md = defaultdict(list)
    for path in paths:
        records, stats = analyzer.read(path)
        if stats is None:
            continue
        md = next((r.get("max_delay") for r in records if r.get("max_delay")), None)
        if md is None:
            continue
        by_md[md].extend(s["settling"] for s in stats)
    return dict(sorted(by_md.items()))


def scale(paths):
    """max_delay -> x position, and a y() closure for settling seconds."""
    mds = list(paths)
    n = len(mds)
    x_of = {md: PAD_L + (i / (n - 1) if n > 1 else 0.5) * PLOT_W
            for i, md in enumerate(mds)}
    y_max = max((max(v) for v in paths.values() if v), default=1.0)
    y_max = max(y_max * 1.15, 0.5)

    def y_of(seconds):
        return PAD_T + PLOT_H - (seconds / y_max) * PLOT_H

    return x_of, y_of, y_max


def polyline(points, color, width=2.5):
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return (f'<polyline points="{pts}" fill="none" stroke="{color}" '
            f'stroke-width="{width}" stroke-linejoin="round" '
            f'stroke-linecap="round"/>')


def render(by_md):
    x_of, y_of, y_max = scale(by_md)
    total_n = sum(len(v) for v in by_md.values())

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace, Menlo, Consolas, monospace">',
        f'<rect width="{W}" height="{H}" fill="{BG}"/>',
    ]

    # y gridlines + labels, every 0.5s up to y_max
    step = 0.5 if y_max <= 3 else 1.0
    g = 0.0
    while g <= y_max:
        y = y_of(g)
        parts.append(f'<line x1="{PAD_L}" y1="{y:.1f}" x2="{W-PAD_R}" y2="{y:.1f}" '
                      f'stroke="{GRID}" stroke-width="1"/>')
        parts.append(f'<text x="{PAD_L-10}" y="{y+4:.1f}" fill="{TEXT}" '
                      f'font-size="12" text-anchor="end">{g:.1f}s</text>')
        g += step

    # axes
    parts.append(f'<line x1="{PAD_L}" y1="{PAD_T}" x2="{PAD_L}" y2="{PAD_T+PLOT_H}" '
                  f'stroke="{AXIS}" stroke-width="1.5"/>')
    parts.append(f'<line x1="{PAD_L}" y1="{PAD_T+PLOT_H}" x2="{W-PAD_R}" '
                  f'y2="{PAD_T+PLOT_H}" stroke="{AXIS}" stroke-width="1.5"/>')

    # x labels + per-point n
    for md, x in x_of.items():
        n = len(by_md[md])
        parts.append(f'<text x="{x:.1f}" y="{H-PAD_B+20}" fill="{TEXT}" '
                      f'font-size="13" text-anchor="middle">{md}</text>')
        parts.append(f'<text x="{x:.1f}" y="{H-PAD_B+36}" fill="{AXIS}" '
                      f'font-size="10" text-anchor="middle">n={n}</text>')

    # p50 / p95 lines
    p50_pts = [(x_of[md], y_of(analyzer.pct(by_md[md], 50))) for md in by_md]
    p95_pts = [(x_of[md], y_of(analyzer.pct(by_md[md], 95))) for md in by_md]
    parts.append(polyline(p95_pts, P95))
    parts.append(polyline(p50_pts, P50))
    for x, y in p50_pts:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{P50}"/>')
    for x, y in p95_pts:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{P95}"/>')

    # title, axis names, legend
    parts.append(f'<text x="{PAD_L}" y="24" fill="{TEXT}" font-size="15">'
                  f'settling time vs max_delay</text>')
    parts.append(f'<text x="{(W)/2:.0f}" y="{H-PAD_B+58}" fill="{AXIS}" font-size="11" '
                  f'text-anchor="middle">max_delay (s) — Speechmatics '
                  f'transcription_config setting</text>')
    parts.append(f'<text x="20" y="{H/2:.0f}" fill="{AXIS}" font-size="11" '
                  f'text-anchor="middle" transform="rotate(-90 20 {H/2:.0f})">'
                  f'settling time (s, wall clock)</text>')
    lx, ly = W - PAD_R - 130, PAD_T + 8
    parts.append(f'<circle cx="{lx}" cy="{ly}" r="3.5" fill="{P50}"/>')
    parts.append(f'<text x="{lx+10}" y="{ly+4}" fill="{TEXT}" font-size="12">p50</text>')
    parts.append(f'<circle cx="{lx+50}" cy="{ly}" r="3.5" fill="{P95}"/>')
    parts.append(f'<text x="{lx+60}" y="{ly+4}" fill="{TEXT}" font-size="12">p95</text>')
    parts.append(f'<text x="{PAD_L}" y="{H-16}" fill="{AXIS}" font-size="10">'
                  f'n = {total_n} words total, 10 clips, 1 speaker — '
                  f'settling = t_last_change - t_first, per docs/METHOD.md</text>')

    parts.append('</svg>')
    return "\n".join(parts)


if __name__ == "__main__":
    paths = sys.argv[1:]
    if not paths:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    by_md = collect(paths)
    if not by_md:
        print("no usable runs", file=sys.stderr)
        sys.exit(1)
    print(render(by_md))
