"""
app/pipeline.py — Core Pipeline Logic
Fungsi reusable untuk menjalankan STT -> Preprocessing -> LLM -> TTS.
Digunakan oleh FastAPI (main.py) dan Gradio (app.py).
"""

import os
import csv
import time
import logging
from pathlib import Path

from app.stt import transcribe_speech_to_text
from app.utils import normalize_transcript, tag_code_switching, get_dominant_language
from app.llm import generate_response
from app.tts import synthesize_speech

logger = logging.getLogger(__name__)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
CORPUS_DIR = os.path.join(ROOT_DIR, "corpus", "audio", "Audio_NLP")

# CSV column order
CSV_FIELDS = [
    "filename", "folder", "status", "mode",
    "raw_transcript", "normalized_transcript",
    "dominant_language", "ratio_id", "ratio_en", "ratio_ar",
    "language_segments",
    "wer", "cer",
    "llm_response",
    "tts_output_path",
    "latency_stt", "latency_llm", "latency_tts", "latency_total",
    "error",
]


# --- Metrics ---

def _levenshtein(s1: list, s2: list) -> int:
    """Levenshtein edit distance."""
    if len(s1) < len(s2):
        return _levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = range(len(s2) + 1)
    for c1 in s1:
        curr = [prev[0] + 1]
        for j, c2 in enumerate(s2):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (c1 != c2)))
        prev = curr
    return prev[-1]


def calculate_wer(ref: str, hyp: str) -> float:
    r, h = ref.lower().split(), hyp.lower().split()
    return round(min(1.0, _levenshtein(r, h) / len(r)), 4) if r else (1.0 if h else 0.0)


def calculate_cer(ref: str, hyp: str) -> float:
    r, h = list(ref.lower()), list(hyp.lower())
    return round(min(1.0, _levenshtein(r, h) / len(r)), 4) if r else (1.0 if h else 0.0)


def compute_language_ratio(segments: list) -> dict:
    """Hitung persentase kata per bahasa dari segmen code-switching."""
    total = sum(len(s["text"].split()) for s in segments)
    if total == 0:
        return {"ID": 0.0, "EN": 0.0, "AR": 0.0}
    ratio = {}
    for lang in ["ID", "EN", "AR"]:
        words = sum(len(s["text"].split()) for s in segments if s["lang"] == lang)
        ratio[lang] = round(words / total * 100, 1)
    return ratio


# --- Corpus Scanner ---

def collect_corpus_files(corpus_dir: str = None) -> list:
    """Scan Audio_NLP directory untuk semua file WAV (termasuk subdirektori)."""
    if corpus_dir is None:
        corpus_dir = CORPUS_DIR
    wav_files = []
    for root, _, files in os.walk(corpus_dir):
        for f in sorted(files):
            if f.lower().endswith(".wav"):
                wav_files.append(os.path.join(root, f))
    return wav_files


def get_folder_label(audio_path: str) -> str:
    """Identifikasi folder asal file (A, B, atau subfolder)."""
    parts = Path(audio_path).parts
    for i, p in enumerate(parts):
        if p == "Audio_NLP" and i + 1 < len(parts):
            return parts[i + 1]
    return "unknown"


# --- Core Pipeline ---

def run_pipeline(audio_path: str, mode: str = "preserve",
                 output_dir: str = None, ref_text: str = None) -> dict:
    """
    Jalankan full pipeline pada satu file audio.
    Returns dict berisi seluruh hasil dan metrik.
    """
    if output_dir is None:
        output_dir = OUTPUT_DIR

    audio_out_dir = os.path.join(output_dir, "audio")
    os.makedirs(audio_out_dir, exist_ok=True)

    filename = os.path.basename(audio_path)
    result = {
        "filename": filename,
        "folder": get_folder_label(audio_path),
        "audio_path": audio_path,
        "mode": mode,
        "status": "error",
        "error": "",
    }

    try:
        # 1. STT
        t0 = time.time()
        raw = transcribe_speech_to_text(audio_path)
        result["latency_stt"] = round(time.time() - t0, 3)
        result["raw_transcript"] = raw

        if not raw.strip():
            result["error"] = "Empty transcript"
            return result

        # 2. Preprocessing / Normalization
        normalized = normalize_transcript(raw)
        result["normalized_transcript"] = normalized

        # 3. Language Analysis
        segments = tag_code_switching(normalized)
        dominant = get_dominant_language(normalized)
        ratio = compute_language_ratio(segments)

        result["dominant_language"] = dominant
        result["language_segments"] = str(segments)
        result["ratio_id"] = ratio["ID"]
        result["ratio_en"] = ratio["EN"]
        result["ratio_ar"] = ratio["AR"]

        # 4. WER / CER (jika ada reference text)
        if ref_text:
            result["wer"] = calculate_wer(ref_text, normalized)
            result["cer"] = calculate_cer(ref_text, normalized)
        else:
            result["wer"] = "N/A"
            result["cer"] = "N/A"

        # 5. LLM
        t1 = time.time()
        llm_response = generate_response(normalized, mode=mode)
        result["latency_llm"] = round(time.time() - t1, 3)
        result["llm_response"] = llm_response

        # 6. TTS
        t2 = time.time()
        stem = Path(audio_path).stem
        output_wav = os.path.join(audio_out_dir, f"{stem}_response.wav")
        synthesize_speech(llm_response, output_wav)
        result["latency_tts"] = round(time.time() - t2, 3)
        result["tts_output_path"] = output_wav

        result["latency_total"] = round(
            result["latency_stt"] + result["latency_llm"] + result["latency_tts"], 3
        )
        result["status"] = "success"

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Pipeline error ({filename}): {e}")

    return result


# --- CSV Export ---

def results_to_csv(results: list, csv_path: str = None) -> str:
    """Export daftar hasil pipeline ke file CSV."""
    if csv_path is None:
        csv_path = os.path.join(OUTPUT_DIR, "pipeline_results.csv")

    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    logger.info(f"CSV disimpan ke: {csv_path}")
    return csv_path
