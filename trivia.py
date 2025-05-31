import json
import random
import os
from utils.currency import update_currency


QUESTIONS_FILE = "trivia_questions.json"
SCORES_FILE = "trivia_scores.json"
QUESTIONS_PER_SESSION = 5

with open(QUESTIONS_FILE, encoding="utf-8") as f:
    all_questions = json.load(f)


user_sessions = {} 
user_session_index = {} 
user_scores = {}  

def load_scores():
    if not os.path.exists(SCORES_FILE):
        return {}
    with open(SCORES_FILE, encoding="utf-8") as f:
        return json.load(f)

def save_scores():
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(user_scores, f, indent=2)

user_scores = load_scores()

def start_trivia_session(user_id):
    if len(all_questions) < QUESTIONS_PER_SESSION:
        return None

    selected = random.sample(all_questions, QUESTIONS_PER_SESSION) 
    user_sessions[user_id] = selected
    user_session_index[user_id] = 0
    return selected[0]

def get_current_question(user_id):
    if user_id not in user_sessions:
        return None
    index = user_session_index.get(user_id, 0)
    return user_sessions[user_id][index]

def answer_question(user_id, answer):
    if user_id not in user_sessions:
        return None

    index = user_session_index[user_id]
    question = user_sessions[user_id][index]
    correct = (answer - 1) == question["answer"]

    user_scores.setdefault(str(user_id), {"correct": 0, "total": 0})
    user_scores[str(user_id)]["total"] += 1

    if correct:
        user_scores[str(user_id)]["correct"] += 1
        update_currency(user_id, 5)  
    else:
        update_currency(user_id, -5)  

    save_scores()

    user_session_index[user_id] += 1
    finished = user_session_index[user_id] >= QUESTIONS_PER_SESSION

    if finished:
        del user_sessions[user_id]
        del user_session_index[user_id]

    return correct, question["options"][question["answer"]], finished, user_scores[str(user_id)]
