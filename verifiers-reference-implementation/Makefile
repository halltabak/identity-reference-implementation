IMAGE     ?= halltabak/digital-id-verifier
TAG       ?= latest
PLATFORMS ?= linux/amd64,linux/arm64
BUILDER   ?= digital-id-verifier-builder
CHART_DIR ?= ./python-server/helm/digital-id-verifier
RELEASE   ?= digital-id-verifier
NAMESPACE ?= digital-id-verifier-prd

.PHONY: help up down build buildx-setup push logs ps install uninstall lint template

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS=":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

up: ## Build and run locally via docker compose (http://localhost:5001)
	docker compose up --build

down: ## Stop and remove compose containers
	docker compose down

build: ## Build the container image via docker compose (host arch only)
	docker compose build


buildx-setup: ## Create a buildx builder for multi-arch builds (one-time)
	@docker buildx inspect $(BUILDER) >/dev/null 2>&1 || \
	  docker buildx create --name $(BUILDER) --driver docker-container --use
	@docker buildx use $(BUILDER)
	@docker buildx inspect --bootstrap >/dev/null

push: buildx-setup ## Build multi-arch image ($(PLATFORMS)) and push to registry
	docker buildx build \
	  --platform $(PLATFORMS) \
	  --tag $(IMAGE):$(TAG) \
	  --push \
	  ./python-server

logs: ## Tail compose logs
	docker compose logs -f

ps: ## Show compose container status
	docker compose ps

install: ## Install/upgrade the Helm release into $(NAMESPACE)
	helm upgrade --install $(RELEASE) $(CHART_DIR) \
	  --namespace $(NAMESPACE) --create-namespace

uninstall: ## Uninstall the Helm release
	helm uninstall $(RELEASE) --namespace $(NAMESPACE)

lint: ## Lint the Helm chart
	helm lint $(CHART_DIR)

template: ## Render chart manifests to stdout
	helm template $(RELEASE) $(CHART_DIR) --namespace $(NAMESPACE)
