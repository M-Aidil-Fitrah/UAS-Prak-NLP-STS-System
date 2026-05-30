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
# Model utama dari env
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "models/gemma-4-31b-it")

# Rantai model fallback otomatis yang diakses secara berurutan jika terjadi kegagalan (Rate Limit / Server Error):
# gemma-4-31b-it -> gemma-4-26b-a4b-it -> gemini-2.5-flash -> gemini-3.1-flash-lite
FALLBACK_CHAIN = []
for model in [GEMINI_MODEL, "models/gemma-4-26b-a4b-it", "models/gemini-2.5-flash", "models/gemini-3.1-flash-lite"]:
    if model not in FALLBACK_CHAIN:
        FALLBACK_CHAIN.append(model)

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
1. Pahami apa yang dimaksud atau ditanyakan pengguna, lalu JAWAB atau RESPONS pernyataan tersebut (bukan sekadar menerjemahkan atau mengulangi ucapannya).
2. Berikan respons yang MEMPERTAHANKAN pola code-switching yang sama seperti input.
3. JANGAN menggunakan markdown formatting apapun selain JSON (tanpa blok ```json).
4. Kamu WAJIB mengembalikan output murni dalam format JSON dengan dua key:
   - "teks_asli": Respons aktual dengan ejaan baku. Untuk bahasa Arab WAJIB menggunakan Harakat (Tashkeel) penuh.
   - "teks_fonetik": Transliterasi khusus mesin Text-to-Speech (TTS) Indonesia. Untuk bahasa Arab gunakan huruf Latin, dan untuk bahasa Inggris WAJIB gunakan ejaan pelafalan ala Indonesia (contoh: "flight" ditulis "flait", "schedule" ditulis "skedul").
""".strip()

SYSTEM_PROMPT_NORMALIZE = """
Kamu adalah asisten percakapan cerdas yang fasih berbahasa Indonesia.
Pengguna mungkin berbicara dengan campuran bahasa.

INSTRUKSI:
1. Pahami apa yang dimaksud pengguna, lalu JAWAB atau RESPONS pernyataan tersebut (bukan sekadar menerjemahkan/mengulangi ucapannya).
2. Berikan respons SELURUHNYA dalam Bahasa Indonesia baku.
3. JANGAN menggunakan markdown formatting apapun selain JSON (tanpa blok ```json).
4. Kamu WAJIB mengembalikan output murni dalam format JSON dengan dua key:
   - "teks_asli": Respons baku dalam bahasa Indonesia.
   - "teks_fonetik": Sama dengan teks_asli (karena bahasa Indonesia).
""".strip()

SYSTEM_PROMPT_TRANSLATE_EN = """
You are a conversational assistant. The user will say something (possibly mixing languages). 
DO NOT just translate their speech. You must UNDERSTAND what they are saying and RESPOND to them (answer their question or continue the conversation) COMPLETELY in **English**.
DO NOT use any markdown formatting other than JSON (no ```json blocks).
You MUST return the output strictly in JSON format with two keys:
- "teks_asli": The actual English response.
- "teks_fonetik": The exact English pronunciation spelled out using Indonesian phonetics/alphabet (e.g., "flight" written as "flait", "I want" written as "ai won").
""".strip()

SYSTEM_PROMPT_TRANSLATE_AR = """
أنت مساعد محادثة ذكي. سيقول المستخدم شيئًا (ربما يخلط بين اللغات).
لا تترجم فقط ما يقوله. يجب عليك فهم ما يعنيه والرد عليه (الإجابة على سؤاله أو مواصلة المحادثة) بالكامل باللغة **العربية**.
لا تستخدم أي تنسيق Markdown بخلاف JSON.
يجب إرجاع الإخراج بتنسيق JSON صارم مع مفتاحين:
- "teks_asli": الرد باللغة العربية مع التشكيل الكامل (Full Harakat).
- "teks_fonetik": الترجمة الصوتية (Transliteration) للرد العربي باستخدام الحروف اللاتينية.
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
    Mengirim transkrip ke Gemini/Gemma dan mengembalikan teks respons.
    Mendukung sistem Auto-Fallback jika salah satu model mengalami error 500/503 atau rate-limit.

    Args:
        transcript: Teks hasil transkripsi STT (sudah dinormalisasi).
        mode: "preserve" (pertahankan code-switching) atau "normalize" (Bahasa Indonesia baku).

    Returns:
        Teks respons dari LLM.
    """
    if not transcript or not transcript.strip():
        return "Maaf, saya tidak dapat memahami input yang kosong."

    # Pilih system prompt sesuai mode
    if mode == "normalize":
        system_prompt = SYSTEM_PROMPT_NORMALIZE
    elif mode == "translate_en":
        system_prompt = SYSTEM_PROMPT_TRANSLATE_EN
    elif mode == "translate_ar":
        system_prompt = SYSTEM_PROMPT_TRANSLATE_AR
    else:
        system_prompt = SYSTEM_PROMPT_PRESERVE

    client = _get_client()

    # Menggunakan rantai model fallback otomatis yang diatur secara terpusat di tingkat modul
    fallback_list = FALLBACK_CHAIN

    last_error = None
    for model_name in fallback_list:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"[LLM] Mengirim ke {model_name} (Percobaan {attempt}/{MAX_RETRIES})")

                response = client.models.generate_content(
                    model=model_name,
                    contents=transcript,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.7,
                        max_output_tokens=2048,
                        response_mime_type="application/json",
                    ),
                )

                import json
                result_text = response.text.strip()
                logger.info(f"[LLM] Respons sukses diterima dari {model_name}")
                
                try:
                    parsed = json.loads(result_text)
                    if "teks_asli" not in parsed or "teks_fonetik" not in parsed:
                        raise ValueError("JSON tidak memiliki key teks_asli atau teks_fonetik")
                    return parsed
                except json.JSONDecodeError:
                    logger.error(f"[LLM] Gagal parsing JSON. Raw: {result_text}")
                    import re
                    # Hapus sintaks JSON kotor agar TTS tidak membaca "kurung kurawal teks asli"
                    clean_text = re.sub(r'\{|"teks_asli"\s*:\s*"|"teks_fonetik"\s*:\s*"|"', '', result_text).strip()
                    return {"teks_asli": result_text, "teks_fonetik": clean_text}

            except Exception as e:
                error_str = str(e).lower()
                last_error = e

                # Cek tipe error untuk menentukan strategi retry
                is_rate_limit = "429" in error_str or "quota" in error_str or "rate" in error_str
                is_server_error = "500" in error_str or "503" in error_str or "internal" in error_str or "service unavailable" in error_str

                if is_rate_limit:
                    logger.warning(
                        f"[LLM] Rate limit tercapai pada {model_name}. "
                        f"Menunggu {RETRY_SLEEP_SEC}s sebelum mencoba lagi..."
                    )
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_SLEEP_SEC)
                        continue
                elif is_server_error:
                    logger.warning(
                        f"[LLM] Server Google mengalami gangguan 500/503 pada {model_name}. "
                        f"Menunggu 2s sebelum mencoba lagi..."
                    )
                    if attempt < MAX_RETRIES:
                        time.sleep(2)
                        continue

                # Jika sudah mencapai limit retry atau error permanen lainnya, beralih ke model fallback berikutnya
                logger.error(f"[LLM] Gagal mendapatkan respons dari {model_name}: {e}")
                break

    raise RuntimeError(f"Seluruh model LLM gagal merespons. Error terakhir: {last_error}")


# ─── Test mandiri ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_input = "Aku mau book flight ke Jeddah minggu depan, bisa bantu schedule?"
    print("=== Mode: preserve ===")
    print(generate_response(test_input, mode="preserve"))
    print("\n=== Mode: normalize ===")
    print(generate_response(test_input, mode="normalize"))
