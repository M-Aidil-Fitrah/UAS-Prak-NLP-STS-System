"""
app/main.py — FastAPI Backend Server
Endpoint voice-chat end-to-end (STT -> Processing -> LLM -> TTS).
Menggunakan app.pipeline untuk logika inti dan app.file_manager untuk manajemen file.
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
from app.file_manager import (
    TEMP_UPLOAD, cleanup_temp_file, cleanup_old_temp,
)

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


@app.on_event("startup")
def startup_cleanup():
    """Bersihkan file temp yang kadaluarsa (> 1 jam) saat server dijalankan."""
    cleanup_old_temp(max_age_seconds=3600)


@app.post("/voice-chat")
async def voice_chat_endpoint(
    audio: UploadFile = File(...),
    mode: str = Form("preserve"),
):
    """Endpoint Voice-Chat: audio -> STT -> LLM -> TTS -> audio response."""
    if mode not in ["preserve", "normalize", "translate_id", "translate_en", "translate_ar"]:
        raise HTTPException(status_code=400, detail="Mode tidak valid")

    session_id = uuid.uuid4().hex[:8]
    logger.info(f"\n=== [Pipeline Started] Session: {session_id} | Mode: {mode} ===")

    input_ext = os.path.splitext(audio.filename or ".wav")[1] or ".wav"
    temp_input = os.path.join(TEMP_UPLOAD, f"api_{session_id}{input_ext}")

    try:
        # Simpan audio input ke temp/upload/
        with open(temp_input, "wb") as buf:
            shutil.copyfileobj(audio.file, buf)

        # Jalankan pipeline (mode upload)
        result = run_pipeline(temp_input, mode=mode, pipeline_mode="upload")

        if result["status"] != "success":
            raise RuntimeError(result.get("error", "Pipeline gagal"))

        output_path = result["tts_output_path"]
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError("Audio output kosong")

        logger.info(f"=== [Pipeline Finished] Session: {session_id} ===")

        headers = {
            "X-Transcription": urllib.parse.quote(result.get("raw_transcript", "")),
            "X-LLM-Response":  urllib.parse.quote(result.get("llm_response", "")),
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
        cleanup_temp_file(temp_input)


@app.on_event("shutdown")
def shutdown_cleanup():
    """Bersihkan semua file temp upload saat server dimatikan."""
    cleanup_old_temp(max_age_seconds=0)  # max_age=0 hapus semua
