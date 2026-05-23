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
            btn_upload = gr.Button("Upload Audio", elem_classes="nav-top-btn")
            btn_record = gr.Button("Record Audio", elem_classes="nav-top-btn-active")
            btn_batch = gr.Button("Input Audio NLP", elem_classes="nav-top-btn")

        # Main Content
        with gr.Row(elem_classes="max-w-6xl mx-auto px-6 py-4"):
            
            # Left: Mic
            with gr.Column(scale=3, elem_classes="glass-card"):
                gr.Markdown("## <span class='material-symbols-outlined text-[#adc6ff]'>mic</span> AUDIO INPUT")
                audio_input = gr.Audio(sources=["microphone"], type="filepath", label="")

            # Right: Settings & Outputs
            with gr.Column(scale=2):
                with gr.Column(elem_classes="glass-card"):
                    gr.Markdown("### <span class='material-symbols-outlined'>tune</span> Mode Output Bahasa")
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

                with gr.Column(elem_classes="glass-card"):
                    gr.Markdown("### <span class='material-symbols-outlined text-[#b9c7e0]'>output</span> RESPONSE")
                    out_audio = gr.Audio(label="Audio Respons", interactive=False)
                    out_csv = gr.File(label="Download CSV", interactive=False)

                with gr.Column(elem_classes="glass-card"):
                    gr.Markdown("### <span class='material-symbols-outlined text-[#c1c6d7]'>terminal</span> LOGS")
                    log_output = gr.Textbox(value="*Menunggu input...*", show_label=False, elem_classes="terminal-output", lines=4)

    return audio_input, mode, run_btn, clear_btn, out_audio, out_csv, log_output, btn_upload, btn_record, btn_batch
