.PHONY: install api worker migrate migrate-create migrate-down test lint

install:
	pip install -r requirements.txt

api:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	celery -A app.worker.celery_app worker --loglevel=info

migrate:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(MSG)"

migrate-down:
	alembic downgrade -1

test:
	pytest tests/ -v --tb=short
