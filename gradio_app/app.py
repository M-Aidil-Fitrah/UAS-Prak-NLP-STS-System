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

# Jalankan Central Logger
from app.logger import setup_logger
setup_logger()

VENV_SCRIPTS = os.path.join(ROOT_DIR, "venv", "Scripts")
if os.path.exists(os.path.join(VENV_SCRIPTS, "ffmpeg.exe")):
    os.environ["PATH"] += os.pathsep + VENV_SCRIPTS
    
# Force pydub to see ffmpeg if it's imported later
os.environ["FFMPEG_BINARY"] = os.path.join(VENV_SCRIPTS, "ffmpeg.exe")

# 2. BYPASS WINDOWS TEMP FOLDER LOCKS (Antivirus/Defender)
# Create a local temp folder so Windows Defender doesn't aggressively lock short audio files
LOCAL_TEMP = os.path.join(ROOT_DIR, "temp", "upload")
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
    run_pipeline, results_to_csv, collect_corpus_files_with_meta,
    compute_language_ratio, REFERENCE_TRANSCRIPTS,
    calculate_wer_best, calculate_cer_best
)
from app.stt import transcribe_speech_to_text
from app.utils import normalize_transcript, tag_code_switching, get_dominant_language
from app.llm import generate_response
from app.tts import synthesize_speech
from app.file_manager import (
    get_temp_path, get_output_audio_path, get_batch_csv_path,
    get_checkpoint_path,
    cleanup_temp_file, cleanup_output_file, CORPUS_DIR, OUTPUT_DIR, OUTPUT_BATCH
)
from app.evaluator import build_eval_dataframe, build_avg_charts

# Import theme
from gradio_app.theme import HEAD_HTML, CSS

os.makedirs(os.path.join(OUTPUT_DIR, "audio"), exist_ok=True)

# --- Stop flag for cancellation ---
_stop_flag = threading.Event()


def request_stop():
    _stop_flag.set()
    return "⛔ Stop diminta. Menunggu proses saat ini selesai..."


def _process_single_audio(audio_input, mode, target_lang, tts_voice, ref_id, pipeline_mode):
    """Process satu file audio dengan logging bertahap dan output rapi."""
    if audio_input is None:
        yield None, None, "⚠️ Tidak ada audio. Silakan upload atau rekam terlebih dahulu."
        return

    # --- Bypassing Gradio's internal processing bugs ---
    import subprocess

    import os
    
    _stop_flag.clear()
    results = []

    # Pastikan file audio valid dan ukurannya tidak 0
    if not os.path.exists(audio_input) or os.path.getsize(audio_input) == 0:
        yield None, None, "❌ **Error:** File audio kosong. Harap rekam lebih lama (minimal 2-3 detik)."
        return

    # Paksa konversi ke WAV menggunakan FFmpeg sistem
    temp_wav = get_temp_path(pipeline_mode)
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", audio_input, 
            "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", temp_wav
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        audio_path = temp_wav
    except Exception as e:
        cleanup_temp_file(temp_wav)
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
    actual_mode = mode
    if mode == "translate":
        actual_mode = f"translate_{target_lang}"

    yield None, None, (
        f"🤖 **[3/5] Large Language Model** — Mengirim ke Gemini...\n\n"
        f"> Normalized: *{normalized}*\n"
        f"> Bahasa dominan: **{dominant}** | Rasio: ID {ratio['ID']}% / EN {ratio['EN']}% / AR {ratio['AR']}%\n"
        f"> Mode: **{actual_mode}**"
    )
    try:
        t1 = time.time()
        llm_response_data = generate_response(normalized, mode=actual_mode)
        lat_llm = round(time.time() - t1, 3)
        
        if isinstance(llm_response_data, dict):
            teks_asli = llm_response_data.get("teks_asli", str(llm_response_data))
            teks_fonetik = llm_response_data.get("teks_fonetik", teks_asli)
        else:
            teks_asli = str(llm_response_data)
            teks_fonetik = teks_asli
            
    except Exception as e:
        yield None, None, f"❌ **Error pada LLM**\n\n{str(e)}"
        return

    if _stop_flag.is_set():
        yield None, None, "⛔ Proses dihentikan oleh pengguna."
        return

    # ── Step 4: TTS ──────────────────────────────────────────
    yield None, None, f"🔊 **[4/5] Text-to-Speech** — Mensintesis audio respons via VITS...\n\n> LLM Response: *{teks_asli[:200]}...*"
    try:
        t2 = time.time()
        from pathlib import Path
        stem = Path(audio_path).stem
        output_wav = get_output_audio_path(pipeline_mode, stem)
        os.makedirs(os.path.dirname(output_wav), exist_ok=True)
        synthesize_speech(teks_fonetik, output_wav, speaker_name=tts_voice)
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
        refs = ref_text if isinstance(ref_text, list) else [ref_text]
        wer_val = f"{calculate_wer_best(refs, normalized) * 100:.2f}%"
        cer_val = f"{calculate_cer_best(refs, normalized) * 100:.2f}%"

    # ── Step 5: Evaluation & Result ──────────────────────────
    result = {
        "filename": filename,
        "folder": "-",
        "status": "success",
        "mode": actual_mode,
        "raw_transcript": raw,
        "normalized_transcript": normalized,
        "dominant_language": dominant,
        "ratio_id": ratio["ID"],
        "ratio_en": ratio["EN"],
        "ratio_ar": ratio["AR"],
        "language_segments": str(segments),
        "wer": wer_val,
        "cer": cer_val,
        "llm_response": teks_asli,
        "tts_output_path": output_wav,
        "latency_stt": lat_stt,
        "latency_llm": lat_llm,
        "latency_tts": lat_tts,
        "latency_total": lat_total,
        "error": "",
    }
    results.append(result)

    csv_path = os.path.join(OUTPUT_DIR, pipeline_mode, f"result_{stem}.csv")
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
        f"> {teks_asli}\n\n"
        f"---\n\n"
        f"**📊 Evaluasi**\n\n"
        f"| Metrik | Nilai |\n"
        f"|--------|-------|\n"
        f"| WER | {wer_val} |\n"
        f"| CER | {cer_val} |\n"
        f"| Latency STT | {lat_stt}s |\n"
        f"| Latency LLM | {lat_llm}s |\n"
        f"| Latency TTS | {lat_tts}s |\n"
        f"| **Latency Total** | **{lat_total}s** |\n"
    )

    cleanup_temp_file(temp_wav)
    yield output_wav, csv_path, final_log


def process_upload(audio_input, mode, target_lang, tts_voice, ref_id):
    yield from _process_single_audio(audio_input, mode, target_lang, tts_voice, ref_id, "upload")


def process_record(audio_input, mode, target_lang, tts_voice, ref_id):
    yield from _process_single_audio(audio_input, mode, target_lang, tts_voice, ref_id, "record")


# --- Batch Pipeline ---

def process_batch_nlp(mode, target_lang, progress=gr.Progress()):
    import json
    from collections import defaultdict
    
    _stop_flag.clear()
    
    actual_mode = mode
    if mode == "translate":
        actual_mode = f"translate_{target_lang}"
    file_meta = collect_corpus_files_with_meta()
    total = len(file_meta)

    if total == 0:
        yield None, None, None, None, f"⚠️ Tidak ada file WAV ditemukan di:\n`{CORPUS_DIR}`"
        return

    valid_files = [m for m in file_meta if m["is_valid"]]
    invalid_files = [m for m in file_meta if not m["is_valid"]]
    
    start_msg = f"📂 Ditemukan **{total}** file audio.\n✅ Valid: {len(valid_files)} | ❌ Invalid: {len(invalid_files)}\n\n"
    if invalid_files:
        start_msg += "**File dilewati (nama salah):**\n" + "\n".join([f"- {m['filename']}" for m in invalid_files[:5]])
        if len(invalid_files) > 5:
            start_msg += f"\n...dan {len(invalid_files)-5} lainnya."

    yield None, None, None, None, start_msg + "\n\nMemulai batch processing..."

    # Group files by student
    student_groups = defaultdict(list)
    for m in valid_files:
        student_groups[m["student_id"]].append(m)
        
    results = []
    skipped = 0
    total_students = len(student_groups)
    
    for idx, (student_id, st_files) in enumerate(student_groups.items(), 1):
        if _stop_flag.is_set():
            yield None, None, None, None, f"⛔ Batch dihentikan pada Mahasiswa {idx}/{total_students}."
            break
            
        progress(idx / total_students, desc=f"[{idx}/{total_students}] Mahasiswa {student_id}")
        yield None, None, None, None, start_msg + f"\n\n👨‍🎓 **[{idx}/{total_students}]** Memproses Mahasiswa `{student_id}` ({len(st_files)} Audio)..."
        
        ckpt_path = get_checkpoint_path(student_id)
        if os.path.exists(ckpt_path):
            try:
                with open(ckpt_path, "r", encoding="utf-8") as f:
                    st_results = json.load(f)
                results.extend(st_results)
                skipped += len(st_files)
                continue
            except Exception:
                # Jika checkpoint korup, proses ulang
                pass
                
        # Proses semua file untuk mahasiswa ini
        st_results = []
        for meta in st_files:
            if _stop_flag.is_set():
                break
                

            norm_fname = meta["normalized"]
            
            try:
                res = run_pipeline(
                    meta["path"], 
                    mode=actual_mode, 
                    pipeline_mode="batch",
                    student_id=student_id,
                    normalized_filename=norm_fname
                )
                st_results.append(res)
            except Exception as e:
                st_results.append({
                    "filename": norm_fname,
                    "folder": meta["folder"],
                    "status": "error",
                    "error": str(e),
                    "mode": actual_mode,
                })
                
        # Simpan checkpoint untuk mahasiswa ini
        if not _stop_flag.is_set():
            os.makedirs(os.path.dirname(ckpt_path), exist_ok=True)
            with open(ckpt_path, "w", encoding="utf-8") as f:
                json.dump(st_results, f, ensure_ascii=False, indent=2)
            
            results.extend(st_results)

    csv_path = get_batch_csv_path()
    results_to_csv(results, csv_path)

    ok = sum(1 for r in results if r.get("status") == "success")
    fail = len(results) - ok

    summary = (
        f"✅ **Batch Processing Selesai**\n\n"
        f"| Metrik | Nilai |\n"
        f"|--------|-------|\n"
        f"| Total File | {total} |\n"
        f"| Berhasil | {ok} |\n"
        f"| Dilewati (Resume) | {skipped} |\n"
        f"| Gagal | {fail} |\n\n"
        f"📁 CSV: `output/batch/batch_results.csv`\n"
        f"🔊 Audio: `output/batch/audio/`"
    )
    
    # Generate Tabel & Grafik
    df = build_eval_dataframe(results)
    fig = build_avg_charts(results)
    
    # Save the chart to a file for downloading
    plot_path = os.path.join(OUTPUT_BATCH, "batch_evaluation_charts.png")
    fig.savefig(plot_path, dpi=200, bbox_inches="tight")
    
    yield csv_path, df, plot_path, plot_path, summary


def clear_upload(audio_out_path, csv_out_path):
    cleanup_output_file(audio_out_path)
    cleanup_output_file(csv_out_path)
    return None, None, None, ""


def clear_record(audio_out_path, csv_out_path):
    cleanup_output_file(audio_out_path)
    cleanup_output_file(csv_out_path)
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
        with gr.Column(scale=12):
            with gr.Tabs() as tabs:

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
                                        choices=[("Preserve", "preserve"), ("Normalize", "normalize"), ("Translate", "translate")],
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
                                    up_target_lang = gr.Dropdown(
                                        choices=[("English", "en"), ("Arabic", "ar")],
                                        value="en", label="Target Translate Language", container=True, visible=False
                                    )
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
                                choices=[("Preserve", "preserve"), ("Normalize", "normalize"), ("Translate", "translate")],
                                value="preserve", label="", container=False,
                                elem_classes="toggle-radio",
                            )
                            gr.HTML('<p class="toggle-label" style="margin-top: 1rem;">TTS Voice</p>')
                            rec_voice = gr.Radio(
                                choices=[("Gadis (Wanita)", "gadis"), ("Ardi (Pria)", "ardi"), ("Wibowo (Pria)", "wibowo")],
                                value="gadis", label="", container=False,
                                elem_classes="toggle-radio",
                            )
                            rec_target_lang = gr.Dropdown(
                                        choices=[("English", "en"), ("Arabic", "ar")],
                                        value="en", label="Target Translate Language", container=True, visible=False
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
                                choices=[("Preserve", "preserve"), ("Normalize", "normalize"), ("Translate", "translate")],
                                value="preserve", label="", container=False,
                                elem_classes="toggle-radio",
                            )
                            bat_target_lang = gr.Dropdown(
                                choices=[("English", "en"), ("Arabic", "ar")],
                                value="en", label="Target Translate Language", container=True, visible=False
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
                                with gr.Row():
                                    bat_out_csv = gr.File(label="Download CSV Akhir", interactive=False)
                                    bat_out_plot_file = gr.File(label="Download Grafik (PNG)", interactive=False)
                                bat_out_df = gr.Dataframe(label="Tabel Evaluasi per File", interactive=False)

                            with gr.Column(elem_classes="glass-card-no-blur"):
                                gr.HTML("""<div class="card-header">
                                    <span class="material-symbols-outlined icon" style="color:#fcd34d;">bar_chart</span>
                                    <span class="label">Interactive Chart</span>
                                </div>""")
                                bat_out_plot = gr.Image(label="Grafik Rata-Rata Evaluasi", interactive=False, show_download_button=False, type="filepath", height=480)



    # ═══════════════════════════════════════════════════════════
    #  PIPELINE TRIGGERS
    # ═══════════════════════════════════════════════════════════

    # Upload
    up_mode.change(lambda x: gr.update(visible=(x == "translate")), inputs=up_mode, outputs=up_target_lang)
    up_run.click(process_upload, inputs=[up_audio, up_mode, up_target_lang, up_voice, up_ref], outputs=[up_out_audio, up_out_csv, up_log])
    up_clear.click(clear_upload, inputs=[up_out_audio, up_out_csv], outputs=[up_audio, up_out_audio, up_out_csv, up_log])
    up_stop.click(request_stop, outputs=[up_log])

    # Record
    rec_mode.change(lambda x: gr.update(visible=(x == "translate")), inputs=rec_mode, outputs=rec_target_lang)
    rec_run.click(process_record, inputs=[rec_audio, rec_mode, rec_target_lang, rec_voice, rec_ref], outputs=[rec_out_audio, rec_out_csv, rec_log])
    rec_clear.click(clear_record, inputs=[rec_out_audio, rec_out_csv], outputs=[rec_audio, rec_out_audio, rec_out_csv, rec_log])
    rec_stop.click(request_stop, outputs=[rec_log])

    # Batch
    bat_mode.change(lambda x: gr.update(visible=(x == "translate")), inputs=bat_mode, outputs=bat_target_lang)
    bat_run.click(
        process_batch_nlp, 
        inputs=[bat_mode, bat_target_lang], 
        outputs=[bat_out_csv, bat_out_df, bat_out_plot, bat_out_plot_file, bat_log]
    )
    bat_stop.click(request_stop, outputs=[bat_log])


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
