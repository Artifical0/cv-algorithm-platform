.PHONY: backend-dev backend-test manager-dev manager-test frontend-dev frontend-test frontend-build

backend-dev:
	cd backend && uv run uvicorn cv_platform.main:app --reload --port 8000

backend-test:
	cd backend && uv run pytest

manager-dev:
	cd services/algorithm-manager && uv run uvicorn algorithm_manager.main:app --reload --port 8010

manager-test:
	cd services/algorithm-manager && uv run pytest

frontend-dev:
	cd frontend && npm run dev

frontend-test:
	cd frontend && npm test

frontend-build:
	cd frontend && npm run build
