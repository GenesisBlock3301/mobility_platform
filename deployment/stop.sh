#!/bin/sh
# Stops the app. Profiles and shortlists are kept for next time.
# To delete all data as well, run in this folder: docker compose down -v
set -eu
cd "$(dirname "$0")"
docker compose down
printf '\nThe app is stopped. Start it again with:  sh deployment/start.sh\n\n'
