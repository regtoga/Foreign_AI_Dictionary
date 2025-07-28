import subprocess
import sqlite3
import os

def run_ollama(prompt):
    try:
        command = ['ollama', 'run', 'gemma3', prompt]
        print(f"Running command: {' '.join(command)}")
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
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

def store_definition(word, definition, language, conn):
    with conn:
        conn.execute(f'''
            INSERT OR REPLACE INTO {language} (word, definition)
            VALUES (?, ?)
        ''', (word, definition))

def main():
    # Ensure the database is stored in the same directory as the script
    default_output_dir = os.path.dirname(os.path.abspath(__file__))
    database_path = os.path.join(default_output_dir, 'definitions.db')
    
    conn = sqlite3.connect(database_path)
    current_language = input("Enter the language for definitions: ")
    create_table(current_language, conn)

    while True:
        user_input = input("Enter a word to define or '/switch LANGUAGE': ").strip()
        
        if user_input.startswith('/switch'):
            current_language = user_input.split(' ', 1)[1]
            print(f"Switched to {current_language}")
            create_table(current_language, conn)
            continue
        
        definition = get_definition(user_input, current_language, conn)
        
        if definition:
            print(f"Definition found: {definition}")
            redefine = input("Do you want to redefine it? (yes/no): ").strip().lower()
            if redefine != 'yes':
                continue
        
        context = f"Imagine you are a Dictionary that defines a word in as few sentences as possible from the language: {current_language}. If not English for example Chinese please explain the logograms, to an English speaker (if not english explain). Do not ask follow up questions. Define: "
        full_prompt = f"{context} {user_input}"
        definition = run_ollama(full_prompt)
        
        if definition:
            print(f"Definition: {definition}")
            store_definition(user_input, definition, current_language, conn)
        else:
            print("Failed to retrieve definition.")
            
if __name__ == "__main__":
    main()