.PHONY: test lint build sandbox
test:
	cd backend && pytest -q
lint:
	cd backend && ruff check app tests migrations
build:
	cd frontend && npm ci && npm run build
sandbox:
	docker build -f Dockerfile.sandbox -t agentbench-sandbox:1 .
