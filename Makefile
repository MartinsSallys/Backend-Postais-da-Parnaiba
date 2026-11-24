# =============================================================================
# Postais da Parnaiba — Makefile
# =============================================================================

.PHONY: help dev prod stop restart status logs logs-app logs-nginx test lint \
	format clean nuke setup db-shell db-reset nginx-config ssl-init ssl-renew deploy

COMPOSE := docker compose

# --- Default target ----------------------------------------------------------
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# --- Setup -------------------------------------------------------------------
setup: ## Initial setup: copy .env and generate SECRET_KEY / DB password
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		SECRET=$$(openssl rand -hex 32); \
		DB_PASS=$$(openssl rand -hex 16); \
		sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$$SECRET|" .env; \
		sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$$DB_PASS|" .env; \
		echo "  ✓ .env created with generated SECRET_KEY and POSTGRES_PASSWORD"; \
		echo "  ⚠ Edit .env and set ADMIN_PASSWORD before deploying"; \
	else \
		echo "  ✓ .env already exists"; \
	fi

nginx-config: ## Create the runtime nginx config from the HTTP template
	@if [ ! -f nginx.runtime.conf ]; then \
		cp nginx.prod.conf nginx.runtime.conf; \
		echo "  ✓ nginx.runtime.conf created (HTTP)"; \
	else \
		echo "  ✓ nginx.runtime.conf already exists"; \
	fi

# --- Development -------------------------------------------------------------
dev: ## Start development environment (hot-reload)
	$(COMPOSE) --profile dev up -d --build
	@echo ""
	@echo "  ✓ Frontend: http://localhost"
	@echo "  ✓ API:      http://localhost/api/health"
	@echo ""

# --- Production --------------------------------------------------------------
prod: nginx-config ## Start production environment
	$(COMPOSE) --profile prod up -d --build
	@echo ""
	@echo "  ✓ App running on port 80/443"
	@echo ""

# --- Control -----------------------------------------------------------------
stop: ## Stop all containers
	$(COMPOSE) --profile dev --profile prod down

restart: ## Restart all running containers
	$(COMPOSE) restart

status: ## Show container status
	$(COMPOSE) ps

# --- Logs --------------------------------------------------------------------
logs: ## Tail all logs
	$(COMPOSE) logs -f --tail=100

logs-app: ## Tail app logs only
	$(COMPOSE) logs -f --tail=100 prod-app

logs-nginx: ## Tail nginx logs only
	$(COMPOSE) logs -f --tail=100 prod-nginx

# --- Database ----------------------------------------------------------------
db-shell: ## Open psql shell
	$(COMPOSE) exec db sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

db-reset: ## Reset database (DESTRUCTIVE)
	$(COMPOSE) down -v
	@echo "  ✓ Database reset. Run 'make prod' to start again."

# --- Development tools -------------------------------------------------------
test: ## Run tests
	python -m pytest -q

lint: ## Run linter
	ruff check .

format: ## Format code
	ruff format .

# --- SSL (Let's Encrypt) ----------------------------------------------------
ssl-init: ## Initialize SSL certificate (run once, asks for domain/email)
	@read -p "Domain name: " domain; \
	read -p "Email: " email; \
	mkdir -p certbot/conf certbot/www; \
	cp nginx.prod.conf nginx.runtime.conf; \
	$(COMPOSE) --profile prod up -d db prod-app prod-nginx; \
	docker run --rm \
		-v "$(PWD)/certbot/conf:/etc/letsencrypt" \
		-v "$(PWD)/certbot/www:/var/www/certbot" \
		certbot/certbot certonly --webroot -w /var/www/certbot \
		--email $$email --agree-tos --no-eff-email -d $$domain; \
	sed "s/YOUR_DOMAIN/$$domain/g" nginx.prod.https.conf > nginx.runtime.conf; \
	$(COMPOSE) restart prod-nginx; \
	echo "  ✓ HTTPS enabled for $$domain"

ssl-renew: ## Renew SSL certificates
	$(COMPOSE) --profile cert run --rm certbot renew --webroot -w /var/www/certbot
	$(COMPOSE) restart prod-nginx

# --- Deploy (VPS) -----------------------------------------------------------
deploy: ## Deploy to VPS (run inside the repo on the server)
	@echo "  → Pulling latest backend code..."
	git pull --ff-only origin main
	@echo "  → Pulling latest frontend code..."
	@if [ -d ../Postais-da-Parnaiba/.git ]; then \
		git -C ../Postais-da-Parnaiba pull --ff-only origin main; \
	else \
		echo "  ⚠ Frontend repo not found at ../Postais-da-Parnaiba"; \
	fi
	@echo "  → Building containers..."
	$(COMPOSE) --profile prod up -d --build
	@echo "  ✓ Deployed!"

# --- Cleanup -----------------------------------------------------------------
clean: ## Remove stopped containers, dangling images, unused networks
	$(COMPOSE) down --remove-orphans
	docker image prune -f
	docker network prune -f

nuke: ## Full cleanup: containers, volumes, images (DESTRUCTIVE)
	$(COMPOSE) down -v --remove-orphans
	docker image prune -a -f
	docker volume prune -f
