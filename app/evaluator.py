"""
app/evaluator.py — Evaluasi Pipeline: Tabel & Grafik
Mengolah list hasil pipeline menjadi:
  - pandas DataFrame untuk gr.Dataframe (tabel per file)
  - matplotlib Figure untuk gr.Plot (grafik rata-rata per utterance)

Hanya digunakan oleh mode Batch NLP.
"""

import re
import logging
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

matplotlib.use("Agg")  # Non-interactive backend (thread-safe untuk Gradio)

logger = logging.getLogger(__name__)

# ─── Konstanta Kolom ──────────────────────────────────────────────────────────

TABLE_COLUMNS = [
    "filename",
    "folder",
    "utterance_id",
    "status",
    "dominant_language",
    "wer (%)",
    "cer (%)",
    "latency_stt (s)",
    "latency_llm (s)",
    "latency_tts (s)",
    "latency_total (s)",
    "error",
]


# ─── Helper ───────────────────────────────────────────────────────────────────

def _extract_utterance_id(filename: str) -> str:
    """Ekstrak utterance ID (01–20) dari nama file format {id}_{uttid}.wav."""
    match = re.search(r"_(\d{2})\.wav$", filename.lower())
    return match.group(1) if match else "??"


def _to_pct(val) -> str:
    """Konversi float WER/CER (0.0–1.0) ke string persentase."""
    if isinstance(val, (int, float)):
        return f"{val * 100:.2f}"
    return str(val)  # "N/A" atau lainnya


# ─── Builder Tabel ────────────────────────────────────────────────────────────

def build_eval_dataframe(results: list) -> pd.DataFrame:
    """
    Konversi list result dict dari pipeline.run_pipeline() ke pandas DataFrame
    yang siap ditampilkan di gr.Dataframe.

    Args:
        results: list of dict (output run_pipeline)

    Returns:
        pd.DataFrame dengan kolom TABLE_COLUMNS
    """
    rows = []
    for r in results:
        fname = r.get("filename", "")
        rows.append({
            "filename":          fname,
            "folder":            r.get("folder", "-"),
            "utterance_id":      _extract_utterance_id(fname),
            "status":            r.get("status", "error"),
            "dominant_language": r.get("dominant_language", "-"),
            "wer (%)":           _to_pct(r.get("wer", "N/A")),
            "cer (%)":           _to_pct(r.get("cer", "N/A")),
            "latency_stt (s)":   r.get("latency_stt", "-"),
            "latency_llm (s)":   r.get("latency_llm", "-"),
            "latency_tts (s)":   r.get("latency_tts", "-"),
            "latency_total (s)": r.get("latency_total", "-"),
            "error":             r.get("error", ""),
        })

    if not rows:
        return pd.DataFrame(columns=TABLE_COLUMNS)

    return pd.DataFrame(rows, columns=TABLE_COLUMNS)


# ─── Builder Grafik ───────────────────────────────────────────────────────────

_DARK_BG    = "#0d1117"
_CARD_BG    = "#161b22"
_GRID_COLOR = "#30363d"
_TEXT_COLOR = "#c9d1d9"

_COLORS_BAR  = ["#3b82f6", "#f59e0b", "#10b981"]   # WER, CER, Latency
_COLOR_STT   = "#60a5fa"
_COLOR_LLM   = "#a78bfa"
_COLOR_TTS   = "#34d399"


def build_avg_charts(results: list) -> plt.Figure:
    """
    Buat 2 subplot grafik rata-rata dari hasil batch:
      1. Bar chart rata-rata WER & CER per utterance_id
      2. Bar chart rata-rata latency (STT / LLM / TTS) per utterance_id

    Args:
        results: list of dict (output run_pipeline)

    Returns:
        matplotlib Figure
    """
    success = [r for r in results if r.get("status") == "success"]
    if not success:
        fig, ax = plt.subplots(facecolor=_DARK_BG)
        ax.set_facecolor(_CARD_BG)
        ax.text(0.5, 0.5, "Tidak ada data berhasil untuk ditampilkan",
                ha="center", va="center", color=_TEXT_COLOR, fontsize=12)
        ax.axis("off")
        return fig

    # Kelompokkan per utterance_id
    uid_map: dict[str, list] = {}
    for r in success:
        uid = _extract_utterance_id(r.get("filename", ""))
        uid_map.setdefault(uid, []).append(r)

    uids = sorted(uid_map.keys())

    # Hitung rata-rata per utterance
    avg_wer  = []
    avg_cer  = []
    avg_stt  = []
    avg_llm  = []
    avg_tts  = []

    for uid in uids:
        group = uid_map[uid]
        wer_vals = [r["wer"] for r in group if isinstance(r.get("wer"), (int, float))]
        cer_vals = [r["cer"] for r in group if isinstance(r.get("cer"), (int, float))]
        stt_vals = [r["latency_stt"] for r in group if isinstance(r.get("latency_stt"), (int, float))]
        llm_vals = [r["latency_llm"] for r in group if isinstance(r.get("latency_llm"), (int, float))]
        tts_vals = [r["latency_tts"] for r in group if isinstance(r.get("latency_tts"), (int, float))]

        avg_wer.append((sum(wer_vals) / len(wer_vals) * 100) if wer_vals else 0.0)
        avg_cer.append((sum(cer_vals) / len(cer_vals) * 100) if cer_vals else 0.0)
        avg_stt.append((sum(stt_vals) / len(stt_vals)) if stt_vals else 0.0)
        avg_llm.append((sum(llm_vals) / len(llm_vals)) if llm_vals else 0.0)
        avg_tts.append((sum(tts_vals) / len(tts_vals)) if tts_vals else 0.0)

    x       = range(len(uids))
    width   = 0.35
    x_off   = [i - width / 2 for i in x]
    x_off2  = [i + width / 2 for i in x]

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(max(10, len(uids) * 0.9), 9),
        facecolor=_DARK_BG,
    )
    fig.subplots_adjust(hspace=0.45)

    # ── Subplot 1: WER & CER ─────────────────────────────────────────────────
    ax1.set_facecolor(_CARD_BG)
    bars1 = ax1.bar(x_off,  avg_wer, width, label="WER (%)", color=_COLORS_BAR[0], alpha=0.9, zorder=3)
    bars2 = ax1.bar(x_off2, avg_cer, width, label="CER (%)", color=_COLORS_BAR[1], alpha=0.9, zorder=3)

    ax1.set_title("Rata-rata WER & CER per Utterance ID", color=_TEXT_COLOR, fontsize=13, pad=12)
    ax1.set_ylabel("Error Rate (%)", color=_TEXT_COLOR, fontsize=10)
    ax1.set_xticks(list(x))
    ax1.set_xticklabels([f"#{u}" for u in uids], color=_TEXT_COLOR, fontsize=9)
    ax1.tick_params(axis="y", colors=_TEXT_COLOR)
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
    ax1.set_ylim(bottom=0)
    ax1.spines[:].set_color(_GRID_COLOR)
    ax1.grid(axis="y", color=_GRID_COLOR, linestyle="--", linewidth=0.5, zorder=0)
    ax1.legend(facecolor=_CARD_BG, edgecolor=_GRID_COLOR, labelcolor=_TEXT_COLOR, fontsize=9)

    # Label nilai di atas bar
    for bar in bars1:
        h = bar.get_height()
        if h > 0:
            ax1.text(bar.get_x() + bar.get_width() / 2, h + 0.3,
                     f"{h:.1f}%", ha="center", va="bottom", color=_COLORS_BAR[0], fontsize=7)
    for bar in bars2:
        h = bar.get_height()
        if h > 0:
            ax1.text(bar.get_x() + bar.get_width() / 2, h + 0.3,
                     f"{h:.1f}%", ha="center", va="bottom", color=_COLORS_BAR[1], fontsize=7)

    # ── Subplot 2: Latency STT / LLM / TTS ───────────────────────────────────
    ax2.set_facecolor(_CARD_BG)
    w3 = 0.25
    x_stt = [i - w3 for i in x]
    x_llm = list(x)
    x_tts = [i + w3 for i in x]

    bars_stt = ax2.bar(x_stt, avg_stt, w3, label="STT (s)", color=_COLOR_STT, alpha=0.9, zorder=3)
    bars_llm = ax2.bar(x_llm, avg_llm, w3, label="LLM (s)", color=_COLOR_LLM, alpha=0.9, zorder=3)
    bars_tts = ax2.bar(x_tts, avg_tts, w3, label="TTS (s)", color=_COLOR_TTS, alpha=0.9, zorder=3)

    ax2.set_title("Rata-rata Latency per Utterance ID", color=_TEXT_COLOR, fontsize=13, pad=12)
    ax2.set_ylabel("Latency (detik)", color=_TEXT_COLOR, fontsize=10)
    ax2.set_xticks(list(x))
    ax2.set_xticklabels([f"#{u}" for u in uids], color=_TEXT_COLOR, fontsize=9)
    ax2.tick_params(axis="y", colors=_TEXT_COLOR)
    ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1fs"))
    ax2.set_ylim(bottom=0)
    ax2.spines[:].set_color(_GRID_COLOR)
    ax2.grid(axis="y", color=_GRID_COLOR, linestyle="--", linewidth=0.5, zorder=0)
    ax2.legend(facecolor=_CARD_BG, edgecolor=_GRID_COLOR, labelcolor=_TEXT_COLOR, fontsize=9)

    for bars, color in [(bars_stt, _COLOR_STT), (bars_llm, _COLOR_LLM), (bars_tts, _COLOR_TTS)]:
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax2.text(bar.get_x() + bar.get_width() / 2, h + 0.05,
                         f"{h:.1f}", ha="center", va="bottom", color=color, fontsize=7)

    fig.patch.set_facecolor(_DARK_BG)
    return fig
