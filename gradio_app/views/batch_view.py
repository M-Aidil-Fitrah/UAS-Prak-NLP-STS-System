# gradio_app/views/batch_view.py
import gradio as gr


def build():
    with gr.Row(equal_height=True):

        # ── LEFT SIDEBAR ──────────────────────────────────────
        with gr.Column(scale=1, elem_classes="glass-card", min_width=240):
            gr.HTML("""
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:2rem;">
                <span class="material-symbols-outlined" style="color:#3b82f6; font-size:26px;">graphic_eq</span>
                <span style="font-size:1.2rem; font-weight:700; color:#dae2fc; letter-spacing:-0.02em;">Sonic Lingua</span>
            </div>
            <p style="font-size:0.65rem; font-weight:600; color:#334155; text-transform:uppercase; letter-spacing:0.18em; margin-bottom:0.75rem;">Workflow</p>
            """)

            btn_upload = gr.Button(
                "⬆  Upload Audio",
                elem_classes="nav-btn",
            )
            btn_record = gr.Button(
                "⏺  Record Audio",
                elem_classes="nav-btn",
            )
            btn_batch = gr.Button(
                "⚙  Batch NLP",
                elem_classes="nav-btn nav-active",
            )

            gr.HTML("""
            <div class="sidebar-footer" style="margin-top:auto; padding-top:3rem; border-top: 1px solid rgba(255,255,255,0.06); margin-top:10rem;">
                <a href="#">
                    <span class="material-symbols-outlined" style="font-size:16px;">api</span>
                    Use via API
                </a>
                <a href="#">
                    <span class="material-symbols-outlined" style="font-size:16px;">settings</span>
                    Settings
                </a>
                <p style="font-size:0.7rem; color:#1e293b; margin-top:1rem;">Built with Gradio</p>
            </div>
            """)

        # ── MAIN CONTENT ─────────────────────────────────────
        with gr.Column(scale=4):

            # Page Header
            gr.HTML("""
            <div style="text-align:center; margin-bottom:2rem; padding-top:0.5rem;">
                <h1 style="font-size:1.9rem; font-weight:700; color:#dae2fc; letter-spacing:-0.03em; margin:0 0 0.6rem 0; line-height:1.2;">
                    Multilingual Speech-to-Speech System
                </h1>
                <div style="display:inline-flex; align-items:center; gap:6px; background:rgba(19,27,46,0.6); border:1px solid rgba(255,255,255,0.08); border-radius:9999px; padding:0.35rem 1.1rem;">
                    <span style="font-size:0.82rem; color:#94a3b8;">Saudi Tourism AI Assistant — Code-Switching Support</span>
                    <span style="font-size:0.82rem; font-weight:600; color:#93c5fd;">(ID / EN / AR)</span>
                </div>
            </div>
            """)

            with gr.Row(equal_height=False):

                # ── Batch Control Panel ──────────────────────
                with gr.Column(scale=1, min_width=300, elem_classes="glass-card"):
                    gr.HTML("""
                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:1.25rem;">
                        <span class="material-symbols-outlined" style="color:#93c5fd; font-size:20px;">settings_b_roll</span>
                        <span style="font-size:0.95rem; font-weight:600; color:#dae2fc;">Batch Control</span>
                    </div>

                    <div style="display:flex; align-items:center; gap:6px; margin-bottom:0.6rem;">
                        <span class="material-symbols-outlined" style="color:#64748b; font-size:16px;">folder_open</span>
                        <span style="font-size:0.75rem; font-weight:600; color:#64748b; text-transform:uppercase; letter-spacing:0.1em;">Source Directory</span>
                    </div>
                    <div style="background:rgba(6,14,32,0.55); border:1px solid rgba(59,130,246,0.15); border-radius:0.75rem; padding:0.875rem 1rem; margin-bottom:1.5rem;">
                        <p style="font-size:0.78rem; color:#64748b; margin:0 0 0.4rem 0;">Processing all WAV files from:</p>
                        <span class="path-badge">corpus/audio/Audio_NLP/</span>
                    </div>

                    <div style="display:flex; align-items:center; gap:6px; margin-bottom:0.6rem;">
                        <span class="material-symbols-outlined" style="color:#64748b; font-size:16px;">language</span>
                        <span style="font-size:0.75rem; font-weight:600; color:#64748b; text-transform:uppercase; letter-spacing:0.1em;">Output Language Mode</span>
                    </div>
                    """)

                    mode = gr.Radio(
                        choices=[("Preserve", "preserve"), ("Normalize", "normalize")],
                        value="preserve",
                        label="",
                        container=False,
                        elem_classes="toggle-radio",
                    )

                    gr.HTML('<div style="height:1.5rem;"></div>')

                    run_btn = gr.Button(
                        "▶  Start Processing Run",
                        variant="primary",
                        size="lg",
                    )

                # ── Right: Logs + Results ────────────────────
                with gr.Column(scale=2):

                    with gr.Column(elem_classes="glass-card"):
                        gr.HTML("""
                        <div style="display:flex; align-items:center; gap:8px; margin-bottom:1rem;">
                            <span class="material-symbols-outlined" style="color:#7dd3fc; font-size:20px;">terminal</span>
                            <span style="font-size:0.85rem; font-weight:600; color:#dae2fc; font-family:'JetBrains Mono',monospace; letter-spacing:0.04em;">system_process_log.sh</span>
                        </div>
                        """)
                        log_output = gr.Textbox(
                            value="# NLP Audio Batch Processor v2.4.1\n# Initialization complete. Waiting for user command...",
                            show_label=False,
                            elem_classes="terminal-output",
                            lines=8,
                            max_lines=8,
                        )

                    with gr.Column(elem_classes="glass-card"):
                        gr.HTML("""
                        <div style="display:flex; align-items:center; gap:8px; margin-bottom:1rem;">
                            <span class="material-symbols-outlined" style="color:#b9c7e0; font-size:20px;">analytics</span>
                            <span style="font-size:0.95rem; font-weight:600; color:#dae2fc;">Analysis Results</span>
                        </div>
                        """)
                        out_csv = gr.File(
                            label="Download CSV",
                            interactive=False,
                        )

    return (
        mode, run_btn, out_csv, log_output,
        btn_upload, btn_record, btn_batch,
    )