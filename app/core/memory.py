import json
import sqlite3
import numpy as np
from loguru import logger


class TranslationMemory:
    def __init__(self, db_path: str ="memory.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self._create_tables()

    def _create_tables(self):
        # Unique concepts table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS concepts (
                concept_id INTEGER PRIMARY KEY AUTOINCREMENT
            )
        """)
        # Translations table with unique constraint on concept + language
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS translations (
                concept_id INTEGER,
                lang TEXT,
                content TEXT,
                PRIMARY KEY (concept_id, lang),
                FOREIGN KEY (concept_id) REFERENCES concepts(concept_id)
            )
        """)
        self.conn.commit()

    def add_translation(self, text: str, lang_from: str, translation: str, lang_to: str, overwrite: bool):
        cursor = self.conn.cursor()
        
        # 1. Find if the concept already exists in any language
        cursor.execute("SELECT concept_id FROM translations WHERE content = ?", (text,))
        result = cursor.fetchone()
        
        if result:
            concept_id = result[0]
        else:
            # 2. Create new concept if not found
            cursor.execute("INSERT INTO concepts DEFAULT VALUES")
            concept_id = cursor.lastrowid
            # Add the source text for the source language
            cursor.execute("INSERT INTO translations (concept_id, lang, content) VALUES (?, ?, ?)", 
            (concept_id, lang_from, text))

        # 3. Add the target translation (replaces or ignores if already exists for that lang)
        if overwrite:
            write = 'REPLACE'
        else:
            write = 'IGNORE'

        cursor.execute(f"""
            INSERT OR {write} INTO translations (concept_id, lang, content) 
            VALUES (?, ?, ?)
        """, (concept_id, lang_to, translation))
        
        self.conn.commit()

    def translate(self, text: str, target_lang: str):
        """Translates text to target_lang regardless of original source direction."""
        cursor = self.conn.cursor()
        # Find the concept ID of the input text, then find its translation in target_lang
        query = """
            SELECT t2.content FROM translations t1
            JOIN translations t2 ON t1.concept_id = t2.concept_id
            WHERE t1.content = ? AND t2.lang = ?
        """
        cursor.execute(query, (text, target_lang))
        result = cursor.fetchone()
        return result[0] if result else None


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        # Convert NumPy arrays to lists
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        # Convert NumPy integers (int32, int64) to Python int
        if isinstance(obj, np.integer):
            return int(obj)
        # Convert NumPy floats (float32, float64) to Python float
        if isinstance(obj, np.floating):
            return float(obj)
        return super().default(obj)


def load_result_json(result_json_path: str, memory: list[object|str|bool]):
    logger.info(f"\nLoading existing result.json")

    tm, overwrite_memory, source_language, target_language = memory

    with open(result_json_path, "r", encoding="utf-8") as f:
        loaded_result_json = json.load(f)

    for item in loaded_result_json:
        # Convert bounding boxes back to NumPy arrays
        item["box"] = np.array(item["box"], dtype=np.int32)
        # Overwrite or keep translation memory
        if overwrite_memory:
            tm.add_translation(item["original_text"], source_language, item["translated_text"], target_language, overwrite_memory)

    logger.success(f"Existing result.json loaded.")

    return loaded_result_json