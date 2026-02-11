# Variables
IMAGE_NAME = booking-ba-scraper
CONTAINER_NAME = booking_interactive_scraper

# Ayuda
.DEFAULT_GOAL := help
.PHONY: help
help:
	@grep -h -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- COMANDOS DE DOCKER ---

up: ## Levantar el sistema interactivo (Bucle principal)
	docker-compose run --rm booking-scraper

build: ## Construir la imagen desde cero
	docker-compose build

clean: ## Limpiar contenedores y volúmenes huérfanos
	docker-compose down --volumes --remove-orphans


fix-perms: ## Corregir permisos de archivos creados por Docker
	sudo chown -R $(shell id -u):$(shell id -g) .

# --- COMANDOS LOCALES (Requiere uv instalado) ---

install: ## Instalación inicial de dependencias y binarios de Playwright
	uv sync
	uv run playwright install chromium --with-deps

test: ## Ejecutar la suite de pruebas unitarias
	uv run pytest

run-local: ## Ejecutar el scraper localmente sin Docker
	uv run python src/main.py

clc: ## Eliminar archivos temporales de Python
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
