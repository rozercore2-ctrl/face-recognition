import cv2
import os
import json
import base64
import logging
import time
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SERVICE_ACCOUNT_FILE = 'D:\\face_recog\\face-recognition-481607-b0cb180a1d23.json'
SPREADSHEET_ID = '1OhPYhrGuJt7UgLQhTDRXV7stff18Ao7spwzofrDTgO4'
SHEET_NAME = 'Sheet1'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SCOPES_IAM = ['https://www.googleapis.com/auth/cloud-platform']

PROJECT_ID = 'face-recognition-481607'
SERVICE_ACCOUNT_EMAIL = 'your-service-account@face-recognition-481607.iam.gserviceaccount.com'
OLD_KEY_ID = 'd5bbb1c3045db0ce54af77bf4035d920cfb35ba5'
NEW_KEY_FILE_PATH = 'D:\\face_recog\\new-face-recognition-key.json'

creds = None
service = None
sheet = None

def initialize_google_sheets(retry_count=3):
    global creds, service, sheet
    for attempt in range(retry_count):
        try:
            creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            service = build('sheets', 'v4', credentials=creds)
            sheet = service.spreadsheets()
            logging.info("Google Sheets berhasil diinisialisasi.")
            return True
        except Exception as e:
            logging.warning(f"Gagal inisialisasi (attempt {attempt+1}): {e}")
            if attempt < retry_count - 1:
                time.sleep(2)
            else:
                logging.error("Gagal setelah retry.")
                raise

def rotate_service_account_key():
    global SERVICE_ACCOUNT_FILE
    try:
        if PROJECT_ID == 'face-recognition-481607' or SERVICE_ACCOUNT_EMAIL.startswith('your-'):
            logging.error("Placeholder belum diganti!")
            raise ValueError("Placeholder invalid.")
        
        temp_creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES_IAM)
        iam_service = build('iam', 'v1', credentials=temp_creds)
        
        name = f'projects/{PROJECT_ID}/serviceAccounts/{SERVICE_ACCOUNT_EMAIL}'
        key_response = iam_service.projects().serviceAccounts().keys().create(name=name, body={}).execute()
        
        private_key_data = base64.b64decode(key_response['privateKeyData']).decode('utf-8')
        key_json = json.loads(private_key_data)
        with open(NEW_KEY_FILE_PATH, 'w') as f:
            json.dump(key_json, f)
        
        logging.info(f"Key baru dibuat: {NEW_KEY_FILE_PATH}")
        
        if OLD_KEY_ID:
            iam_service.projects().serviceAccounts().keys().delete(name=f'{name}/keys/{OLD_KEY_ID}').execute()
            logging.info(f"Key lama {OLD_KEY_ID} dihapus")
        
        SERVICE_ACCOUNT_FILE = NEW_KEY_FILE_PATH
        initialize_google_sheets()
        logging.info("Rotasi key berhasil.")
        
    except Exception as e:
        logging.error(f"Gagal rotasi key: {e}")
        raise

def write_header_if_empty():
    try:
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=f"{SHEET_NAME}!A1:F1").execute()
        values = result.get('values', [])
        if not values:
            header = [['ID', 'Nama', 'Keterangan', 'Hari', 'Tanggal', 'Jam']]
            body = {'values': header}
            sheet.values().update(spreadsheetId=SPREADSHEET_ID, range=f"{SHEET_NAME}!A1:F1", valueInputOption='RAW', body=body).execute()
            logging.info("Header ditulis.")
        else:
            logging.info("Header ada.")
    except RefreshError as e:
        logging.error(f"RefreshError: {e}. Rotasi key...")
        rotate_service_account_key()
        write_header_if_empty()
    except Exception as e:
        logging.error(f"Error lain: {e}")
        raise

def load_today_attendance(file_path='attendance_today.json'):
    """
    Load absensi hari ini dari file lokal (backup untuk cek duplikasi).
    Reset otomatis jika hari baru.
    """
    today = datetime.now().date().isoformat()
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
        if data.get('date') != today:
            data = {'date': today, 'users': []}
            with open(file_path, 'w') as f:
                json.dump(data, f)
    else:
        data = {'date': today, 'users': []}
        with open(file_path, 'w') as f:
            json.dump(data, f)
    return data

def save_today_attendance(data, file_path='attendance_today.json'):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def is_attendance_recorded(user_id):
    """
    Cek duplikasi: Pertama cek file lokal, lalu Google Sheets.
    Jika ada di lokal, langsung return True.
    """
    today_data = load_today_attendance()
    if user_id in today_data['users']:
        logging.info(f"Absensi {user_id} sudah tercatat hari ini (cek lokal).")
        return True
    
    try:
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=f"{SHEET_NAME}!A:F").execute()
        values = result.get('values', [])
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        logging.info(f"Cek Sheets untuk {user_id} pada {today_str}. Total baris: {len(values)}")
        
        for i, row in enumerate(values):
            if len(row) >= 5:
                recorded_id = row[0].strip()
                recorded_date = row[4].strip()
                logging.debug(f"Baris {i+1}: ID='{recorded_id}', Tanggal='{recorded_date}'")
                if recorded_id == user_id and recorded_date == today_str:
                    today_data['users'].append(user_id)
                    save_today_attendance(today_data)
                    logging.info(f"Absensi {user_id} sudah tercatat (Sheets, baris {i+1}).")
                    return True
        logging.info(f"Absensi {user_id} belum tercatat.")
        return False
    except Exception as e:
        logging.error(f"Error cek Sheets: {e}. Gunakan cek lokal saja.")
        return user_id in today_data['users']

def append_attendance_to_sheets_if_not_exists(user_id, name, status='Hadir'):
    if is_attendance_recorded(user_id):
        logging.info(f"Absensi untuk {name} sudah tercatat hari ini. Lewati.")
        return
    now = datetime.now()
    hari_indonesia = {"Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu", "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"}.get(now.strftime("%A"), now.strftime("%A"))
    tanggal = now.strftime("%Y-%m-%d")
    jam = now.strftime("%H:%M:%S")
    values = [[user_id, name, status, hari_indonesia, tanggal, jam]]
    body = {'values': values}
    try:
        sheet.values().append(spreadsheetId=SPREADSHEET_ID, range=f"{SHEET_NAME}!A:F", valueInputOption='USER_ENTERED', body=body).execute()
        today_data = load_today_attendance()
        today_data['users'].append(user_id)
        save_today_attendance(today_data)
        logging.info(f"Absensi {name} ({user_id}) berhasil dikirim.")
    except RefreshError as e:
        logging.error(f"RefreshError saat append: {e}. Rotasi key...")
        rotate_service_account_key()
        append_attendance_to_sheets_if_not_exists(user_id, name, status)
    except Exception as e:
        logging.error(f"Gagal kirim: {e}")

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
    try:
        initialize_google_sheets()
        write_header_if_empty()
    except RefreshError as e:
        logging.error(f"Error awal: {e}. Rotasi key...")
        rotate_service_account_key()
        write_header_if_empty()
    
    if not os.path.exists(model_path):
        logging.error("Model belum ada.")
        return
    label_dict = load_label_dict(dataset_path)
    users_data = load_users_data(os.path.join(dataset_path, 'users.json'))
    if label_dict is None:
        logging.error("Label kosong.")
        return
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(model_path)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("Kamera tidak akses.")
        return
    logging.info("Tekan 'q' untuk keluar.")
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
    logging.info("Recognition selesai.")

if __name__ == '__main__':
    recognize_face()
