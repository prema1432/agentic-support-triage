.PHONY: up down logs test seed clean api-install api-dev web-install web-dev

up:
	docker compose up -d --build
	@echo "API: http://localhost:8000/docs  Web: http://localhost:5173"

down:
	docker compose down

logs:
	docker compose logs -f api

test:
	cd backend && python3 -m pytest -q

seed:
	cd backend && python3 -m scripts.seed

clean:
	docker compose down -v

api-install:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

api-dev:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000

web-install:
	cd frontend && npm install

web-dev:
	cd frontend && npm run dev
