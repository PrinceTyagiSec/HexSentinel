import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "signatures.db")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signatures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            magic_hex TEXT UNIQUE,
            extension TEXT,
            category TEXT,
            risk_level TEXT
        )
    """)

    conn.commit()
    conn.close()


def insert_sample_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    data = [
    ("25504446", "pdf", "document", "low"),
    ("4D5A", "exe", "executable", "high"),
    ("4D5A", "dll", "executable", "high"),
    ("FFD8FF", "jpg", "image", "low"),
    ("FFD8FF", "jpeg", "image", "low"),
    ("89504E47", "png", "image", "low"),
    ("47494638", "gif", "image", "low"),
    ("424D", "bmp", "image", "low"),
    ("504B0304", "zip", "archive", "medium"),
    ("52617221", "rar", "archive", "medium"),
    ("377ABCAF271C", "7z", "archive", "medium"),
    ("75737461", "tar", "archive", "low"),
    ("1F8B08", "gz", "archive", "low"),
    ("66747970", "mp4", "media", "low"),
    ("52494646", "avi", "media", "low"),
    ("6D6F6F76", "mov", "media", "low"),
    ("1A45DFA3", "mkv", "media", "low"),
    ("494433", "mp3", "audio", "low"),
    ("52494646", "wav", "audio", "low"),
    ("664C6143", "flac", "audio", "low"),
    ("D0CF11E0", "doc", "document", "low"),
    ("D0CF11E0", "xls", "document", "low"),
    ("D0CF11E0", "ppt", "document", "low"),
    ("504B0304", "docx", "document", "low"),
    ("504B0304", "xlsx", "document", "low"),
    ("504B0304", "pptx", "document", "low"),
    ("43443030", "iso", "disk", "medium"),
    ("43443030", "img", "disk", "medium"),
    ("53514C69", "sql", "database", "low"),
    ("53514C69", "db", "database", "low"),
    ("53514C69", "sqlite", "database", "low"),
    ("504B0304", "apk", "android", "medium"),
    ("504B0304", "jar", "java", "medium"),
    ("CAFEBABE", "class", "java", "low"),
    ("420D0D0A", "pyc", "python", "low"),
    ("7F454C46", "elf", "executable", "high"),
    ("38425053", "psd", "image", "low"),
    ("49492A00", "tif", "image", "low"),
    ("4D4D002A", "tiff", "image", "low"),
    ("52494646", "webp", "image", "low"),
    ("465753", "swf", "flash", "medium"),
    ("7B5C727466", "rtf", "document", "low"),
    ("52656365", "eml", "email", "low"),
    ("D0CF11E0", "msg", "email", "low"),
    ("D4C3B2A1", "pcap", "network", "medium"),
    ("A1B2C3D4", "cap", "network", "medium"),
    ("00000000", "dat", "unknown", "unknown"),
    ("00000000", "bin", "unknown", "unknown"),
    ("00000000", "tmp", "unknown", "unknown"),
]
    cursor.executemany("""
        INSERT OR IGNORE INTO signatures (magic_hex, extension, category, risk_level)
        VALUES (?, ?, ?, ?)
    """,data) 

    conn.commit()
    conn.close()

def get_file_type(magic_hex):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT extension, category, risk_level 
        FROM signatures 
        WHERE ? LIKE magic_hex || '%'
        LIMIT 1
    """, (magic_hex,))

    result = cursor.fetchone()

    conn.close()
    return result

def search_signatures(query):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT magic_hex, extension, category, risk_level
        FROM signatures
        WHERE extension LIKE ?
        LIMIT 10
    """, (query + "%",))

    results = cursor.fetchall()
    conn.close()

    return results