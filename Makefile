.PHONY: backend-dev backend-test manager-dev manager-test frontend-dev frontend-test frontend-build db-install db-current db-history db-upgrade db-sql

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

db-install:
	pwsh -File scripts/database.ps1 -Action install

db-current:
	pwsh -File scripts/database.ps1 -Action current

db-history:
	pwsh -File scripts/database.ps1 -Action history

db-upgrade:
	pwsh -File scripts/database.ps1 -Action upgrade -Revision head

db-sql:
	pwsh -File scripts/database.ps1 -Action sql -Revision head
