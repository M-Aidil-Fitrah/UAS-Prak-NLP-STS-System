"""
gradio_app/analisis_pipeline.py — CLI Batch Evaluation
Skrip mandiri untuk menjalankan evaluasi pipeline pada seluruh korpus audio NLP.
Menggunakan app.pipeline sebagai logika inti (shared dengan Gradio UI).

Usage:
    python gradio_app/analisis_pipeline.py
"""

import os
import sys
import json
import logging

# Root path setup
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from app.pipeline import (
    run_pipeline, results_to_csv, collect_corpus_files,
    OUTPUT_DIR,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_batch_evaluation():
    """Iterasi seluruh file WAV di corpus Audio_NLP, jalankan pipeline, export CSV + JSON."""
    wav_files = collect_corpus_files()
    total = len(wav_files)

    print("=" * 60)
    print(f"  BATCH EVALUATION — {total} file audio ditemukan")
    print("=" * 60)

    if total == 0:
        print("Tidak ada file WAV ditemukan di corpus/audio/Audio_NLP/")
        return

    results = []
    for i, wav_path in enumerate(wav_files, 1):
        fname = os.path.basename(wav_path)
        print(f"\n[{i}/{total}] {fname}")

        try:
            result = run_pipeline(wav_path, mode="preserve", output_dir=OUTPUT_DIR)
            results.append(result)

            if result["status"] == "success":
                lat = result.get("latency_total", "?")
                print(f"  OK — Latency: {lat}s")
            else:
                print(f"  FAIL — {result.get('error', '?')}")

        except Exception as e:
            results.append({
                "filename": fname,
                "status": "error",
                "error": str(e),
                "mode": "preserve",
            })
            print(f"  ERROR — {e}")

    # Export CSV
    csv_path = results_to_csv(results, os.path.join(OUTPUT_DIR, "batch_results.csv"))
    print(f"\nCSV: {csv_path}")

    # Export JSON
    json_path = os.path.join(OUTPUT_DIR, "batch_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"JSON: {json_path}")

    # Summary
    ok = sum(1 for r in results if r.get("status") == "success")
    print(f"\n{'=' * 60}")
    print(f"  SELESAI — Berhasil: {ok}/{total}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    run_batch_evaluation()
