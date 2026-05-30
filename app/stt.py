"""
app/stt.py — Speech-to-Text (Whisper.cpp)
Transkripsi audio ke teks menggunakan whisper.cpp binary lokal.
Semua audio di-remux terlebih dahulu via ffmpeg ke format WAV 16kHz Mono
untuk menjamin kompatibilitas penuh dengan whisper.cpp.
"""

import os
import tempfile
import subprocess
import logging

logger = logging.getLogger(__name__)

# Path langsung ke binary dan model whisper (tidak perlu .env)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WHISPER_BIN = os.path.join(ROOT_DIR, "models", "whisper.cpp", "build", "bin", "whisper-cli.exe")
WHISPER_MODEL = os.path.join(ROOT_DIR, "models", "whisper.cpp", "models", "ggml-small.bin")
FFMPEG_BIN = os.path.join(ROOT_DIR, "venv", "Scripts", "ffmpeg.exe")


def _convert_to_wav16k(input_path: str) -> str:
    """
    Remux/konversi file audio apa pun ke format WAV 16kHz Mono 16-bit PCM murni
    menggunakan ffmpeg. Diperlukan agar whisper.cpp dapat membaca semua jenis
    audio (termasuk file WAV yang isi binarynya sebenarnya M4A/AAC).

    Args:
        input_path: Path ke file audio asli (bisa WAV asli, WAV palsu, dll.)

    Returns:
        Path ke file WAV sementara yang sudah bersih (harus dihapus setelah dipakai).
    """
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".wav")
    os.close(tmp_fd)  # Tutup file descriptor, ffmpeg akan menulis ke path ini

    command = [
        FFMPEG_BIN,
        "-y",               # Overwrite output tanpa konfirmasi
        "-i", input_path,   # File input
        "-ar", "16000",     # Sample rate 16kHz (standar Whisper)
        "-ac", "1",         # Mono channel
        "-c:a", "pcm_s16le",# Codec PCM 16-bit Little Endian (WAV murni)
        tmp_path,
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if result.returncode != 0:
        os.remove(tmp_path)
        raise RuntimeError(
            f"FFmpeg gagal meremux audio '{os.path.basename(input_path)}': "
            f"{result.stderr.decode('utf-8', errors='replace')}"
        )

    return tmp_path


def transcribe_speech_to_text(audio_path: str) -> str:
    """
    Melakukan transkripsi audio ke teks menggunakan whisper.cpp.
    Mendukung deteksi bahasa otomatis untuk input multibahasa.
    Seluruh audio diremux terlebih dahulu agar dijamin kompatibel.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"File audio tidak ditemukan: {audio_path}")
    if not os.path.exists(WHISPER_BIN):
        raise FileNotFoundError(f"Binary Whisper tidak ditemukan: {WHISPER_BIN}")
    if not os.path.exists(WHISPER_MODEL):
        raise FileNotFoundError(f"Model Whisper tidak ditemukan: {WHISPER_MODEL}")
    if not os.path.exists(FFMPEG_BIN):
        raise FileNotFoundError(f"Binary FFmpeg tidak ditemukan: {FFMPEG_BIN}")

    tmp_wav_path = None
    try:
        # Remux audio ke WAV 16kHz murni sebelum diproses Whisper
        logger.debug(f"Meremux audio: {os.path.basename(audio_path)}")
        tmp_wav_path = _convert_to_wav16k(audio_path)

        command = [
            WHISPER_BIN,
            "-m", WHISPER_MODEL,
            "-f", tmp_wav_path,  # Gunakan file hasil remux
            "-nt",               # No timestamps
            "-l", "auto",        # Auto detect language
        ]

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
    finally:
        # Selalu hapus file temp meski ada error, agar tidak menumpuk di disk
        if tmp_wav_path and os.path.exists(tmp_wav_path):
            os.remove(tmp_wav_path)
