"""
gradio_app/analisis_pipeline.py — CLI Batch Evaluation
Skrip mandiri untuk menjalankan evaluasi pipeline pada seluruh korpus audio NLP.

Fitur:
  - Validasi format nama file sebelum pipeline dijalankan
  - Checkpoint CSV setiap 10 file (tidak hilang jika terhenti)
  - Resume: skip file yang sudah ada outputnya
  - Export CSV + JSON hasil akhir ke output/batch/

Usage:
    python gradio_app/analisis_pipeline.py
"""

import os
import sys
import json
import logging

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from app.pipeline import (
    run_pipeline, results_to_csv, save_checkpoint,
    collect_corpus_files_with_meta,
)
from app.file_manager import (
    OUTPUT_BATCH, get_batch_csv_path, get_output_audio_path,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CHECKPOINT_EVERY = 10  # Simpan checkpoint setiap N file


def run_batch_evaluation():
    """Iterasi seluruh file WAV di corpus Audio_NLP, jalankan pipeline, export CSV + JSON."""
    file_meta = collect_corpus_files_with_meta()
    total = len(file_meta)

    print("=" * 60)
    print(f"  BATCH EVALUATION — {total} file audio ditemukan")
    print("=" * 60)

    if total == 0:
        print("Tidak ada file WAV ditemukan di corpus/audio/Audio_NLP/")
        return

    # ── Validasi nama file sebelum pipeline jalan ────────────────────────────
    valid_files   = [m for m in file_meta if m["is_valid"]]
    invalid_files = [m for m in file_meta if not m["is_valid"]]

    print(f"\n  ✅ Valid   : {len(valid_files)} file")
    print(f"  ❌ Invalid : {len(invalid_files)} file")

    if invalid_files:
        print("\n  File yang dilewati (nama tidak sesuai format):")
        for m in invalid_files:
            print(f"    - {m['filename']}  →  {m['reason']}")
    print()

    # ── Resume: cek file yang sudah diproses ─────────────────────────────────
    results = []
    skipped = 0
    for meta in valid_files:
        stem = os.path.splitext(meta["filename"])[0]
        expected_output = get_output_audio_path("batch", stem)
        if os.path.exists(expected_output):
            skipped += 1
            results.append({
                "filename":  meta["filename"],
                "folder":    meta["folder"],
                "status":    "skipped (resume)",
                "mode":      "preserve",
                "error":     "",
            })

    if skipped:
        print(f"  ⏩ Resume: {skipped} file sudah diproses, di-skip.\n")

    # ── Proses file yang belum diproses ──────────────────────────────────────
    pending = [
        m for m in valid_files
        if not os.path.exists(get_output_audio_path("batch", os.path.splitext(m["filename"])[0]))
    ]

    total_pending = len(pending)
    print(f"  🔄 Akan diproses: {total_pending} file\n")

    for i, meta in enumerate(pending, 1):
        fname = meta["filename"]
        print(f"[{i}/{total_pending}] {fname}")

        try:
            result = run_pipeline(
                meta["path"],
                mode="preserve",
                pipeline_mode="batch",
            )
            results.append(result)

            if result["status"] == "success":
                lat = result.get("latency_total", "?")
                wer = result.get("wer", "N/A")
                print(f"  OK — Latency: {lat}s | WER: {wer}")
            else:
                print(f"  FAIL — {result.get('error', '?')}")

        except Exception as e:
            results.append({
                "filename": fname,
                "folder":   meta["folder"],
                "status":   "error",
                "error":    str(e),
                "mode":     "preserve",
            })
            print(f"  ERROR — {e}")

        # Simpan checkpoint setiap CHECKPOINT_EVERY file
        if i % CHECKPOINT_EVERY == 0:
            save_checkpoint(results)

    # ── Export Akhir ─────────────────────────────────────────────────────────
    csv_path = results_to_csv(results, get_batch_csv_path())
    print(f"\nCSV: {csv_path}")

    json_path = os.path.join(OUTPUT_BATCH, "batch_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"JSON: {json_path}")

    ok      = sum(1 for r in results if r.get("status") == "success")
    skipped = sum(1 for r in results if "skipped" in r.get("status", ""))
    fail    = len(results) - ok - skipped

    print(f"\n{'=' * 60}")
    print(f"  SELESAI — Berhasil: {ok} | Dilewati: {skipped} | Gagal: {fail} | Total: {total}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    run_batch_evaluation()
