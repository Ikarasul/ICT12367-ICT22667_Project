import os
import re

STITCH_DIR = r"C:\Users\ilike\Downloads\stitch_customer_login (1)\stitch_customer_login"
TEMPLATES_DIR = r"D:\WORK\Pro\myproject\templates"

# Map exactly which stitch folder goes to which template file
MAPPING = {
    "tours.html": "balanced_tours_marketplace",
    "login.html": "updated_balanced_login",
    "register.html": "balanced_customer_registration",
    "booking.html": "balanced_booking_checkout",
    "dashboard.html": "balanced_staff_dashboard",
    "my_tickets.html": "balanced_my_tickets",
    "audit_log.html": "balanced_database_management",
    "admin/table_list.html": "table_data_view_staff_admin", # Or balanced_table_data_view? Let's check both
    "admin/table_data.html": "balanced_table_data_view",
    "admin/table_form.html": "balanced_table_form_entry",
}

def extract_content(html):
    # Extract style block
    style_match = re.search(r'<style>(.*?)</style>', html, re.DOTALL)
    style = style_match.group(1) if style_match else ""
    
    # Extract main body content, we prefer everything inside <body>, but exclude <nav> and <footer> if possible, 
    # since base.html already has navbar and footer.
    # Actually, Stitch files have <nav>, <main>, <footer> inside <body>. We only want <main>.
    main_match = re.search(r'<main[^>]*>(.*?)</main>', html, re.DOTALL)
    
    if main_match:
        # Keep the <main> tag itself to preserve its classes, or just its content?
        # Let's keep the <main> tag by matching the whole thing.
        main_full_match = re.search(r'(<main[^>]*>.*?</main>)', html, re.DOTALL)
        content = main_full_match.group(1)
    else:
        # Fallback to body content
        body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL)
        content = body_match.group(1) if body_match else html

    return style, content

def get_best_stitch_folder(template_name, preferred_folder):
    if os.path.exists(os.path.join(STITCH_DIR, preferred_folder, "code.html")):
        return preferred_folder
    # try without balanced_
    alt = preferred_folder.replace("balanced_", "")
    if os.path.exists(os.path.join(STITCH_DIR, alt, "code.html")):
        return alt
    # try with staff_admin
    for d in os.listdir(STITCH_DIR):
        if "table_list" in template_name and "table_data_view" in d:
            return d
    return preferred_folder

def build_django_template(template_name, style, content):
    # Some files need {% extends 'base.html' %} and some might need {% extends 'admin/base_site.html' %} ?
    # The user's prompt shows they are in `admin/` but maybe they just use base.html
    # We will use base.html for all to be safe, or just insert the raw HTML if they are stand-alone?
    # Usually Django templates have base.html. Let's use it.
    
    # Check if there are form elements, we should inject {% csrf_token %} right after <form ...>
    content = re.sub(r'(<form[^>]*>)', r'\1\n            {% csrf_token %}', content)
    
    # Keep the original string as much as possible but wrapped in Django tags
    
    res = f"""{{% extends 'base.html' %}}
{{% load static %}}
{{% block title %}}{template_name.replace('.html', '').title()} - TourCompanyDB{{% endblock %}}

{{% block extra_head %}}
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<style>
{style}
</style>
{{% endblock %}}

{{% block content %}}
{content}
{{% endblock %}}
"""
    return res

for target_file, stitch_folder_hint in MAPPING.items():
    stitch_folder = get_best_stitch_folder(target_file, stitch_folder_hint)
    stitch_file = os.path.join(STITCH_DIR, stitch_folder, "code.html")
    
    target_path = os.path.join(TEMPLATES_DIR, target_file.replace("/", "\\"))
    
    if os.path.exists(stitch_file):
        with open(stitch_file, "r", encoding="utf-8") as f:
            html = f.read()
            
        style, content = extract_content(html)
        final_html = build_django_template(target_file, style, content)
        
        # Ensure dir exists
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(final_html)
        print(f"Replaced {target_file} using {stitch_folder}")
    else:
        print(f"COULD NOT FIND stitch file for {target_file} (tried {stitch_folder})")

