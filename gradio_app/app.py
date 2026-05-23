"""
gradio_app/app.py — Gradio Web UI v4 (SwitchSpeak Modular)
Glassmorphism Dark Theme with Tailwind CSS.
Modularized UI (views/, theme.py).
"""

import os
import sys
import time
import gradio as gr

# Root path setup
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Import logic
from app.pipeline import (
    run_pipeline, results_to_csv, collect_corpus_files,
    compute_language_ratio, OUTPUT_DIR, CORPUS_DIR,
)
from app.stt import transcribe_speech_to_text
from app.utils import normalize_transcript, tag_code_switching, get_dominant_language
from app.llm import generate_response
from app.tts import synthesize_speech

# Import theme and views
from gradio_app.theme import HEAD_HTML, CSS
from gradio_app.views import upload_view, record_view, batch_view

os.makedirs(os.path.join(OUTPUT_DIR, "audio"), exist_ok=True)

# --- Pipeline Logic ---

def process_single_audio(audio_path, mode):
    """Process satu file audio (Upload/Record) dengan logging bertahap."""
    if audio_path is None:
        yield None, None, "⚠️ Tidak ada audio. Silakan upload atau rekam terlebih dahulu."
        return

    results = []

    yield None, None, "**[1/5]** Menjalankan transkripsi STT (Whisper)..."
    try:
        t0 = time.time()
        raw = transcribe_speech_to_text(audio_path)
        lat_stt = round(time.time() - t0, 3)
    except Exception as e:
        yield None, None, f"### ❌ Error pada STT\n\n{str(e)}"
        return

    if not raw.strip():
        yield None, None, "### ❌ Error pada STT\n\nTranskripsi kosong, audio tidak terdeteksi."
        return

    yield None, None, f"**[2/5]** Preprocessing & normalisasi teks...\n\n**Transkripsi:** *{raw}*"
    normalized = normalize_transcript(raw)
    segments = tag_code_switching(normalized)
    dominant = get_dominant_language(normalized)
    ratio = compute_language_ratio(segments)

    yield None, None, f"**[3/5]** Mengirim ke LLM (Gemma)...\n\n**Bahasa dominan:** {dominant} | **Rasio:** ID {ratio['ID']}% / EN {ratio['EN']}% / AR {ratio['AR']}%"
    try:
        t1 = time.time()
        llm_response = generate_response(normalized, mode=mode)
        lat_llm = round(time.time() - t1, 3)
    except Exception as e:
        yield None, None, f"### ❌ Error pada LLM\n\n{str(e)}"
        return

    yield None, None, f"**[4/5]** Mensintesis audio respons (VITS TTS)...\n\n**Respons LLM:** *{llm_response[:150]}...*"
    try:
        t2 = time.time()
        from pathlib import Path
        stem = Path(audio_path).stem
        output_wav = os.path.join(OUTPUT_DIR, "audio", f"{stem}_response.wav")
        os.makedirs(os.path.dirname(output_wav), exist_ok=True)
        synthesize_speech(llm_response, output_wav)
        lat_tts = round(time.time() - t2, 3)
    except Exception as e:
        yield None, None, f"### ❌ Error pada TTS\n\n{str(e)}"
        return

    lat_total = round(lat_stt + lat_llm + lat_tts, 3)

    result = {
        "filename": os.path.basename(audio_path),
        "folder": "-",
        "status": "success",
        "mode": mode,
        "raw_transcript": raw,
        "normalized_transcript": normalized,
        "dominant_language": dominant,
        "ratio_id": ratio["ID"],
        "ratio_en": ratio["EN"],
        "ratio_ar": ratio["AR"],
        "language_segments": str(segments),
        "wer": "N/A",
        "cer": "N/A",
        "llm_response": llm_response,
        "tts_output_path": output_wav,
        "latency_stt": lat_stt,
        "latency_llm": lat_llm,
        "latency_tts": lat_tts,
        "latency_total": lat_total,
        "error": "",
    }
    results.append(result)

    csv_path = os.path.join(OUTPUT_DIR, "single_result.csv")
    results_to_csv(results, csv_path)

    # Build tag string
    seg_parts = [f"<span class='lang-badge lang-{seg['lang'].lower()}'>{seg['lang']}</span> <span style='color:#ccc'>{seg['text']}</span>" for seg in segments]
    seg_html = "<div style='line-height:2'>" + " &middot; ".join(seg_parts) + "</div>"

    final_log = (
        f"### ✅ Pipeline Selesai\n\n"
        f"**Transkripsi (Whisper)**\n{normalized}\n\n"
        f"**Bahasa Dominan**\n"
        f"<span class='lang-badge lang-{dominant.lower()}'>{dominant}</span>"
        f" — ID {ratio['ID']}% / EN {ratio['EN']}% / AR {ratio['AR']}%\n\n"
        f"**Segmen Code-Switching**\n{seg_html}\n\n---\n\n"
        f"**Respons LLM**\n{llm_response}\n\n---\n\n"
        f"**Latency** — STT: {lat_stt}s | LLM: {lat_llm}s | TTS: {lat_tts}s | Total: **{lat_total}s**"
    )

    yield output_wav, csv_path, final_log


def process_batch_nlp(mode, progress=gr.Progress()):
    """Process semua file WAV dari corpus/audio/Audio_NLP/."""
    wav_files = collect_corpus_files()
    total = len(wav_files)

    if total == 0:
        yield None, f"⚠️ Tidak ada file WAV ditemukan di:\n`{CORPUS_DIR}`"
        return

    yield None, f"Ditemukan **{total}** file audio. Memulai batch processing..."

    results = []
    for i, wav_path in enumerate(wav_files):
        fname = os.path.basename(wav_path)
        progress((i + 1) / total, desc=f"[{i+1}/{total}] {fname}")
        yield None, f"**[{i+1}/{total}]** Processing: `{fname}`"

        try:
            result = run_pipeline(wav_path, mode=mode, output_dir=OUTPUT_DIR)
            results.append(result)
        except Exception as e:
            results.append({
                "filename": fname,
                "folder": "?",
                "status": "error",
                "error": str(e),
                "mode": mode,
            })

    csv_path = os.path.join(OUTPUT_DIR, "batch_results.csv")
    results_to_csv(results, csv_path)

    ok = sum(1 for r in results if r.get("status") == "success")
    fail = total - ok

    ok_results = [r for r in results if r.get("status") == "success"]
    avg_wer = "-"
    avg_cer = "-"
    avg_lat = "-"
    if ok_results:
        numeric_wer = [r["wer"] for r in ok_results if isinstance(r.get("wer"), (int, float))]
        numeric_cer = [r["cer"] for r in ok_results if isinstance(r.get("cer"), (int, float))]
        if numeric_wer:
            avg_wer = f"{sum(numeric_wer)/len(numeric_wer):.2%}"
        if numeric_cer:
            avg_cer = f"{sum(numeric_cer)/len(numeric_cer):.2%}"
        lats = [r["latency_total"] for r in ok_results if "latency_total" in r]
        if lats:
            avg_lat = f"{sum(lats)/len(lats):.2f}s"

    summary = (
        f"### ⚙️ Batch Processing Selesai\n\n"
        f"**Total File:** {total} | **Berhasil:** {ok} | **Gagal:** {fail}\n\n"
        f"**Rata-rata WER:** {avg_wer} | **CER:** {avg_cer} | **Latency:** {avg_lat}\n\n"
        f"CSV disimpan di `output/batch_results.csv`\n\n"
        f"Audio output disimpan di `output/audio/`"
    )
    yield csv_path, summary


def clear_outputs():
    return None, None, None, "*Menunggu input...*"


# --- Gradio UI Layout ---

with gr.Blocks(css=CSS, head=HEAD_HTML, theme=gr.themes.Base()) as demo:
    
    # View 1: Upload (Sidebar layout)
    with gr.Column(visible=True, elem_classes="w-full") as v_upload:
        up_audio, up_mode, up_run, up_clear, up_out_audio, up_out_csv, up_log, btn_upload1, btn_record1, btn_batch1 = upload_view.build()
        
    # View 2: Record (TopNav layout)
    with gr.Column(visible=False, elem_classes="w-full") as v_record:
        rec_audio, rec_mode, rec_run, rec_clear, rec_out_audio, rec_out_csv, rec_log, btn_upload2, btn_record2, btn_batch2 = record_view.build()

    # View 3: Batch (TopNav layout)
    with gr.Column(visible=False, elem_classes="w-full") as v_batch:
        bat_mode, bat_run, bat_out_csv, bat_log, btn_upload3, btn_record3, btn_batch3 = batch_view.build()

    # --- Interactivity ---

    # Navigation Logic
    def show_upload():
        return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)
        
    def show_record():
        return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)
        
    def show_batch():
        return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)

    # Bind buttons from View 1 (Upload sidebar)
    btn_upload1.click(show_upload, outputs=[v_upload, v_record, v_batch])
    btn_record1.click(show_record, outputs=[v_upload, v_record, v_batch])
    btn_batch1.click(show_batch, outputs=[v_upload, v_record, v_batch])

    # Bind buttons from View 2 (Record topnav)
    btn_upload2.click(show_upload, outputs=[v_upload, v_record, v_batch])
    btn_record2.click(show_record, outputs=[v_upload, v_record, v_batch])
    btn_batch2.click(show_batch, outputs=[v_upload, v_record, v_batch])

    # Bind buttons from View 3 (Batch topnav)
    btn_upload3.click(show_upload, outputs=[v_upload, v_record, v_batch])
    btn_record3.click(show_record, outputs=[v_upload, v_record, v_batch])
    btn_batch3.click(show_batch, outputs=[v_upload, v_record, v_batch])

    # Pipeline Triggers
    up_run.click(process_single_audio, inputs=[up_audio, up_mode], outputs=[up_out_audio, up_out_csv, up_log])
    up_clear.click(clear_outputs, outputs=[up_audio, up_out_audio, up_out_csv, up_log])

    rec_run.click(process_single_audio, inputs=[rec_audio, rec_mode], outputs=[rec_out_audio, rec_out_csv, rec_log])
    rec_clear.click(clear_outputs, outputs=[rec_audio, rec_out_audio, rec_out_csv, rec_log])

    bat_run.click(process_batch_nlp, inputs=[bat_mode], outputs=[bat_out_csv, bat_log])


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)


