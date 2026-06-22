import os
import re

DIR = "/home/leduc1009/BTL_AIT2004-2"
EXCLUDES = {'.git', 'node_modules', '__pycache__', '.venv', 'backups'}
BINARY_EXTS = {'.onnx', '.png', '.jpg', '.jpeg', '.gif', '.mp4', '.sqlite', '.db', '.pyc', '.ico', '.svg', '.lock'}

replacements = [
    ("license_plate_recognition", "license_plate_recognition"),
    ("LicensePlateRecognition", "LicensePlateRecognition"),
    ("license_plate_extract", "license_plate_extract"),
    ("LicensePlateExtract", "LicensePlateExtract"),
    ("lpr_system", "lpr_system"),
    ("LprSystem", "LprSystem"),
    ("license_plate_detection", "license_plate_detection"),
    ("LicensePlateDetection", "LicensePlateDetection"),
    ("license_plate_embedding", "license_plate_embedding"),
    ("LicensePlateEmbedding", "LicensePlateEmbedding"),
    ("license_plate_id", "license_plate_id"),
    ("LicensePlateId", "LicensePlateId"),
    ("lpr", "lpr"),
    ("Lpr", "Lpr"),
    ("Biển số", "Biển số"),
    ("biển số", "biển số"),
    ("Biển Số", "Biển Số"),
]

# For standalone or partial matches like `license_plate`, `LicensePlate`
# We will use regex to catch variables
regex_replacements = [
    (re.compile(r'\bface\b'), 'license_plate'),
    (re.compile(r'\bFace\b'), 'LicensePlate'),
    (re.compile(r'license_plate_'), 'license_plate_'),
    (re.compile(r'_license_plate'), '_license_plate'),
    (re.compile(r'\bFace(?=[A-Z])'), 'LicensePlate'), # LicensePlateModel -> LicensePlateModel
]

def rename_paths():
    # To safely prune and rename, we'll collect all paths first with topdown=True
    all_files = []
    all_dirs = []
    for root, dirs, files in os.walk(DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDES and not d.startswith('.git')]
        for d in dirs:
            all_dirs.append(os.path.join(root, d))
        for f in files:
            all_files.append(os.path.join(root, f))
            
    # Rename files first
    for old_path in all_files:
        name = os.path.basename(old_path)
        root = os.path.dirname(old_path)
        new_name = name
        for old, new in replacements:
            new_name = new_name.replace(old, new)
        for rx, new in regex_replacements:
            new_name = rx.sub(new, new_name)
            
        if new_name != name:
            new_path = os.path.join(root, new_name)
            if not os.path.exists(new_path):
                os.rename(old_path, new_path)
                
    # Rename dirs in reverse order (longest paths first)
    all_dirs.sort(key=len, reverse=True)
    for old_path in all_dirs:
        name = os.path.basename(old_path)
        root = os.path.dirname(old_path)
        new_name = name
        for old, new in replacements:
            new_name = new_name.replace(old, new)
        for rx, new in regex_replacements:
            new_name = rx.sub(new, new_name)
            
        if new_name != name:
            new_path = os.path.join(root, new_name)
            if not os.path.exists(new_path):
                os.rename(old_path, new_path)

def refactor_content():
    for root, dirs, files in os.walk(DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDES and not d.startswith('.git')]
        for name in files:
            _, ext = os.path.splitext(name)
            if ext.lower() in BINARY_EXTS:
                continue
            
            filepath = os.path.join(root, name)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                continue # Skip if unreadable (e.g., binary without ext)
                
            new_content = content
            for old, new in replacements:
                new_content = new_content.replace(old, new)
            for rx, new in regex_replacements:
                new_content = rx.sub(new, new_content)
                
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)

if __name__ == "__main__":
    rename_paths()
    refactor_content()
    # Run a second pass of rename paths because sometimes renaming a dir means we need to do it again? 
    # topdown=False already handles this since we rename children first, then parent.
    # Wait, if we rename children first, the root path for them was the old parent name. 
    # os.walk yields the old root. So os.path.join(root, name) is valid!
    print("Refactoring complete.")
