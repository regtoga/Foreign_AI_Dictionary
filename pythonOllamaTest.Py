import subprocess
import sqlite3
import os
import asyncio
import tkinter as tk
from tkinter import scrolledtext, messagebox

async def run_ollama(prompt):
    try:
        command = ['ollama', 'run', 'gemma3', prompt]
        print(f"Running command: {' '.join(command)}")

        result = await asyncio.get_running_loop().run_in_executor(
            None, lambda: subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
        )
        
        return result.stdout.strip()

    except FileNotFoundError:
        print("Ollama CLI is not found. Please ensure it's installed and in your PATH.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e.stderr}")
        return None

def create_table(language, conn):
    with conn:
        conn.execute(f'''
            CREATE TABLE IF NOT EXISTS {language} (
                word TEXT PRIMARY KEY,
                definition TEXT
            )
        ''')

def get_definition(word, language, conn):
    cursor = conn.execute(f'SELECT definition FROM {language} WHERE word = ?', (word,))
    row = cursor.fetchone()
    return row[0] if row else None

async def store_definition_in_db(queue, conn):
    while True:
        word, definition, language = await queue.get()
        with conn:
            conn.execute(f'''
                INSERT OR REPLACE INTO {language} (word, definition)
                VALUES (?, ?)
            ''', (word, definition))
        queue.task_done()

async def process_word(word, language, output_text, db_queue, conn, from_file=False):
    print(f"Processing word: {word}")
    
    existing_definition = get_definition(word, language, conn)
    if existing_definition:
        append_message = f"{word}: {existing_definition} (from DB)\n"
        if not from_file:
            clear_and_append(output_text, append_message)
            regenerate = messagebox.askyesno("Regenerate Definition", f"Definition for '{word}' already exists. Would you like to regenerate it?")
            if not regenerate:
                return
        else:
            clear_and_append(output_text, append_message)
            return

    context = (f"Imagine you are a Dictionary that defines a word in as few sentences as possible "
               f"from the language: {language}. If not English for example Chinese please explain "
               f"the logograms to an English speaker (if not English already), do not comment about this if not relelvant. Define:")
               
    full_prompt = f"{context} {word}"
    definition = await run_ollama(full_prompt)
    
    if definition:
        clear_and_append(output_text, f"{word}: {definition}\n")
        await db_queue.put((word, definition, language))
    else:
        clear_and_append(output_text, f"Failed to retrieve definition for '{word}'\n")

def clear_and_append(widget, message):
    if widget.winfo_exists():
        widget.delete('1.0', tk.END)
        widget.insert(tk.END, message)
        widget.see(tk.END)

async def process_file(file_path, language, output_text, db_queue, conn):
    global processing_file
    processing_file = True
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if not processing_file:
                break
            word = line.strip()
            if word:
                await process_word(word, language, output_text, db_queue, conn, from_file=True)
    processing_file = False

def main():
    root = tk.Tk()
    root.title("Dictionary Processor")

    conn = sqlite3.connect('Word_Definitions.db')
    db_queue = asyncio.Queue()

    language_var = tk.StringVar(value="English")
    global processing_file
    processing_file = False

    def set_language():
        language = language_var.get()
        create_table(language, conn)

    def stop_processing():
        global processing_file
        processing_file = False

    async def async_process_word(word, language, output_text):
        await process_word(word, language, output_text, db_queue, conn)

    async def async_process_file(file_path, language, output_text):
        await process_file(file_path, language, output_text, db_queue, conn)

    def process_user_input():
        input_text = user_input_entry_var.get().strip()
        user_input_entry_var.set('')
        if not input_text:
            return
        
        elif input_text.startswith('/file'):
            file_name = input_text.split(' ', 1)[1]
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
            if os.path.exists(file_path):
                asyncio.ensure_future(async_process_file(file_path, language_var.get(), output_text))
            else:
                clear_and_append(output_text, f"File {file_name} not found.\n")
        
        else:
            asyncio.ensure_future(async_process_word(input_text, language_var.get(), output_text))

    language_label = tk.Label(root, text="Language:")
    language_label.grid(row=0, column=0, padx=5, pady=5)

    language_entry = tk.Entry(root, textvariable=language_var)
    language_entry.grid(row=0, column=1, padx=5, pady=5)

    enter_button = tk.Button(root, text="Set Language", command=set_language)
    enter_button.grid(row=0, column=2, padx=5, pady=5)

    user_input_label = tk.Label(root, text="Enter a word, or '/file FILENAME':")
    user_input_label.grid(row=1, column=0, padx=5, pady=5, columnspan=2)

    user_input_entry_var = tk.StringVar()
    user_input_entry = tk.Entry(root, textvariable=user_input_entry_var)
    user_input_entry.grid(row=2, column=0, padx=5, pady=5, columnspan=2)

    process_button = tk.Button(root, text="Process Input", command=process_user_input)
    process_button.grid(row=2, column=2, padx=5, pady=5)

    output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=10, width=50)
    output_text.grid(row=3, column=0, columnspan=3, padx=5, pady=5)

    stop_button = tk.Button(root, text="Stop Processing", command=stop_processing)
    stop_button.grid(row=4, column=1, padx=5, pady=10)

    async def run_async():
        asyncio.create_task(store_definition_in_db(db_queue, conn))
        while True:
            root.update()
            await asyncio.sleep(0.1)

    def start_event_loop():
        asyncio.run(run_async())

    root.after(100, start_event_loop)
    root.mainloop()

if __name__ == "__main__":
    main()