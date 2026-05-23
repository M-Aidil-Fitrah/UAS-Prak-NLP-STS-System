"""
app/main.py — FastAPI Backend Server
Endpoint voice-chat end-to-end (STT -> Processing -> LLM -> TTS).
Menggunakan app.pipeline untuk logika inti.
"""

import os
import uuid
import shutil
import logging
import urllib.parse
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.pipeline import run_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Speech-to-Speech Code-Switching System",
    description="UAS Praktikum NLP — Speech-to-Speech dengan Code-Switching (ID-EN-AR)",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "temp"
OUTPUT_DIR = "output"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "audio"), exist_ok=True)


@app.post("/voice-chat")
async def voice_chat_endpoint(
    audio: UploadFile = File(...),
    mode: str = Form("preserve"),
):
    """Endpoint Voice-Chat: audio -> STT -> LLM -> TTS -> audio response."""
    if mode not in ["preserve", "normalize"]:
        raise HTTPException(status_code=400, detail="Mode harus 'preserve' atau 'normalize'")

    session_id = uuid.uuid4().hex[:8]
    logger.info(f"\n=== [Pipeline Started] Session: {session_id} | Mode: {mode} ===")

    input_ext = os.path.splitext(audio.filename or ".wav")[1] or ".wav"
    temp_input = os.path.join(TEMP_DIR, f"input_{session_id}{input_ext}")

    try:
        # Simpan audio input
        with open(temp_input, "wb") as buf:
            shutil.copyfileobj(audio.file, buf)

        # Jalankan pipeline
        result = run_pipeline(temp_input, mode=mode, output_dir=OUTPUT_DIR)

        if result["status"] != "success":
            raise RuntimeError(result.get("error", "Pipeline gagal"))

        output_path = result["tts_output_path"]
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError("Audio output kosong")

        logger.info(f"=== [Pipeline Finished] Session: {session_id} ===")

        # Kirim audio + metadata via URL-encoded headers
        headers = {
            "X-Transcription": urllib.parse.quote(result.get("raw_transcript", "")),
            "X-LLM-Response": urllib.parse.quote(result.get("llm_response", "")),
            "Access-Control-Expose-Headers": "X-Transcription, X-LLM-Response",
        }
        return FileResponse(
            path=output_path,
            media_type="audio/wav",
            filename=f"response_{session_id}.wav",
            headers=headers,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Pipeline Error]: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        _safe_delete(temp_input)


@app.on_event("shutdown")
def cleanup_temp():
    """Bersihkan folder temp saat server dimatikan."""
    if os.path.exists(TEMP_DIR):
        logger.info("Cleaning up temp directory...")
        for f in os.listdir(TEMP_DIR):
            if f != ".gitkeep":
                _safe_delete(os.path.join(TEMP_DIR, f))


def _safe_delete(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logger.warning(f"Gagal hapus {path}: {e}")
