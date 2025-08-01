import tkinter as tk
from tkinter import filedialog, messagebox
from story_interface import StoryInterface
from db_handler import DatabaseHandler

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Language Learning App")
        self.root.state('zoomed')  # Maximize the window

        self.db_handler = DatabaseHandler()
        self.setup_ui()

    def setup_ui(self):
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)  # Handle close for the main window
        self.main_menu_frame = tk.Frame(self.root)
        self.main_menu_frame.pack(fill=tk.BOTH, expand=True)

        tk.Button(self.main_menu_frame, text="Open Last Story", command=self.open_last_story).pack(pady=10)
        tk.Button(self.main_menu_frame, text="Upload Story", command=self.open_story_prompt).pack(pady=10)
        tk.Button(self.main_menu_frame, text="Load Saved Stories", command=self.load_save_screen).pack(pady=10)

    def exit_app(self):
        if hasattr(self, 'story_frame') and self.story_frame:
            self.story_frame.save_user_progress()
        self.root.quit()

    def open_story_prompt(self):
        filepath = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if filepath:
            with open(filepath, encoding='utf-8') as file:
                story_content = file.read()
            default_name = ' '.join(story_content.split()[:3])
            story_id = self.db_handler.insert_story(default_name, story_content)
            self.open_story_window(story_id)

    def open_last_story(self):
        last_story_id = self.db_handler.get_last_opened_story_id()
        if last_story_id:
            self.open_story_window(last_story_id)
        else:
            self.open_story_prompt()

    def open_story_window(self, story_id):
        self.clear_frame(self.root)
        self.db_handler.set_last_opened_story_id(story_id)
        StoryInterface(self.root, story_id, self.back_to_menu)

    def load_save_screen(self):
        self.clear_frame(self.root)  # Clear any existing frames

        self.story_list_frame = tk.Frame(self.root)
        self.story_list_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(self.story_list_frame, text="Select a Story to Load:", font=("Helvetica", 16)).pack(pady=10)
        
        stories = self.db_handler.get_all_stories()
        for story_id, title in stories:
            story_button = tk.Button(
                self.story_list_frame, 
                text=title, 
                command=lambda sid=story_id: self.open_story_window(sid)
            )
            story_button.pack(pady=5)
            
            # Bind right-click event
            story_button.bind("<Button-3>", lambda event, sid=story_id: self.confirm_delete(self.story_list_frame, sid))
        
        tk.Button(self.story_list_frame, text="Back to Menu", command=self.back_to_menu).pack(pady=10)

    def confirm_delete(self, parent, story_id):
        result = messagebox.askyesno("Delete Story", "Are you sure you want to delete this story?")
        if result:
            self.db_handler.delete_story(story_id)
            self.load_save_screen()

    def back_to_menu(self):
        self.clear_frame(self.root)
        self.setup_ui()

    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()