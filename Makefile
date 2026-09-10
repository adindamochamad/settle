PY ?= python3
CLIP ?= call1
MD ?= 1.0

.PHONY: setup record sweep analyze sidecar clean

setup:
	$(PY) -m pip install -r requirements.txt

record:
	$(PY) recorder.py clips/$(CLIP).pcm runs/$(CLIP)_md$(MD).jsonl $(MD)

sweep:
	@for d in 0.7 1.0 2.0 4.0; do \
		echo "--> $(CLIP) @ max_delay=$$d"; \
		$(PY) recorder.py clips/$(CLIP).pcm runs/$(CLIP)_md$$d.jsonl $$d; \
	done

analyze:
	$(PY) analyzer.py runs/*.jsonl

sidecar:
	$(PY) -m uvicorn sidecar:app --reload --port 8000

clean:
	rm -rf __pycache__
