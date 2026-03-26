import os
import re
from pathlib import Path
import sys

# FIX: dynamic path แทน hardcode D:/WORK
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from myproject.context_processors import custom_translations  # type: ignore

dummy_request = type('DummyRequest', (), {'session': {'django_language': 'th'}})()
th_dict = custom_translations(dummy_request)['t']

dummy_request_en = type('DummyRequest', (), {'session': {'django_language': 'en'}})()
en_dict = custom_translations(dummy_request_en)['t']

BASE_DIR = SCRIPT_DIR
TEMPLATES_DIR = BASE_DIR / 'templates'

# Mapping English text to Thai text
translations_map = {}
for key in th_dict:
    th_text = th_dict[key].split(' / ')[0] if ' / ' in th_dict[key] else th_dict[key]
    en_text = en_dict[key].split(' / ')[-1] if ' / ' in en_dict[key] else en_dict[key]
    translations_map[en_text] = th_text

# Regex to find {{ t.some_key|default:"Some Text" }} or {{ t.some_key }}
pattern = re.compile(r'{{\s*t\.([a-zA-Z0-9_]+)(?:\|default:"([^"]*)")?\s*}}')

for filepath in TEMPLATES_DIR.rglob('*.html'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    def replacer(match):
        key = match.group(1)
        fallback = match.group(2)
        # Find the english text from our dict
        en_text = en_dict.get(key, fallback or key)
        if hasattr(en_text, 'split') and ' / ' in en_text:
            en_text = en_text.split(' / ')[-1]
        
        # We must escape quotes inside trans string
        en_text = en_text.replace('"', '\\"')
        return f'{{% trans "{en_text}" %}}'

    new_content, count = pattern.subn(replacer, content)
    
    # Also ensure {% load i18n %} is present
    if count > 0 and '{% load i18n %}' not in new_content:
        extends_match = re.search(r'{%\s*extends\s+[^%]+%}', new_content)
        if extends_match:
            # FIX: เก็บ pos ไว้ก่อน แก้ Pyre2 "Cannot index into str" (string slice false positive)
            pos: int = extends_match.end()
            new_content = new_content[:pos] + '\n{% load i18n %}\n' + new_content[pos:]
        else:
            new_content = '{% load i18n %}\n' + new_content

    if count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Refactored {filepath.name}: {count} tags replaced.")

print("Template refactoring completed.")
