import datetime
import os
import platform

# =========================
# PATH FIX (IMPORTANT)
# =========================
def get_base_path():
    system = platform.system()

    if system == "Windows":
        return os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "HexSentinel")

    elif system == "Linux":
        return os.path.join(os.path.expanduser("~/.local/share"), "HexSentinel")
    
    else:
        return os.path.expanduser("~/.HexSentinel")

BASE_PATH = get_base_path()

LOG_DIR = BASE_PATH
LOG_FILE = os.path.join(LOG_DIR, "logs.txt")

logs_list = []
logs_text = None


def set_log_widget(widget):
    global logs_text
    logs_text = widget

def clear_logs():
    global logs_list

    logs_list.clear()

    # ✅ ensure folder exists
    os.makedirs(LOG_DIR, exist_ok=True)

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        pass

def clear_memory():
    global logs_list
    logs_list.clear()

def add_log(text, show_ui=True):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_log = f"[{timestamp}] {text}"

    logs_list.append(full_log)

    os.makedirs(LOG_DIR, exist_ok=True)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_log + "\n")

    if show_ui and logs_text:
        logs_text.configure(state="normal")
        logs_text.insert("end", full_log + "\n")
        logs_text.configure(state="disabled")
        logs_text.yview("end")