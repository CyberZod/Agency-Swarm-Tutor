import json
import os

def load_threads(channel_id):
    if os.path.exists(f"{channel_id}_threads.json"):
        with open(f"{channel_id}_threads.json", "r") as file:
            threads = json.load(file)
    else:
        threads = []
    return threads

def save_threads(new_threads, channel_id):
    # Save threads to a file or database using the channel_id
    with open(f"{channel_id}_threads.json", "w") as file:
        json.dump(new_threads, file)
