import gradio as gr

def build():
    with gr.Column(elem_classes="w-full relative overflow-x-hidden"):
        
        # Top Nav
        gr.HTML("""
        <header class="relative z-10 w-full pt-10 pb-6 px-6 flex flex-col items-center">
            <div class="max-w-7xl w-full flex flex-col items-center">
                <h1 class="text-[32px] font-bold text-[#dae2fd] text-center mb-2 tracking-tight drop-shadow-sm">
                    Multilingual Speech-to-Speech System
                </h1>
                <p class="text-[16px] text-[#c1c6d7] text-center mb-6 bg-[#131b2e]/50 backdrop-blur-sm px-6 py-2 rounded-full border border-[#414755]/30">
                    Saudi Tourism AI Assistant — Code-Switching Support <span class="text-[#adc6ff] font-medium">(ID / EN / AR)</span>
                </p>
            </div>
        </header>
        """)

        with gr.Row(elem_classes="flex justify-center w-full z-10 mb-8"):
            with gr.Row(elem_classes="p-1 bg-[#060e20]/80 backdrop-blur-md rounded-full border border-[#414755]/40"):
                btn_upload = gr.Button("Upload Audio", elem_classes="nav-top-btn")
                btn_record = gr.Button("Record Audio", elem_classes="nav-top-btn")
                btn_batch = gr.Button("Input Audio NLP", elem_classes="nav-top-btn-active")

        # Main Content
        with gr.Row(elem_classes="max-w-[1400px] mx-auto px-6 py-4"):
            
            # Left: Batch Config
            with gr.Column(scale=1, min_width=380, elem_classes="glass-card"):
                gr.Markdown("## <span class='material-symbols-outlined text-[#adc6ff]'>settings_b_roll</span> Batch Control")
                
                gr.Markdown("### <span class='material-symbols-outlined'>folder_open</span> Source Directory")
                gr.HTML("""
                <div class="bg-[#060e20]/50 border border-[#414755]/50 rounded-2xl p-4 mb-6">
                    <p class="text-[14px] text-[#c1c6d7] mb-2">Processing all WAV files from:</p>
                    <div class="flex items-center gap-2 flex-wrap">
                        <span class="bg-[#222a3d]/80 border border-[#414755]/60 text-[13px] font-mono text-[#adc6ff] px-3 py-1.5 rounded-lg">corpus/audio/Audio_NLP/</span>
                    </div>
                </div>
                """)

                gr.Markdown("### <span class='material-symbols-outlined'>language</span> Output Language Mode")
                mode = gr.Radio(
                    choices=[("Preserve", "preserve"), ("Normalize", "normalize")],
                    value="preserve", 
                    label="", 
                    container=False, 
                    elem_classes="toggle-radio mb-8"
                )
                
                run_btn = gr.Button("Start Processing Run", variant="primary", elem_classes="gr-button-primary w-full")

            # Right: Results
            with gr.Column(scale=2):
                with gr.Column(elem_classes="glass-card"):
                    gr.Markdown("### <span class='material-symbols-outlined text-[#adc6ff]'>terminal</span> system_process_log.sh")
                    log_output = gr.Textbox(
                        value="*# NLP Audio Batch Processor v2.4.1\\n# Initialization complete. Waiting for user command...*", 
                        show_label=False, 
                        elem_classes="terminal-output", 
                        lines=8
                    )

                with gr.Column(elem_classes="glass-card"):
                    gr.Markdown("### <span class='material-symbols-outlined text-[#b9c7e0]'>analytics</span> Analysis Results")
                    out_csv = gr.File(label="Download CSV", interactive=False)

    return mode, run_btn, out_csv, log_output, btn_upload, btn_record, btn_batch
