import os

files_to_edit = [
    "Backend/notifications.py",
    "Backend/settings_routes.py",
    "Backend/audit.py",
    "Backend/services.py",
]

for fb in files_to_edit:
    fp = os.path.join(r"c:\Users\USER\Documents\Final_Sentinel_Integrations\genai_sentinel_banking_integration", fb)
    if not os.path.exists(fp):
        continue
    with open(fp, "r", encoding="utf-8") as f:
        content = f.read()
        
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith("from Backend.models import "):
            if "Customer" not in line:
                lines[i] = line.replace("from Backend.models import ", "from Backend.models import Customer, ")
    
    with open(fp, "w", encoding="utf-8") as f:
        f.write('\n'.join(lines))
