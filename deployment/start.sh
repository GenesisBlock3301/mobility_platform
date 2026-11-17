#!/bin/sh
# One-step start for macOS and Linux: run `sh deployment/start.sh` from the project folder.
# Checks Docker, creates .env with random secrets on first run, picks free ports,
# starts every service, waits until the site answers, then opens it.
set -eu

cd "$(dirname "$0")"

say() { printf '\n%s\n' "$*"; }
fail() { printf '\n[!] %s\n\n' "$*" >&2; exit 1; }

# 1. Docker must be installed and running.
command -v docker >/dev/null 2>&1 ||
  fail "Docker is not installed. Install Docker Desktop from https://www.docker.com/products/docker-desktop/ then run this again."
docker info >/dev/null 2>&1 ||
  fail "Docker is installed but not running. Open the Docker Desktop app, wait until it says 'running', then run this again."
docker compose version >/dev/null 2>&1 ||
  fail "Docker Compose is missing. Update Docker Desktop to the latest version, then run this again."

# A port is busy if something answers on it. lsof alone misses ports published by Docker.
port_busy() {
  if command -v nc >/dev/null 2>&1; then nc -z 127.0.0.1 "$1" >/dev/null 2>&1
  else command -v lsof >/dev/null 2>&1 && lsof -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
  fi
}
free_port() {
  p=$1
  while port_busy "$p"; do p=$((p + 1)); done
  echo "$p"
}
secret() { LC_ALL=C tr -dc 'a-f0-9' </dev/urandom | head -c 32; }

# 2. First run only: create .env with random secrets and free ports.
if [ ! -f .env ]; then
  say "First run: creating settings (.env) with random passwords..."
  web_port=$(free_port 3000)
  api_port=$(free_port 8000)
  [ "$api_port" = "$web_port" ] && api_port=$(free_port $((web_port + 1)))
  sed \
    -e "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$(secret)/" \
    -e "s/^APP_DB_PASSWORD=.*/APP_DB_PASSWORD=$(secret)/" \
    -e "s/^INTERNAL_TOKEN=.*/INTERNAL_TOKEN=$(secret)/" \
    -e "s/^WEB_PORT=.*/WEB_PORT=$web_port/" \
    -e "s/^API_PORT=.*/API_PORT=$api_port/" \
    .env.example >.env
fi

WEB_PORT=$(sed -n 's/^WEB_PORT=//p' .env)
WEB_PORT=${WEB_PORT:-3000}
URL="http://localhost:$WEB_PORT"

# 3. Build and start everything in the background.
say "Starting the app. The first time this downloads and builds everything, which can take 5-10 minutes..."
docker compose up --build --detach ||
  fail "The app did not start. Run 'docker compose logs' in the deployment folder and send the output to the developer."

# 4. Wait for the website to answer (up to 5 minutes).
say "Waiting for the website to be ready..."
i=0
until curl -fsS -o /dev/null "$URL" 2>/dev/null; do
  i=$((i + 1))
  [ "$i" -gt 150 ] &&
    fail "The website did not respond after 5 minutes. Run 'docker compose logs' in the deployment folder and send the output to the developer."
  sleep 2
done

say "Ready: $URL"
say "To stop the app later, run:  sh deployment/stop.sh"
if command -v open >/dev/null 2>&1; then open "$URL"
elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1 || true
fi
