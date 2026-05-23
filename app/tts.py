"""
app/tts.py — FASE 5: Text-to-Speech (Coqui TTS)
Sintesis suara dari teks menggunakan model Indonesian-VITS lokal.
Mendukung segmentasi per bahasa untuk pelafalan multibahasa yang lebih natural.
"""

import os
import logging
import tempfile
import uuid
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── Konfigurasi path model ───────────────────────────────────────────────────

BASE_DIR         = Path(__file__).resolve().parent
TTS_MODEL_PATH   = os.getenv("TTS_MODEL_PATH",   str(BASE_DIR / "coqui_tts" / "data" / "checkpoint_1260000-inference.pth"))
TTS_CONFIG_PATH  = os.getenv("TTS_CONFIG_PATH",  str(BASE_DIR / "coqui_tts" / "data" / "config.json"))
TTS_SPEAKERS_PATH = os.getenv("TTS_SPEAKERS_PATH", str(BASE_DIR / "coqui_tts" / "data" / "speakers.pth"))
TTS_SPEAKER_ID   = int(os.getenv("TTS_SPEAKER_ID", "0"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Inisialisasi model (lazy, dimuat saat pertama kali dipakai) ──────────────

_tts_instance = None


def _get_tts() -> "TTS":  # type: ignore[name-defined]
    """
    Memuat model Coqui TTS secara lazy (hanya sekali saat pertama dipanggil).
    Menggunakan model VITS lokal dari path yang dikonfigurasi.
    """
    global _tts_instance
    if _tts_instance is not None:
        return _tts_instance

    # Validasi keberadaan file model
    for path_name, path_val in [
        ("TTS_MODEL_PATH", TTS_MODEL_PATH),
        ("TTS_CONFIG_PATH", TTS_CONFIG_PATH),
    ]:
        if not os.path.exists(path_val):
            raise FileNotFoundError(
                f"File model TTS tidak ditemukan: {path_val}\n"
                f"Download dari: https://github.com/wikidepia/indonesian-tts\n"
                f"Letakkan di: app/coqui_tts/data/"
            )

    logger.info("[TTS] Memuat model Coqui TTS Indonesian-VITS...")

    try:
        from TTS.api import TTS  # type: ignore

        # Load model lokal menggunakan path langsung (bukan nama model online)
        tts = TTS(progress_bar=False)
        tts.load_tts_model_by_path(
            model_path=TTS_MODEL_PATH,
            config_path=TTS_CONFIG_PATH,
            gpu=False,
        )
        _tts_instance = tts
        logger.info("[TTS] Model berhasil dimuat.")
        return _tts_instance

    except ImportError as e:
        raise ImportError(
            f"Gagal memuat modul TTS. Pesan asli: {e}\n"
            "Pastikan PyTorch (torch) dan coqui-tts sudah terinstall dengan benar."
        )
    except Exception as e:
        raise RuntimeError(f"Gagal memuat model TTS: {e}")


# ─── Segmentasi per bahasa ────────────────────────────────────────────────────

def _merge_short_segments(segments: list[dict], min_words: int = 3) -> list[dict]:
    """
    Menggabungkan segmen yang terlalu pendek ke segmen tetangga
    agar hasil sintesis lebih natural.
    """
    if not segments:
        return []

    merged = []
    i = 0
    while i < len(segments):
        seg = segments[i]
        word_count = len(seg["text"].split())
        if word_count < min_words and merged:
            # Gabungkan ke segmen sebelumnya
            merged[-1]["text"] += " " + seg["text"]
        else:
            merged.append({"lang": seg["lang"], "text": seg["text"]})
        i += 1
    return merged


# ─── Fungsi utama ─────────────────────────────────────────────────────────────

def synthesize_speech(text: str, output_path: str) -> str:
    """
    Mengonversi teks ke file audio WAV.
    Untuk teks multibahasa, dilakukan sintesis per segmen lalu digabungkan.

    Args:
        text      : Teks yang akan disintesis (bisa berisi code-switching).
        output_path: Path file WAV output.

    Returns:
        Path file audio yang berhasil dibuat.
    """
    if not text or not text.strip():
        raise ValueError("Teks untuk sintesis tidak boleh kosong.")

    # Import utils untuk segmentasi bahasa
    from app.utils import tag_code_switching

    tts = _get_tts()
    segments = tag_code_switching(text)

    if not segments:
        segments = [{"lang": "ID", "text": text}]

    # Gabungkan segmen pendek
    segments = _merge_short_segments(segments)

    logger.info(f"[TTS] Mensintesis {len(segments)} segmen: {[s['lang'] for s in segments]}")

    if len(segments) == 1:
        # Sintesis langsung jika hanya satu segmen
        _synthesize_segment(tts, segments[0]["text"], output_path)
    else:
        # Sintesis per segmen → gabungkan jadi satu file
        _synthesize_and_merge(tts, segments, output_path)

    logger.info(f"[TTS] Audio disimpan ke: {output_path}")
    return output_path


def _synthesize_segment(tts, text: str, output_path: str) -> None:
    """Sintesis satu segmen teks ke file WAV."""
    tts.tts_to_file(
        text=text,
        file_path=output_path,
    )


def _synthesize_and_merge(tts, segments: list[dict], output_path: str) -> None:
    """
    Sintesis setiap segmen ke file WAV temporer, lalu gabungkan jadi satu.
    Menggunakan numpy/scipy untuk concatenate audio.
    """
    import numpy as np
    import soundfile as sf

    temp_files = []
    combined_audio = None
    sample_rate = None

    try:
        for i, seg in enumerate(segments):
            tmp_path = os.path.join(
                tempfile.gettempdir(),
                f"tts_seg_{uuid.uuid4().hex[:8]}_{i}.wav"
            )
            _synthesize_segment(tts, seg["text"], tmp_path)
            temp_files.append(tmp_path)

        # Baca dan gabungkan semua file WAV
        for tmp_path in temp_files:
            audio, sr = sf.read(tmp_path)
            if sample_rate is None:
                sample_rate = sr
            if combined_audio is None:
                combined_audio = audio
            else:
                # Tambahkan jeda singkat (0.3 detik silence) antar segmen
                silence = np.zeros(int(sr * 0.3), dtype=audio.dtype)
                combined_audio = np.concatenate([combined_audio, silence, audio])

        # Simpan file gabungan
        if combined_audio is not None and sample_rate is not None:
            sf.write(output_path, combined_audio, sample_rate)

    finally:
        # Hapus file temporer
        for tmp_path in temp_files:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


# ─── Test mandiri ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_text = "Halo, selamat datang di sistem percakapan multibahasa."
    out_file = "temp/test_output.wav"
    os.makedirs("temp", exist_ok=True)
    print(f"Mensintesis: '{test_text}'")
    result = synthesize_speech(test_text, out_file)
    print(f"Audio tersimpan di: {result}")
