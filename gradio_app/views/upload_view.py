# gradio_app/views/upload_view.py
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
                elem_classes="nav-btn nav-active",
            )
            btn_record = gr.Button(
                "⏺  Record Audio",
                elem_classes="nav-btn",
            )
            btn_batch = gr.Button(
                "⚙  Batch NLP",
                elem_classes="nav-btn",
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

            # ── Input Card ──────────────────────────────────
            with gr.Column(elem_classes="glass-card"):
                gr.HTML("""
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:1.25rem;">
                    <span class="material-symbols-outlined" style="color:#93c5fd; font-size:20px;">input</span>
                    <span style="font-size:0.95rem; font-weight:600; color:#dae2fc;">Input Source</span>
                </div>
                """)

                audio_input = gr.Audio(
                    sources=["upload"],
                    type="filepath",
                    label="Drop Audio Here",
                    elem_classes="audio-upload",
                )

                with gr.Row(equal_height=True):
                    with gr.Column(scale=2, min_width=180):
                        gr.HTML('<p style="font-size:0.78rem; font-weight:500; color:#64748b; margin-bottom:0.5rem; text-transform:uppercase; letter-spacing:0.08em;">Output Language Mode</p>')
                        mode = gr.Radio(
                            choices=[("Preserve", "preserve"), ("Normalize", "normalize")],
                            value="preserve",
                            label="",
                            container=False,
                            elem_classes="toggle-radio",
                        )

                    with gr.Column(scale=3, min_width=220):
                        with gr.Row():
                            clear_btn = gr.Button(
                                "Clear",
                                variant="secondary",
                                size="lg",
                            )
                            run_btn = gr.Button(
                                "▶  Run Pipeline",
                                variant="primary",
                                size="lg",
                            )

            # ── Output Row ──────────────────────────────────
            with gr.Row(equal_height=False):

                with gr.Column(scale=1, elem_classes="glass-card"):
                    gr.HTML("""
                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:1rem;">
                        <span class="material-symbols-outlined" style="color:#c084fc; font-size:20px;">output</span>
                        <span style="font-size:0.95rem; font-weight:600; color:#dae2fc;">Results</span>
                    </div>
                    """)
                    out_audio = gr.Audio(
                        label="Audio Response",
                        interactive=False,
                    )
                    out_csv = gr.File(
                        label="Download CSV Transcript",
                        interactive=False,
                    )

                with gr.Column(scale=2, elem_classes="glass-card"):
                    gr.HTML("""
                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:1rem;">
                        <span class="material-symbols-outlined" style="color:#34d399; font-size:20px;">terminal</span>
                        <span style="font-size:0.95rem; font-weight:600; color:#dae2fc;">Pipeline Logs</span>
                    </div>
                    """)
                    log_output = gr.Textbox(
                        value="# Waiting for input...",
                        show_label=False,
                        elem_classes="terminal-output",
                        lines=14,
                        max_lines=14,
                    )

    return (
        audio_input, mode, run_btn, clear_btn,
        out_audio, out_csv, log_output,
        btn_upload, btn_record, btn_batch,
    )