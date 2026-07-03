"""Local Kokoro TTS microservice — a real, open-source neural voice.

Runs in its own Python 3.12 venv (Kokoro's ML deps don't have 3.14 wheels) and
loads the model ONCE, then serves MP3 narration over HTTP so the main app never
pays model-load latency. Fully local, no API key, nothing leaves the machine —
which is exactly the self-hosted, open-source story Engram is built on.

Launch (paths via env, with espeak-ng wired for phonemization):
    KOKORO_MODEL=.../kokoro-v1.0.onnx KOKORO_VOICES=.../voices-v1.0.bin \
    PHONEMIZER_ESPEAK_LIBRARY=$(brew --prefix espeak-ng)/lib/libespeak-ng.dylib \
    ESPEAKNG_DATA_PATH=$(brew --prefix espeak-ng)/share/espeak-ng-data \
    tts-venv/bin/python tts_server.py
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import lameenc
import numpy as np
from kokoro_onnx import Kokoro

MODEL = os.environ["KOKORO_MODEL"]
VOICES = os.environ["KOKORO_VOICES"]
DEFAULT_VOICE = os.environ.get("KOKORO_VOICE", "am_michael")  # warm male narrator
SPEED = float(os.environ.get("KOKORO_SPEED", "0.92"))         # unhurried, reminiscing
PORT = int(os.environ.get("KOKORO_PORT", "8765"))

_kokoro = Kokoro(MODEL, VOICES)


def synth_mp3(text: str, voice: str) -> bytes:
    samples, sr = _kokoro.create(text, voice=voice or DEFAULT_VOICE, speed=SPEED, lang="en-us")
    pcm = (np.clip(np.asarray(samples), -1.0, 1.0) * 32767.0).astype("<i2").tobytes()
    enc = lameenc.Encoder()
    enc.set_bit_rate(128)
    enc.set_in_sample_rate(int(sr))
    enc.set_channels(1)
    enc.set_quality(2)
    return bytes(enc.encode(pcm) + enc.flush())


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # health check
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n) or b"{}")
            mp3 = synth_mp3(body.get("text", ""), body.get("voice", DEFAULT_VOICE))
            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Content-Length", str(len(mp3)))
            self.end_headers()
            self.wfile.write(mp3)
        except Exception as e:  # noqa: BLE001
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def log_message(self, *a):  # quiet
        pass


if __name__ == "__main__":
    print(f"Kokoro TTS ready on :{PORT} (voice={DEFAULT_VOICE}, speed={SPEED})", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
