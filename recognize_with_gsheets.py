import cv2
import os
import json
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- Konfigurasi Google Sheets ---
SERVICE_ACCOUNT_FILE = 'face-recognition-481607-c42b491e98b3.json'  # Ganti sesuai nama file JSON Anda
SPREADSHEET_ID = '1OhPYhrGuJt7UgLQhTDRXV7stff18Ao7spwzofrDTgO4'      # Ganti dengan Spreadsheet ID Google Sheets Anda
SHEET_NAME = 'Sheet1'   # Ganti sesuai nama sheet/tab di Google Sheets Anda

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

def write_header_if_empty():
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1:F1").execute()
    values = result.get('values', [])
    if not values:
        header = [['ID', 'Nama', 'Keterangan', 'Hari', 'Tanggal', 'Jam']]
        body = {'values': header}
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A1:F1",
            valueInputOption='RAW',
            body=body).execute()
        print("Header ditulis di Google Sheets")
    else:
        print("Header sudah ada di Google Sheets")

def is_attendance_recorded(user_id):
    try:
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A2:F").execute()
        values = result.get('values', [])
        today_str = datetime.now().strftime("%Y-%m-%d")
        for row in values:
            if len(row) >= 5:
                recorded_id = row[0]
                recorded_date = row[4]  # tanggal di kolom E (indeks 4)
                if recorded_id == user_id and recorded_date == today_str:
                    return True
        return False
    except Exception as e:
        print(f"Error saat cek absensi di Google Sheets: {e}")
        return False

def append_attendance_to_sheets_if_not_exists(user_id, name, status='Hadir'):
    if is_attendance_recorded(user_id):
        print(f"Absensi untuk {name} sudah tercatat hari ini.")
        return
    now = datetime.now()
    hari_eng = now.strftime("%A")
    hari_indonesia = {
        "Monday": "Senin",
        "Tuesday": "Selasa",
        "Wednesday": "Rabu",
        "Thursday": "Kamis",
        "Friday": "Jumat",
        "Saturday": "Sabtu",
        "Sunday": "Minggu"
    }.get(hari_eng, hari_eng)
    tanggal = now.strftime("%Y-%m-%d")
    jam = now.strftime("%H:%M:%S")
    values = [[user_id, name, status, hari_indonesia, tanggal, jam]]
    body = {'values': values}
    try:
        sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:F",
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        print(f"Data absensi {name} ({user_id}) berhasil dikirim ke Google Sheets.")
    except Exception as e:
        print(f"Gagal mengirim data ke Google Sheets: {e}")

def load_users_data(users_file='dataset/users.json'):
    if os.path.exists(users_file):
        with open(users_file, 'r') as f:
            return json.load(f)
    return {}

def load_label_dict(dataset_path='dataset/'):
    label_dict = {}
    label_id = 0
    for person_name in os.listdir(dataset_path):
        person_folder = os.path.join(dataset_path, person_name)
        if os.path.isdir(person_folder) and person_name != 'users.json':
            label_dict[label_id] = person_name
            label_id += 1
    return label_dict if label_dict else None

def recognize_face(model_path='trainer.yml', dataset_path='dataset/'):
    write_header_if_empty()
    if not os.path.exists(model_path):
        print("Model belum ada, lakukan training terlebih dahulu.")
        return
    label_dict = load_label_dict(dataset_path)
    users_data = load_users_data(os.path.join(dataset_path, 'users.json'))
    if label_dict is None:
        print("Label dictionary kosong, jalankan training dulu.")
        return
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(model_path)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Kamera tidak dapat diakses.")
        return
    print("Tekan 'q' untuk keluar.")
    offset_y_below_box = 30
    recognized_today = set()
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        for (x, y, w, h) in faces:
            face_img = gray[y:y + h, x:x + w]
            id, confidence = recognizer.predict(face_img)
            if confidence < 50:
                name = label_dict.get(id, "Unknown")
                unique_id = "Unknown"
                for uid, data in users_data.items():
                    if data['nama'] == name:
                        unique_id = uid
                        break
                cv2.putText(frame, name, (x, y - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                cv2.putText(frame, f"ID: {unique_id}", (x, y + h + offset_y_below_box), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                if unique_id != "Unknown" and unique_id not in recognized_today:
                    append_attendance_to_sheets_if_not_exists(unique_id, name)
                    recognized_today.add(unique_id)
            else:
                cv2.putText(frame, "Unknown", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 4)
        cv2.imshow('Recognition', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    print("Recognition selesai.")

if __name__ == '__main__':
    recognize_face()
