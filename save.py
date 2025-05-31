import json
import os

SAVE_FILE = "user_data.json"

def load_user_data():
    if not os.path.exists(SAVE_FILE):
        return {}
    with open(SAVE_FILE, "r") as f:
        return json.load(f)

def save_user_data(data):
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user_progress(user_id):
    data = load_user_data()
    user_id_str = str(user_id)

    
    if user_id_str not in data:
        data[user_id_str] = {
            "story": "city_corruption",  
            "node": "start"
        }
        save_user_data(data)
    else:
        
        if "story" not in data[user_id_str]:
            data[user_id_str]["story"] = "city_corruption"
        if "node" not in data[user_id_str]:
            data[user_id_str]["node"] = "start"
        save_user_data(data)  

    return data[user_id_str]["story"], data[user_id_str]["node"]


def update_user_progress(user_id, story_id, node_id):
    data = load_user_data()
    data[str(user_id)] = {"story": story_id, "node": node_id}
    save_user_data(data)

