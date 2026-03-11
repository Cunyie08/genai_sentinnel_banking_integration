import os
import re

files_to_edit = [
    "Backend/admin.py",
]

def refactor_content(content):
    # Common type hint
    content = re.sub(r'current_user:\s*User\s*=\s*Depends', r'current_user: Customer = Depends', content)
    content = re.sub(r'admin:\s*User\s*=\s*Depends', r'admin: Customer = Depends', content)
    content = re.sub(r'user:\s*User\s*=\s*Depends', r'user: Customer = Depends', content)
    
    # Imports
    content = re.sub(r'\bUser,\s*', '', content)  # from ... import User, Customer
    content = re.sub(r',\s*User\b', '', content)  # from ... import Customer, User
    content = re.sub(r'from Backend\.models import User\b', r'from Backend.models import Customer', content)
    content = re.sub(r'from Backend\.models import User as UserTable', r'from Backend.models import Customer', content)
    content = re.sub(r'from Backend\.models import User, ', r'from Backend.models import Customer, ', content)
    content = re.sub(r'\[User\]', r'[Customer]', content)
    
    # ID usages
    content = re.sub(r'current_user\.user_id', r'current_user.customer_id', content)
    content = re.sub(r'user\.user_id', r'user.customer_id', content)
    content = re.sub(r'admin\.user_id', r'admin.customer_id', content)
    content = re.sub(r'UserSettings\.user_id', r'UserSettings.customer_id', content)
    content = re.sub(r'Notification\.user_id', r'Notification.customer_id', content)

    # Some variables named `user` might be left alone, but let's check `select(User)`
    content = re.sub(r'select\(User\)', r'select(Customer)', content)
    content = re.sub(r'select\(UserTable\)', r'select(Customer)', content)
    content = re.sub(r'UserTable\.customer_id', r'Customer.customer_id', content)
    content = re.sub(r'UserTable\.user_id', r'Customer.customer_id', content) # if any
    content = re.sub(r'User\.user_id', r'Customer.customer_id', content)
    content = re.sub(r'User\.email', r'Customer.email', content)
    
    # Endpoints with userId
    content = re.sub(r'userId', r'customerId', content)
    content = re.sub(r'user_id', r'customer_id', content)
    
    # Specific edge case in app.py
    content = content.replace("current_user: User", "current_user: Customer")
    content = content.replace("current_user.user_id", "current_user.customer_id")
    
    return content

for fb in files_to_edit:
    fp = os.path.join(r"c:\Users\USER\Documents\Final_Sentinel_Integrations\genai_sentinel_banking_integration", fb)
    if not os.path.exists(fp):
        print(f"Not found: {fp}")
        continue
    with open(fp, "r", encoding="utf-8") as f:
        content = f.read()
    
    new_content = refactor_content(content)
    
    with open(fp, "w", encoding="utf-8") as f:
        f.write(new_content)
        
    print(f"Refactored: {fp}")
