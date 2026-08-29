#!/usr/bin/env bash
# Arranca LiteLLM como puente: Agent SDK (formato Anthropic) -> suscripción de ChatGPT (Codex).
# Instalar una vez:  uv tool install "litellm[proxy]==1.98.0"
# Llave local que usa el SDK: sk-taller-local (ver config.yaml)
cd "$(dirname "$0")"
export CHATGPT_USER_AGENT="codex_cli_rs/0.151.0 (Mac OS 27.0.0; arm64) cmux"
exec litellm --config config.yaml --port 4000
