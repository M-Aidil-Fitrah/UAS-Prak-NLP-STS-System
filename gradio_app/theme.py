# gradio_app/theme.py

HEAD_HTML = """
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
<script>
    tailwind.config = {
        darkMode: "class",
        theme: {
            extend: {
                colors: {
                    primary: "#3b82f6",
                    "primary-container": "#2563eb",
                    background: "#070b14",
                    surface: "#0a0f1c",
                    "surface-container-low": "#131b2e",
                    "surface-container-lowest": "#060e20",
                    "surface-container-high": "#222a3d",
                    "surface-variant": "#2d3449",
                    "on-surface": "#e2e8f0",
                    "on-surface-variant": "#94a3b8",
                    "outline-variant": "#334155",
                    error: "#ffb4ab",
                }
            }
        }
    }
</script>
"""

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* 1. Global Reset - Force Transparency Everywhere */
body, .gradio-container, .main, .wrap, .prose {
    background: radial-gradient(circle at top right, #131b2e, #060e20) !important;
    font-family: 'Inter', sans-serif !important;
    color: white !important;
    border: none !important;
}

/* 2. Glass Card Definition */
.glass-card {
    background: rgba(19, 27, 46, 0.6) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 1.25rem !important;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4) !important;
    padding: 1.5rem !important;
    overflow: hidden !important;
}

/* 3. Strip Gradio's default "Group" and "Box" styles */
.glass-card .gr-group, 
.glass-card .gr-box, 
.glass-card .gr-form,
.glass-card div[class*="p-4"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* 4. Fix File/Audio Upload Areas */
.gr-audio .upload-container, .gr-file .upload-container {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 2px dashed rgba(255, 255, 255, 0.1) !important;
    border-radius: 1rem !important;
    transition: all 0.3s ease !important;
}
.gr-audio .upload-container:hover {
    border-color: #3b82f6 !important;
    background: rgba(59, 130, 246, 0.1) !important;
}

/* 5. Modern Button styling */
.gr-button-primary {
    background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important;
    border: none !important;
    border-radius: 0.75rem !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    box-shadow: 0 4px 14px 0 rgba(59, 130, 246, 0.39) !important;
}

/* 6. Terminal Console Look */
.terminal-output {
    background: rgba(0, 0, 0, 0.3) !important;
    font-family: 'JetBrains Mono', monospace !important;
    color: #a8c7fa !important;
    border-radius: 0.5rem !important;
}

/* 7. Hide Scrollbars */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }

/* Radio Buttons overrides */
.toggle-radio {
    background: transparent !important;
    border: none !important;
}
.toggle-radio .wrap {
    display: flex !important;
    flex-direction: row !important;
    background: rgba(6, 14, 32, 0.5) !important;
    border-radius: 0.75rem !important;
    padding: 0.25rem !important;
    border: 1px solid rgba(65, 71, 85, 0.5) !important;
}
.toggle-radio label {
    flex: 1 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0.5rem 1rem !important;
    border-radius: 0.5rem !important;
    cursor: pointer !important;
    background: transparent !important;
    border: none !important;
    transition: all 0.2s ease !important;
}
.toggle-radio label.selected {
    background: rgba(45, 52, 73, 0.8) !important;
}
.toggle-radio input[type="radio"] { display: none !important; }

/* Navigation buttons (Sidebar/Top) */
.nav-btn {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    text-align: left !important;
    color: #94a3b8 !important;
    justify-content: flex-start !important;
}
.nav-btn:hover { color: white !important; background: transparent !important; }
.nav-active {
    color: white !important;
}
.nav-active::after {
    content: '';
    position: absolute;
    bottom: -8px;
    left: 0;
    width: 100%;
    height: 2px;
    background: #007aff;
}
.nav-top-btn {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
.nav-top-btn-active {
    color: #adc6ff !important;
    font-weight: bold !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
"""
