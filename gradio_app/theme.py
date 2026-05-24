# gradio_app/theme.py — Lumina Glass Design System v3 (Revised)

HEAD_HTML = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
<style>
/* Pre-declare Material Symbols so icons load before Gradio mounts */
.material-symbols-outlined {
    font-family: 'Material Symbols Outlined' !important;
    font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24 !important;
    font-style: normal !important;
    font-weight: normal !important;
    line-height: 1 !important;
    display: inline-block !important;
    text-transform: none !important;
    letter-spacing: normal !important;
    white-space: nowrap !important;
    direction: ltr !important;
    font-size: 18px !important;
    vertical-align: -3px !important;
    margin-right: 5px !important;
}
</style>
"""

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ==========================================================
   1. ROOT BACKGROUND — Put gradient on html so nothing covers it
   ========================================================== */
html {
    background:
        radial-gradient(ellipse at 70% 0%, rgba(29, 78, 216, 0.32) 0%, transparent 55%),
        radial-gradient(ellipse at 15% 100%, rgba(67, 56, 202, 0.22) 0%, transparent 50%),
        #07101f !important;
    min-height: 100% !important;
    background-attachment: fixed !important;
}

/* Body and every Gradio wrapper must be transparent */
body,
.gradio-container,
.gradio-container > *,
.main,
.contain,
.app,
.wrap {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* ==========================================================
   2. GRADIO CSS VARIABLE OVERRIDE
   ========================================================== */
.gradio-container {
    max-width: 100% !important;
    min-height: 100vh !important;
    padding: 0 !important;
    font-family: 'Inter', sans-serif !important;

    --background-fill-primary:          transparent !important;
    --background-fill-secondary:        transparent !important;
    --block-background-fill:            transparent !important;
    --panel-background-fill:            transparent !important;
    --block-border-width:               0px !important;
    --block-border-color:               transparent !important;
    --block-shadow:                     none !important;
    --block-label-background-fill:      transparent !important;
    --block-label-border-color:         transparent !important;
    --block-label-border-width:         0px !important;
    --block-label-text-color:           #4b5563 !important;
    --block-label-text-size:            0.72rem !important;
    --block-title-text-color:           #dae2fc !important;
    --block-title-background-fill:      transparent !important;
    --border-color-primary:             rgba(255,255,255,0.07) !important;
    --border-color-accent:              #3b82f6 !important;
    --input-background-fill:            rgba(5, 12, 28, 0.65) !important;
    --input-background-fill-focus:      rgba(5, 12, 28, 0.8) !important;
    --input-border-color:               rgba(255,255,255,0.08) !important;
    --input-border-color-focus:         rgba(59,130,246,0.45) !important;
    --input-border-width:               1px !important;
    --input-placeholder-color:          #374151 !important;
    --body-text-color:                  #dae2fc !important;
    --body-text-color-subdued:          #475569 !important;
    --checkbox-background-color:        rgba(5,12,28,0.65) !important;
    --checkbox-border-color:            rgba(255,255,255,0.1) !important;
    --radio-circle-color:               #3b82f6 !important;
    --color-accent:                     #3b82f6 !important;
    --color-accent-soft:                rgba(59,130,246,0.15) !important;
    --shadow-drop:                      none !important;
    --shadow-drop-lg:                   none !important;
    --shadow-inset:                     none !important;
    --stat-background-fill:             transparent !important;
    --button-primary-background-fill:           linear-gradient(135deg, #1d4ed8, #2563eb) !important;
    --button-primary-background-fill-hover:     linear-gradient(135deg, #2563eb, #3b82f6) !important;
    --button-primary-text-color:                white !important;
    --button-primary-border-color:              rgba(96,165,250,0.25) !important;
    --button-secondary-background-fill:         rgba(255,255,255,0.04) !important;
    --button-secondary-background-fill-hover:   rgba(255,255,255,0.08) !important;
    --button-secondary-text-color:              #94a3b8 !important;
    --button-secondary-border-color:            rgba(255,255,255,0.1) !important;
}

/* ==========================================================
   3. NUKE ALL GRADIO INTERNAL BACKGROUNDS
   ========================================================== */
.block, .form, fieldset, .gap-4, .gap-2,
.gr-group, .gr-box, .gr-panel, .gr-form,
div[data-testid="block"],
.gradio-container .col,
.gradio-container .row,
.gradio-container .column {
    background: transparent !important;
    border-color: transparent !important;
    box-shadow: none !important;
}

/* ==========================================================
   4. GLASS CARD
   ========================================================== */
.glass-card {
    background: rgba(11, 20, 40, 0.65) !important;
    backdrop-filter: blur(20px) saturate(1.5) !important;
    -webkit-backdrop-filter: blur(20px) saturate(1.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-top-color: rgba(255, 255, 255, 0.15) !important;
    border-radius: 1.125rem !important;
    box-shadow:
        0 4px 24px rgba(0, 0, 0, 0.5),
        inset 0 1px 0 rgba(255,255,255,0.06) !important;
    padding: 1.5rem !important;
    margin-bottom: 0 !important;
    position: relative !important;
    overflow: hidden !important;

    /* Scope vars so child Gradio components inherit transparency */
    --background-fill-primary:          transparent !important;
    --background-fill-secondary:        transparent !important;
    --block-background-fill:            transparent !important;
    --panel-background-fill:            transparent !important;
    --block-border-width:               0px !important;
    --block-border-color:               transparent !important;
    --block-shadow:                     none !important;
    --block-label-background-fill:      transparent !important;
    --block-label-border-color:         transparent !important;
    --border-color-primary:             rgba(255,255,255,0.08) !important;
}

/* Top shimmer line */
.glass-card::before {
    content: '';
    position: absolute;
    top: 0; left: 20%; right: 20%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(147,197,253,0.35), transparent);
    pointer-events: none;
}

/* Kill inner wrapper backgrounds */
.glass-card > div,
.glass-card .block,
.glass-card .wrap,
.glass-card fieldset,
.glass-card .form,
.glass-card .gap-4,
.glass-card .gap-2,
.glass-card div[data-testid] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

/* ==========================================================
   5. CARD SECTION HEADER (replaces gr.Markdown headings)
   ========================================================== */
.card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 1.125rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.card-header .icon {
    font-size: 17px;
    opacity: 0.85;
}
.card-header .label {
    font-size: 0.82rem;
    font-weight: 600;
    color: #dae2fc;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
.card-header .label.mono {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    letter-spacing: 0.06em;
    color: #7dd3fc;
}

/* ==========================================================
   6. PAGE HEADER (title + subtitle) — FULL WIDTH above sidebar
   ========================================================== */
.page-header {
    text-align: center;
    padding: 1.25rem 0 1.5rem 0;
    width: 100%;
}
.page-header h1 {
    font-size: 1.75rem;
    font-weight: 700;
    color: #dae2fc;
    letter-spacing: -0.025em;
    margin: 0 0 0.65rem 0;
    line-height: 1.2;
    text-align: center !important;
}
.page-header .subtitle {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: rgba(15, 25, 50, 0.7);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 9999px;
    padding: 0.3rem 1rem;
    font-size: 0.78rem;
    color: #64748b;
}
.page-header .subtitle strong {
    color: #93c5fd;
    font-weight: 600;
}

/* Toggle label (above radio) */
.toggle-label {
    font-size: 0.68rem;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    margin-bottom: 0.4rem;
    font-weight: 600;
}

/* Sidebar fixed min-height */
.sidebar-col {
    min-height: 70vh;
}

/* ==========================================================
   7. SIDEBAR
   ========================================================== */
.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 9px;
    margin-bottom: 1.75rem;
}
.sidebar-logo .logo-icon {
    color: #3b82f6;
    font-size: 20px;
}
.sidebar-logo .logo-text {
    font-size: 1.05rem;
    font-weight: 700;
    color: #dae2fc;
    letter-spacing: -0.02em;
}
.sidebar-section-label {
    font-size: 0.6rem;
    font-weight: 700;
    color: #1e3a5f;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    margin-bottom: 0.5rem;
    padding-left: 2px;
}

/* ==========================================================
   8. NAV BUTTONS
   ========================================================== */
.nav-btn {
    background: transparent !important;
    border: none !important;
    border-left: 2px solid transparent !important;
    border-radius: 0 0.5rem 0.5rem 0 !important;
    box-shadow: none !important;
    text-align: left !important;
    padding: 0.55rem 0.875rem 0.55rem 0.75rem !important;
    color: #334155 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    width: 100% !important;
    justify-content: flex-start !important;
    transition: all 0.15s ease !important;
    margin-bottom: 2px !important;
    min-height: unset !important;
    height: auto !important;
}
.nav-btn:hover {
    color: #94a3b8 !important;
    background: rgba(255,255,255,0.04) !important;
    border-left-color: rgba(59,130,246,0.3) !important;
}
.nav-active {
    color: #dae2fc !important;
    background: rgba(37, 99, 235, 0.14) !important;
    border-left: 2px solid #3b82f6 !important;
    font-weight: 600 !important;
}
.nav-active:hover {
    background: rgba(37, 99, 235, 0.18) !important;
}

/* ==========================================================
   9. BUTTONS — Consistent sizing across ALL views
   ========================================================== */
button.primary,
.gr-button-primary {
    background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%) !important;
    border: 1px solid rgba(96,165,250,0.25) !important;
    border-radius: 0.6rem !important;
    color: #fff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.02em !important;
    padding: 0.55rem 1.25rem !important;
    box-shadow: 0 3px 12px rgba(37,99,235,0.35), inset 0 1px 0 rgba(255,255,255,0.15) !important;
    transition: all 0.18s ease !important;
    min-height: 38px !important;
    height: 38px !important;
}
button.primary:hover {
    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%) !important;
    box-shadow: 0 5px 18px rgba(37,99,235,0.5) !important;
    transform: translateY(-1px) !important;
}
button.primary:active { transform: translateY(0) !important; }

button.secondary,
.gr-button-secondary {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 0.6rem !important;
    color: #64748b !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 0.55rem 1.25rem !important;
    transition: all 0.18s ease !important;
    min-height: 38px !important;
    height: 38px !important;
}
button.secondary:hover {
    background: rgba(255,255,255,0.07) !important;
    color: #94a3b8 !important;
    border-color: rgba(255,255,255,0.15) !important;
}

/* ==========================================================
   10. RADIO TOGGLE
   ========================================================== */
.toggle-radio { background: transparent !important; border: none !important; }
.toggle-radio > div,
.toggle-radio .wrap {
    display: flex !important;
    flex-direction: row !important;
    background: rgba(5,12,28,0.7) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 0.5rem !important;
    padding: 3px !important;
    gap: 2px !important;
    width: 100% !important;
}
.toggle-radio label {
    flex: 1 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0.4rem 0.75rem !important;
    border-radius: 0.35rem !important;
    cursor: pointer !important;
    background: transparent !important;
    border: none !important;
    color: #374151 !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.15s ease !important;
    margin: 0 !important;
    user-select: none !important;
    min-height: unset !important;
}
.toggle-radio label:has(input[type="radio"]:checked) {
    background: rgba(29, 78, 216, 0.32) !important;
    color: #93c5fd !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.07) !important;
}
.toggle-radio input[type="radio"] {
    position: absolute !important; opacity: 0 !important; width: 0 !important; height: 0 !important;
}

/* ==========================================================
   11. TERMINAL LOG
   ========================================================== */
.terminal-output textarea,
.terminal-output > label > textarea {
    background: rgba(2, 6, 18, 0.8) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.75rem !important;
    line-height: 1.8 !important;
    color: #38bdf8 !important;
    border-radius: 0.625rem !important;
    border: 1px solid rgba(56, 189, 248, 0.07) !important;
    padding: 0.875rem !important;
    resize: none !important;
}
.terminal-output label,
.terminal-output .label-wrap,
.terminal-output > label > span {
    display: none !important;
}

/* ==========================================================
   12. AUDIO COMPONENT — Full visibility for record mode
   ========================================================== */
[data-testid="audio"],
[data-testid="file"],
.gr-audio,
.gr-file {
    background: transparent !important;
    border: none !important;
}

/* Drop / upload zone */
.upload-container,
.empty.svelte-p3y7hu,
.boundedheight {
    background: rgba(5,12,28,0.55) !important;
    border: 1.5px dashed rgba(255,255,255,0.12) !important;
    border-radius: 0.875rem !important;
    min-height: 90px !important;
    transition: border-color 0.2s ease, background 0.2s ease !important;
}
.upload-container:hover {
    border-color: rgba(59,130,246,0.4) !important;
    background: rgba(29,78,216,0.06) !important;
}

/* Audio component internal wrapper */
.waveform-container,
.audio-container {
    background: rgba(5,12,28,0.5) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 0.75rem !important;
}

/* All buttons INSIDE audio component (record, play, stop, delete) */
[data-testid="audio"] button,
.gr-audio button {
    background: rgba(15, 28, 55, 0.8) !important;
    border: 1px solid rgba(59,130,246,0.25) !important;
    color: #93c5fd !important;
    border-radius: 0.5rem !important;
    transition: all 0.15s ease !important;
}
[data-testid="audio"] button:hover,
.gr-audio button:hover {
    background: rgba(29,78,216,0.25) !important;
    border-color: rgba(59,130,246,0.45) !important;
    color: #bfdbfe !important;
}

/* Record-specific (blue dot button) */
.record-button,
button[aria-label="record"],
button[title="record"] {
    background: rgba(239,68,68,0.12) !important;
    border-color: rgba(239,68,68,0.3) !important;
    color: #fca5a5 !important;
}

/* Microphone selector / device dropdown */
[data-testid="audio"] select,
.gr-audio select {
    background: rgba(5,12,28,0.7) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #64748b !important;
    border-radius: 0.4rem !important;
    font-size: 0.75rem !important;
    padding: 0.25rem 0.5rem !important;
}

/* Time display in waveform */
[data-testid="audio"] .time,
.gr-audio .time {
    color: #334155 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem !important;
}

/* Audio label pill (e.g. "Audio Response", "Drop Audio Here") */
.block .label-wrap {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 0.35rem !important;
    padding: 0.18rem 0.55rem !important;
    margin-bottom: 0.4rem !important;
}
.block .label-wrap span {
    color: #334155 !important;
    font-size: 0.72rem !important;
    font-family: 'Inter', sans-serif !important;
}

/* ==========================================================
   13. FILE DOWNLOAD COMPONENT
   ========================================================== */
.file-preview-holder {
    background: rgba(5,12,28,0.55) !important;
    border: 1px solid rgba(59,130,246,0.15) !important;
    border-radius: 0.625rem !important;
    padding: 0.625rem 0.875rem !important;
    color: #93c5fd !important;
    font-size: 0.78rem !important;
}

/* ==========================================================
   14. PATH BADGE (batch source directory)
   ========================================================== */
.path-badge {
    display: inline-block;
    background: rgba(5,12,28,0.75);
    border: 1px solid rgba(59,130,246,0.18);
    border-radius: 0.4rem;
    padding: 0.3rem 0.65rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #60a5fa;
    letter-spacing: 0.03em;
}

/* ==========================================================
   15. LANGUAGE BADGES
   ========================================================== */
.lang-badge {
    display: inline-block !important; padding: 0.15rem 0.45rem !important;
    border-radius: 0.3rem !important; font-size: 0.65rem !important;
    font-family: 'JetBrains Mono', monospace !important; font-weight: 600 !important;
    letter-spacing: 0.05em !important; text-transform: uppercase !important;
}
.lang-id { background:rgba(59,130,246,0.18)!important; color:#93c5fd!important; border:1px solid rgba(59,130,246,0.28)!important; }
.lang-en { background:rgba(16,185,129,0.18)!important; color:#6ee7b7!important; border:1px solid rgba(16,185,129,0.28)!important; }
.lang-ar { background:rgba(245,158,11,0.18)!important; color:#fcd34d!important; border:1px solid rgba(245,158,11,0.28)!important; }

/* ==========================================================
   16. GRADIO DEFAULT FOOTER BAR
   ========================================================== */
footer, footer.svelte-1rjryqp {
    background: transparent !important;
    border-top: 1px solid rgba(255,255,255,0.04) !important;
}
footer a, footer svg { opacity: 0.3 !important; }

/* ==========================================================
   17. SCROLLBARS
   ========================================================== */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(59,130,246,0.18); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: rgba(59,130,246,0.35); }

/* ==========================================================
   18. SPACING NORMALISATION
   ========================================================== */
/* Gradio Rows/Columns add margins we need to control */
.gradio-container .block.padded { padding: 0 !important; }
.gradio-container { overflow-x: hidden !important; }

/* Gap between sidebar and content */
.main-row { gap: 1rem !important; }

/* ==========================================================
   19. MARKDOWN LOG OUTPUT STYLES
   ========================================================== */
.glass-card .prose,
.glass-card .markdown-body,
.glass-card .md {
    color: #dae2fc !important;
    font-size: 0.82rem !important;
    line-height: 1.65 !important;
}
.glass-card .prose h1,
.glass-card .prose h2,
.glass-card .prose h3 {
    color: #dae2fc !important;
    border: none !important;
}
.glass-card .prose strong {
    color: #93c5fd !important;
}
.glass-card .prose blockquote {
    border-left: 3px solid rgba(59,130,246,0.3) !important;
    background: rgba(5,12,28,0.5) !important;
    padding: 0.5rem 0.875rem !important;
    border-radius: 0 0.5rem 0.5rem 0 !important;
    color: #94a3b8 !important;
    margin: 0.5rem 0 !important;
    font-style: normal !important;
}
.glass-card .prose blockquote p {
    color: #94a3b8 !important;
}
.glass-card .prose hr {
    border-color: rgba(255,255,255,0.06) !important;
    margin: 0.75rem 0 !important;
}
.glass-card .prose table {
    width: 100% !important;
    border-collapse: collapse !important;
    font-size: 0.78rem !important;
    margin: 0.5rem 0 !important;
}
.glass-card .prose th {
    background: rgba(59,130,246,0.1) !important;
    color: #93c5fd !important;
    font-weight: 600 !important;
    text-align: left !important;
    padding: 0.4rem 0.75rem !important;
    border-bottom: 1px solid rgba(255,255,255,0.1) !important;
}
.glass-card .prose td {
    padding: 0.35rem 0.75rem !important;
    border-bottom: 1px solid rgba(255,255,255,0.04) !important;
    color: #c3c6d7 !important;
}
.glass-card .prose code {
    background: rgba(5,12,28,0.6) !important;
    color: #60a5fa !important;
    padding: 0.1rem 0.35rem !important;
    border-radius: 0.25rem !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.75rem !important;
}
.glass-card .prose ul, .glass-card .prose ol {
    padding-left: 1.25rem !important;
    color: #c3c6d7 !important;
}
.glass-card .prose li {
    margin-bottom: 0.2rem !important;
}
"""