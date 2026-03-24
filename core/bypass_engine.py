import os


def apply_bypass(file_path, magic_hex, extension, output_path):
    try:
        # Convert hex → bytes
        magic_bytes = bytes.fromhex(magic_hex)

        # Read original file
        with open(file_path, "rb") as f:
            original_data = f.read()

        # 🔥 BYPASS TECHNIQUES (SIMULATION)

        # 1. Replace magic header
        # Preserve file after header replacement
        if len(original_data) > 8:
            modified = magic_bytes + original_data[8:]
        else:
            modified = magic_bytes

        # 2. Add junk data (noise)
        modified = magic_bytes + original_data

        # 3. Add random padding
        modified += os.urandom(20)

        # Write modified file
        with open(output_path, "wb") as f:
            f.write(modified)

        return True

    except Exception as e:
        print("Bypass Error:", e)
        return False