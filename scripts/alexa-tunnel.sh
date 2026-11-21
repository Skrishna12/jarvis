#!/usr/bin/env bash
# Expose jarvis alexa (port 39847) with a public HTTPS URL. No ngrok account.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="$ROOT/.local/bin/cloudflared"
mkdir -p "$ROOT/.local/bin"
if [[ ! -x "$BIN" ]]; then
  echo "Downloading cloudflared (one-time)..."
  curl -fsSL -o "$BIN" \
    "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
  chmod +x "$BIN"
fi
echo "Leave jarvis alexa running in another terminal first."
echo "Copy the https://....trycloudflare.com URL into the Alexa skill endpoint."
exec "$BIN" tunnel --url "http://127.0.0.1:39847"
