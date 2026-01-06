import sqlite3

class TranslationMemory:
    def __init__(self, db_path="multi_tm.db"):
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

    def add_translation(self, text, lang_from, translation, lang_to):
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

        # 3. Add the target translation (ignores if already exists for that lang)
        cursor.execute("""
            INSERT OR IGNORE INTO translations (concept_id, lang, content) 
            VALUES (?, ?, ?)
        """, (concept_id, lang_to, translation))
        
        self.conn.commit()

    def translate(self, text, target_lang):
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