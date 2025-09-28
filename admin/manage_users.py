from config import load_users, save_users, is_admin

def add_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)
        return True
    return False

def remove_user(user_id):
    users = load_users()
    if user_id in users:
        users.remove(user_id)
        save_users(users)
        return True
    return False

def list_users():
    return load_users()

def is_super_admin(user_id):
    # صلاحية الادمن الأعلى (الذي أنشأ البوت أو من ENV)
    from config import ADMINS
    return int(user_id) in ADMINS
