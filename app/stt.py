"""
app/stt.py — Speech-to-Text (Whisper.cpp)
Transkripsi audio ke teks menggunakan whisper.cpp binary lokal.
"""

import os
import subprocess
import logging

logger = logging.getLogger(__name__)

# Path langsung ke binary dan model whisper (tidak perlu .env)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WHISPER_BIN = os.path.join(ROOT_DIR, "models", "whisper.cpp", "build", "bin", "whisper-cli.exe")
WHISPER_MODEL = os.path.join(ROOT_DIR, "models", "whisper.cpp", "models", "ggml-small.bin")


def transcribe_speech_to_text(audio_path: str) -> str:
    """
    Melakukan transkripsi audio ke teks menggunakan whisper.cpp.
    Mendukung deteksi bahasa otomatis untuk input multibahasa.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"File audio tidak ditemukan: {audio_path}")
    if not os.path.exists(WHISPER_BIN):
        raise FileNotFoundError(f"Binary Whisper tidak ditemukan: {WHISPER_BIN}")
    if not os.path.exists(WHISPER_MODEL):
        raise FileNotFoundError(f"Model Whisper tidak ditemukan: {WHISPER_MODEL}")

    command = [
        WHISPER_BIN,
        "-m", WHISPER_MODEL,
        "-f", audio_path,
        "-nt",          # No timestamps
        "-l", "auto",   # Auto detect language
    ]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            encoding="utf-8",
        )

        clean_lines = []
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("[") and not line.startswith("whisper_"):
                clean_lines.append(line)

        return " ".join(clean_lines)

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Gagal transkripsi: {e.stderr or str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error saat transkripsi: {str(e)}")
