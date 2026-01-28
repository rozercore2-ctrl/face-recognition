import json
from datetime import datetime
import os

def load_attendance(file_path='attendance_log.json'):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {}

def save_attendance(data, file_path='attendance_log.json'):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def log_attendance(user_id, name, file_path='attendance_log.json'):
    attendance = load_attendance(file_path)
    
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now().date().isoformat()

    if user_id not in attendance:
        attendance[user_id] = {
            "name": name,
            "dates": []
        }
    if not any(log.split()[0] == today for log in attendance[user_id]["dates"]):
        attendance[user_id]["dates"].append(time_now)
        print(f"Absensi tercatat: {name} pada {time_now}")
    else:
        print(f"{name} sudah melakukan absensi hari ini.")
    
    save_attendance(attendance, file_path)
