"""
gradio_app/app.py — Sonic Lingua Unified Gradio App
Single sidebar, three switchable views. Full pipeline with detailed output.
"""

import os
import sys

# 1. PATH SETUP (MUST BE BEFORE IMPORTING GRADIO/PYDUB)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

VENV_SCRIPTS = os.path.join(ROOT_DIR, "venv", "Scripts")
if os.path.exists(os.path.join(VENV_SCRIPTS, "ffmpeg.exe")):
    os.environ["PATH"] += os.pathsep + VENV_SCRIPTS
    
# Force pydub to see ffmpeg if it's imported later
os.environ["FFMPEG_BINARY"] = os.path.join(VENV_SCRIPTS, "ffmpeg.exe")

# 2. BYPASS WINDOWS TEMP FOLDER LOCKS (Antivirus/Defender)
# Create a local temp folder so Windows Defender doesn't aggressively lock short audio files
LOCAL_TEMP = os.path.join(ROOT_DIR, "gradio_temp")
os.makedirs(LOCAL_TEMP, exist_ok=True)
os.environ["GRADIO_TEMP_DIR"] = LOCAL_TEMP

import time
import threading
import gradio as gr

# Try to explicitly patch pydub (Gradio's internal audio processor)
try:
    import pydub
    pydub.AudioSegment.converter = os.path.join(VENV_SCRIPTS, "ffmpeg.exe")
except Exception:
    pass

# Import logic
from app.pipeline import (
    run_pipeline, results_to_csv, collect_corpus_files,
    compute_language_ratio, OUTPUT_DIR, CORPUS_DIR,
    REFERENCE_TRANSCRIPTS, calculate_wer, calculate_cer
)
from app.stt import transcribe_speech_to_text
from app.utils import normalize_transcript, tag_code_switching, get_dominant_language
from app.llm import generate_response
from app.tts import synthesize_speech

# Import theme
from gradio_app.theme import HEAD_HTML, CSS

os.makedirs(os.path.join(OUTPUT_DIR, "audio"), exist_ok=True)

# --- Stop flag for cancellation ---
_stop_flag = threading.Event()


def request_stop():
    _stop_flag.set()
    return "⛔ Stop diminta. Menunggu proses saat ini selesai..."


# --- Single Audio Pipeline (Upload / Record) ---

def process_single_audio(audio_input, mode, tts_voice, ref_id):
    """Process satu file audio (Upload/Record) dengan logging bertahap dan output rapi."""
    if audio_input is None:
        yield None, None, "⚠️ Tidak ada audio. Silakan upload atau rekam terlebih dahulu."
        return

    # --- Bypassing Gradio's internal processing bugs ---
    import subprocess
    import tempfile
    import os
    
    # Diagnostik jika filepath None
    if audio_input is None:
        yield None, None, "⚠️ Tidak ada audio. Silakan upload atau rekam terlebih dahulu."
        return

    _stop_flag.clear()
    results = []

    # Pastikan file audio valid dan ukurannya tidak 0
    if not os.path.exists(audio_input) or os.path.getsize(audio_input) == 0:
        yield None, None, "❌ **Error:** File audio kosong. Harap rekam lebih lama (minimal 2-3 detik) agar browser sempat mengirimkan data suara."
        return

    # Paksa konversi ke WAV menggunakan FFmpeg sistem untuk menghindari bug Pydub
    temp_wav = tempfile.mktemp(suffix=".wav")
    try:
        # Gunakan FFmpeg yang sudah didaftarkan di PATH
        subprocess.run([
            "ffmpeg", "-y", "-i", audio_input, 
            "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", temp_wav
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        audio_path = temp_wav
    except Exception as e:
        yield None, None, f"❌ **Error Konversi Audio:** Gagal mengonversi rekaman menggunakan FFmpeg. {str(e)}"
        return

    # ── Step 1: STT ──────────────────────────────────────────
    yield None, None, "🎙️ **[1/5] Speech-to-Text** — Menjalankan transkripsi via Whisper..."
    try:
        t0 = time.time()
        raw = transcribe_speech_to_text(audio_path)
        lat_stt = round(time.time() - t0, 3)
    except Exception as e:
        yield None, None, f"❌ **Error pada STT**\n\n{str(e)}"
        return

    if not raw.strip():
        yield None, None, "❌ **Error pada STT** — Transkripsi kosong, audio tidak terdeteksi."
        return

    # ── Step 2: Preprocessing ────────────────────────────────
    yield None, None, f"🔧 **[2/5] Preprocessing & Normalisasi**\n\n> Raw transcript: *{raw}*"
    normalized = normalize_transcript(raw)
    segments = tag_code_switching(normalized)
    dominant = get_dominant_language(normalized)
    ratio = compute_language_ratio(segments)

    if _stop_flag.is_set():
        yield None, None, "⛔ Proses dihentikan oleh pengguna."
        return

    # ── Step 3: LLM ──────────────────────────────────────────
    yield None, None, (
        f"🤖 **[3/5] Large Language Model** — Mengirim ke Gemma...\n\n"
        f"> Normalized: *{normalized}*\n"
        f"> Bahasa dominan: **{dominant}** | Rasio: ID {ratio['ID']}% / EN {ratio['EN']}% / AR {ratio['AR']}%"
    )
    try:
        t1 = time.time()
        llm_response = generate_response(normalized, mode=mode)
        lat_llm = round(time.time() - t1, 3)
    except Exception as e:
        yield None, None, f"❌ **Error pada LLM**\n\n{str(e)}"
        return

    if _stop_flag.is_set():
        yield None, None, "⛔ Proses dihentikan oleh pengguna."
        return

    # ── Step 4: TTS ──────────────────────────────────────────
    yield None, None, f"🔊 **[4/5] Text-to-Speech** — Mensintesis audio respons via VITS...\n\n> LLM Response: *{llm_response[:200]}...*"
    try:
        t2 = time.time()
        from pathlib import Path
        stem = Path(audio_path).stem
        output_wav = os.path.join(OUTPUT_DIR, "audio", f"{stem}_response.wav")
        os.makedirs(os.path.dirname(output_wav), exist_ok=True)
        synthesize_speech(llm_response, output_wav, speaker_name=tts_voice)
        lat_tts = round(time.time() - t2, 3)
    except Exception as e:
        yield None, None, f"❌ **Error pada TTS**\n\n{str(e)}"
        return

    lat_total = round(lat_stt + lat_llm + lat_tts, 3)

    # ── Calculate WER / CER if Reference Provided ────────────
    filename = os.path.basename(audio_path)
    wer_val = "N/A"
    cer_val = "N/A"
    
    ref_text = None
    if ref_id and ref_id != "None":
        ref_text = REFERENCE_TRANSCRIPTS.get(ref_id)
    else:
        # Fallback: Deteksi ID dari nama file (misal: 2030_audio05.wav -> 05)
        import re
        match = re.search(r'(?:audio|_)?(\d{2})\.wav$', filename.lower())
        if match:
            ref_text = REFERENCE_TRANSCRIPTS.get(match.group(1))

    if ref_text:
        wer_val = calculate_wer(ref_text, normalized)
        cer_val = calculate_cer(ref_text, normalized)

    # ── Step 5: Evaluation & Result ──────────────────────────
    result = {
        "filename": filename,
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
        "wer": wer_val,
        "cer": cer_val,
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

    # ── Build final detailed output ──────────────────────────
    final_log = (
        f"✅ **Pipeline Selesai**\n\n"
        f"---\n\n"
        f"**📝 Transkripsi (Raw — Whisper)**\n"
        f"> {raw}\n\n"
        f"**🔧 Teks Setelah Preprocessing & Normalisasi**\n"
        f"> {normalized}\n\n"
        f"**🌐 Analisis Bahasa**\n"
        f"- Bahasa Dominan: **{dominant}**\n"
        f"- Rasio: ID {ratio['ID']}% · EN {ratio['EN']}% · AR {ratio['AR']}%\n\n"
        f"---\n\n"
        f"**🤖 Respons LLM (Gemma)**\n"
        f"> {llm_response}\n\n"
        f"---\n\n"
        f"**📊 Evaluasi**\n\n"
        f"| Metrik | Nilai |\n"
        f"|--------|-------|\n"
        f"| WER | N/A (tanpa referensi) |\n"
        f"| CER | N/A (tanpa referensi) |\n"
        f"| Latency STT | {lat_stt}s |\n"
        f"| Latency LLM | {lat_llm}s |\n"
        f"| Latency TTS | {lat_tts}s |\n"
        f"| **Latency Total** | **{lat_total}s** |\n"
    )

    yield output_wav, csv_path, final_log


# --- Batch Pipeline ---

def process_batch_nlp(mode, progress=gr.Progress()):
    """Process semua file WAV dari corpus/audio/Audio_NLP/."""
    _stop_flag.clear()
    wav_files = collect_corpus_files()
    total = len(wav_files)

    if total == 0:
        yield None, f"⚠️ Tidak ada file WAV ditemukan di:\n`{CORPUS_DIR}`"
        return

    yield None, f"📂 Ditemukan **{total}** file audio. Memulai batch processing..."

    results = []
    for i, wav_path in enumerate(wav_files):
        if _stop_flag.is_set():
            yield None, f"⛔ Batch dihentikan pada file {i}/{total}."
            break

        fname = os.path.basename(wav_path)
        progress((i + 1) / total, desc=f"[{i+1}/{total}] {fname}")
        yield None, f"🎙️ **[{i+1}/{total}]** Processing: `{fname}`"

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
    fail = len(results) - ok

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
        f"✅ **Batch Processing Selesai**\n\n"
        f"| Metrik | Nilai |\n"
        f"|--------|-------|\n"
        f"| Total File | {total} |\n"
        f"| Berhasil | {ok} |\n"
        f"| Gagal | {fail} |\n"
        f"| Rata-rata WER | {avg_wer} |\n"
        f"| Rata-rata CER | {avg_cer} |\n"
        f"| Rata-rata Latency | {avg_lat} |\n\n"
        f"📁 CSV: `output/batch_results.csv`\n"
        f"🔊 Audio: `output/audio/`"
    )
    yield csv_path, summary


def clear_single():
    return None, None, None, ""


def clear_record():
    return None, None, None, ""


# ═══════════════════════════════════════════════════════════════
#  GRADIO UI — Unified Sidebar + Switchable Views
# ═══════════════════════════════════════════════════════════════

with gr.Blocks(css=CSS, head=HEAD_HTML, theme=gr.themes.Base()) as demo:

    # ── Full-Width Title ─────────────────────────────────────
    gr.HTML("""
    <div class="page-header">
        <h1>Multilingual Speech-to-Speech System</h1>
        <div class="subtitle">
            Saudi Tourism AI Assistant — Code-Switching Support
            <strong>(ID / EN / AR)</strong>
        </div>
    </div>
    """)

    with gr.Row(elem_classes="main-row"):

        # ── SHARED SIDEBAR ───────────────────────────────────
        with gr.Column(scale=1, elem_classes="glass-card sidebar-col", min_width=220):
            gr.HTML("""
            <div class="sidebar-logo">
                <span class="material-symbols-outlined logo-icon">graphic_eq</span>
                <span class="logo-text">Sonic Lingua</span>
            </div>
            <p class="sidebar-section-label">Workflow</p>
            """)
            nav_upload = gr.Button("Upload Audio",  elem_classes="nav-btn nav-active")
            nav_record = gr.Button("Record Audio",  elem_classes="nav-btn")
            nav_batch  = gr.Button("Input Audio NLP", elem_classes="nav-btn")

        # ── MAIN WORKSPACE ───────────────────────────────────
        with gr.Column(scale=5):
            with gr.Tabs(elem_classes="hidden-tabs") as tabs:

                # ═══ VIEW 1: UPLOAD AUDIO ════════════════════════
                with gr.TabItem("Upload", id="tab_upload"):
                    with gr.Row():
                        # Input Card
                        with gr.Column(scale=3, elem_classes="glass-card"):
                            gr.HTML("""<div class="card-header">
                                <span class="material-symbols-outlined icon" style="color:#93c5fd;">input</span>
                                <span class="label">Input Source</span>
                            </div>""")
                            up_audio = gr.Audio(sources=["upload"], type="filepath", label="Drop Audio Here")
                            with gr.Row():
                                with gr.Column(scale=2, min_width=160):
                                    gr.HTML('<p class="toggle-label">Output Language Mode</p>')
                                    up_mode = gr.Radio(
                                        choices=[("Preserve", "preserve"), ("Normalize", "normalize")],
                                        value="preserve", label="", container=False,
                                        elem_classes="toggle-radio",
                                    )
                                    gr.HTML('<p class="toggle-label" style="margin-top: 1rem;">TTS Voice</p>')
                                    up_voice = gr.Radio(
                                        choices=[("Gadis (Wanita)", "gadis"), ("Ardi (Pria)", "ardi"), ("Wibowo (Pria)", "wibowo")],
                                        value="gadis", label="", container=False,
                                        elem_classes="toggle-radio",
                                    )
                                with gr.Column(scale=3, min_width=200):
                                    up_ref = gr.Dropdown(
                                        choices=["None"] + [f"{i:02d}" for i in range(1, 21)],
                                        value="None", label="Evaluasi Kunci Jawaban (Opsional)", container=True,
                                    )
                                    gr.HTML('<div style="height:0.5rem;"></div>')
                                    with gr.Row():
                                        up_clear = gr.Button("Clear", variant="secondary")
                                        up_stop  = gr.Button("⬛ Stop", variant="secondary")
                                        up_run   = gr.Button("▶ Run Pipeline", variant="primary")

                        # Results Card
                        with gr.Column(scale=2, elem_classes="glass-card"):
                            gr.HTML("""<div class="card-header">
                                <span class="material-symbols-outlined icon" style="color:#c084fc;">output</span>
                                <span class="label">Results</span>
                            </div>""")
                            up_out_audio = gr.Audio(label="Audio Response (TTS)", interactive=False)
                            up_out_csv = gr.File(label="Download CSV Transcript", interactive=False)

                    # Logs Card (full width)
                    with gr.Column(elem_classes="glass-card"):
                        gr.HTML("""<div class="card-header">
                            <span class="material-symbols-outlined icon" style="color:#34d399;">terminal</span>
                            <span class="label">Pipeline Logs</span>
                        </div>""")
                        up_log = gr.Markdown(value="*Menunggu input...*")

                # ═══ VIEW 2: RECORD AUDIO ════════════════════════
                with gr.TabItem("Record", id="tab_record"):
                    with gr.Row():
                        # Mic Card
                        with gr.Column(scale=3, elem_classes="glass-card"):
                            gr.HTML("""<div class="card-header">
                                <span class="material-symbols-outlined icon" style="color:#93c5fd;">mic</span>
                                <span class="label">Audio Input</span>
                            </div>""")
                            rec_audio = gr.Audio(sources=["microphone"], type="filepath", label="Record dari Microphone")

                        # Settings Card
                        with gr.Column(scale=2, elem_classes="glass-card"):
                            gr.HTML("""<div class="card-header">
                                <span class="material-symbols-outlined icon" style="color:#64748b;">tune</span>
                                <span class="label">Settings</span>
                            </div>""")
                            gr.HTML('<p class="toggle-label">Output Language Mode</p>')
                            rec_mode = gr.Radio(
                                choices=[("Preserve", "preserve"), ("Normalize", "normalize")],
                                value="preserve", label="", container=False,
                                elem_classes="toggle-radio",
                            )
                            gr.HTML('<p class="toggle-label" style="margin-top: 1rem;">TTS Voice</p>')
                            rec_voice = gr.Radio(
                                choices=[("Gadis (Wanita)", "gadis"), ("Ardi (Pria)", "ardi"), ("Wibowo (Pria)", "wibowo")],
                                value="gadis", label="", container=False,
                                elem_classes="toggle-radio",
                            )
                            rec_ref = gr.Dropdown(
                                choices=["None"] + [f"{i:02d}" for i in range(1, 21)],
                                value="None", label="Evaluasi Kunci Jawaban (Opsional)", container=True,
                            )
                            gr.HTML('<div style="height:0.5rem;"></div>')
                            with gr.Row():
                                rec_clear = gr.Button("Clear", variant="secondary")
                                rec_stop  = gr.Button("⬛ Stop", variant="secondary")
                                rec_run   = gr.Button("▶ Run Pipeline", variant="primary")

                    # Results Card
                    with gr.Column(elem_classes="glass-card"):
                        gr.HTML("""<div class="card-header">
                            <span class="material-symbols-outlined icon" style="color:#c084fc;">output</span>
                            <span class="label">Response</span>
                        </div>""")
                        with gr.Row():
                            rec_out_audio = gr.Audio(label="Audio Respons (TTS)", interactive=False)
                            rec_out_csv = gr.File(label="Download CSV", interactive=False)

                    # Logs Card
                    with gr.Column(elem_classes="glass-card"):
                        gr.HTML("""<div class="card-header">
                            <span class="material-symbols-outlined icon" style="color:#38bdf8;">terminal</span>
                            <span class="label">Logs</span>
                        </div>""")
                        rec_log = gr.Markdown(value="*Menunggu input...*")

                # ═══ VIEW 3: BATCH NLP ═══════════════════════════
                with gr.TabItem("Batch", id="tab_batch"):
                    with gr.Row():
                        # Batch Control Card
                        with gr.Column(scale=2, elem_classes="glass-card"):
                            gr.HTML("""<div class="card-header">
                                <span class="material-symbols-outlined icon" style="color:#93c5fd;">settings_b_roll</span>
                                <span class="label">Batch Control</span>
                            </div>
                            <p class="toggle-label">Source Directory</p>
                            <div style="background:rgba(5,12,28,0.6);border:1px solid rgba(59,130,246,0.12);border-radius:0.625rem;padding:0.75rem;margin-bottom:1.25rem;">
                                <p style="font-size:0.75rem;color:#64748b;margin:0 0 0.4rem 0;">Processing all WAV files from:</p>
                                <span class="path-badge">corpus/audio/Audio_NLP/</span>
                            </div>
                            <p class="toggle-label">Output Language Mode</p>
                            """)
                            bat_mode = gr.Radio(
                                choices=[("Preserve", "preserve"), ("Normalize", "normalize")],
                                value="preserve", label="", container=False,
                                elem_classes="toggle-radio",
                            )
                            gr.HTML('<div style="height:1rem;"></div>')
                            with gr.Row():
                                bat_stop = gr.Button("⬛ Stop", variant="secondary")
                                bat_run  = gr.Button("▶ Start Processing Run", variant="primary")

                        # Right Column: Logs + Results
                        with gr.Column(scale=3):
                            with gr.Column(elem_classes="glass-card"):
                                gr.HTML("""<div class="card-header">
                                    <span class="material-symbols-outlined icon" style="color:#38bdf8;">terminal</span>
                                    <span class="label mono">system_process_log.sh</span>
                                </div>""")
                                bat_log = gr.Markdown(
                                    value="*# NLP Audio Batch Processor v2.4.1\n# Initialization complete. Waiting for user command...*"
                                )

                            with gr.Column(elem_classes="glass-card"):
                                gr.HTML("""<div class="card-header">
                                    <span class="material-symbols-outlined icon" style="color:#b9c7e0;">analytics</span>
                                    <span class="label">Analysis Results</span>
                                </div>""")
                                bat_out_csv = gr.File(label="Download CSV", interactive=False)

    # ═══════════════════════════════════════════════════════════
    #  NAVIGATION LOGIC
    # ═══════════════════════════════════════════════════════════

    def show_upload():
        return gr.Tabs(selected="tab_upload")

    def show_record():
        return gr.Tabs(selected="tab_record")

    def show_batch():
        return gr.Tabs(selected="tab_batch")

    nav_upload.click(show_upload, outputs=tabs)
    nav_record.click(show_record, outputs=tabs)
    nav_batch.click(show_batch,  outputs=tabs)

    # ═══════════════════════════════════════════════════════════
    #  PIPELINE TRIGGERS
    # ═══════════════════════════════════════════════════════════

    # Upload
    up_run.click(process_single_audio, inputs=[up_audio, up_mode, up_voice, up_ref], outputs=[up_out_audio, up_out_csv, up_log])
    up_clear.click(clear_single, outputs=[up_audio, up_out_audio, up_out_csv, up_log])
    up_stop.click(request_stop, outputs=[up_log])

    # Record
    rec_run.click(process_single_audio, inputs=[rec_audio, rec_mode, rec_voice, rec_ref], outputs=[rec_out_audio, rec_out_csv, rec_log])
    rec_clear.click(clear_record, outputs=[rec_audio, rec_out_audio, rec_out_csv, rec_log])
    rec_stop.click(request_stop, outputs=[rec_log])

    # Batch
    bat_run.click(process_batch_nlp, inputs=[bat_mode], outputs=[bat_out_csv, bat_log])
    bat_stop.click(request_stop, outputs=[bat_log])


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
