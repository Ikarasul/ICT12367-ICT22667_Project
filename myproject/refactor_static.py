import os
import re
from pathlib import Path

# FIX: dynamic path แทน hardcode D:/WORK
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / 'templates'
STATIC_CSS_DIR = BASE_DIR / 'static' / 'css'
STATIC_JS_DIR = BASE_DIR / 'static' / 'js'

os.makedirs(STATIC_CSS_DIR, exist_ok=True)
os.makedirs(STATIC_JS_DIR, exist_ok=True)

for filepath in TEMPLATES_DIR.rglob('*.html'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    css_pattern = re.compile(r'<style[^>]*>(.*?)</style>', re.DOTALL | re.IGNORECASE)
    js_pattern = re.compile(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', re.DOTALL | re.IGNORECASE)
    
    css_matches = css_pattern.findall(content)
    js_matches = js_pattern.findall(content)

    if not css_matches and not js_matches:
        continue

    rel_path = filepath.relative_to(TEMPLATES_DIR)
    file_prefix = str(rel_path).replace('\\', '_').replace('/', '_').replace('.html', '')

    has_static_load_regex = re.search(r'{%\s*load\s+static\s*%}', content)
    
    if not has_static_load_regex:
        extends_match = re.search(r'{%\s*extends\s+[^%]+%}', content)
        if extends_match:
            # FIX: เก็บ pos ก่อน แก้ Pyre2 "Cannot index into str" false positive
            pos: int = extends_match.end()
            content = content[:pos] + '\n{% load static %}\n' + content[pos:]
        else:
            content = '{% load static %}\n' + content

    if css_matches:
        combined_css = "\n".join(css_matches)
        css_file_path = STATIC_CSS_DIR / f"{file_prefix}.css"
        with open(css_file_path, 'w', encoding='utf-8') as f:
            f.write(combined_css.strip())
        
        css_link = f'<link rel="stylesheet" href="{{% static \'css/{file_prefix}.css\' %}}">'
        
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        if '{% block extra_head %}' in content:
            content = content.replace('{% block extra_head %}', f'{{% block extra_head %}}\n{css_link}')
        else:
            if '</head>' in content:
                content = content.replace('</head>', f'{css_link}\n</head>')
            else:
                load_static_match = re.search(r'{%\s*load\s+static\s*%}', content)
                if load_static_match:
                    pos2: int = load_static_match.end()
                    content = content[:pos2] + f'\n{css_link}\n' + content[pos2:]

    if js_matches:
        combined_js = "\n".join(js_matches)
        js_file_path = STATIC_JS_DIR / f"{file_prefix}.js"
        with open(js_file_path, 'w', encoding='utf-8') as f:
            f.write(combined_js.strip())
        
        js_link = f'<script src="{{% static \'js/{file_prefix}.js\' %}}"></script>'
        content = js_pattern.sub('', content)
        
        if '{% block extra_js %}' in content:
            content = content.replace('{% block extra_js %}', f'{{% block extra_js %}}\n{js_link}')
        elif '</body>' in content:
            content = content.replace('</body>', f'{js_link}\n</body>')
        else:
            last_endblock = content.rfind('{% endblock %}')
            if last_endblock != -1:
                pos3: int = last_endblock
                content = content[:pos3] + f'\n{js_link}\n' + content[pos3:]
            else:
                content += f'\n{js_link}'

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Refactored {rel_path} -> {file_prefix}.css/js")
