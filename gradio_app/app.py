"""
gradio_app/app.py — FASE 7: Gradio Web UI
Membangun antarmuka web interaktif yang modern, premium, dan responsif.
"""

import os
import sys
import requests
import gradio as gr
from dotenv import load_dotenv

# Tambahkan root directory ke sys.path agar import folder 'app' berhasil
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

load_dotenv()

# Konfigurasi Endpoint Backend
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_ENDPOINT = f"{BACKEND_URL}/voice-chat"

# Custom Premium CSS untuk Tampilan Mewah (Glassmorphism & Sleek Dark Mode)
CUSTOM_CSS = """
body, .gradio-container {
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%) !important;
    font-family: 'Outfit', 'Inter', -apple-system, sans-serif !important;
    color: #f8fafc !important;
}

.main-title {
    text-align: center;
    margin-bottom: 2rem;
    padding: 1.5rem;
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(12px);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}

.main-title h1 {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}

.main-title p {
    color: #94a3b8;
    font-size: 1rem;
}

.premium-card {
    background: rgba(30, 41, 59, 0.45) !important;
    backdrop-filter: blur(16px) !important;
    border-radius: 20px !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2) !important;
    padding: 1.5rem !important;
}

.gr-button-primary {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
    border: none !important;
    color: white !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 14px 0 rgba(99, 102, 241, 0.4) !important;
}

.gr-button-primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px 0 rgba(99, 102, 241, 0.6) !important;
}

.gr-button-secondary {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #cbd5e1 !important;
    border-radius: 12px !important;
}

.gr-button-secondary:hover {
    background: rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
}

.status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.85rem;
    font-weight: 600;
}

.badge-id { background: rgba(56, 189, 248, 0.15); color: #38bdf8; }
.badge-en { background: rgba(129, 140, 248, 0.15); color: #818cf8; }
.badge-ar { background: rgba(192, 132, 252, 0.15); color: #c084fc; }

.log-box {
    background: rgba(15, 23, 42, 0.6) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    padding: 1rem !important;
    font-family: 'Fira Code', monospace !important;
}
"""

def process_voice_chat(audio_filepath, mode):
    """
    Mengirim file audio ke server backend FastAPI dan memproses hasilnya.
    """
    if audio_filepath is None:
        yield None, "### ⚠️ Peringatan\nSilakan rekam atau unggah audio terlebih dahulu."
        return

    # Update info status saat pemrosesan dimulai
    yield None, "⏳ *Sedang memproses audio... Silakan tunggu.*"

    try:
        # Buka file audio input untuk diunggah
        with open(audio_filepath, "rb") as f:
            files = {"audio": (os.path.basename(audio_filepath), f, "audio/wav")}
            data = {"mode": mode}
            
            # Request ke Backend FastAPI
            response = requests.post(API_ENDPOINT, files=files, data=data, timeout=180)

        if response.status_code == 200:
            # Simpan file WAV respons dari backend ke file lokal
            temp_output = "temp_gradio_response.wav"
            with open(temp_output, "wb") as f_out:
                f_out.write(response.content)

            # Untuk analisis lokal di Gradio, panggil fungsi pendeteksi bahasa secara manual
            # agar visualisasi log di UI menjadi kaya informasi & premium.
            from app.stt import transcribe_speech_to_text
            from app.utils import tag_code_switching, get_dominant_language

            # Cepat transcribe & tag secara internal untuk log (hanya untuk Gradio visual log)
            raw_text = transcribe_speech_to_text(audio_filepath)
            segments = tag_code_switching(raw_text)
            dominant = get_dominant_language(raw_text)

            # Buat representasi visual log yang indah dengan HTML
            tagging_html = []
            for seg in segments:
                badge_class = f"badge-{seg['lang'].lower()}"
                tagging_html.append(
                    f"<span class='status-badge {badge_class}'>{seg['lang']}</span> "
                    f"<span style='color: #f1f5f9;'>{seg['text']}</span>"
                )
            
            log_markdown = (
                f"### 🎯 Hasil Analisis Transkripsi & Bahasa\n\n"
                f"**📝 Teks Input (Transkripsi Whisper):**\n"
                f"*{raw_text}*\n\n"
                f"**🌍 Bahasa Dominan:** \n"
                f"<span class='status-badge badge-{dominant.lower()}'>{dominant}</span>\n\n"
                f"**🔀 Deteksi Segmen Code-Switching:**\n"
                f"<div style='margin-top: 0.5rem; line-height: 1.8;'>{' | '.join(tagging_html)}</div>\n\n"
                f"--- \n"
                f"**✨ Respons LLM (Gemini AI):**\n"
                f"*Respons disintesis ke audio WAV di bawah.*"
            )

            yield temp_output, log_markdown
        else:
            try:
                error_detail = response.json().get("detail", "Error tidak dikenal pada backend.")
            except Exception:
                error_detail = response.text
            yield None, f"### ❌ Gagal Memproses\n**Detail Error:** {error_detail}"

    except Exception as e:
        yield None, f"### ❌ Masalah Koneksi\nGagal terhubung ke backend server FastAPI di `{BACKEND_URL}`.\n\n*Pastikan backend server FastAPI sudah dijalankan terlebih dahulu via terminal (`uvicorn app.main:app`).*"


# ─── Gradio Block UI Design ───────────────────────────────────────────────────

with gr.Blocks(css=CUSTOM_CSS, title="Multilingual Speech-to-Speech") as demo:
    
    # Header Card
    gr.HTML(
        """
        <div class="main-title">
            <h1>🎙️ Multilingual Speech-to-Speech AI System</h1>
            <p>Sistem Asisten Suara Pintar untuk Saudi Tourism dengan Dukungan Code-Switching (Bahasa Indonesia, Inggris, Arab)</p>
        </div>
        """
    )

    with gr.Row():
        # Kolom Kiri: Input & Kontrol
        with gr.Column(scale=1):
            with gr.Group(elem_classes=["premium-card"]):
                gr.Markdown("### 🎤 Input Suara Anda")
                audio_input = gr.Audio(
                    sources=["microphone", "upload"],
                    type="filepath",
                    label="Rekam Suara atau Unggah File Audio (WAV 16kHz)"
                )
                
                gr.Markdown("### ⚙️ Konfigurasi Respons")
                mode_select = gr.Radio(
                    choices=[("Preserve (Pertahankan Campuran Bahasa)", "preserve"), 
                             ("Normalize (Baku Bahasa Indonesia)", "normalize")],
                    value="preserve",
                    label="Pola Output Bahasa"
                )
                
                with gr.Row():
                    clear_btn = gr.Button("🗑️ Bersihkan", elem_classes=["gr-button-secondary"])
                    submit_btn = gr.Button("🚀 Kirim Audio", elem_classes=["gr-button-primary"])

        # Kolom Kanan: Output & Monitoring
        with gr.Column(scale=1):
            with gr.Group(elem_classes=["premium-card"]):
                gr.Markdown("### 🔊 Audio Balasan")
                audio_output = gr.Audio(
                    label="Respons Suara Akhir (Hasil Sintesis VITS)",
                    interactive=False
                )
                
                gr.Markdown("### 🖥️ Konsol Log Pipeline")
                log_output = gr.Markdown(
                    value="*Menunggu input suara untuk memulai analisis...*",
                    elem_classes=["log-box"]
                )

    # Event Handlers
    submit_btn.click(
        fn=process_voice_chat,
        inputs=[audio_input, mode_select],
        outputs=[audio_output, log_output]
    )
    
    clear_btn.click(
        fn=lambda: (None, None, "*Menunggu input suara untuk memulai analisis...*"),
        inputs=None,
        outputs=[audio_input, audio_output, log_output]
    )

if __name__ == "__main__":
    # Jalankan Gradio App di Port 7860
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
