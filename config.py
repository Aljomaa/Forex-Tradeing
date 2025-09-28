import os
import json
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TWELVE_API_KEY = os.getenv("TWELVE_API_KEY")
USERS_FILE = "allowed_users.json"
ADMINS_ENV = os.getenv("ADMINS", "")

# دعم أكثر من أدمن من ENV (مفصولة بفواصل)
ADMINS = [int(uid.strip()) for uid in ADMINS_ENV.split(",") if uid.strip().isdigit()]
if not ADMINS:
    ADMINS = [6849903309]  # الافتراضي: أنت فقط

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump(ADMINS, f)

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def is_admin(user_id):
    return int(user_id) in ADMINS
