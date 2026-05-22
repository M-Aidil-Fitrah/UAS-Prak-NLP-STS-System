import os
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Konfigurasi path
# Default ke hasil kompilasi whisper.cpp dari source (MinGW build)
WHISPER_BIN = os.getenv("WHISPER_BIN", "models/whisper.cpp/build/bin/whisper-cli.exe")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "models/whisper.cpp/models/ggml-small.bin")

def transcribe_speech_to_text(audio_path: str) -> str:
    """
    Melakukan transkripsi audio ke teks menggunakan whisper.cpp secara dinamis.
    Mendukung deteksi bahasa dan translasi opsional.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"File audio tidak ditemukan di: {audio_path}")
        
    if not os.path.exists(WHISPER_BIN):
        raise FileNotFoundError(f"Binary Whisper tidak ditemukan di: {WHISPER_BIN}. Pastikan sudah dikompilasi atau diunduh.")
        
    if not os.path.exists(WHISPER_MODEL):
        raise FileNotFoundError(f"Model Whisper tidak ditemukan di: {WHISPER_MODEL}. Jalankan download-ggml-model.sh.")

    # Menjalankan whisper-cli
    # Gunakan flag -f untuk file, -m untuk model, -nt untuk menghilangkan timestamp (no-timestamps), -l auto untuk deteksi bahasa
    command = [
        WHISPER_BIN,
        "-m", WHISPER_MODEL,
        "-f", audio_path,
        "-nt",  # No timestamps
        "-l", "auto" # Auto detect language (berguna untuk code-switching)
    ]
    
    try:
        # Eksekusi command dan tangkap outputnya
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            encoding='utf-8'
        )
        
        # Ambil teks transkripsi (biasanya di stdout)
        # Menghapus baris kosong dan whitespace ekstra
        transcript = result.stdout.strip()
        
        # Filter jika whisper.cpp mengeluarkan info ke stdout yang tidak diperlukan (seperti tag [00:00:00])
        clean_lines = []
        for line in transcript.split('\n'):
            line = line.strip()
            if line and not line.startswith('[') and not line.startswith('whisper_'):
                clean_lines.append(line)
                
        return " ".join(clean_lines)

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        raise RuntimeError(f"Gagal melakukan transkripsi: {error_msg}")
    except Exception as e:
        raise RuntimeError(f"Error tidak terduga saat transkripsi: {str(e)}")

# Fungsi pengujian mandiri
if __name__ == "__main__":
    print("Testing STT Module...")
    print(f"Whisper Bin: {WHISPER_BIN}")
    print(f"Whisper Model: {WHISPER_MODEL}")
