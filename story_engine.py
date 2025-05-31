import json
import os
from .save import get_user_progress, update_user_progress

STORY_FILE = "story/story_data.json"

def load_stories():
    with open(STORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_story_node(user_id):
    story_id, node_id = get_user_progress(user_id)
    stories = load_stories()

    if story_id not in stories:
        raise Exception(f"Story ID '{story_id}' not found in stories JSON.")
    
    story = stories[story_id]

    if node_id not in story:
        raise Exception(f"Node ID '{node_id}' not found in story '{story_id}'.")
    
    return node_id, story[node_id]


def make_choice(user_id, choice_index):
    story_id, node_id = get_user_progress(user_id)
    stories = load_stories()
    story = stories.get(story_id, {})
    node = story.get(node_id)

    if not node or choice_index >= len(node["choices"]):
        return node_id, node, "Invalid choice number."

    next_id = node["choices"][choice_index]["next"]
    update_user_progress(user_id, story_id, next_id)
    return next_id, story[next_id], None
