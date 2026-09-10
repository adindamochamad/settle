PY ?= $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)
CLIP ?= call1
MD ?= 1.0

.PHONY: setup prep record sweep sweepall analyze results sidecar clean

setup:
	$(PY) -m pip install -r requirements.txt

prep:
	@for f in clips/*.m4a clips/*.wav clips/*.mp3; do \
		[ -e "$$f" ] || continue; \
		b=`basename "$$f"`; b=$${b%.*}; \
		ffmpeg -loglevel error -y -i "$$f" -ac 1 -ar 16000 -f s16le "clips/$$b.pcm"; \
		$(PY) -c "import os,sys;n=os.path.getsize(sys.argv[1]);print(f'  {sys.argv[1]}  {n/32000:.1f}s')" "clips/$$b.pcm"; \
	done

record:
	$(PY) recorder.py clips/$(CLIP).pcm runs/$(CLIP)_md$(MD).jsonl $(MD)

sweep:
	@for d in 0.7 1.0 2.0 4.0; do \
		echo "--> $(CLIP) @ max_delay=$$d"; \
		$(PY) recorder.py clips/$(CLIP).pcm runs/$(CLIP)_md$$d.jsonl $$d; \
	done

sweepall:
	@echo "--> warm-up run, discarded: a cold session emits its first text ~6x later"
	-@$(PY) recorder.py `ls clips/*.pcm | head -1` /tmp/settle_warmup.jsonl 1.0
	@for p in clips/*.pcm; do \
		c=`basename "$$p" .pcm`; \
		for d in 0.7 1.0 2.0 4.0; do \
			echo "--> $$c @ max_delay=$$d"; \
			$(PY) recorder.py "$$p" "runs/$${c}_md$$d.jsonl" $$d || echo "    ^ run failed, re-record it"; \
		done; \
	done

analyze:
	$(PY) analyzer.py runs/*.jsonl

results:
	@$(PY) analyzer.py --table runs/*.jsonl

sidecar:
	$(PY) -m uvicorn sidecar:app --reload --port 8000

clean:
	rm -rf __pycache__
