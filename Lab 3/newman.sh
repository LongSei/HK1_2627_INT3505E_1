#!/usr/bin/env bash
set -e
BASE_URL="${BASE_URL:-http://127.0.0.1:5000}"
mkdir -p reports
npx -y newman run books-api.postman_collection.json \
  -e postman/local.postman_environment.json \
  --env-var base_url="$BASE_URL" \
  -r cli,junit --reporter-junit-export reports/junit.xml
