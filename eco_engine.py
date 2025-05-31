import json
import os

DATA_PATH = "data/eco_data.json"

default_questions = [
    {
        "id": "car_km",
        "question": "¿Cuántos kilómetros conduces por semana?",
        "coefficient": 0.192
    },
    {
        "id": "flights",
        "question": "¿Cuántos vuelos cortos (menos de 3 horas) realizas al año?",
        "coefficient": 250
    },
    {
        "id": "electricity",
        "question": "¿Cuál es tu consumo mensual de electricidad en kWh?",
        "coefficient": 0.233
    },
    {
        "id": "meat",
        "question": "¿Cuántas comidas con carne consumes por semana?",
        "coefficient": 2.5
    }
]

def load_eco_data():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_eco_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def start_session(user_id):
    data = load_eco_data()
    data[str(user_id)] = {"step": 0, "answers": {}}
    save_eco_data(data)
    return default_questions[0]["question"]

def handle_answer(user_id, answer):
    data = load_eco_data()
    user_data = data.get(str(user_id))
    if user_data is None:
        return None, "No hay sesión activa. Usa el comando !eco para comenzar."

    step = user_data["step"]
    try:
        val = float(answer.replace(",", ".")) 
        if val < 0:
            return None, "Por favor, ingresa un número positivo."
    except ValueError:
        return None, "Por favor, ingresa un número válido."

    question = default_questions[step]
    qid = question["id"]

    troll_limits = {
        "car_km": 10000,
        "flights": 200,
        "electricity": 3000,
        "meat": 140
    }
    impossible_limits = {
        "car_km": 100000,
        "flights": 10000,
        "electricity": 100000,
        "meat": 1000
    }

    if val > impossible_limits[qid]:
        return None, (
            "🧢 Eso es físicamente imposible. Por favor, verifica tu respuesta."
        )

    if val > troll_limits[qid]:
        warned = user_data.get("warned", False)
        if not warned:
            user_data["warned"] = True
            save_eco_data(data)
            return None, (
                "El cambio climático no lo causamos nosotros...\n"
                "¡El cambio climático lo causaste tú con esos números! "
                "Si es cierto, wow. Si no... inténtalo de nuevo "
            )

    user_data["answers"][qid] = val
    user_data["step"] += 1

    if user_data["step"] >= len(default_questions):
        answers = user_data["answers"]


        car_annual = answers["car_km"] * 52 * 0.192 / 1000
        flights_annual = answers["flights"] * 250 / 1000
        electricity_annual = answers["electricity"] * 12 * 0.233 / 1000
        meat_annual = answers["meat"] * 52 * 2.5 / 1000

        total = car_annual + flights_annual + electricity_annual + meat_annual

        data[str(user_id)] = {"completed": True, "total": total}
        save_eco_data(data)

        if total < 2:
            feedback = (
                "Tu huella anual de CO₂ es baja, ¡bien hecho! "
                "Sigue manteniendo estos hábitos y considera apoyar iniciativas de conservación."
            )
        elif total < 5:
            feedback = (
                "Tu huella de CO₂ es moderada. Hay áreas donde puedes mejorar, "
                "como reducir vuelos o consumo de carne. "
                "Pequeños cambios pueden marcar una gran diferencia."
            )
        else:
            feedback = (
                "Tu huella de CO₂ es alta y representa un riesgo para el planeta. "
                "Te recomendamos reducir viajes en avión, usar transporte sostenible, "
                "y disminuir el consumo de productos animales. "
                "Cada acción cuenta para proteger el clima."
            )

        result = f"Tu huella estimada de CO₂ anual es **{total:.2f} toneladas**.\n{feedback}"
        return None, result
    else:
        save_eco_data(data)
        return default_questions[user_data["step"]]["question"], None


