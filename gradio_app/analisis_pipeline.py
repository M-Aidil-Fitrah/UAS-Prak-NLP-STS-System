"""
gradio_app/analisis_pipeline.py — CLI Batch Evaluation
Skrip mandiri untuk menjalankan evaluasi pipeline pada seluruh korpus audio NLP.

Fitur:
  - Validasi & Normalisasi nama file sebelum pipeline dijalankan
  - Checkpoint JSON per-mahasiswa (tidak hilang jika terhenti)
  - Resume: skip file yang sudah ada outputnya (berbasis mahasiswa)
  - Export CSV + JSON hasil akhir ke output/batch/

Usage:
    python gradio_app/analisis_pipeline.py
"""

import os
import sys
import json
import logging
from collections import defaultdict

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

# Inisialisasi CLI Logger — menulis ke log/cli.log (terpisah dari log Gradio)
from app.logger import setup_cli_logger
setup_cli_logger()

from app.pipeline import (
    run_pipeline, results_to_csv,
    collect_corpus_files_with_meta,
)
from app.file_manager import (
    OUTPUT_BATCH, get_batch_csv_path, get_checkpoint_path,
)


logger = logging.getLogger(__name__)

def run_batch_evaluation() -> None:
    """Iterasi seluruh file WAV di corpus Audio_NLP, jalankan pipeline per mahasiswa."""
    file_meta = collect_corpus_files_with_meta()
    total = len(file_meta)

    logger.info("=" * 60)
    logger.info(f"BATCH EVALUATION — {total} file audio ditemukan")
    logger.info("=" * 60)

    if total == 0:
        logger.warning("Tidak ada file WAV ditemukan di corpus/audio/Audio_NLP/")
        return

    # ── Validasi nama file sebelum pipeline jalan ────────────────────────────
    valid_files   = [m for m in file_meta if m["is_valid"]]
    invalid_files = [m for m in file_meta if not m["is_valid"]]

    logger.info(f"Valid   : {len(valid_files)} file")
    logger.info(f"Invalid : {len(invalid_files)} file")

    if invalid_files:
        logger.warning("File yang dilewati (nama tidak sesuai format):")
        for m in invalid_files:
            logger.warning(f"  - {m['filename']}  ->  {m['reason']}")

    # Group files by student
    student_groups = defaultdict(list)
    for m in valid_files:
        student_groups[m["student_id"]].append(m)

    results = []
    skipped = 0
    total_students = len(student_groups)

    logger.info(f"Akan diproses: {total_students} Mahasiswa")

    for idx, (student_id, st_files) in enumerate(student_groups.items(), 1):
        logger.info(f"[{idx}/{total_students}] Memproses Mahasiswa {student_id} ({len(st_files)} Audio)")

        ckpt_path = get_checkpoint_path(student_id)
        if os.path.exists(ckpt_path):
            try:
                with open(ckpt_path, "r", encoding="utf-8") as f:
                    st_results = json.load(f)
                results.extend(st_results)
                skipped += len(st_files)
                logger.info(f"  -> Resume: Checkpoint ditemukan untuk {student_id}, dilewati.")
                continue
            except Exception:
                logger.warning(f"  -> Checkpoint {student_id} korup, memproses ulang...")

        st_results = []
        for i, meta in enumerate(st_files, 1):
            norm_fname = meta["normalized"]
            try:
                res = run_pipeline(
                    meta["path"],
                    mode="preserve",
                    pipeline_mode="batch",
                    student_id=student_id,
                    normalized_filename=norm_fname
                )
                st_results.append(res)

                if res["status"] == "success":
                    lat = res.get("latency_total", "?")
                    wer = res.get("wer", "N/A")
                    logger.info(f"  [{i}/{len(st_files)}] {norm_fname} -> OK (Lat: {lat}s | WER: {wer})")
                else:
                    logger.warning(f"  [{i}/{len(st_files)}] {norm_fname} -> FAIL ({res.get('error', '?')})")

            except Exception as e:
                st_results.append({
                    "filename": norm_fname,
                    "folder": meta["folder"],
                    "status": "error",
                    "error": str(e),
                    "mode": "preserve",
                })
                logger.error(f"  [{i}/{len(st_files)}] {norm_fname} -> ERROR ({e})")

        # Simpan checkpoint untuk mahasiswa ini
        os.makedirs(os.path.dirname(ckpt_path), exist_ok=True)
        with open(ckpt_path, "w", encoding="utf-8") as f:
            json.dump(st_results, f, ensure_ascii=False, indent=2)

        results.extend(st_results)

    # ── Export Akhir ─────────────────────────────────────────────────────────
    csv_path = results_to_csv(results, get_batch_csv_path())
    logger.info(f"CSV tersimpan: {csv_path}")

    json_path = os.path.join(OUTPUT_BATCH, "batch_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"JSON tersimpan: {json_path}")

    ok   = sum(1 for r in results if r.get("status") == "success")
    fail = len(results) - ok

    logger.info("=" * 60)
    logger.info(f"SELESAI — Berhasil: {ok} | Dilewati: {skipped} | Gagal: {fail} | Total: {len(valid_files)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_batch_evaluation()
