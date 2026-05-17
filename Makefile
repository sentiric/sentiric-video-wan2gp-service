.PHONY: setup clean dev-up dev-down dev-logs test

VENV = .venv
UV = uv

setup:
	@echo "🚀 Setting up virtual environment..."
	$(UV) venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt

clean:
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +

dev-up:
	@echo "🔥 Starting Wan2.1 Video environment..."
	docker compose up --build -d

dev-logs:
	@echo "📋 Tailing logs..."
	docker compose logs -f video-wan2gp-service

dev-down:
	@echo "🛑 Shutting down..."
	docker compose down -v

setup-test:
	uv venv
	uv pip install grpcio 
	uv pip install sentiric-contracts-py git+https://github.com/sentiric/sentiric-contracts.git@v1.25.0

test:
	@echo "🧪 Running Wan2.1 Video Test..."
	@. $(VENV)/bin/activate && python test_client.py