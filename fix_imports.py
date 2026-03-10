import os
import re

files_to_edit = [
    "Backend/cards.py",
    "Backend/settings_routes.py",
    "Backend/notifications.py",
    "Backend/audit.py",
    "Backend/services.py"
]

def add_customer_import(content):
    # Check if we need to add Customer to the imports from Backend.models
    if "from Backend.models import" in content and "Customer" not in content:
        content = re.sub(r'from Backend\.models import ', r'from Backend.models import Customer, ', content)
    return content

for fb in files_to_edit:
    fp = os.path.join(r"c:\Users\USER\Documents\Final_Sentinel_Integrations\genai_sentinel_banking_integration", fb)
    if not os.path.exists(fp):
        continue
    with open(fp, "r", encoding="utf-8") as f:
        content = f.read()
    
    new_content = add_customer_import(content)
    
    with open(fp, "w", encoding="utf-8") as f:
        f.write(new_content)
