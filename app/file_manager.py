"""
app/file_manager.py — Manajemen File Terpusat
Mengatur path temp, output, dan cleanup berdasarkan mode operasi.

Mode yang didukung:
  - "upload"  : file sementara dari mode Upload Audio
  - "record"  : file sementara dari mode Record Audio
  - "batch"   : output permanen dari mode Input Audio NLP (tidak pakai temp)
"""

import os
import time
import uuid
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ─── Root & Direktori Dasar ───────────────────────────────────────────────────

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMP_DIR   = os.path.join(ROOT_DIR, "temp")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")

# Subdirektori temp per mode
TEMP_UPLOAD = os.path.join(TEMP_DIR, "upload")
TEMP_RECORD = os.path.join(TEMP_DIR, "record")

# Subdirektori output per mode
OUTPUT_UPLOAD = os.path.join(OUTPUT_DIR, "upload")
OUTPUT_RECORD = os.path.join(OUTPUT_DIR, "record")
OUTPUT_BATCH  = os.path.join(OUTPUT_DIR, "batch")
OUTPUT_BATCH_AUDIO = os.path.join(OUTPUT_BATCH, "audio")

# Direktori corpus (read-only, bukan temp)
CORPUS_DIR = os.path.join(ROOT_DIR, "corpus", "audio", "Audio_NLP")


def _ensure_dirs() -> None:
    """Buat semua direktori yang diperlukan (idempotent)."""
    for d in [
        TEMP_UPLOAD, TEMP_RECORD,
        OUTPUT_UPLOAD, OUTPUT_RECORD,
        OUTPUT_BATCH_AUDIO,
    ]:
        os.makedirs(d, exist_ok=True)


_ensure_dirs()


# ─── Getter Path Temp ─────────────────────────────────────────────────────────

def get_temp_path(mode: str, suffix: str = ".wav") -> str:
    """
    Kembalikan path file temp unik berdasarkan mode.
    File ini harus dihapus menggunakan cleanup_temp_file() setelah selesai.

    Args:
        mode: "upload" atau "record"
        suffix: ekstensi file, default ".wav"

    Returns:
        Path lengkap ke file temp (belum tentu ada, harus dibuat oleh pemanggil).
    """
    if mode == "upload":
        base = TEMP_UPLOAD
    elif mode == "record":
        base = TEMP_RECORD
    else:
        raise ValueError(f"Mode tidak dikenal: '{mode}'. Gunakan 'upload' atau 'record'.")

    unique_name = f"{int(time.time())}_{uuid.uuid4().hex[:8]}{suffix}"
    return os.path.join(base, unique_name)


# ─── Getter Path Output ───────────────────────────────────────────────────────

def get_output_audio_path(mode: str, stem: str) -> str:
    """
    Kembalikan path output audio TTS berdasarkan mode.

    Args:
        mode: "upload", "record", atau "batch"
        stem: nama dasar file tanpa ekstensi (misal: "1685100000_a1b2c3d4")

    Returns:
        Path lengkap ke file output WAV.
    """
    if mode == "upload":
        return os.path.join(OUTPUT_UPLOAD, f"{stem}_response.wav")
    elif mode == "record":
        return os.path.join(OUTPUT_RECORD, f"{stem}_response.wav")
    elif mode == "batch":
        return os.path.join(OUTPUT_BATCH_AUDIO, f"{stem}_response.wav")
    else:
        raise ValueError(f"Mode tidak dikenal: '{mode}'.")


def get_batch_csv_path(name: str = "batch_results.csv") -> str:
    """Kembalikan path CSV hasil batch."""
    return os.path.join(OUTPUT_BATCH, name)


def get_batch_checkpoint_path() -> str:
    """Kembalikan path CSV checkpoint sementara batch (overwrite setiap N file)."""
    return os.path.join(OUTPUT_BATCH, "_checkpoint.csv")


# ─── Cleanup ──────────────────────────────────────────────────────────────────

def cleanup_temp_file(path: str) -> None:
    """
    Hapus satu file temp secara aman.
    Tidak akan raise exception jika file tidak ada atau gagal dihapus.
    """
    try:
        if path and os.path.exists(path):
            os.remove(path)
            logger.debug(f"[FileManager] Temp dihapus: {path}")
    except Exception as e:
        logger.warning(f"[FileManager] Gagal hapus temp {path}: {e}")


def cleanup_output_file(path: str) -> None:
    """
    Hapus satu file output secara aman (dipanggil saat user clear/input baru).
    Tidak akan raise exception jika file tidak ada atau gagal dihapus.
    """
    try:
        if path and os.path.exists(path):
            os.remove(path)
            logger.debug(f"[FileManager] Output dihapus: {path}")
    except Exception as e:
        logger.warning(f"[FileManager] Gagal hapus output {path}: {e}")


def cleanup_old_temp(max_age_seconds: int = 3600) -> None:
    """
    Garbage collector: hapus file di folder temp yang umurnya
    melebihi max_age_seconds (default 1 jam).
    Dipanggil sekali saat aplikasi startup.
    """
    now = time.time()
    for folder in [TEMP_UPLOAD, TEMP_RECORD]:
        if not os.path.isdir(folder):
            continue
        for fname in os.listdir(folder):
            fpath = os.path.join(folder, fname)
            try:
                if os.path.isfile(fpath) and (now - os.path.getmtime(fpath)) > max_age_seconds:
                    os.remove(fpath)
                    logger.info(f"[FileManager] GC hapus file kadaluarsa: {fpath}")
            except Exception as e:
                logger.warning(f"[FileManager] GC gagal hapus {fpath}: {e}")
