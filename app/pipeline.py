"""
app/pipeline.py — Core Pipeline Logic
Fungsi reusable untuk menjalankan STT -> Preprocessing -> LLM -> TTS.
Digunakan oleh FastAPI (main.py) dan Gradio (app.py).
"""

import os
import re
import csv
import time
import logging
from pathlib import Path

from app.stt import transcribe_speech_to_text
from app.utils import normalize_transcript, tag_code_switching, get_dominant_language
from app.llm import generate_response
from app.tts import synthesize_speech
from app.file_manager import (
    CORPUS_DIR,
    get_output_audio_path, get_batch_csv_path,
)

logger = logging.getLogger(__name__)

# --- Dictionary / Kunci Jawaban (Dual-Reference) ---
# Setiap entry adalah list berisi 1 atau 2 referensi:
# - 1 referensi: kalimat Indonesia/Inggris (tidak perlu versi fonetik)
# - 2 referensi: [versi Arab formal (ground truth), versi fonetik Latin (untuk Whisper)]
REFERENCE_TRANSCRIPTS: dict[str, list[str]] = {
    "01": [
        "Aku mau book flight ke Jeddah minggu depan, bisa bantu schedule?"
    ],
    "02": [
        "Aku butuh travel umrah simple tapi include Madinah visit"
    ],
    "03": [
        "Can you help aku arrange transport dari Jeddah ke Madinah tomorrow"
    ],
    "04": [
        "Explain step by step cara apply visa Saudi dengan benar"
    ],
    "05": [
        "يَا أَخِي، أُرِيدُ book flight إِلَى Jeddah الأُسْبُوع القَادِم. هَلْ bisa bantu أَجِد أَفْضَل schedule وَرِحْلَةً مُبَاشِرَةً؟",
        "ya akhi uridu book flight ila Jeddah al usbuu al qadim hal bisa bantu ajid afdhal schedule wa rihlatan mubashirah"
    ],
    "06": [
        "أُرِيدُ arrange transport مِن Jeddah إِلَى Madinah غَدًا",
        "uridu arrange transport min Jeddah ila Madinah ghadan"
    ],
    "07": [
        "Book flight ke Jeddah lalu lanjut ke Madinah, schedule terbaik kapan"
    ],
    "08": [
        "اريد schedule trip dari Jeddah ke Makkah besok pagi",
        "uridu schedule trip dari Jeddah ke Makkah besok pagi"
    ],
    "09": [
        "ممكن book transport dari Makkah ke Madinah untuk besok",
        "mumkin book transport dari Makkah ke Madinah untuk besok"
    ],
    "10": [
        "Apa perbedaan umrah dan hajj secara detail dalam Islam"
    ],
    "11": [
        "Kenapa fasting di Ramadan itu wajib bagi Muslim"
    ],
    "12": [
        "Bagaimana proses visa Saudi untuk umrah dari Indonesia sekarang"
    ],
    "13": [
        "Jelaskan step by step cara booking flight ke Jeddah secara online"
    ],
    "14": [
        "How to prepare dokumen umrah dari Indonesia dengan benar"
    ],
    "15": [
        "Tolong buat checklist persiapan umrah termasuk barang wajib dibawa"
    ],
    "16": [
        "Guide aku cara pilih hotel di Makkah dekat Haram dengan budget terbatas"
    ],
    "17": [
        "Menurut kamu belajar bahasa Arab itu susah gak untuk pemula"
    ],
    "18": [
        "I feel overwhelmed dengan persiapan umrah, ada tips sederhana?"
    ],
    "19": [
        "احيانا saya bingung mulai dari mana untuk umrah",
        "ahyanan saya bingung mulai dari mana untuk umrah"
    ],
    "20": [
        "Translate ke English: aku mau pergi ke Makkah minggu depan"
    ],
}

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


def _clean_for_wer(text: str) -> str:
    import re
    # Hapus harakat bahasa Arab (diacritics)
    text = re.sub(r'[\u064B-\u065F\u0670\u0640]', '', text)
    # Normalisasi Ortografi Arab
    text = re.sub(r'[أإآ]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    # Hapus tanda baca umum
    text = re.sub(r'[.,!?؛،؟"\'\-_]', ' ', text)
    # Bersihkan spasi ganda
    text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()


def calculate_wer(ref: str, hyp: str) -> float:
    r = _clean_for_wer(ref).split()
    h = _clean_for_wer(hyp).split()
    return round(min(1.0, _levenshtein(r, h) / len(r)), 4) if r else (1.0 if h else 0.0)


def calculate_cer(ref: str, hyp: str) -> float:
    r = list(_clean_for_wer(ref).replace(" ", ""))
    h = list(_clean_for_wer(hyp).replace(" ", ""))
    return round(min(1.0, _levenshtein(r, h) / len(r)), 4) if r else (1.0 if h else 0.0)


def calculate_wer_best(refs: list[str], hyp: str) -> float:
    """Hitung WER terbaik (minimum) dari semua referensi yang tersedia (Dual-Reference)."""
    if not refs:
        return 1.0
    return min(calculate_wer(ref, hyp) for ref in refs)


def calculate_cer_best(refs: list[str], hyp: str) -> float:
    """Hitung CER terbaik (minimum) dari semua referensi yang tersedia (Dual-Reference)."""
    if not refs:
        return 1.0
    return min(calculate_cer(ref, hyp) for ref in refs)


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


# --- Corpus Scanner & Validasi Nama File ---

# Pola nama file sesuai dictionary.md: {id}_{utteranceid}.wav
# id       = 4 digit (2 digit awal + 2 digit akhir NPM)
# uttid    = 2 digit angka (01–20)
_FILENAME_RE = re.compile(r"^(\d{4})_(\d{2})\.wav$", re.IGNORECASE)


def normalize_and_validate_filename(filename: str) -> tuple[bool, str, str, str, str]:
    """
    Fuzzy parsing nama file audio dan validasi.
    
    Returns:
        (is_valid, student_id, utterance_id, normalized_filename, reason)
    """
    norm = filename.lower()
    norm = norm.replace(".m4a", "")
    norm = re.sub(r'\(\d+\)', '', norm)  # hapus (1), (2), dsb
    
    # Mencari pola: 4 digit (NPM) + (opsional _audio) + 1/2 digit (Utt ID)
    match = re.search(r'^(\d{4})_?(?:audio)?(\d{1,2})\.wav$', norm)
    if not match:
        return False, "", "", norm, f"Gagal dinormalisasi (bukan NNNN_NN.wav), dapat: '{filename}'"

    student_id = match.group(1)
    utterance_id = match.group(2).zfill(2)  # pastikan 2 digit
    normalized_filename = f"{student_id}_{utterance_id}.wav"

    if utterance_id not in REFERENCE_TRANSCRIPTS:
        return (
            False, student_id, utterance_id, normalized_filename,
            f"Utterance ID '{utterance_id}' tidak ada di kamus (01–20)"
        )

    return True, student_id, utterance_id, normalized_filename, ""


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


def collect_corpus_files_with_meta(corpus_dir: str = None) -> list:
    """
    Scan Audio_NLP dan kembalikan metadata validasi per file.

    Returns:
        list of dict: {
            "path": str,
            "filename": str,
            "folder": str,
            "is_valid": bool,
            "student_id": str,
            "utterance_id": str,
            "reason": str,
        }
    """
    files = collect_corpus_files(corpus_dir)
    temp_dict = {}

    for wav_path in files:
        fname = os.path.basename(wav_path)
        is_valid, sid, uid, norm_fname, reason = normalize_and_validate_filename(fname)
        file_size = os.path.getsize(wav_path)

        new_meta = {
            "path":         wav_path,
            "filename":     fname,
            "normalized":   norm_fname,
            "folder":       get_folder_label(wav_path),
            "is_valid":     is_valid,
            "student_id":   sid,
            "utterance_id": uid,
            "reason":       reason,
            "size":         file_size
        }

        # Deduplikasi: ambil file terbesar jika normalized_filename sama
        if norm_fname in temp_dict:
            if temp_dict[norm_fname]["size"] < file_size:
                temp_dict[norm_fname] = new_meta
        else:
            temp_dict[norm_fname] = new_meta

    meta = list(temp_dict.values())
    meta.sort(key=lambda x: (x["student_id"], x["utterance_id"]))
    return meta


def get_folder_label(audio_path: str) -> str:
    """Identifikasi folder asal file (A, B, atau subfolder)."""
    parts = Path(audio_path).parts
    for i, p in enumerate(parts):
        if p == "Audio_NLP" and i + 1 < len(parts):
            return parts[i + 1]
    return "unknown"


# --- Core Pipeline ---

def run_pipeline(audio_path: str, mode: str = "preserve",
                 pipeline_mode: str = "batch",
                 ref_text: str = None,
                 student_id: str = None,
                 normalized_filename: str = None) -> dict:
    """
    Jalankan full pipeline pada satu file audio.

    Args:
        audio_path    : path ke file audio input
        mode          : "preserve" atau "normalize" (mode LLM)
        pipeline_mode : "upload", "record", atau "batch" (menentukan folder output)
        ref_text      : teks referensi untuk WER/CER; None = auto-detect dari nama file

    Returns:
        dict berisi seluruh hasil dan metrik.
    """

    filename = os.path.basename(audio_path)
    final_filename = normalized_filename if normalized_filename else filename

    # Auto-detect reference text dari nama file (format: {id}_{uttid}.wav)
    if ref_text is None:
        match = re.search(r"_(\d{2})\.wav$", final_filename.lower())
        if match:
            ref_text = REFERENCE_TRANSCRIPTS.get(match.group(1))

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
            # Normalisasi: ref_text bisa string (lama) atau list (dual-reference)
            refs = ref_text if isinstance(ref_text, list) else [ref_text]
            result["wer"] = calculate_wer_best(refs, normalized)
            result["cer"] = calculate_cer_best(refs, normalized)
        else:
            result["wer"] = "N/A"
            result["cer"] = "N/A"

        # 5. LLM
        t1 = time.time()
        llm_response_data = generate_response(normalized, mode=mode)
        result["latency_llm"] = round(time.time() - t1, 3)
        
        if isinstance(llm_response_data, dict):
            teks_asli = llm_response_data.get("teks_asli", str(llm_response_data))
            teks_fonetik = llm_response_data.get("teks_fonetik", teks_asli)
        else:
            teks_asli = str(llm_response_data)
            teks_fonetik = teks_asli
            
        result["llm_response"] = teks_asli

        # 6. TTS
        t2 = time.time()
        final_filename = normalized_filename if normalized_filename else filename
        stem = Path(final_filename).stem
        output_wav = get_output_audio_path(pipeline_mode, stem, student_id=student_id)
        synthesize_speech(teks_fonetik, output_wav)
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
        csv_path = get_batch_csv_path()

    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    logger.info(f"CSV disimpan ke: {csv_path}")
    return csv_path



