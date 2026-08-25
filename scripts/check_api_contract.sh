#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "${temporary_directory}"' EXIT

cd "${repository_root}/services/api"
uv run python -m app.scripts.export_openapi "${temporary_directory}/openapi.json"
cd "${repository_root}"
npx openapi-typescript "${temporary_directory}/openapi.json" \
  -o "${temporary_directory}/schema.d.ts" >/dev/null

diff -u packages/api-client/openapi.json "${temporary_directory}/openapi.json"
diff -u packages/api-client/src/schema.d.ts "${temporary_directory}/schema.d.ts"
echo "API contract validation passed: OpenAPI and TypeScript declarations are current."
