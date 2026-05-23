# gradio_app/theme.py — Lumina Glass Design System v2
# Full Nuclear Reset + Glassmorphism Dark Theme

HEAD_HTML = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=block" />
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    darkMode: 'class',
    theme: {
      extend: {
        colors: {
          primary: '#3b82f6',
          surface: '#0a1020',
          glass: 'rgba(13,22,45,0.6)',
        }
      }
    }
  }
</script>
<style>
  /* Pre-load Material Symbols before Gradio mounts */
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
    font-size: 22px !important;
    vertical-align: middle !important;
    margin-right: 4px !important;
  }
</style>
"""

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* =========================================================
   1. ROOT & BODY — Deep Navy Radial Background
   ========================================================= */
html {
    background: #060e20 !important;
    scroll-behavior: smooth !important;
}

body {
    background:
        radial-gradient(ellipse at 80% -10%, rgba(37,99,235,0.18) 0%, transparent 50%),
        radial-gradient(ellipse at 10% 90%, rgba(99,102,241,0.1) 0%, transparent 50%),
        linear-gradient(160deg, #0a1428 0%, #060e20 60%) !important;
    background-attachment: fixed !important;
    min-height: 100vh !important;
    font-family: 'Inter', sans-serif !important;
    color: #dae2fc !important;
}

/* =========================================================
   2. GRADIO CONTAINER — CSS Variable Nuclear Override
   ========================================================= */
.gradio-container {
    max-width: 100% !important;
    min-height: 100vh !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
    font-family: 'Inter', sans-serif !important;

    /* ── Gradio v4 CSS Variable Overrides ── */
    --background-fill-primary:      transparent !important;
    --background-fill-secondary:    transparent !important;
    --block-background-fill:        transparent !important;
    --panel-background-fill:        transparent !important;
    --block-border-width:           0px !important;
    --block-border-color:           transparent !important;
    --block-shadow:                 none !important;
    --block-label-background-fill:  transparent !important;
    --block-label-border-color:     transparent !important;
    --block-label-border-width:     0px !important;
    --block-label-text-color:       #64748b !important;
    --block-label-text-size:        0.75rem !important;
    --block-title-text-color:       #dae2fc !important;
    --block-title-background-fill:  transparent !important;
    --border-color-primary:         rgba(255,255,255,0.08) !important;
    --border-color-accent:          #3b82f6 !important;
    --input-background-fill:        rgba(6,14,32,0.7) !important;
    --input-background-fill-focus:  rgba(10,20,40,0.8) !important;
    --input-border-color:           rgba(255,255,255,0.1) !important;
    --input-border-color-focus:     rgba(59,130,246,0.5) !important;
    --input-border-width:           1px !important;
    --input-placeholder-color:      #475569 !important;
    --body-text-color:              #dae2fc !important;
    --body-text-color-subdued:      #64748b !important;
    --checkbox-background-color:    rgba(6,14,32,0.7) !important;
    --checkbox-border-color:        rgba(255,255,255,0.12) !important;
    --radio-circle-color:           #3b82f6 !important;
    --color-accent:                 #3b82f6 !important;
    --color-accent-soft:            rgba(59,130,246,0.15) !important;
    --shadow-drop:                  none !important;
    --shadow-drop-lg:               none !important;
    --shadow-inset:                 none !important;
    --stat-background-fill:         transparent !important;
    --table-even-background-fill:   rgba(13,22,45,0.4) !important;
    --table-odd-background-fill:    rgba(6,14,32,0.4) !important;
    --button-primary-background-fill:       linear-gradient(135deg, #1d4ed8, #2563eb) !important;
    --button-primary-background-fill-hover: linear-gradient(135deg, #2563eb, #3b82f6) !important;
    --button-primary-text-color:            white !important;
    --button-primary-border-color:          rgba(96,165,250,0.3) !important;
    --button-secondary-background-fill:       rgba(255,255,255,0.04) !important;
    --button-secondary-background-fill-hover: rgba(255,255,255,0.08) !important;
    --button-secondary-text-color:            #94a3b8 !important;
    --button-secondary-border-color:          rgba(255,255,255,0.1) !important;
    --button-small-padding:     0.4rem 0.875rem !important;
    --button-large-padding:     0.7rem 1.5rem !important;
    --button-large-text-size:   0.9rem !important;
    --button-medium-text-size:  0.875rem !important;
    --section-header-text-size: 0.8rem !important;
}

/* =========================================================
   3. GLOBAL TRANSPARENT WIPE — Kill all Gradio backgrounds
   ========================================================= */
.gradio-container .main,
.gradio-container > div,
.contain,
.app,
.form,
.block,
.wrap,
.gap-4,
.gap-2,
.gr-group,
.gr-box,
.gr-panel,
.gr-padded,
.gr-form,
.panel,
div[data-testid="block"] {
    background: transparent !important;
    border-color: transparent !important;
    box-shadow: none !important;
}

/* Keep padding but strip background on inner column wrappers */
.gradio-container .col,
.gradio-container .row,
.gradio-container .column {
    background: transparent !important;
}

/* =========================================================
   4. GLASS CARD — The core design component
   ========================================================= */
.glass-card {
    background: rgba(13, 22, 45, 0.60) !important;
    backdrop-filter: blur(18px) saturate(1.4) !important;
    -webkit-backdrop-filter: blur(18px) saturate(1.4) !important;
    border: 1px solid rgba(255, 255, 255, 0.09) !important;
    border-top-color: rgba(255, 255, 255, 0.17) !important;
    border-radius: 1.25rem !important;
    box-shadow:
        0 4px 32px rgba(0, 0, 0, 0.45),
        inset 0 1px 0 rgba(255, 255, 255, 0.07) !important;
    padding: 1.75rem !important;
    margin-bottom: 1rem !important;
    position: relative !important;
    overflow: hidden !important;

    /* Scope CSS vars inside card so Gradio children pick them up */
    --background-fill-primary:   transparent !important;
    --background-fill-secondary: transparent !important;
    --block-background-fill:     transparent !important;
    --block-border-width:        0px !important;
    --block-border-color:        transparent !important;
    --block-shadow:              none !important;
    --panel-background-fill:     transparent !important;
    --border-color-primary:      rgba(255,255,255,0.08) !important;
    --block-label-background-fill: transparent !important;
}

/* Prismatic top-edge shimmer */
.glass-card::before {
    content: '';
    position: absolute;
    top: 0; left: 15%; right: 15%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(173,198,255,0.4), transparent);
    pointer-events: none;
}

/* Wipe ALL inner Gradio wrapper backgrounds inside glass-card */
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

/* =========================================================
   5. BUTTONS
   ========================================================= */
/* Primary */
button.primary,
.gr-button-primary,
.btn-primary {
    background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%) !important;
    border: 1px solid rgba(96, 165, 250, 0.35) !important;
    border-radius: 0.75rem !important;
    color: #fff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    letter-spacing: 0.02em !important;
    box-shadow:
        0 4px 14px rgba(37,99,235,0.4),
        inset 0 1px 0 rgba(255,255,255,0.18) !important;
    transition: all 0.2s ease !important;
    padding: 0.65rem 1.5rem !important;
}
button.primary:hover,
.gr-button-primary:hover {
    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%) !important;
    box-shadow: 0 6px 22px rgba(37,99,235,0.55) !important;
    transform: translateY(-1px) !important;
}
button.primary:active {
    transform: translateY(0) !important;
}

/* Secondary */
button.secondary,
.gr-button-secondary {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 0.75rem !important;
    color: #94a3b8 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.875rem !important;
    transition: all 0.2s ease !important;
    padding: 0.65rem 1.25rem !important;
}
button.secondary:hover,
.gr-button-secondary:hover {
    background: rgba(255,255,255,0.08) !important;
    color: #e2e8f0 !important;
    border-color: rgba(255,255,255,0.16) !important;
}

/* =========================================================
   6. NAVIGATION BUTTONS
   ========================================================= */
.nav-btn {
    background: transparent !important;
    border: none !important;
    border-left: 3px solid transparent !important;
    border-radius: 0 0.625rem 0.625rem 0 !important;
    box-shadow: none !important;
    text-align: left !important;
    padding: 0.6rem 1rem 0.6rem 0.875rem !important;
    color: #475569 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    width: 100% !important;
    justify-content: flex-start !important;
    transition: all 0.18s ease !important;
    letter-spacing: 0.01em !important;
}
.nav-btn:hover {
    color: #cbd5e1 !important;
    background: rgba(255,255,255,0.05) !important;
    border-left-color: rgba(59,130,246,0.35) !important;
}

/* Active state */
.nav-active {
    color: #e2e8f0 !important;
    background: rgba(59,130,246,0.12) !important;
    border-left: 3px solid #3b82f6 !important;
    font-weight: 600 !important;
}

/* =========================================================
   7. RADIO TOGGLE (Preserve / Normalize)
   ========================================================= */
.toggle-radio {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}
.toggle-radio > div,
.toggle-radio .wrap {
    display: flex !important;
    flex-direction: row !important;
    gap: 2px !important;
    background: rgba(6, 14, 32, 0.65) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 0.625rem !important;
    padding: 3px !important;
    width: 100% !important;
}
.toggle-radio label {
    flex: 1 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0.45rem 0.875rem !important;
    border-radius: 0.4rem !important;
    cursor: pointer !important;
    background: transparent !important;
    border: none !important;
    color: #475569 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.18s ease !important;
    margin: 0 !important;
    user-select: none !important;
}
.toggle-radio label:has(input[type="radio"]:checked) {
    background: rgba(37, 99, 235, 0.28) !important;
    color: #93c5fd !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.08) !important;
}
.toggle-radio label span { pointer-events: none !important; }
.toggle-radio input[type="radio"] {
    position: absolute !important;
    opacity: 0 !important;
    width: 0 !important;
    height: 0 !important;
}

/* =========================================================
   8. TERMINAL / LOG OUTPUT
   ========================================================= */
.terminal-output,
.terminal-output textarea,
.terminal-output > label > textarea {
    background: rgba(2, 6, 18, 0.75) !important;
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    font-size: 0.8rem !important;
    line-height: 1.75 !important;
    color: #7dd3fc !important;
    border-radius: 0.75rem !important;
    border: 1px solid rgba(125,211,252,0.08) !important;
    padding: 1rem !important;
    resize: none !important;
}
.terminal-output label,
.terminal-output .label-wrap,
.terminal-output span.svelte-1b6s6s {
    display: none !important;
}

/* =========================================================
   9. AUDIO & FILE COMPONENTS
   ========================================================= */
[data-testid="audio"],
[data-testid="file"],
.gr-audio,
.gr-file {
    background: transparent !important;
    border: none !important;
}

/* Drop zone inside audio upload */
.audio-container,
.upload-container,
.empty {
    background: rgba(6, 14, 32, 0.5) !important;
    border: 2px dashed rgba(255,255,255,0.1) !important;
    border-radius: 1rem !important;
    min-height: 100px !important;
    transition: all 0.2s ease !important;
}
.upload-container:hover,
.empty:hover {
    border-color: rgba(59,130,246,0.4) !important;
    background: rgba(37,99,235,0.05) !important;
}

/* Waveform wrapper */
.waveform-container {
    background: rgba(6,14,32,0.5) !important;
    border-radius: 0.75rem !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
}

/* Audio component label tags (e.g. "Audio Response" pill) */
.component-wrapper .label-wrap,
.block .label-wrap {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 0.4rem !important;
    padding: 0.2rem 0.6rem !important;
    margin-bottom: 0.5rem !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 4px !important;
}
.block .label-wrap span {
    color: #64748b !important;
    font-size: 0.75rem !important;
    font-family: 'Inter', sans-serif !important;
}

/* File download component */
.file-preview-holder,
.download-link {
    background: rgba(6,14,32,0.5) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 0.75rem !important;
    padding: 0.75rem 1rem !important;
    color: #93c5fd !important;
    font-size: 0.85rem !important;
}

/* =========================================================
   10. MARKDOWN / PROSE INSIDE CARDS
   ========================================================= */
.gr-markdown, .prose, .md {
    background: transparent !important;
    border: none !important;
}
.gr-markdown h1, .gr-markdown h2, .gr-markdown h3,
.prose h1, .prose h2, .prose h3,
.md h1, .md h2, .md h3 {
    color: #dae2fc !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    margin: 0 0 0.75rem 0 !important;
    padding: 0 !important;
    border: none !important;
    line-height: 1.3 !important;
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
}
.gr-markdown h1 { font-size: 1.15rem !important; }
.gr-markdown h2 { font-size: 1rem !important; }
.gr-markdown h3 { font-size: 0.9rem !important; color: #94a3b8 !important; }
.gr-markdown p, .prose p, .md p {
    color: #94a3b8 !important;
    font-size: 0.875rem !important;
    margin: 0 0 0.5rem 0 !important;
}

/* =========================================================
   11. LANGUAGE BADGE
   ========================================================= */
.lang-badge {
    display: inline-block !important;
    padding: 0.2rem 0.55rem !important;
    border-radius: 0.35rem !important;
    font-size: 0.7rem !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}
.lang-id  { background: rgba(59,130,246,0.2) !important; color: #93c5fd !important; border: 1px solid rgba(59,130,246,0.3) !important; }
.lang-en  { background: rgba(16,185,129,0.2) !important; color: #6ee7b7 !important; border: 1px solid rgba(16,185,129,0.3) !important; }
.lang-ar  { background: rgba(245,158,11,0.2) !important; color: #fcd34d !important; border: 1px solid rgba(245,158,11,0.3) !important; }

/* =========================================================
   12. SIDEBAR FOOTER LINKS
   ========================================================= */
.sidebar-footer a {
    color: #475569 !important;
    text-decoration: none !important;
    font-size: 0.85rem !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    padding: 0.35rem 0 !important;
    transition: color 0.15s !important;
}
.sidebar-footer a:hover { color: #93c5fd !important; }

/* =========================================================
   13. PATH BADGE (Batch Source Directory)
   ========================================================= */
.path-badge {
    display: inline-block !important;
    background: rgba(13,22,45,0.8) !important;
    border: 1px solid rgba(59,130,246,0.2) !important;
    border-radius: 0.5rem !important;
    padding: 0.4rem 0.75rem !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
    color: #93c5fd !important;
    letter-spacing: 0.02em !important;
}

/* =========================================================
   14. GRADIO FOOTER BAR
   ========================================================= */
footer,
.footer,
footer.svelte-1rjryqp {
    background: transparent !important;
    border-top: 1px solid rgba(255,255,255,0.05) !important;
    color: #334155 !important;
}
footer a, footer svg { opacity: 0.4 !important; }

/* =========================================================
   15. SCROLLBARS
   ========================================================= */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(59,130,246,0.2);
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(59,130,246,0.4);
}

/* =========================================================
   16. MISC UTILITIES
   ========================================================= */
/* Gradio adds padding to rows/columns that breaks layout */
.gradio-container .block.padded {
    padding: 0 !important;
}

/* Prevent overflow */
.gradio-container {
    overflow-x: hidden !important;
}

/* Ensure text inputs render correctly */
input[type="text"],
input[type="number"],
textarea {
    background: rgba(6,14,32,0.6) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 0.5rem !important;
    color: #dae2fc !important;
    font-family: 'Inter', sans-serif !important;
}
input:focus, textarea:focus {
    border-color: rgba(59,130,246,0.5) !important;
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important;
}

/* Radio labels that show next to each option */
.toggle-radio .gr-radio-row,
.toggle-radio .selected-only {
    display: none !important;
}

/* Ensure row in glass-card has no padding */
.glass-card .gap-4 {
    gap: 0.75rem !important;
}
"""