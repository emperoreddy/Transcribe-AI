import customtkinter as ctk
import threading
import os
from datetime import datetime
from audio_recorder import AudioRecorder
from transcriber import CloudTranscriber
from summarizer import Summarizer

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TranscrAIbe")
        self.geometry("900x650")
        self.minsize(700, 500)

        # Setup Obsidian Notes directory
        self.notes_dir = os.path.join(os.path.expanduser("~"), "Desktop", "transcrAIbe", "Obsidian_Notes")
        os.makedirs(self.notes_dir, exist_ok=True)

        # Initialize Modules
        self.recorder = AudioRecorder()
        self.transcriber = CloudTranscriber()
        self.summarizer = Summarizer()

        # Grid Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header Frame
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.header_frame.grid_columnconfigure(1, weight=1)

        # Device Selection
        self.device_label = ctk.CTkLabel(self.header_frame, text="Audio Source:")
        self.device_label.grid(row=0, column=0, padx=10, pady=10)

        self.devices = self.recorder.get_input_devices()
        self.device_names = list(self.devices.keys())
        
        self.device_var = ctk.StringVar(value=self.device_names[0] if self.device_names else "No Devices Found")
        self.device_dropdown = ctk.CTkOptionMenu(self.header_frame, values=self.device_names, variable=self.device_var, width=300)
        self.device_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Controls Frame
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.controls_frame.grid_columnconfigure((0, 1), weight=1)

        self.record_button = ctk.CTkButton(self.controls_frame, text="Start Recording", command=self.toggle_recording, height=40, font=("Arial", 16, "bold"))
        self.record_button.grid(row=0, column=0, padx=(20, 10), pady=15, sticky="ew")

        self.cancel_button = ctk.CTkButton(self.controls_frame, text="Discard", command=self.cancel_recording, height=40, font=("Arial", 16, "bold"), fg_color="gray", state="disabled")
        self.cancel_button.grid(row=0, column=1, padx=(10, 20), pady=15, sticky="ew")

        self.status_label = ctk.CTkLabel(self.controls_frame, text="Status: Ready", text_color="gray")
        self.status_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))

        # Output Tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="nsew")

        self.tabview.add("Summary")
        self.tabview.add("Transcription")
        self.tabview.add("History")

        self.summary_textbox = ctk.CTkTextbox(self.tabview.tab("Summary"), wrap="word")
        self.summary_textbox.pack(fill="both", expand=True, padx=10, pady=10)

        self.transcription_textbox = ctk.CTkTextbox(self.tabview.tab("Transcription"), wrap="word")
        self.transcription_textbox.pack(fill="both", expand=True, padx=10, pady=10)

        # History Tab layout
        self.tabview.tab("History").grid_columnconfigure(0, weight=1)
        self.tabview.tab("History").grid_columnconfigure(1, weight=3)
        self.tabview.tab("History").grid_rowconfigure(0, weight=1)
        
        self.history_list_frame = ctk.CTkScrollableFrame(self.tabview.tab("History"), width=200)
        self.history_list_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        
        self.history_textbox = ctk.CTkTextbox(self.tabview.tab("History"), wrap="word")
        self.history_textbox.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")

        self.load_history()

        # Preload the transcriber model in the background
        threading.Thread(target=self.preload_model, daemon=True).start()

    def preload_model(self):
        self.update_status("Status: Ready")

    def update_status(self, text, color="gray"):
        self.status_label.configure(text=text, text_color=color)
        self.update_idletasks()

    def toggle_recording(self):
        if not self.recorder.is_recording:
            # Start Recording
            device_name = self.device_var.get()
            device_index = self.devices.get(device_name)
            
            self.recorder.start_recording(device_index=device_index)
            self.record_button.configure(text="Stop & Process", fg_color="red", hover_color="darkred")
            self.cancel_button.configure(state="normal", fg_color=["#3B8ED0", "#1F6AA5"])
            self.update_status("Recording...", "red")
            self.transcription_textbox.delete("1.0", "end")
            self.summary_textbox.delete("1.0", "end")
        else:
            # Stop Recording and process
            self.record_button.configure(text="Start Recording", fg_color=["#3B8ED0", "#1F6AA5"], hover_color=["#36719F", "#144870"], state="disabled")
            self.cancel_button.configure(state="disabled", fg_color="gray")
            self.update_status("Processing audio...", "orange")
            
            audio_file = self.recorder.stop_recording()
            
            # Start processing pipeline in background
            threading.Thread(target=self.process_audio, args=(audio_file,), daemon=True).start()

    def cancel_recording(self):
        if self.recorder.is_recording:
            self.recorder.stop_recording()
            self.record_button.configure(text="Start Recording", fg_color=["#3B8ED0", "#1F6AA5"], hover_color=["#36719F", "#144870"], state="normal")
            self.cancel_button.configure(state="disabled", fg_color="gray")
            self.update_status("Recording discarded.", "gray")
            self.transcription_textbox.delete("1.0", "end")
            self.summary_textbox.delete("1.0", "end")

    def process_audio(self, audio_file):
        try:
            # 1. Transcribe
            self.update_status("Transcribing audio...", "orange")
            transcription = self.transcriber.transcribe(audio_file)
            
            self.transcription_textbox.insert("1.0", transcription)
            
            if not transcription.strip() or transcription.startswith("Error:"):
                self.update_status("Error or no speech detected in audio.", "red")
                self.record_button.configure(state="normal")
                return

            # 2. Summarize
            self.update_status("Generating summary...", "orange")
            self.tabview.set("Summary")
            result = self.summarizer.summarize(transcription)
            
            if isinstance(result, dict):
                title = result.get("title", "Meeting Notes")
                summary = result.get("summary", "No summary available.")
            else:
                title = "Meeting Notes"
                summary = str(result)
            
            self.summary_textbox.insert("1.0", f"# {title}\n\n{summary}")
            
            # 3. Save to Obsidian .md file
            self.save_to_obsidian(transcription, title, summary)

            self.update_status("Status: Ready (Saved to Obsidian Notes)", "green")

        except Exception as e:
            self.update_status(f"Error: {e}", "red")
        finally:
            self.record_button.configure(state="normal")

    def save_to_obsidian(self, transcription, title, summary):
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        # Sanitize title for filename
        clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        if not clean_title:
            clean_title = "Meeting"
            
        filename = f"{clean_title} - {timestamp}.md"
        filepath = os.path.join(self.notes_dir, filename)
        
        content = f"# {title}\n*Date: {timestamp}*\n\n"
        content += summary + "\n\n"
        content += "---\n## Full Transcription\n\n"
        content += transcription + "\n"
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        # Refresh history
        self.load_history()

    def load_history(self):
        # Clear existing history buttons
        for widget in self.history_list_frame.winfo_children():
            widget.destroy()
            
        if not os.path.exists(self.notes_dir):
            return
            
        files = [f for f in os.listdir(self.notes_dir) if f.endswith(".md")]
        files.sort(reverse=True) # Newest first
        
        for f in files:
            btn = ctk.CTkButton(self.history_list_frame, text=f.replace(".md", ""), 
                                command=lambda filepath=os.path.join(self.notes_dir, f): self.open_history_file(filepath),
                                anchor="w", fg_color="transparent", text_color=("black", "white"), hover_color=("gray70", "gray30"))
            btn.pack(fill="x", pady=2, padx=2)

    def open_history_file(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.history_textbox.delete("1.0", "end")
            self.history_textbox.insert("1.0", content)
        except Exception as e:
            self.history_textbox.delete("1.0", "end")
            self.history_textbox.insert("1.0", f"Error reading file: {e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()
