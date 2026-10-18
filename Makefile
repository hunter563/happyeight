.PHONY: run test check
run:
	python run.py
test:
	python -m unittest discover -s tests -v
check:
	python -m compileall -q fusion run.py
	node --check web/app.js
	node --check fusion/bridge.mjs
	python -m unittest discover -s tests -v
