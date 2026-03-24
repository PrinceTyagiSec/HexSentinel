import os
from core.database import get_file_type
from core.file_handler import get_magic_number, get_extension, read_file_bytes
import math
from collections import Counter
import re
from core.yara_scanner import scan_with_yara

def calculate_entropy(data):
    if not data:
        return 0

    freq = Counter(data)
    entropy = 0

    for count in freq.values():
        p = count / len(data)
        entropy -= p * math.log2(p)

    return entropy


def extract_strings(data):
    return re.findall(rb"[ -~]{4,}", data)

# def analyze_file(file_path):

def analyze_file(file_path):
    file_name = os.path.basename(file_path)
    extension = file_name.split(".")[-1].lower()

    data = read_file_bytes(file_path)

    magic_hex = get_magic_number(file_path)

    magic_key = (magic_hex or "")[:8]
    db_result = get_file_type(magic_key)

    entropy = calculate_entropy(data)
    strings = extract_strings(data[:100000])  # limit for performance

    risk_score = 0
    reasons = []

    yara_results = scan_with_yara(file_path)

    suspicious_matches = []
    filetype_matches = []

    for r in yara_results:
        rule_name = r.get("rule", "")

        # Collect suspicious
        if "Suspicious" in rule_name:
            suspicious_matches.append(rule_name)

            # 🔥 Try extracting language from suspicious rule
            if "PHP" in rule_name:
                filetype_matches.append("FileType_PHP")
            elif "Python" in rule_name:
                filetype_matches.append("FileType_Python")
            elif "Bash" in rule_name:
                filetype_matches.append("FileType_Bash")
            elif "Perl" in rule_name:
                filetype_matches.append("FileType_Perl")
            elif "Ruby" in rule_name:
                filetype_matches.append("FileType_Ruby")

        elif "FileType" in rule_name:
            filetype_matches.append(rule_name)

    # Apply scoring ONLY for suspicious rules
    if suspicious_matches:
        risk_score += 3
        reasons.append(f"Suspicious patterns: {suspicious_matches}")

    # Optional: show detected file type from YARA
    yara_detected_ext = None
    detected_format = None

    if filetype_matches:
        raw_type = filetype_matches[0].replace("FileType_", "").lower()

        # 🔥 Format (REAL type)
        detected_format = raw_type.upper()

        # 🔥 Extension guess (optional mapping)
        FORMAT_TO_EXT = {
            "pe": "exe",
            "elf": "elf",
            "zip": "zip"
        }

        yara_detected_ext = FORMAT_TO_EXT.get(raw_type, raw_type)

    # Entropy check
    if entropy > 7.5:
        risk_score += 2
        reasons.append("High entropy (packed/encrypted file)")

    # String check
    if len(strings) > 50:
        risk_score += 1
        reasons.append("High embedded strings")


    if db_result:
        db_detected_ext, category, risk = db_result
        # 🔥 Set format from DB
        if not detected_format:
            detected_format = db_detected_ext.upper()

        if yara_detected_ext:
            detected_ext = yara_detected_ext
        else:
            detected_ext = db_detected_ext

        if detected_ext == extension:
            status = "SAFE"
            reasons.append("Extension matches file content")
        else:
            status = "SUSPICIOUS"
            reasons.append(f"Extension '{extension}' != '{detected_ext}'")

    elif yara_detected_ext:
        detected_ext = yara_detected_ext
        category = "script"
        risk = "low"
        status = "SAFE"
        reasons.append("Detected via YARA (no magic number)")

    else:
        detected_ext = extension
        detected_format = "UNKNOWN"   # 🔥 ADD THIS
        category = "unknown"
        risk = "unknown"
        status = "UNKNOWN"
        reasons.append("No signature found")

    # Final decision
    if suspicious_matches:
        status = "MALICIOUS"

    elif risk_score >= 4:
        status = "MALICIOUS"

    elif risk_score >= 2:
        if status != "SAFE":
            status = "SUSPICIOUS"

    return {
        "detected_format": detected_format,
        "file_name": file_name,
        "extension": extension,
        "magic_number": magic_hex[:8],
        "detected": detected_ext,
        "status": status,
        "category": category,
        "risk": risk,
        "risk_score": risk_score,
        "yara": yara_results,
        "reason": "\n".join(reasons)
    }


def detect_file(file_path):
    ext = get_extension(file_path)
    magic = get_magic_number(file_path)

    # Query DB for known magic
    db_result = get_file_type(magic[:8])

    if db_result:
        detected_ext, category, risk = db_result
        magic_type = detected_ext
    else:
        detected_ext = None
        magic_type = None
        category = "unknown"
        risk = "unknown"

    # ---------------------------
    # LOGIC (Improved)
    # ---------------------------

    if magic_type and ext == magic_type:
        status = "Legit"
        reason = "Extension and magic number match"

    elif magic_type and ext != magic_type:
        status = "Suspicious"
        reason = "Extension does not match file signature"

    else:
        status = "Unknown"
        reason = "No matching signature found"

    return {
        
        "magic_number": magic[:8],
        "extension": ext,
        "detected_type": detected_ext,
        "status": status,
        "category": category,
        "risk": risk,
        "reason": reason
    }