# ai_handler.py
import asyncio
import threading
import tkinter as tk
from ai_interface import run_ollama

def run_asyncio_task(task):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(task)
    loop.close()

class AIHandler:
    def __init__(self, parent, word, sentence):
        self.parent = parent
        self.context = sentence or word
        self.word = word

        self.setup_ui()
        threading.Thread(target=run_asyncio_task, args=(self.prompt_ai(),)).start()

    def setup_ui(self):
        self.top = tk.Toplevel(self.parent)
        self.top.title(f"Definition of {self.word}")

        self.scrollbar = tk.Scrollbar(self.top)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.definition_text = tk.Text(self.top, wrap=tk.WORD, height=20, width=60, yscrollcommand=self.scrollbar.set)
        self.definition_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.definition_text.yview)

        self.definition_text.insert(tk.END, "Your query is being generated...\n")

        self.followup_entry = tk.Entry(self.top)
        self.followup_entry.pack(pady=5, fill=tk.X)
        tk.Button(self.top, text="Send", command=self.send_followup).pack()

        self.top.protocol("WM_DELETE_WINDOW", self.close_window)

    async def prompt_ai(self):
        prompt = (f"You are a Helpful AI that helps a user understand a language they don't know yet. "
                  f"Here is the context: '{self.context}'. Please define the word '{self.word}'.")

        print(f"AI Prompt: {prompt}")

        process = await run_ollama(prompt)
        if process:
            await self.stream_response(process)
        else:
            self.definition_text.insert(tk.END, "Failed to start AI process.\n")

    async def stream_response(self, process):
        buffer = b""
        try:
            while True:
                byte = await process.stdout.read(1)
                if not byte:
                    break
                buffer += byte
                if byte == b'\n':
                    try:
                        line = buffer.decode("utf-8")
                        self.definition_text.insert(tk.END, line)
                        self.definition_text.yview(tk.END)
                        self.definition_text.update_idletasks()
                    except UnicodeDecodeError:
                        line = buffer.decode("utf-8", errors='replace')
                    buffer = b""
        except Exception as e:
            print(f"Error during AI response streaming: {e}")
        finally:
            await process.wait()

    def send_followup(self):
        followup_question = self.followup_entry.get()
        if followup_question:
            print(f"Follow-up Prompt: {followup_question}")
            self.definition_text.insert(tk.END, f"\nUser's follow-up: {followup_question}\n")
            followup_prompt = (f"Previous context: '{self.context}'. User asks: {followup_question}")
            threading.Thread(target=run_asyncio_task, args=(self.handle_followup(followup_prompt),)).start()
            self.followup_entry.delete(0, tk.END)

    async def handle_followup(self, prompt):
        self.context += " " + prompt
        process = await run_ollama(prompt)
        if process:
            await self.stream_response(process)

    def close_window(self):
        self.top.destroy()