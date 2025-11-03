# Makefile
# Convenient commands for development and deployment

.PHONY: help install run docker-build docker-up docker-down ingest test clean

help: ## Show this help message
	@echo "GraphRAG System - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r requirements.txt

run: ## Run the Streamlit application
	streamlit run app.py

ingest: ## Run data ingestion script
	python scripts/ingest_data.py

embeddings: ## Generate vector embeddings
	python scripts/generate_embeddings.py

docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start all services with Docker
	docker-compose up -d
	@echo "Waiting for services to start..."
	@sleep 10
	@echo "Neo4j Browser: http://localhost:7474"
	@echo "Streamlit App: http://localhost:8501"

docker-down: ## Stop all Docker services
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f

docker-ingest: ## Run data ingestion in Docker
	docker-compose exec streamlit python scripts/ingest_data.py

docker-clean: ## Remove all Docker containers and volumes
	docker-compose down -v
	docker system prune -f

test: ## Run tests
	python -m pytest tests/

clean: ## Clean up temporary files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

setup: ## Complete setup (install + ingest)
	make install
	make ingest
	@echo "Setup complete! Run 'make run' to start the application."

dev: ## Start development environment
	docker-compose up neo4j -d
	@echo "Neo4j started. Run 'make run' in another terminal."

prod: ## Start production deployment
	make docker-build
	make docker-up
	@echo "Production environment started!"