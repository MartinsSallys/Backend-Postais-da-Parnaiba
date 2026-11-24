#!/usr/bin/env bash
# =============================================================================
# Postais da Parnaiba — VPS Deploy Script
#
# Run this ON THE VPS, inside the cloned backend repository:
#   bash deploy.sh                 # HTTP only (no domain / no SSL)
#   bash deploy.sh example.com     # configure domain + Let's Encrypt SSL
#
# The frontend repo must live next to this directory:
#   /opt/postais/Backend-Postais_da_Parnaiba   <- this repo
#   /opt/postais/Postais-da-Parnaiba           <- frontend repo
#
# If the frontend is not there yet, set FRONTEND_REPO_URL and the script clones it:
#   FRONTEND_REPO_URL=https://github.com/USER/Postais-da-Parnaiba.git bash deploy.sh example.com
# =============================================================================

set -euo pipefail

# --- Configuration -----------------------------------------------------------
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="${FRONTEND_DIR:-$(dirname "$APP_DIR")/Postais-da-Parnaiba}"
FRONTEND_REPO_URL="${FRONTEND_REPO_URL:-}"
COMPOSE="docker compose"

# --- Colors ------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

# --- Checks ------------------------------------------------------------------
command -v docker >/dev/null 2>&1 || error "Docker nao instalado. Rode: curl -fsSL https://get.docker.com | sh"
docker compose version >/dev/null 2>&1 || error "Docker Compose v2 nao encontrado"

cd "$APP_DIR"

# --- Frontend -----------------------------------------------------------------
if [ ! -f "$FRONTEND_DIR/index.html" ]; then
    if [ -n "$FRONTEND_REPO_URL" ]; then
        info "Clonando frontend em $FRONTEND_DIR..."
        git clone "$FRONTEND_REPO_URL" "$FRONTEND_DIR"
    else
        error "Frontend nao encontrado em $FRONTEND_DIR. Clone o repositorio do site
       nesse caminho ou defina FRONTEND_REPO_URL."
    fi
fi

# --- Environment file -------------------------------------------------------
if [ ! -f .env ]; then
    info "Criando .env a partir do .env.example..."
    cp .env.example .env

    SECRET_KEY=$(openssl rand -hex 32)
    DB_PASS=$(openssl rand -hex 16)

    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" .env
    sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${DB_PASS}|" .env
    sed -i "s|^DEBUG=.*|DEBUG=false|" .env

    if [ -n "${ADMIN_PASSWORD:-}" ]; then
        sed -i "s|^ADMIN_PASSWORD=.*|ADMIN_PASSWORD=${ADMIN_PASSWORD}|" .env
    else
        echo ""
        warn "Defina uma senha forte para o admin."
        read -r -s -p "ADMIN_PASSWORD: " admin_pass
        echo ""
        [ -n "$admin_pass" ] || error "ADMIN_PASSWORD nao pode ser vazio"
        sed -i "s|^ADMIN_PASSWORD=.*|ADMIN_PASSWORD=${admin_pass}|" .env
    fi

    info ".env criado (SECRET_KEY e POSTGRES_PASSWORD gerados)."
else
    info ".env ja existe — mantendo."
fi

# Sanity checks on .env
grep -q "^SECRET_KEY=.\+" .env || error "SECRET_KEY vazio em .env (gere com: openssl rand -hex 32)"
if grep -q "CHANGE_ME" .env; then
    error "Ajuste os valores placeholder no .env antes de deployar"
fi
if grep -qE "^ADMIN_PASSWORD=(admin123|change-this-to-a-strong-password|)?$" .env; then
    error "Defina um ADMIN_PASSWORD forte no .env"
fi
if grep -qE "^POSTGRES_PASSWORD=(postgres|)?$" .env; then
    error "Defina um POSTGRES_PASSWORD forte no .env (openssl rand -hex 16)"
fi

# --- Domain / runtime nginx config ------------------------------------------
domain="${1:-}"

if [ -z "$domain" ]; then
    info "Sem dominio informado — usando HTTP puro."
    cp nginx.prod.conf nginx.runtime.conf
    $COMPOSE --profile prod up -d --build
    info "Deploy concluido (HTTP). Acesse http://IP_DA_VPS"
    exit 0
fi

info "Configurando dominio: ${domain}"

# Update CORS to the production origin
sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=[\"https://${domain}\",\"http://${domain}\",\"http://localhost\"]|" .env

cert_path="certbot/conf/live/${domain}/fullchain.pem"

if [ ! -f "$cert_path" ]; then
    info "Subindo stack em HTTP para o desafio ACME..."
    sed "s/server_name _;/server_name ${domain};/" nginx.prod.conf > nginx.runtime.conf
    $COMPOSE --profile prod up -d --build db prod-app prod-nginx

    # Wait for nginx to answer
    for i in $(seq 1 30); do
        if curl -fsS "http://localhost/.well-known/acme-challenge/" >/dev/null 2>&1 || \
           curl -fsS -o /dev/null "http://localhost/" >/dev/null 2>&1; then
            break
        fi
        sleep 2
    done

    if [ -n "${SSL_EMAIL:-}" ]; then
        email="$SSL_EMAIL"
    else
        read -p "E-mail para o Let's Encrypt: " email
    fi
    [ -n "$email" ] || error "E-mail obrigatorio para o Let's Encrypt"

    info "Obtendo certificado SSL..."
    mkdir -p certbot/conf certbot/www
    docker run --rm \
        -v "${APP_DIR}/certbot/conf:/etc/letsencrypt" \
        -v "${APP_DIR}/certbot/www:/var/www/certbot" \
        certbot/certbot certonly --webroot -w /var/www/certbot \
        --email "$email" --agree-tos --no-eff-email \
        -d "$domain"

    [ -f "$cert_path" ] || error "Nao foi possivel obter o certificado. Verifique o DNS de ${domain} apontando para esta VPS e a porta 80 liberada."
fi

info "Ativando HTTPS..."
sed "s|YOUR_DOMAIN|${domain}|g" nginx.prod.https.conf > nginx.runtime.conf
$COMPOSE --profile prod up -d --build

# --- Auto-renewal cron -------------------------------------------------------
cron_cmd="cd ${APP_DIR} && docker compose --profile cert run --rm certbot renew --webroot -w /var/www/certbot >/dev/null 2>&1 && docker compose restart prod-nginx >/dev/null 2>&1"
if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
    (crontab -l 2>/dev/null; echo "0 3 * * * ${cron_cmd}") | crontab -
    info "Renovacao automatica do SSL agendada (diariamente as 3h)."
fi

echo ""
info "=========================================="
info "  Deploy concluido!"
info "=========================================="
info "  Site:  https://${domain}"
info "  Admin: https://${domain}/admin/"
info "  API:   https://${domain}/api/health"
echo ""
info "  Logs:   make logs"
info "  Status: make status"
