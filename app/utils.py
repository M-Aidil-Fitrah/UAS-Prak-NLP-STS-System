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

# Kata-kata umum Bahasa Indonesia yang sering muncul (Ekspansi)
COMMON_ID_WORDS = {
    "aku", "kamu", "dia", "kami", "mereka", "kita", "saya", "dan", "atau",
    "yang", "ini", "itu", "ada", "tidak", "bisa", "mau", "minta", "tolong",
    "bantu", "pergi", "dari", "ke", "di", "untuk", "dengan", "cara",
    "bagaimana", "belajar", "susah", "gak", "dong", "nih", "lagi", "sudah",
    "belum", "punya", "perlu", "butuh", "coba", "jelaskan", "buat", "proses",
    "step", "minggu", "depan", "besok", "sekarang", "nanti", "tadi", "lalu",
    "pada", "dalam", "tapi", "tetapi", "juga", "ya", "bukan", "akan", "sedang",
    "telah", "kalian", "apa", "siapa", "kapan", "dimana", "mengapa", "berapa",
    "ingin", "suka", "tahu", "mengerti", "paham", "bikin", "kasih", "beri",
    "ambil", "datang", "pulang", "makan", "minum", "tidur", "bangun", "mandi",
    "jalan", "lari", "bicara", "ngobrol", "bilang", "kata", "buku", "meja",
    "kursi", "mobil", "motor", "rumah", "sekolah", "kantor", "pasar", "toko",
    "harga", "murah", "mahal", "bagus", "jelek", "besar", "kecil", "panjang",
    "pendek", "baru", "lama", "tua", "muda", "panas", "dingin", "hari", "bulan",
    "tahun", "jam", "menit", "detik", "pagi", "siang", "sore", "malam", "lusa",
    "kemarin", "terus", "kemudian", "setelah", "sebelum", "karena", "sebab",
    "akibat", "jadi", "maka", "jika", "kalau", "asalkan", "walaupun", "meskipun",
    "namun", "sih", "kok", "kan", "lah", "deh"
}

# Kata kunci bahasa Arab (transliterasi umum/romanisasi)
COMMON_AR_WORDS = {
    "uridu", "urīdu", "akhi", "ukhti", "ya", "ila", "ilā", "min", "hal", "afdhal",
    "rihlatan", "mubashirah", "qadim", "ghadan", "wa", "fi", "ala", "an", "maa",
    "man", "ayna", "kayfa", "mata", "kam", "ana", "anta", "anti", "huwa", "hiya",
    "nahnu", "hum", "antum", "hadha", "hadhihi", "dhalika", "tilka", "na'am",
    "la", "lā", "shukran", "afwan", "marhaban", "assalamu", "alaikum", "bismillah",
    "insyaallah", "mashaallah", "alhamdulillah", "astaghfirullah", "subhanallah",
    "allahu", "akbar", "masjid", "haram", "nabawi", "makkah", "madinah", "jeddah",
    "saudi", "umrah", "hajj", "tawaf", "sa'i", "zamzam", "ihram", "miqat",
    "mutawwif", "ustadz", "syekh", "qodal", "safaa", "marwah"
}

# Kata kunci bahasa Inggris yang biasa muncul dalam code-switching
COMMON_EN_WORDS = {
    "book", "flight", "schedule", "travel", "include", "visit", "help",
    "arrange", "transport", "tomorrow", "explain", "step", "apply", "visa",
    "how", "prepare", "documents", "can", "you", "the", "and", "to",
    "from", "with", "simple", "online", "correct", "checklist", "the", "be",
    "of", "a", "in", "that", "have", "i", "it", "for", "not", "on", "he", "as",
    "do", "at", "this", "but", "his", "by", "they", "we", "say", "her", "she",
    "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me", "when",
    "make", "like", "time", "no", "just", "him", "know", "take", "people",
    "into", "year", "your", "good", "some", "could", "them", "see", "other",
    "than", "then", "now", "look", "only", "come", "its", "over", "think",
    "also", "back", "after", "use", "two", "our", "work", "first", "well",
    "way", "even", "new", "want", "because", "any", "these", "give", "day",
    "most", "us", "yesterday", "today", "morning", "night", "hotel", "airport",
    "ticket", "passport", "luggage", "baggage", "smooth", "safe", "trip", "journey"
}


# ─── Phonetic Lexical Correction (Error STT) ─────────────────────────────────
# Memperbaiki halusinasi pendengaran STT (Whisper) berdasarkan kemiripan suara.
PHONETIC_CORRECTIONS = {
    # Kesalahan STT Inggris
    r"\bflag\b": "flight",
    r"\bflek\b": "flight",
    r"\bsekedul\b": "schedule",
    r"\bskedul\b": "schedule",
    r"\bschedul\b": "schedule",
    r"\barrenge\b": "arrange",
    r"\btranspor\b": "transport",
    r"\baply\b": "apply",
    r"\bpespor\b": "passport",
    r"\bpaspot\b": "passport",
    r"\bcek lis\b": "checklist",
    r"\bceklist\b": "checklist",

    # Kesalahan Nama Tempat & Indonesia
    r"\bkejada\b": "ke Jeddah",
    r"\bke jada\b": "ke Jeddah",
    r"\bjedah\b": "Jeddah",
    r"\bmadina\b": "Madinah",
    r"\bmekah\b": "Makkah",
    r"\bmekkah\b": "Makkah",
    r"\bfisa\b": "visa",

    # Kesalahan Arab Transliterasi
    r"\baki\b": "akhi",
    r"\bukti\b": "ukhti",
    r"\bkodal\b": "qodal",
    r"\bkudal\b": "qodal",
    r"\bmin jidah\b": "min Jeddah",
    r"\bmin jida\b": "min Jeddah",
    r"\bsapa\b": "safaa",
    r"\bmarwa\b": "marwah",
    r"\bjam jam\b": "zamzam",
    r"\bjamzam\b": "zamzam",
    
    # Halusinasi Whisper Ekstrem (Code-Switching Arab-Inggris)
    r"\bhri du\b": "uridu",
    r"\bhri\b": "uridu",
    r"\barin\b": "arrange",
    r"\bsangspor\b": "transport"
}

def apply_phonetic_corrections(text: str) -> str:
    """Koreksi kata salah dengar STT berdasarkan Regex dari PHONETIC_CORRECTIONS."""
    for pattern, replacement in PHONETIC_CORRECTIONS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


# ─── Normalisasi ─────────────────────────────────────────────────────────────

def normalize_transcript(text: str) -> str:
    """
    Membersihkan teks mentah hasil transkripsi STT:
    - Menghapus spasi ganda & newline berlebih
    - Menghilangkan karakter kontrol non-printable
    - Menormalkan tanda baca dan kutipan
    - (Baru) Menghapus harakat/diacritics Arab & tatweel agar seragam
    """
    if not text:
        return ""

    # 1. Hapus Diakritik Global (Harakat Arab & Aksen Latin Whisper seperti Ḥ, ī)
    # Ubah ke NFD untuk memecah huruf dan tanda bacanya (marks)
    text = unicodedata.normalize("NFD", text)
    # Filter buang semua 'Mn' (Mark, Nonspacing)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    # Kembalikan ke NFC murni
    text = unicodedata.normalize("NFC", text)

    # Hapus karakter kontrol kecuali newline/tab
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # 2. Terapkan koreksi fonetik spesifik domain Umrah (setelah aksen bersih)
    text = apply_phonetic_corrections(text)

    # Normalkan tanda kutip miring ke kutip lurus
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')

    # 3. Hapus Tatweel (garis panjang Arab) yang tersisa
    text = re.sub(r'[\u0640]', '', text)

    # Advanced NLP: Arabic Orthographic Normalization
    text = re.sub(r'[أإآ]', 'ا', text) # Normalisasi Alif
    text = re.sub(r'ة', 'ه', text)     # Normalisasi Ta Marbuthoh
    text = re.sub(r'ى', 'ي', text)     # Normalisasi Alif Maqsura

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
    significant = [lang for lang, c in lang_counts.items() if c / total > 0.2]
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
