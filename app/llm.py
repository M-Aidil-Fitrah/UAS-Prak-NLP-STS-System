"""
app/llm.py — FASE 4: Integrasi LLM (Google Gemini API)
Mendukung dua mode respons:
  - "preserve"  : Mempertahankan pola code-switching dari input
  - "normalize" : Menormalisasi respons ke Bahasa Indonesia baku
"""

import os
import time
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# ─── Konfigurasi ─────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Sesuai instruksi proyek: kita gunakan model Gemma 4 31B
# Sesuaikan juga dengan rate limit RPM & RPD yang berlaku di Google AI Studio kamu
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "models/gemma-4-31b-it")

# Rate-limit control
MAX_RETRIES     = 3
RETRY_SLEEP_SEC = 60   # Sleep saat RPM limit tercapai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── System Prompts ───────────────────────────────────────────────────────────

SYSTEM_PROMPT_PRESERVE = """
Kamu adalah asisten percakapan cerdas yang fasih berbahasa Indonesia, Inggris, dan Arab.
Pengguna berbicara dengan pola code-switching (mencampur bahasa Indonesia, Inggris, dan Arab).

INSTRUKSI:
1. Pahami makna penuh dari pesan pengguna meskipun mengandung campuran bahasa.
2. Berikan respons yang MEMPERTAHANKAN pola code-switching yang sama seperti input.
   Contoh: jika pengguna memakai ID+EN, balaslah juga dengan ID+EN secara natural.
3. Respons harus relevan, informatif, dan terdengar natural dalam percakapan multibahasa.
4. Jangan terjemahkan ke satu bahasa tunggal kecuali diminta.
5. Tetap sopan dan membantu.
""".strip()

SYSTEM_PROMPT_NORMALIZE = """
Kamu adalah asisten percakapan cerdas yang fasih berbahasa Indonesia.
Pengguna mungkin berbicara dengan campuran bahasa (Indonesia, Inggris, Arab).

INSTRUKSI:
1. Pahami makna penuh dari pesan pengguna meskipun mengandung campuran bahasa.
2. Berikan respons SELURUHNYA dalam Bahasa Indonesia yang baku dan mudah dipahami.
3. Jangan gunakan kata-kata bahasa Inggris atau Arab kecuali kata serapan resmi.
4. Respons harus relevan, informatif, dan terdengar natural.
5. Tetap sopan dan membantu.
""".strip()


# ─── Client inisialisasi ──────────────────────────────────────────────────────

def _get_client() -> genai.Client:
    """Membuat Gemini API client dari API key di .env"""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        raise ValueError(
            "GEMINI_API_KEY belum diatur. "
            "Isi file .env dengan API key dari https://aistudio.google.com/app/apikey"
        )
    return genai.Client(api_key=GEMINI_API_KEY)


# ─── Fungsi utama ─────────────────────────────────────────────────────────────

def generate_response(transcript: str, mode: str = "preserve") -> str:
    """
    Mengirim transkrip ke Gemini dan mengembalikan teks respons.

    Args:
        transcript: Teks hasil transkripsi STT (sudah dinormalisasi).
        mode: "preserve" (pertahankan code-switching) atau "normalize" (Bahasa Indonesia baku).

    Returns:
        Teks respons dari LLM.

    Raises:
        ValueError: Jika API key tidak dikonfigurasi.
        RuntimeError: Jika permintaan gagal setelah semua retry.
    """
    if not transcript or not transcript.strip():
        return "Maaf, saya tidak dapat memahami input yang kosong."

    # Pilih system prompt sesuai mode
    if mode == "normalize":
        system_prompt = SYSTEM_PROMPT_NORMALIZE
    else:
        system_prompt = SYSTEM_PROMPT_PRESERVE

    client = _get_client()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"[LLM] Attempt {attempt}/{MAX_RETRIES} | Mode: {mode} | Model: {GEMINI_MODEL}")

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=transcript,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                    max_output_tokens=512,
                ),
            )

            result_text = response.text.strip()
            logger.info(f"[LLM] Response received ({len(result_text)} chars)")
            return result_text

        except Exception as e:
            error_str = str(e).lower()

            # Deteksi rate limit (429 / quota exceeded)
            if "429" in error_str or "quota" in error_str or "rate" in error_str:
                logger.warning(
                    f"[LLM] Rate limit tercapai pada attempt {attempt}. "
                    f"Menunggu {RETRY_SLEEP_SEC}s sebelum retry..."
                )
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_SLEEP_SEC)
                    continue
                else:
                    raise RuntimeError(
                        f"Rate limit masih aktif setelah {MAX_RETRIES} percobaan. "
                        f"Cek Request Per Minute (RPM) di Google AI Studio."
                    )

            # Error lain yang tidak perlu retry
            logger.error(f"[LLM] Error tidak terduga: {e}")
            raise RuntimeError(f"Gagal mendapatkan respons dari LLM: {e}")

    raise RuntimeError("Gagal mendapatkan respons setelah semua percobaan.")


# ─── Test mandiri ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_input = "Aku mau book flight ke Jeddah minggu depan, bisa bantu schedule?"
    print("=== Mode: preserve ===")
    print(generate_response(test_input, mode="preserve"))
    print("\n=== Mode: normalize ===")
    print(generate_response(test_input, mode="normalize"))
