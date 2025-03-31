import json
import os

def load_threads(session_name):
    if os.path.exists(f"{session_name}_threads.json"):
        with open(f"{session_name}_threads.json", "r") as file:
            threads = json.load(file)
    else:
        threads = []
    return threads

def save_threads(new_threads, session_name):
    # Save threads to a file or database using the session_name
    with open(f"{session_name}_threads.json", "w") as file:
        json.dump(new_threads, file)
