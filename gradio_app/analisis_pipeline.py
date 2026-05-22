"""
gradio_app/analisis_pipeline.py — FASE 8: Otomatisasi Evaluasi Korpus
Sesuai planning.md Fase 8: skrip mandiri untuk iterasi ke-11 audio korpus,
menyimpan log transkripsi STT, jawaban LLM, dan latensi eksekusi.

Nama file audio sesuai planning.md format: {id}_{utteranceid}.wav
NPM Mahasiswa: 2335
"""

import os
import sys
import time
import json
import logging

# Tambahkan root project ke path agar import app.* bisa berjalan
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from app.stt import transcribe_speech_to_text
from app.utils import normalize_transcript, get_dominant_language, tag_code_switching
from app.llm import generate_response
from app.tts import synthesize_speech

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─── Daftar Korpus Audio Resmi (sesuai planning.md & projects.md) ─────────────
# Format penamaan: {id}_{utteranceid}.wav  |  id = 2335 (NPM mahasiswa)

CORPUS = [
    # ── Audio Wajib (Mandatory) ──
    {
        "id": "2335_audio01",
        "audio_path": os.path.join(ROOT_DIR, "corpus", "audio", "2335_audio01.wav"),
        "scenario": "ID-EN",
        "ref_text": "Aku mau book flight ke Jeddah minggu depan, bisa bantu schedule?"
    },
    {
        "id": "2335_audio02",
        "audio_path": os.path.join(ROOT_DIR, "corpus", "audio", "2335_audio02.wav"),
        "scenario": "ID-EN",
        "ref_text": "Aku butuh travel umrah simple tapi include Madinah visit"
    },
    {
        "id": "2335_audio03",
        "audio_path": os.path.join(ROOT_DIR, "corpus", "audio", "2335_audio03.wav"),
        "scenario": "EN-ID",
        "ref_text": "Can you help aku arrange transport dari Jeddah ke Madinah tomorrow"
    },
    {
        "id": "2335_audio04",
        "audio_path": os.path.join(ROOT_DIR, "corpus", "audio", "2335_audio04.wav"),
        "scenario": "EN-ID",
        "ref_text": "Explain step by step cara apply visa Saudi dengan benar"
    },
    {
        "id": "2335_audio05",
        "audio_path": os.path.join(ROOT_DIR, "corpus", "audio", "2335_audio05.wav"),
        "scenario": "AR-EN-ID",
        "ref_text": "Ya akhi, uridu book flight ila Jeddah al-usbu al qadim. Hal bisa bantu ajida afdhal schedule wa rihlatan mubashirah?"
    },
    {
        "id": "2335_audio06",
        "audio_path": os.path.join(ROOT_DIR, "corpus", "audio", "2335_audio06.wav"),
        "scenario": "AR-EN",
        "ref_text": "Uridu arrange transport min Jeddah ila Madinah ghadan"
    },
    # ── Audio Pilihan (Free-Pick) ──
    {
        "id": "2335_audio12",
        "audio_path": os.path.join(ROOT_DIR, "corpus", "audio", "2335_audio12.wav"),
        "scenario": "ID",
        "ref_text": "Bagaimana proses visa Saudi untuk umrah dari Indonesia sekarang"
    },
    {
        "id": "2335_audio13",
        "audio_path": os.path.join(ROOT_DIR, "corpus", "audio", "2335_audio13.wav"),
        "scenario": "ID-EN",
        "ref_text": "Jelaskan step by step cara booking flight ke Jeddah secara online"
    },
    {
        "id": "2335_audio14",
        "audio_path": os.path.join(ROOT_DIR, "corpus", "audio", "2335_audio14.wav"),
        "scenario": "EN-ID",
        "ref_text": "How to prepare dokumen umrah dari Indonesia dengan benar"
    },
    {
        "id": "2335_audio15",
        "audio_path": os.path.join(ROOT_DIR, "corpus", "audio", "2335_audio15.wav"),
        "scenario": "ID",
        "ref_text": "Tolong buat checklist persiapan umrah termasuk barang wajib dibawa"
    },
    {
        "id": "2335_audio17",
        "audio_path": os.path.join(ROOT_DIR, "corpus", "audio", "2335_audio17.wav"),
        "scenario": "ID-AR",
        "ref_text": "Menurut kamu belajar bahasa Arab itu susah gak untuk pemula"
    },
]


# ─── Metrik WER & CER (Implementasi Manual, tanpa library eksternal) ──────────

def _levenshtein(s1: list, s2: list) -> int:
    """Menghitung Levenshtein edit-distance antara dua urutan."""
    if len(s1) < len(s2):
        return _levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            curr_row.append(min(prev_row[j + 1] + 1, curr_row[j] + 1, prev_row[j] + (c1 != c2)))
        prev_row = curr_row
    return prev_row[-1]


def calculate_wer(ref: str, hyp: str) -> float:
    """Word Error Rate."""
    r, h = ref.lower().split(), hyp.lower().split()
    return min(1.0, _levenshtein(r, h) / len(r)) if r else (1.0 if h else 0.0)


def calculate_cer(ref: str, hyp: str) -> float:
    """Character Error Rate."""
    r, h = list(ref.lower()), list(hyp.lower())
    return min(1.0, _levenshtein(r, h) / len(r)) if r else (1.0 if h else 0.0)


# ─── Fungsi Evaluasi Utama ────────────────────────────────────────────────────

def run_pipeline_evaluation():
    """
    Iterasi seluruh korpus audio (11 file), jalankan full pipeline STT->LLM->TTS,
    tangkap log transkripsi, jawaban LLM, latensi, dan hitung WER/CER.
    Simpan hasil ke log JSON dan laporan Markdown.
    """
    print("=" * 70)
    print("🚀 MEMULAI OTOMATISASI EVALUASI KORPUS PIPELINE STS MULTILINGUAL")
    print(f"   Total corpus: {len(CORPUS)} file audio | NPM: 2335")
    print("=" * 70)

    os.makedirs(os.path.join(ROOT_DIR, "temp"), exist_ok=True)
    log_dir = os.path.join(ROOT_DIR, "log")
    os.makedirs(log_dir, exist_ok=True)

    results = []
    skipped = []

    for i, sample in enumerate(CORPUS, 1):
        print(f"\n[{i}/{len(CORPUS)}] Memproses: {sample['id']} | Skenario: {sample['scenario']}")

        if not os.path.exists(sample["audio_path"]):
            print(f"  ⚠️  File tidak ditemukan: {sample['audio_path']} — Dilewati.")
            skipped.append(sample["id"])
            continue

        entry = {
            "id":       sample["id"],
            "scenario": sample["scenario"],
            "ref_text": sample["ref_text"],
        }

        try:
            # ── STT ──
            t0 = time.time()
            raw_stt  = transcribe_speech_to_text(sample["audio_path"])
            clean_stt = normalize_transcript(raw_stt)
            lat_stt   = time.time() - t0

            entry["stt_raw"]     = raw_stt
            entry["stt_clean"]   = clean_stt
            entry["lat_stt_sec"] = round(lat_stt, 3)
            entry["dominant_lang"] = get_dominant_language(clean_stt)
            entry["cs_segments"]   = tag_code_switching(clean_stt)

            # WER & CER STT
            entry["wer"] = round(calculate_wer(sample["ref_text"], clean_stt), 4)
            entry["cer"] = round(calculate_cer(sample["ref_text"], clean_stt), 4)

            # ── LLM (preserve mode) ──
            t1 = time.time()
            llm_response  = generate_response(clean_stt, mode="preserve")
            lat_llm        = time.time() - t1

            entry["llm_response"] = llm_response
            entry["lat_llm_sec"]  = round(lat_llm, 3)

            # ── TTS ──
            t2 = time.time()
            out_wav = os.path.join(ROOT_DIR, "temp", f"eval_{sample['id']}.wav")
            synthesize_speech(llm_response, out_wav)
            lat_tts = time.time() - t2

            entry["tts_output"]   = out_wav
            entry["lat_tts_sec"]  = round(lat_tts, 3)
            entry["lat_total_sec"] = round(lat_stt + lat_llm + lat_tts, 3)
            entry["status"]       = "OK"

            print(f"  ✅ STT: {lat_stt:.2f}s | LLM: {lat_llm:.2f}s | TTS: {lat_tts:.2f}s | WER: {entry['wer']:.2%}")

        except Exception as exc:
            entry["status"] = "ERROR"
            entry["error"]  = str(exc)
            print(f"  ❌ Gagal: {exc}")

        results.append(entry)

    # ── Simpan Log JSON ──
    json_log_path = os.path.join(log_dir, "pipeline_log.json")
    with open(json_log_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n📄 Log JSON disimpan di: {json_log_path}")

    # ── Buat Laporan Markdown ──
    _write_markdown_report(results, skipped, log_dir)


def _write_markdown_report(results: list, skipped: list, log_dir: str):
    """Menghasilkan laporan evaluasi markdown dari hasil pipeline."""
    ok_results = [r for r in results if r.get("status") == "OK"]

    avg_wer = sum(r["wer"] for r in ok_results) / len(ok_results) if ok_results else 0
    avg_cer = sum(r["cer"] for r in ok_results) / len(ok_results) if ok_results else 0
    avg_lat = sum(r["lat_total_sec"] for r in ok_results) / len(ok_results) if ok_results else 0

    md  = "# Laporan Evaluasi Pipeline Speech-to-Speech Multilingual\n"
    md += "**UAS Praktikum NLP 2025/2026 Genap** | NPM: 2335\n\n"
    md += "---\n\n"
    md += "## Ringkasan Metrik\n\n"
    md += f"- **Jumlah audio diuji:** {len(ok_results)} / {len(CORPUS)}\n"
    md += f"- **Rata-rata WER (STT):** {avg_wer:.2%}\n"
    md += f"- **Rata-rata CER (STT):** {avg_cer:.2%}\n"
    md += f"- **Rata-rata Latensi End-to-End:** {avg_lat:.2f} detik\n"
    if skipped:
        md += f"- **File dilewati (tidak ada):** {', '.join(skipped)}\n"
    md += "\n---\n\n"

    md += "## Detail Hasil Per Audio\n\n"
    md += "| ID | Skenario | Bahasa Dominan | WER | CER | Latensi STT | Latensi LLM | Latensi TTS | Total |\n"
    md += "|---|---|---|---|---|---|---|---|---|\n"
    for r in ok_results:
        md += (
            f"| `{r['id']}` | {r['scenario']} | `{r.get('dominant_lang','?')}` | "
            f"{r['wer']:.2%} | {r['cer']:.2%} | "
            f"{r.get('lat_stt_sec',0):.2f}s | {r.get('lat_llm_sec',0):.2f}s | "
            f"{r.get('lat_tts_sec',0):.2f}s | {r.get('lat_total_sec',0):.2f}s |\n"
        )

    md += "\n---\n\n"
    md += "## Log Transkripsi & Respons LLM\n\n"
    for r in ok_results:
        md += f"### `{r['id']}` — {r['scenario']}\n"
        md += f"- **Referensi:** `{r['ref_text']}`\n"
        md += f"- **STT Output:** `{r.get('stt_clean', '-')}`\n"
        md += f"- **LLM Response:** {r.get('llm_response', '-')}\n"
        md += f"- **CS Segments:** {r.get('cs_segments', [])}\n\n"

    report_path = os.path.join(log_dir, "evaluation_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"📊 Laporan Markdown disimpan di: {report_path}")
    print("\n" + "=" * 70)
    print("✅ EVALUASI SELESAI")
    print("=" * 70)


if __name__ == "__main__":
    run_pipeline_evaluation()
