"""
app/logger.py — Centralized Logging Setup
Mengatur logging global dengan RotatingFileHandler untuk mencatat seluruh aktivitas
sistem secara otomatis ke dalam file 'log/app.log'.
"""

import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logger():
    """
    Mengonfigurasi logging global. Harus dipanggil sekali di awal program.
    """
    # Dapatkan root logger (mempengaruhi semua modul yang menggunakan logging)
    root_logger = logging.getLogger()
    
    # Cegah penambahan handler duplikat jika fungsi dipanggil lebih dari sekali
    if root_logger.hasHandlers():
        return

    # Pastikan folder log tersedia
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "log")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "app.log")
    
    # Format log
    log_format = logging.Formatter(
        fmt="%(asctime)s | [%(levelname)s] | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Console Handler (tampilkan di terminal)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)

    # 2. File Handler (Rotating, maks 5MB, 3 backup)
    file_handler = RotatingFileHandler(
        filename=log_file,
        mode='a',
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,             # Simpan app.log.1, app.log.2, app.log.3
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.INFO)

    # Setup Root Logger
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
