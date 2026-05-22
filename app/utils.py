"""
app/utils.py — FASE 3: Text Processing Layer
Normalisasi transkripsi STT dan language tagging (ID / EN / AR).
"""

import re
import unicodedata


# ─── Karakter khas per bahasa ────────────────────────────────────────────────

ARABIC_CHARS = set(
    "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"
    "أإآؤئءةىﻻ"
    "\u0600-\u06FF"  # blok Unicode Arab
)

LATIN_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")

# Kata-kata umum Bahasa Indonesia yang sering muncul
COMMON_ID_WORDS = {
    "aku", "kamu", "dia", "kami", "mereka", "kita", "saya", "dan", "atau",
    "yang", "ini", "itu", "ada", "tidak", "bisa", "mau", "minta", "tolong",
    "bantu", "pergi", "mau", "dari", "ke", "di", "untuk", "dengan", "cara",
    "bagaimana", "belajar", "susah", "gak", "dong", "nih", "lagi", "sudah",
    "belum", "punya", "perlu", "butuh", "coba", "jelaskan", "buat", "proses",
    "step", "minggu", "depan", "besok", "sekarang", "nanti",
}

# Kata kunci bahasa Arab (transliterasi umum)
COMMON_AR_WORDS = {
    "uridu", "urīdu", "akhi", "ya", "ila", "min", "hal", "afdhal",
    "rihlatan", "mubashirah", "qadim", "ghadan", "wa",
}

# Kata kunci bahasa Inggris yang biasa muncul dalam code-switching
COMMON_EN_WORDS = {
    "book", "flight", "schedule", "travel", "include", "visit", "help",
    "arrange", "transport", "tomorrow", "explain", "step", "apply", "visa",
    "how", "prepare", "documents", "can", "you", "the", "and", "to",
    "from", "with", "simple", "online", "correct", "checklist",
}


# ─── Normalisasi ─────────────────────────────────────────────────────────────

def normalize_transcript(text: str) -> str:
    """
    Membersihkan teks mentah hasil transkripsi STT:
    - Menghapus spasi ganda
    - Menghilangkan karakter kontrol non-printable
    - Menormalkan tanda baca dan kutipan
    - Trim whitespace di awal/akhir
    """
    if not text:
        return ""

    # Normalkan unicode (NFKC: kompatibilitas + komposisi)
    text = unicodedata.normalize("NFKC", text)

    # Hapus karakter kontrol kecuali newline/tab
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Normalkan tanda kutip miring ke kutip lurus
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')

    # Hapus spasi berulang
    text = re.sub(r" {2,}", " ", text)

    # Hapus baris kosong berulang
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ─── Language Tagging ─────────────────────────────────────────────────────────

def detect_word_language(word: str) -> str:
    """
    Deteksi bahasa dari satu kata berdasarkan karakter dan kamus kata umum.
    Mengembalikan: 'AR', 'EN', 'ID', atau 'UNK'.
    """
    word_lower = word.lower().strip(".,!?;:\"'")

    # Cek karakter Arab
    if any(c in ARABIC_CHARS for c in word):
        return "AR"

    # Cek kamus kata umum
    if word_lower in COMMON_AR_WORDS:
        return "AR"
    if word_lower in COMMON_ID_WORDS:
        return "ID"
    if word_lower in COMMON_EN_WORDS:
        return "EN"

    # Fallback: semua karakter Latin → ID (default untuk teks Indonesia)
    if all(c in LATIN_CHARS or c in " '-" for c in word):
        return "ID"

    return "UNK"


def tag_code_switching(text: str) -> list[dict]:
    """
    Memecah teks menjadi segmen berdasarkan bahasa yang terdeteksi.
    Mengembalikan list of dict: [{"lang": "ID", "text": "..."}, ...]

    Contoh output:
        [
            {"lang": "ID", "text": "Aku mau"},
            {"lang": "EN", "text": "book flight"},
            {"lang": "ID", "text": "ke Jeddah"},
        ]
    """
    if not text:
        return []

    words = text.split()
    segments = []
    current_lang = None
    current_words = []

    for word in words:
        lang = detect_word_language(word)

        # Jika language sama, lanjut tambah ke segmen yang sama
        if lang == current_lang or lang == "UNK":
            current_words.append(word)
        else:
            # Simpan segmen sebelumnya
            if current_words:
                segments.append({
                    "lang": current_lang or "ID",
                    "text": " ".join(current_words)
                })
            current_lang = lang
            current_words = [word]

    # Tambahkan segmen terakhir
    if current_words:
        segments.append({
            "lang": current_lang or "ID",
            "text": " ".join(current_words)
        })

    return segments


def get_dominant_language(text: str) -> str:
    """
    Menentukan bahasa dominan dalam sebuah teks (ID / EN / AR / MIXED).
    """
    segments = tag_code_switching(text)
    if not segments:
        return "ID"

    lang_counts = {"ID": 0, "EN": 0, "AR": 0}
    for seg in segments:
        lang = seg["lang"]
        word_count = len(seg["text"].split())
        if lang in lang_counts:
            lang_counts[lang] += word_count

    total = sum(lang_counts.values())
    if total == 0:
        return "ID"

    # Kalau ada 2+ bahasa dengan > 20% masing-masing → MIXED
    significant = [l for l, c in lang_counts.items() if c / total > 0.2]
    if len(significant) > 1:
        return "MIXED"

    return max(lang_counts, key=lang_counts.get)


def prepare_llm_prompt_context(text: str, mode: str = "preserve") -> str:
    """
    Mempersiapkan konteks bahasa untuk disertakan dalam prompt LLM.
    mode: 'preserve' | 'normalize'
    """
    dominant = get_dominant_language(text)
    segments = tag_code_switching(text)
    langs_found = list({seg["lang"] for seg in segments})

    context = (
        f"[Konteks bahasa: dominan={dominant}, "
        f"bahasa terdeteksi={'+'.join(langs_found)}, "
        f"mode={mode}]"
    )
    return context


# ─── Test mandiri ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_texts = [
        "Aku mau book flight ke Jeddah minggu depan, bisa bantu schedule?",
        "Ya akhi, uridu book flight ila Jeddah",
        "Explain step by step cara apply visa Saudi dengan benar",
        "Urīdu arrange transport min Jeddah ilā Madinah ghadan",
    ]

    for t in test_texts:
        print(f"\nInput  : {t}")
        print(f"Cleaned: {normalize_transcript(t)}")
        print(f"Tagged : {tag_code_switching(t)}")
        print(f"Dominant: {get_dominant_language(t)}")
