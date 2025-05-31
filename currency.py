import json
import os

CURRENCY_FILE = "currency.json"

def load_balances():
    if not os.path.exists(CURRENCY_FILE):
        with open(CURRENCY_FILE, "w") as f:
            json.dump({}, f)
    with open(CURRENCY_FILE, "r") as f:
        return json.load(f)

def save_balances(balances):
    with open(CURRENCY_FILE, "w") as f:
        json.dump(balances, f, indent=2)

def get_balance(user_id):
    balances = load_balances()
    return balances.get(str(user_id), 0)

def update_currency(user_id, amount):
    balances = load_balances()
    user_id_str = str(user_id)
    balances.setdefault(user_id_str, 0)
    balances[user_id_str] = max(0, balances[user_id_str] + amount)
    save_balances(balances)
    return balances[user_id_str]
