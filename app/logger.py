"""
app/logger.py — Centralized Logging Setup
Mengatur logging global dengan RotatingFileHandler untuk mencatat seluruh aktivitas
sistem secara otomatis ke dalam file 'log/app.log' (Gradio/API) dan 'log/cli.log' (CLI).
"""

import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logger() -> None:
    """
    Mengonfigurasi logging global untuk Gradio / FastAPI.
    Menulis ke log/app.log — RotatingFileHandler (5MB, 3 backup).
    Harus dipanggil sekali di awal program.
    """
    root_logger = logging.getLogger()

    # Cegah penambahan handler duplikat jika fungsi dipanggil lebih dari sekali
    if root_logger.hasHandlers():
        return

    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "log")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "app.log")

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


def setup_cli_logger() -> None:
    """
    Mengonfigurasi logging global khusus untuk CLI (analisis_pipeline.py).
    Menulis ke log/cli.log — RotatingFileHandler (5MB, 3 backup).
    Sistem identik dengan setup_logger(), namun file target terpisah dari Gradio/API.
    Harus dipanggil sekali di awal skrip CLI.
    """
    root_logger = logging.getLogger()

    # Cegah penambahan handler duplikat jika fungsi dipanggil lebih dari sekali
    if root_logger.hasHandlers():
        return

    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "log")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "cli.log")  # Eksklusif untuk CLI

    log_format = logging.Formatter(
        fmt="%(asctime)s | [%(levelname)s] | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Console Handler (tampilkan di terminal CLI)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)

    # 2. File Handler (Rotating, maks 5MB, 3 backup terbaru)
    file_handler = RotatingFileHandler(
        filename=log_file,
        mode='a',
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,             # Simpan cli.log.1, cli.log.2, cli.log.3
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.INFO)

    # Setup Root Logger
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
