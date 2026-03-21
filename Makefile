.PHONY: lint format check test run help

lint:
	ruff check .

format:
	ruff format .

check: format
	ruff check --fix .

test:
	pytest

run:
	uvicorn app.main:app --reload --port 8000

help:
	@echo "Доступные команды:"
	@echo "  make lint    — проверить код на ошибки"
	@echo "  make format  — отформатировать код"
	@echo "  make check   — исправить ошибки + форматирование"
	@echo "  make test    — запустить тесты"
	@echo "  make run     — запустить сервер разработки"
	@echo "  make help    — показать эту справку"