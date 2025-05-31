import json
import random
import time
import os
from utils.currency import get_balance, update_currency

STATE_FILE = "data/challenge_state.json"

DAILY_CHALLENGES = [
    "Apaga todas las luces innecesarias durante una hora.",
    "Da un paseo corto en lugar de un corto viaje en coche.",
    "Come una comida vegetariana.",
    "Recicla una botella de plástico.",
    "Comparte un consejo ecológico con un amigo."
]

HOURLY_CHALLENGES = [
    "Desconecta un dispositivo que no estés usando.",
    "Rellena una botella de agua reutilizable.",
    "Abre una ventana en lugar de encender el aire acondicionado.",
    "Recoge una pieza de basura.",
    "Tómate un descanso de 5 minutos lejos de las pantallas."
]

REWARD_AMOUNT = 25
PENALTY_AMOUNT = 30
MIN_CLAIM_TIME = 300 

def load_json(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

COOLDOWNS = {
    "daily": 86400,   
    "hourly": 3600    
}

def format_seconds_to_hms(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    parts = []
    if hours > 0:
        parts.append(f"{hours} hora{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minuto{'s' if minutes != 1 else ''}")
    if secs > 0:
        parts.append(f"{secs} segundo{'s' if secs != 1 else ''}")
    return " ".join(parts)

def assign_challenge(user_id, type_):
    state = load_json(STATE_FILE)
    now = time.time()
    user_id_str = str(user_id)

    if type_ not in ["daily", "hourly"]:
        return None, "Tipo de reto inválido."

    last_claim_key = f"last_{type_}_claim"
    last_claim = state.get(user_id_str, {}).get(last_claim_key, 0)

    cooldown = COOLDOWNS[type_]
    time_since_claim = now - last_claim

    if time_since_claim < cooldown:
        remaining = int(cooldown - time_since_claim)
        if type_ == "daily":
            formatted = format_seconds_to_hms(remaining)
            return None, f"Aún debes esperar {formatted} para el próximo reto {type_}."
        else:
            return None, f"Aún debes esperar {remaining // 60} minutos y {remaining % 60} segundos para el próximo reto {type_}."

    if user_id_str not in state:
        state[user_id_str] = {}

    current = state[user_id_str].get("current_challenge")
    if current and not current.get("claimed") and current.get("type") == type_:
        challenge_text = current.get("challenge")
        save_json(STATE_FILE, state)
        return challenge_text, "Ya tienes un reto activo. ¡Termínalo para poder reclamar!"

    if type_ == "daily":
        challenge_text = random.choice(DAILY_CHALLENGES)
    else:
        challenge_text = random.choice(HOURLY_CHALLENGES)

    state[user_id_str]["current_challenge"] = {
        "type": type_,
        "challenge": challenge_text,
        "assigned_at": now,
        "claimed": False
    }
    save_json(STATE_FILE, state)
    return challenge_text, "Reto asignado correctamente."

def claim_challenge(user_id, type_):
    state = load_json(STATE_FILE)
    user_id_str = str(user_id)

    if user_id_str not in state or "current_challenge" not in state[user_id_str]:
        return "No tienes un reto activo para reclamar."

    challenge_data = state[user_id_str]["current_challenge"]
    if challenge_data["type"] != type_:
        return f"No tienes un reto {type_} activo para reclamar."

    if challenge_data["claimed"]:
        return "Ya reclamaste este reto."

    elapsed = time.time() - challenge_data["assigned_at"]

    if elapsed < MIN_CLAIM_TIME:
        update_currency(user_id, -PENALTY_AMOUNT)
        result = f"Reclamas muy rápido. Se detectó posible engaño. -{PENALTY_AMOUNT} eco-coins."
    else:
        update_currency(user_id, REWARD_AMOUNT)
        result = f"Reto completado, ganaste +{REWARD_AMOUNT} eco-coins."


    challenge_data["claimed"] = True
    state[user_id_str]["last_" + type_ + "_claim"] = time.time()

    save_json(STATE_FILE, state)
    return result

