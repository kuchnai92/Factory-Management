import json
import os
from datetime import datetime

FILE_NAME = "factory_data.json"
BACKUP_DIR = "data" # This creates the data folder next to your app

products = []
labourers = []
daily_ledger = []
history_payments = []

data_version = 1 

def load_data():
    global products, labourers, daily_ledger, history_payments, data_version
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, "r", encoding="utf-8") as f:
                data = json.load(f)
                products = data.get("products", [])
                labourers = data.get("labourers", [])
                daily_ledger = data.get("daily_ledger", [])
                history_payments = data.get("history_payments", [])
                data_version += 1 
        except: pass

# --- NEW FEATURE: Smart Rolling Backup System ---
def create_backup(data):
    if not os.path.exists(BACKUP_DIR): 
        os.makedirs(BACKUP_DIR)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = os.path.join(BACKUP_DIR, f"backup_{timestamp}.json")
    
    with open(backup_file, "w", encoding="utf-8") as f: 
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    # Reads all backups and strictly keeps only the last 10
    files = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith("backup_") and f.endswith(".json")])
    while len(files) > 10: 
        oldest = files.pop(0)
        os.remove(os.path.join(BACKUP_DIR, oldest))

def save_data():
    global data_version; data_version += 1 
    data = {"products": products, "labourers": labourers, "daily_ledger": daily_ledger, "history_payments": history_payments}
    
    # --- 🔥 NEW: Power-Cut Protection (Atomic Write) ---
    temp_file = FILE_NAME + ".tmp"
    
    # Step 1: Write all data safely to a temporary invisible file first
    with open(temp_file, "w", encoding="utf-8") as f: 
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    # Step 2: Instantly swap the temp file with the real file
    # If power cuts during Step 1, the real file is completely untouched!
    os.replace(temp_file, FILE_NAME)
    
    create_backup(data) # Triggers the backup automatically

load_data()