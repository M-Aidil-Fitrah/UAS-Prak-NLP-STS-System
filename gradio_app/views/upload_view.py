import gradio as gr

def build():
    with gr.Row():
        
        # Left Sidebar
        with gr.Column(scale=1, elem_classes="glass-card", min_width=280):
            gr.HTML("""
            <div class='flex items-center gap-3 mb-8'>
                <span class='material-symbols-outlined text-blue-500 text-3xl'>waves</span>
                <span class='text-2xl font-bold'>Sonic Lingua</span>
            </div>
            <h2 class="text-xs font-semibold text-[#c1c6d7] uppercase tracking-[0.2em] mb-2">Workflow</h2>
            """)
            
            btn_upload = gr.Button("Upload Audio", elem_classes="nav-btn nav-active text-white text-left font-medium")
            btn_record = gr.Button("Record Audio", elem_classes="nav-btn text-[#c1c6d7] hover:text-white text-left font-medium")
            btn_batch = gr.Button("Input Audio NLP", elem_classes="nav-btn text-[#c1c6d7] hover:text-white text-left font-medium")

            gr.HTML("""
            <div style="margin-top: 15rem;">
                <footer class="flex flex-col gap-4 text-sm text-[#c1c6d7]">
                    <a class="hover:text-white transition-colors flex items-center gap-2" href="#">
                        <span class="material-symbols-outlined text-[18px]">api</span> Use via API
                    </a>
                    <a class="hover:text-white transition-colors flex items-center gap-2" href="#">
                        <span class="material-symbols-outlined text-[18px]">settings</span> Settings
                    </a>
                    <span class="text-xs opacity-50 mt-4">Built with Gradio</span>
                </footer>
            </div>
            """)

        # Main Content
        with gr.Column(scale=4):
            # Input Area
            with gr.Column(elem_classes="glass-card"):
                gr.Markdown("## <span class='material-symbols-outlined'>input</span> Input Source")
                
                audio_input = gr.Audio(sources=["upload"], type="filepath", label="Drop Audio Here")
                
                with gr.Row():
                    with gr.Column(scale=1, min_width=150):
                        gr.HTML('<span class="text-sm font-medium text-[#c1c6d7] block mb-2">Output Language Mode</span>')
                        mode = gr.Radio(
                            choices=[("Preserve", "preserve"), ("Normalize", "normalize")],
                            value="preserve", 
                            label="", 
                            container=False, 
                            elem_classes="toggle-radio"
                        )
                    
                    with gr.Row():
                        clear_btn = gr.Button("Clear", variant="secondary")
                        run_btn = gr.Button("Run Pipeline", variant="primary", elem_classes="gr-button-primary")

            # Output Area
            with gr.Row():
                with gr.Column(scale=1, elem_classes="glass-card"):
                    gr.Markdown("## <span class='material-symbols-outlined text-purple-400'>output</span> Results")
                    out_audio = gr.Audio(label="Audio Response", interactive=False)
                    out_csv = gr.File(label="Download CSV Transcript", interactive=False)

                with gr.Column(scale=2, elem_classes="glass-card"):
                    gr.Markdown("## <span class='material-symbols-outlined text-emerald-400'>terminal</span> Logs")
                    log_output = gr.Textbox(value="*Menunggu input...*", show_label=False, elem_classes="terminal-output", lines=12)

    return audio_input, mode, run_btn, clear_btn, out_audio, out_csv, log_output, btn_upload, btn_record, btn_batch
