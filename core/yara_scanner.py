import yara
import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# ✅ Correct path for both dev + EXE
RULES_PATH = resource_path(os.path.join("yara_rules", "rules.yar"))

rules = yara.compile(filepath=RULES_PATH)

def scan_with_yara(file_path):
    matches = rules.match(file_path)

    results = []

    for match in matches:
        results.append({
            "rule": match.rule,
            "tags": match.tags,
            "meta": match.meta
        })

    return results