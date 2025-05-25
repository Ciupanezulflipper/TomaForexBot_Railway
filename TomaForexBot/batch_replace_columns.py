import os
import re

# List of column name replacements
REPLACEMENTS = [
    (r'ema9', 'ema9'),
    (r'ema21', 'ema21'),
    (r'rsi', 'rsi'),
    (r'close', 'close'),
    (r'open', 'open'),
    (r'high', 'high'),
    (r'low', 'low'),
    (r'volume', 'volume'),
    (r'pattern', 'pattern'),
]

# Extensions and folders to scan
PY_EXT = '.py'
EXCLUDE = {'__pycache__', '.git', 'env', 'venv'}

def batch_replace_columns(folder_path):
    for root, dirs, files in os.walk(folder_path):
        # Skip excluded dirs
        dirs[:] = [d for d in dirs if d not in EXCLUDE]
        for fname in files:
            if fname.endswith(PY_EXT):
                fpath = os.path.join(root, fname)
                with open(fpath, encoding='utf-8') as f:
                    content = f.read()
                orig_content = content
                for old, new in REPLACEMENTS:
                    content = re.sub(old, new, content)
                if content != orig_content:
                    print(f"[UPDATE] {fpath}")
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.write(content)

if __name__ == '__main__':
    # Replace with your actual project folder
    batch_replace_columns(r'C:\Users\tomag\Documents\TomaForexBot_Railway\TomaForexBot')
