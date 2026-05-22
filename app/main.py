"""
app/main.py — FASE 6: FastAPI Backend Server
Menyediakan endpoint voice-chat end-to-end (STT -> Processing -> LLM -> TTS).
"""

import os
import uuid
import shutil
import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.stt import transcribe_speech_to_text
from app.utils import normalize_transcript
from app.llm import generate_response
from app.tts import synthesize_speech

# ─── Setup Logging & Apps ────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Speech-to-Speech Code-Switching System",
    description="UAS Praktikum NLP 2025/2026 Genap - Speech-to-Speech System dengan Pola Code-Switching (ID-EN-AR)",
    version="1.0.0"
)

# Aktifkan CORS agar frontend Gradio/web client lancar berkomunikasi
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

# ─── Endpoint Utama ──────────────────────────────────────────────────────────

@app.post("/voice-chat")
async def voice_chat_endpoint(
    audio: UploadFile = File(...),
    mode: str = Form("preserve")  # "preserve" atau "normalize"
):
    """
    Endpoint Voice-Chat Utama:
    Menerima file audio user -> STT -> Normalisasi -> Gemini LLM -> TTS -> Return WAV file.
    """
    if mode not in ["preserve", "normalize"]:
        raise HTTPException(status_code=400, detail="Mode harus berupa 'preserve' atau 'normalize'")

    session_id = uuid.uuid4().hex[:8]
    logger.info(f"\n=== [Pipeline Started] Session: {session_id} | Mode: {mode} ===")

    # Path file audio temporer
    input_ext = os.path.splitext(audio.filename)[1] if audio.filename else ".wav"
    if not input_ext:
        input_ext = ".wav"
        
    temp_input_path = os.path.join(TEMP_DIR, f"input_{session_id}{input_ext}")
    temp_output_path = os.path.join(TEMP_DIR, f"output_{session_id}.wav")

    try:
        # 1. Simpan audio input secara temporer
        with open(temp_input_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        logger.info(f"[1/5] Audio input disimpan: {temp_input_path}")

        # 2. Jalankan Speech-to-Text (STT)
        logger.info("[2/5] Menjalankan transkripsi STT via Whisper...")
        raw_text = transcribe_speech_to_text(temp_input_path)
        logger.info(f"STT Raw Transcript: '{raw_text}'")

        if not raw_text.strip():
            raise HTTPException(status_code=422, detail="Gagal mentranskripsi audio: Teks kosong/tidak terdengar.")

        # 3. Text Processing (Normalisasi)
        clean_text = normalize_transcript(raw_text)
        logger.info(f"[3/5] Teks bersih (Normalisasi): '{clean_text}'")

        # 4. Hubungkan ke Large Language Model (Gemini LLM)
        logger.info(f"[4/5] Mengirim transkrip ke Gemini (Mode: {mode})...")
        llm_response = generate_response(clean_text, mode=mode)
        logger.info(f"Gemini LLM Response: '{llm_response}'")

        # 5. Sintesis respons ke Speech (TTS)
        logger.info("[5/5] Mensintesis teks respons ke audio via Coqui TTS...")
        synthesize_speech(llm_response, temp_output_path)

        # Cek apakah file audio respons berhasil dibuat
        if not os.path.exists(temp_output_path) or os.path.getsize(temp_output_path) == 0:
            raise RuntimeError("Gagal menghasilkan audio respons TTS.")

        logger.info(f"=== [Pipeline Finished] Session: {session_id} - Mengirim audio respons ===")
        
        # Kirim audio respons
        return FileResponse(
            path=temp_output_path,
            media_type="audio/wav",
            filename=f"response_{session_id}.wav"
        )

    except HTTPException as he:
        logger.error(f"[Pipeline Error] HTTP {he.status_code}: {he.detail}")
        # Hapus file temporer input jika terjadi error
        _safe_delete(temp_input_path)
        raise he
    except Exception as e:
        logger.error(f"[Pipeline Unexpected Error]: {str(e)}", exc_info=True)
        # Hapus file temporer input jika terjadi error
        _safe_delete(temp_input_path)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    finally:
        # PENTING: Hapus file input temporer setelah diproses agar hemat disk
        _safe_delete(temp_input_path)


# ─── Background Cleaner / Cleanup Helper ──────────────────────────────────────

@app.on_event("shutdown")
def cleanup_temp_dir():
    """Hapus seluruh isi folder temp saat server dimatikan."""
    if os.path.exists(TEMP_DIR):
        logger.info("Cleaning up temp directory on shutdown...")
        for filename in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, filename)
            if filename != ".gitkeep":
                _safe_delete(file_path)


def _safe_delete(path: str):
    """Menghapus file secara aman tanpa memicu crash jika file tidak ada."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.warning(f"Gagal menghapus file {path}: {e}")
