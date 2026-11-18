"""Transcribe la voz de Luis con Whisper (local) y guarda cada palabra con su tiempo en voz/palabras.json."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

audio = Path(sys.argv[1])
modelo = WhisperModel("small", device="cpu", compute_type="int8")
# El audio se decodifica con ffmpeg (16 kHz, mono) para no depender de PyAV
crudo = subprocess.run(["ffmpeg", "-v", "error", "-i", str(audio), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                       capture_output=True, check=True).stdout
muestras = np.frombuffer(crudo, np.int16).astype(np.float32) / 32768.0
segmentos, info = modelo.transcribe(muestras, language="es", word_timestamps=True, vad_filter=True,
                                    initial_prompt="MongoDB, Spring Boot, Compass, CAPI, leads, dashboard, DNS, VPS")
palabras = []
for s in segmentos:
    for w in s.words:
        palabras.append({"t0": round(w.start, 2), "t1": round(w.end, 2), "p": w.word.strip()})
salida = audio.parent / "palabras.json"
salida.write_text(json.dumps(palabras, ensure_ascii=False), encoding="utf-8")
print(f"{len(palabras)} palabras · {info.duration:.0f} s → {salida}")
