#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
log_directory="$(mktemp -d)"
playwright_image="mcr.microsoft.com/playwright:v1.62.1-noble"

cd "${repository_root}/services/api"
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 >"${log_directory}/api.log" 2>&1 &
api_pid=$!
cd "${repository_root}"
API_PROXY_TARGET=http://127.0.0.1:8000 npm run start --workspace @math-coach/student-web \
  >"${log_directory}/web.log" 2>&1 &
web_pid=$!

cleanup() {
  kill "${api_pid}" "${web_pid}" 2>/dev/null || true
  wait "${api_pid}" "${web_pid}" 2>/dev/null || true
  rm -rf -- "${log_directory}"
}
trap cleanup EXIT

wait_for_server() {
  local url="$1"
  local process_id="$2"
  local log_file="$3"
  for _attempt in {1..120}; do
    if curl --fail --silent "${url}" >/dev/null; then
      return 0
    fi
    if ! kill -0 "${process_id}" 2>/dev/null; then
      echo "Server exited before becoming ready: ${url}" >&2
      sed -n '1,240p' "${log_file}" >&2
      return 1
    fi
    sleep 1
  done
  echo "Timed out waiting for server: ${url}" >&2
  sed -n '1,240p' "${log_file}" >&2
  return 1
}

wait_for_server "http://127.0.0.1:8000/api/v1/health" "${api_pid}" "${log_directory}/api.log"
wait_for_server "http://127.0.0.1:3000" "${web_pid}" "${log_directory}/web.log"

docker run --rm \
  --network host \
  --user "$(id -u):$(id -g)" \
  --env "CI=${CI:-}" \
  --env HOME=/tmp \
  --env PLAYWRIGHT_EXTERNAL_SERVERS=1 \
  --env "VISUAL_QA=${VISUAL_QA:-}" \
  --volume "${repository_root}:/work" \
  --workdir /work \
  "${playwright_image}" \
  npx playwright test
