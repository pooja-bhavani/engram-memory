#!/usr/bin/env bash
# Start the local Kokoro TTS microservice (real open-source neural voice).
# Requires: espeak-ng (brew install espeak-ng), the tts-venv (Python 3.12), and
# the Kokoro model files. Adjust the paths below if you relocate them.
set -euo pipefail

TTS_VENV="${TTS_VENV:-/Users/sagarbhavani/Desktop/congee-2/tts-venv}"
MODELS="${TTS_MODELS:-/Users/sagarbhavani/Desktop/congee-2/tts-models}"
ESPEAK_PREFIX="$(brew --prefix espeak-ng)"

export KOKORO_MODEL="$MODELS/kokoro-v1.0.onnx"
export KOKORO_VOICES="$MODELS/voices-v1.0.bin"
export KOKORO_VOICE="${KOKORO_VOICE:-em_alex}"
export KOKORO_SPEED="${KOKORO_SPEED:-0.85}"
export KOKORO_PORT="${KOKORO_PORT:-8765}"
export PHONEMIZER_ESPEAK_LIBRARY="$ESPEAK_PREFIX/lib/libespeak-ng.dylib"
export ESPEAKNG_DATA_PATH="$ESPEAK_PREFIX/share/espeak-ng-data"

exec "$TTS_VENV/bin/python" "$(dirname "$0")/tts_server.py"
