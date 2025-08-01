import tkinter as tk
import threading
from ai_handler import AIHandler
from db_handler import DatabaseHandler

class StoryInterface:
    def __init__(self, parent, story_id, back_to_menu_callback):
        self.parent = parent
        self.story_id = story_id
        self.back_to_menu_callback = back_to_menu_callback
        self.db_handler = DatabaseHandler()
        self.story_content = self.db_handler.get_story_content(story_id)
        self.title = self.db_handler.get_story_title(story_id)

        self.pages = []  # Initialize pages as an empty list
        self.current_page = 0

        self.setup_ui()
        # Start processing in the background
        threading.Thread(target=self.process_large_file, args=(self.story_content,)).start()

    def setup_ui(self):
        self.temp_text_widget = tk.Text(self.parent, wrap=tk.WORD)

        top_frame = tk.Frame(self.parent)
        top_frame.pack(fill=tk.X)

        self.title_label = tk.Label(top_frame, text=f"Story: {self.title}")
        self.title_label.pack(side=tk.LEFT, padx=10)

        rename_btn = tk.Button(top_frame, text="Rename Story", command=self.rename_story)
        rename_btn.pack(side=tk.RIGHT, padx=10)

        self.text_frame = tk.Frame(self.parent)
        self.text_frame.pack(fill=tk.BOTH, expand=True)

        self.story_text = tk.Text(self.text_frame, wrap=tk.WORD, height=30, width=80)
        self.story_text.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.BOTH)
        self.story_text.bind("<ButtonRelease-1>", self.on_text_select)

        self.user_text = tk.Text(self.text_frame, wrap=tk.WORD, height=30, width=80)
        self.user_text.pack(side=tk.RIGHT, padx=5, pady=5, expand=True, fill=tk.BOTH)

        control_frame = tk.Frame(self.parent)
        control_frame.pack()

        tk.Button(control_frame, text="Previous Page", command=self.previous_page).pack(side=tk.LEFT, pady=5)
        tk.Button(control_frame, text="Next Page", command=self.next_page).pack(side=tk.RIGHT, pady=5)
        tk.Button(control_frame, text="Back to Menu", command=self.back_and_save).pack(side=tk.BOTTOM, pady=5)

    def rename_story(self):
        new_title = tk.simpledialog.askstring("Rename Story", "Enter a new name for the story:")
        if new_title:
            self.db_handler.update_story_title(self.story_id, new_title)
            self.title = new_title
            self.update_title_label()
            tk.messagebox.showinfo("Success", f"Story renamed to: {new_title}")

    def update_title_label(self):
        self.title_label.config(text=f"Story: {self.title}")

    def save_user_progress(self):
        content = self.user_text.get("1.0", tk.END).strip()
        self.db_handler.save_user_progress(self.story_id, content)

    import threading

    def paginate_story(self, content):
        # Similar to existing function, with threading to handle large files
        threading.Thread(target=self.process_large_file, args=(content,)).start()

    def process_large_file(self, content):
        def process_chunks():
            pages = []
            current_page = []
            lines = content.splitlines()
            max_lines = 60

            for line in lines:
                potential_page = current_page + [line]

                # Ensuring not to block the main thread with UI updates
                self.temp_text_widget.delete("1.0", tk.END)
                self.temp_text_widget.insert(tk.END, "\n".join(potential_page))

                if int(self.temp_text_widget.index('end-1c').split('.')[0]) < max_lines:
                    current_page.append(line)
                else:
                    pages.append("\n".join(current_page))
                    current_page = [line]

            if current_page:
                pages.append("\n".join(current_page))

            self.pages = pages
            self.parent.after(0, self.display_page, 0)

        threading.Thread(target=process_chunks).start()

    def next_page(self):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.display_page(self.current_page)

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_page(self.current_page)

    def display_page(self, page_number):
        if 0 <= page_number < len(self.pages):
            self.current_page = page_number
            self.story_text.delete("1.0", tk.END)
            self.story_text.insert(tk.END, self.pages[page_number].strip())

    def back_and_save(self):
        self.save_user_progress()
        self.back_to_menu_callback()

    def save_and_exit(self):
        self.save_user_progress()
        self.parent.quit()

    def on_text_select(self, event):
        try:
            selected_text = self.story_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            sentence = self.get_sentence_containing_word(selected_text)
            if selected_text.strip():
                self.open_properties_window(selected_text, sentence, event.x_root, event.y_root)
        except tk.TclError:
            pass

    def open_properties_window(self, word, sentence, x, y):
        top = tk.Toplevel(self.parent)
        top.title("Word Options")
        top.geometry(f"+{x}+{y}")

        tk.Label(top, text=f"Word: {word}").pack(pady=5)
        tk.Button(top, text="Get Definition", command=lambda: self.run_ai_handler(word, sentence, top)).pack(pady=5)

    def run_ai_handler(self, word, sentence, top):
        top.destroy()
        AIHandler(self.parent, word, sentence)

    def get_sentence_containing_word(self, word):
        text = self.story_text.get("1.0", tk.END).strip()
        context_length = 50
        start_idx = max(0, text.find(word) - context_length)
        end_idx = min(len(text), text.find(word) + len(word) + context_length)
        return text[start_idx:end_idx].strip()