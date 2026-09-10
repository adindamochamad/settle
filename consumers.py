#!/usr/bin/env python3
"""SETTLE consumers - D3. Not built yet; this pins the interface.

Two mock emergency-dispatch consumers reading the sidecar's two streams. Each
maps transcript text to a response tier and fires an irreversible action the
moment it decides. The naive one acts on partials; the settled one waits.

What the demo has to show, in one frame: the naive consumer's action already
sent, and the text underneath it changing meaning.

Dispatch tiering is deliberately trivial - keyword match, no model. The point
of the demo is the retraction, not the classifier.
"""
raise NotImplementedError("D3 - see docs/SCOPE.md before starting")
