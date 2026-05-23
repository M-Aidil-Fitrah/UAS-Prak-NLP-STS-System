"""
app/tts.py — Text-to-Speech (Coqui TTS VITS)
Sintesis suara dari teks menggunakan model Indonesian-VITS lokal.
Mendukung segmentasi per bahasa untuk pelafalan multibahasa.
"""

import os
import logging
import tempfile
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

# Path langsung ke model TTS (tidak perlu .env)
BASE_DIR = Path(__file__).resolve().parent
TTS_MODEL_PATH = str(BASE_DIR / "coqui_tts" / "data" / "checkpoint_1260000-inference.pth")
TTS_CONFIG_PATH = str(BASE_DIR / "coqui_tts" / "data" / "config.json")
TTS_SPEAKER_ID = 0

# Lazy-loaded singleton
_tts_instance = None


def _get_tts():
    """Memuat model Coqui TTS secara lazy (sekali saat pertama dipanggil)."""
    global _tts_instance
    if _tts_instance is not None:
        return _tts_instance

    for name, path in [("Model", TTS_MODEL_PATH), ("Config", TTS_CONFIG_PATH)]:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"File {name} TTS tidak ditemukan: {path}\n"
                "Download dari: https://github.com/wikidepia/indonesian-tts"
            )

    logger.info("[TTS] Memuat model Coqui TTS Indonesian-VITS...")

    try:
        from TTS.api import TTS

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
        raise ImportError(f"Gagal import TTS: {e}. Pastikan coqui-tts terinstall.")
    except Exception as e:
        raise RuntimeError(f"Gagal memuat model TTS: {e}")


def _merge_short_segments(segments: list, min_words: int = 3) -> list:
    """Gabungkan segmen pendek ke segmen tetangga agar sintesis lebih natural."""
    if not segments:
        return []
    merged = []
    for seg in segments:
        word_count = len(seg["text"].split())
        if word_count < min_words and merged:
            merged[-1]["text"] += " " + seg["text"]
        else:
            merged.append({"lang": seg["lang"], "text": seg["text"]})
    return merged


def synthesize_speech(text: str, output_path: str) -> str:
    """
    Konversi teks ke file audio WAV.
    Untuk teks multibahasa, sintesis per segmen lalu digabungkan.
    """
    if not text or not text.strip():
        raise ValueError("Teks untuk sintesis tidak boleh kosong.")

    from app.utils import tag_code_switching

    # Pastikan direktori output ada
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    tts = _get_tts()
    segments = tag_code_switching(text)

    if not segments:
        segments = [{"lang": "ID", "text": text}]

    segments = _merge_short_segments(segments)
    logger.info(f"[TTS] Mensintesis {len(segments)} segmen: {[s['lang'] for s in segments]}")

    if len(segments) == 1:
        _synthesize_segment(tts, segments[0]["text"], output_path)
    else:
        _synthesize_and_merge(tts, segments, output_path)

    logger.info(f"[TTS] Audio disimpan ke: {output_path}")
    return output_path


def _synthesize_segment(tts, text: str, output_path: str) -> None:
    """Sintesis satu segmen teks ke file WAV."""
    speaker = tts.speakers[TTS_SPEAKER_ID] if getattr(tts, "is_multi_speaker", False) and tts.speakers else None
    tts.tts_to_file(text=text, speaker=speaker, file_path=output_path)


def _synthesize_and_merge(tts, segments: list, output_path: str) -> None:
    """Sintesis per segmen ke file WAV temporer, lalu gabungkan."""
    import numpy as np
    import soundfile as sf

    temp_files = []
    combined_audio = None
    sample_rate = None

    try:
        for i, seg in enumerate(segments):
            tmp_path = os.path.join(tempfile.gettempdir(), f"tts_seg_{uuid.uuid4().hex[:8]}_{i}.wav")
            _synthesize_segment(tts, seg["text"], tmp_path)
            temp_files.append(tmp_path)

        for tmp_path in temp_files:
            audio, sr = sf.read(tmp_path)
            if sample_rate is None:
                sample_rate = sr
            if combined_audio is None:
                combined_audio = audio
            else:
                silence = np.zeros(int(sr * 0.3), dtype=audio.dtype)
                combined_audio = np.concatenate([combined_audio, silence, audio])

        if combined_audio is not None and sample_rate is not None:
            sf.write(output_path, combined_audio, sample_rate)
    finally:
        for tmp_path in temp_files:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
