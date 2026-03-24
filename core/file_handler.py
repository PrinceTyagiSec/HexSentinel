import os

def get_extension(file_path):
    return os.path.splitext(file_path)[1].lower().strip(".")


def get_magic_number(file_path, num_bytes=16):
    with open(file_path, "rb") as f:
        file_bytes = f.read(num_bytes)
        return file_bytes.hex().upper()
    
def read_file_bytes(file_path):
    try:
        with open(file_path, "rb") as f:
            return f.read()
    except Exception:
        return b""