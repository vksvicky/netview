PY := /Users/vivek/Development/netview/backend/.venv/bin/python
PIP := /Users/vivek/Development/netview/backend/.venv/bin/pip

.PHONY: venv backend ui run-backend run-ui test kill-port kill-ui-port

venv:
	python3 -m venv backend/.venv
	$(PIP) install -r backend/requirements.txt

kill-port:
	@echo "Killing any process running on port 8000..."
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || true

kill-ui-port:
	@echo "Killing any process running on port 5170..."
	@lsof -ti:5170 | xargs kill -9 2>/dev/null || true

backend: kill-port
	cd backend && $(PY) -c "from app.models import init_db; init_db()"
	cd backend && /Users/vivek/Development/netview/backend/.venv/bin/uvicorn app.main:app --reload --port 8000

ui: kill-ui-port
	cd ui && npm i && PORT=5170 npm run dev

test:
	cd backend && /Users/vivek/Development/netview/backend/.venv/bin/pytest -q


