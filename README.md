# Voice Code-Switching System (UAS Praktikum NLP 2025/2026 Genap)

Sistem multilingual **Speech-to-Speech** end-to-end yang menerima ujaran **code-switching** Bahasa Indonesia, Inggris, dan Arab, memprosesnya melalui pipeline STT → LLM → TTS, lalu menghasilkan respons suara kembali.

**NPM:** 2335 | **Kelas:** Praktikum NLP 2025/2026 Genap

---

## Pipeline Sistem

```
Audio Input (WAV)
      ↓
[STT] whisper.cpp (model: small)
      ↓  Transkripsi teks
[PROCESSING] utils.py — normalisasi & language tagging (ID/EN/AR)
      ↓  Teks bersih + konteks bahasa
[LLM] Google Gemini API — mode preserve CS / normalize
      ↓  Teks respons
[TTS] Coqui TTS (Indonesian VITS v1.2) — segmentasi per bahasa
      ↓
Audio Output (WAV)
```

---

## Struktur Proyek

```
voice-cs-system/
├── .env                         # API key & konfigurasi (tidak di-commit)
├── .gitignore
├── requirements.txt
├── README.md
├── app/
│   ├── main.py                  # FastAPI backend — endpoint /voice-chat
│   ├── stt.py                   # Speech-to-Text via whisper.cpp subprocess
│   ├── llm.py                   # Gemini API — preserve CS & normalize mode
│   ├── tts.py                   # Coqui TTS — sintesis per segmen bahasa
│   ├── utils.py                 # Normalisasi teks & language tagging
│   └── coqui_tts/
│       └── data/                # Model TTS lokal (download manual)
│           ├── checkpoint_1260000-inference.pth
│           ├── config.json
│           └── speakers.pth
├── corpus/
│   └── audio/                   # 11 file WAV rekaman code-switching
│       ├── 2335_audio01.wav
│       └── ...
├── models/
│   └── whisper.cpp/             # Whisper.cpp hasil clone & kompilasi
├── gradio_app/
│   ├── app.py                   # UI Gradio — input mic & output audio player
│   └── analisis_pipeline.py     # Skrip evaluasi otomatis seluruh korpus
└── temp/                        # Folder audio temporer (auto-dibersihkan)
```

---

## Setup & Menjalankan Proyek

### Prasyarat
- Python 3.11 (direkomendasikan untuk kompatibilitas semua library)
- CMake (untuk kompilasi whisper.cpp)
- Git

### 1. Clone & Setup Virtual Environment

```bash
git clone <url-repo-kamu>
cd voice-cs-system

# Buat dan aktifkan venv
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate
```

### 2. Install Dependensi

```bash
pip install -r requirements.txt

# WAJIB: Fix konflik Coqui TTS + Transformers
pip install transformers==5.0.0
```

### 3. Konfigurasi API Key

Salin `.env` dan isi dengan API key asli kamu:
```bash
# Edit file .env
GEMINI_API_KEY=AIzaSy...isiKeyKamuDisini...
```

> ⚠️ **JANGAN** commit file `.env` ke repositori!

### 4. Setup Whisper.cpp

```bash
# Clone & kompilasi
git clone https://github.com/ggml-org/whisper.cpp.git models/whisper.cpp
cd models/whisper.cpp
cmake -B build
cmake --build build --config Release

# Download model small (±470MB, cocok untuk Intel i5-6300U)
bash ./models/download-ggml-model.sh small
cd ../..
```

### 5. Download Model TTS (Coqui Indonesian-VITS v1.2)

Download dari [wikidepia/indonesian-tts](https://github.com/wikidepia/indonesian-tts) dan letakkan di:
```
app/coqui_tts/data/
├── checkpoint_1260000-inference.pth
├── config.json
└── speakers.pth
```

### 6. Jalankan Backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Jalankan Gradio UI (terminal terpisah)

```bash
cd gradio_app
python app.py
# Akses di: http://127.0.0.1:7860
```

### 8. Jalankan Evaluasi Korpus Penuh

```bash
cd gradio_app
python analisis_pipeline.py
```

---

## Dataset Korpus

| ID File | Transkrip | Pola Bahasa |
|---|---|---|
| `2335_audio01.wav` | Aku mau book flight ke Jeddah minggu depan, bisa bantu schedule? | ID-EN |
| `2335_audio02.wav` | Aku butuh travel umrah simple tapi include Madinah visit | ID-EN |
| `2335_audio03.wav` | Can you help aku arrange transport dari Jeddah ke Madinah tomorrow | EN-ID |
| `2335_audio04.wav` | Explain step by step cara apply visa Saudi dengan benar | EN-ID |
| `2335_audio05.wav` | Ya akhi, uridu book flight ila Jeddah al-usbu'al qadim... | AR-EN-ID |
| `2335_audio06.wav` | Urīdu arrange transport min Jeddah ilā Madinah ghadan | AR-EN |
| `2335_audio12.wav` | Bagaimana proses visa Saudi untuk umrah dari Indonesia sekarang | ID |
| `2335_audio13.wav` | Jelaskan step by step cara booking flight ke Jeddah secara online | ID-EN |
| `2335_audio14.wav` | How to prepare dokumen umrah dari Indonesia dengan benar | EN-ID |
| `2335_audio15.wav` | Tolong buat checklist persiapan umrah termasuk barang wajib dibawa | ID |
| `2335_audio17.wav` | Menurut kamu belajar bahasa Arab itu susah gak untuk pemula | ID-AR |

---

## Evaluasi

| Metrik | Komponen | Metode |
|---|---|---|
| WER / CER | STT | Otomatis vs. referensi transkrip |
| Kualitas Respons | LLM | Penilaian manual |
| Naturalness | TTS | Penilaian subjektif |
| Latency (ms) | End-to-End | Direkam per request di log |

---

## Teknologi

| Komponen | Pilihan |
|---|---|
| STT | whisper.cpp (model: `small`) |
| LLM | Google Gemini API via `google-genai` |
| TTS | Coqui TTS + Indonesian VITS v1.2 |
| Backend | FastAPI + Uvicorn |
| Frontend | Gradio |

---

## Referensi

- [OpenAI Whisper](https://github.com/openai/whisper)
- [ggml-org/whisper.cpp](https://github.com/ggml-org/whisper.cpp)
- [Google AI — Gemini API Docs](https://ai.google.dev/gemini-api/docs)
- [idiap/coqui-ai-TTS](https://github.com/idiap/coqui-ai-TTS)
- [wikidepia/indonesian-tts](https://github.com/wikidepia/indonesian-tts)
