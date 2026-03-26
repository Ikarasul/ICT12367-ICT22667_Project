import os
import re
import subprocess
from pathlib import Path
import sys

# FIX: ใช้ path จาก script location แทน hardcode D:/WORK
SCRIPT_DIR = Path(__file__).resolve().parent
os.chdir(str(SCRIPT_DIR))
os.makedirs('locale', exist_ok=True)

# Create en and th locale directories
print("Running makemessages...")
subprocess.run(['python', 'manage.py', 'makemessages', '-l', 'th', '-l', 'en'], check=True)

print("makemessages successful. Populating django.po with custom translations...")

# FIX: dynamic path + type: ignore เพื่อแก้ Pyre2 false positive
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from myproject.context_processors import custom_translations  # type: ignore

dummy_request = type('DummyRequest', (), {'session': {'django_language': 'th'}})()
th_dict = custom_translations(dummy_request)['t']
dummy_request_en = type('DummyRequest', (), {'session': {'django_language': 'en'}})()
en_dict = custom_translations(dummy_request_en)['t']

# Build english to thai mapping
en_to_th = {}
for key in th_dict:
    en_text = en_dict.get(key, key)
    if ' / ' in en_text:
        en_text = en_text.split(' / ')[-1]
    
    th_text = th_dict.get(key, key)
    if ' / ' in th_text:
        th_text = th_text.split(' / ')[0]

    en_to_th[en_text.replace('"', '\\"')] = th_text.replace('"', '\\"')

po_file_th = Path('locale/th/LC_MESSAGES/django.po')

with open(po_file_th, 'r', encoding='utf-8') as f:
    po_content = f.read()

# For each msgid "...", replace msgstr "" with the translated text if it exists
def replacer(match):
    msgid = match.group(1)
    if msgid in en_to_th:
        return f'msgid "{msgid}"\nmsgstr "{en_to_th[msgid]}"'
    return match.group(0)

# Pattern finds msgid "Text" followed by msgstr ""
pattern = re.compile(r'msgid\s+"([^"]+)"\r?\nmsgstr\s+""')
new_po_content = pattern.sub(replacer, po_content)

with open(po_file_th, 'w', encoding='utf-8') as f:
    f.write(new_po_content)

print("Populated TH django.po. Running compilemessages...")
subprocess.run(['python', 'manage.py', 'compilemessages'], check=True)
print("All done!")
