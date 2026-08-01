#!/bin/sh
# One-time bootstrap to obtain the initial Let's Encrypt certificate.
# Safe to re-run: it recreates a temporary self-signed cert, starts nginx,
# then replaces it with a real certificate for cloudmindai.in + www.
set -e

DOMAIN_ARGS="-d cloudmindai.in -d www.cloudmindai.in"
EMAIL="shivanshusoni1111@gmail.com"
LIVE_PATH="/etc/letsencrypt/live/cloudmindai.in"

echo "### 1/6 Building images ..."
docker compose build

echo "### 2/6 Creating a temporary self-signed cert so nginx can start ..."
docker compose run --rm --entrypoint sh certbot -c "\
  mkdir -p $LIVE_PATH && \
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout $LIVE_PATH/privkey.pem \
    -out $LIVE_PATH/fullchain.pem \
    -subj '/CN=localhost'"

echo "### 3/6 Starting backend + nginx ..."
docker compose up -d backend nginx

echo "### 4/6 Removing the temporary cert ..."
docker compose run --rm --entrypoint sh certbot -c "\
  rm -rf /etc/letsencrypt/live/cloudmindai.in \
         /etc/letsencrypt/archive/cloudmindai.in \
         /etc/letsencrypt/renewal/cloudmindai.in.conf"

echo "### 5/6 Requesting the real Let's Encrypt certificate ..."
docker compose run --rm --entrypoint certbot certbot certonly \
  --webroot -w /var/www/certbot \
  $DOMAIN_ARGS \
  --email "$EMAIL" \
  --rsa-key-size 4096 \
  --agree-tos --no-eff-email --non-interactive

echo "### 6/6 Reloading nginx and starting the auto-renewal service ..."
docker compose exec nginx nginx -s reload
docker compose up -d certbot

echo "### Done — HTTPS should be live at https://cloudmindai.in"
