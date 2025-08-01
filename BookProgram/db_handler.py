import sqlite3

class DatabaseHandler:
    def __init__(self):
        self.conn = sqlite3.connect('language_learning.db')
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS stories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    content TEXT,
                    user_content TEXT
                )
            ''')
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')

    def insert_story(self, title, content):
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute('INSERT INTO stories (title, content) VALUES (?, ?)', (title, content))
                return cursor.lastrowid
        except Exception as e:
            print(f"Error inserting story: {e}")
            return None

    def get_story_content(self, story_id):
        cursor = self.conn.execute('SELECT content FROM stories WHERE id = ?', (story_id,))
        row = cursor.fetchone()
        return row[0] if row else ""

    def get_story_title(self, story_id):
        cursor = self.conn.execute('SELECT title FROM stories WHERE id = ?', (story_id,))
        row = cursor.fetchone()
        return row[0] if row else ""

    def get_user_progress(self, story_id):
        cursor = self.conn.execute('SELECT user_content FROM stories WHERE id = ?', (story_id,))
        row = cursor.fetchone()
        return row[0] if row else ""

    def update_story_title(self, story_id, new_title):
        try:
            with self.conn:
                self.conn.execute('UPDATE stories SET title = ? WHERE id = ?', (new_title, story_id))
        except Exception as e:
            print(f"Error updating story title: {e}")

    def save_user_progress(self, story_id, user_content):
        try:
            with self.conn:
                self.conn.execute('UPDATE stories SET user_content = ? WHERE id = ?', (user_content, story_id))
        except Exception as e:
            print(f"Error saving user progress: {e}")

    def get_all_stories(self):
        cursor = self.conn.execute('SELECT id, title FROM stories')
        return cursor.fetchall()

    def get_last_opened_story_id(self):
        cursor = self.conn.execute('SELECT value FROM app_settings WHERE key = "last_opened_story_id"')
        row = cursor.fetchone()
        return int(row[0]) if row else None

    def set_last_opened_story_id(self, story_id):
        with self.conn:
            self.conn.execute('INSERT OR REPLACE INTO app_settings (key, value) VALUES ("last_opened_story_id", ?)', (str(story_id),))

    def delete_story(self, story_id):
        try:
            with self.conn:
                self.conn.execute('DELETE FROM stories WHERE id = ?', (story_id,))
        except Exception as e:
            print(f"Error deleting story: {e}")