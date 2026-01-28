import cv2
import os
import time
import json
import random
import string

def create_dataset_folder(dataset_path='dataset/'):
    if not os.path.exists(dataset_path):
        os.makedirs(dataset_path)

def load_users_data(users_file='dataset/users.json'):
    if os.path.exists(users_file):
        with open(users_file, 'r') as f:
            return json.load(f)
    return {}

def save_users_data(users_data, users_file='dataset/users.json'):
    with open(users_file, 'w') as f:
        json.dump(users_data, f, indent=4)

def generate_unique_id(users_data):
    while True:
        unique_id = ''.join(random.choices(string.digits, k=11))
        if unique_id not in users_data:
            return unique_id

def check_existing_samples(person_name, dataset_path='dataset/'):
    person_folder = os.path.join(dataset_path, person_name)
    if os.path.exists(person_folder):
        existing_files = [f for f in os.listdir(person_folder) if f.endswith('.jpg')]
        return len(existing_files)
    return 0

def register_face(num_samples=40, dataset_path='dataset/'):
    person_name = input("Masukkan nama lengkap: ").strip()
    if not person_name:
        print("Nama tidak boleh kosong. Registrasi dibatalkan.")
        return
    
    create_dataset_folder(dataset_path)
    users_file = os.path.join(dataset_path, 'users.json')
    users_data = load_users_data(users_file)
    existing_user_id = None
    for uid, data in users_data.items():
        if data['nama'].strip().lower() == person_name.lower():
            existing_user_id = uid
            break
    
    if existing_user_id:
        print(f"User '{person_name}' sudah terdaftar dengan ID {existing_user_id}. Lewati input tanggal lahir dan lanjut ke registrasi wajah.")
        birth_date = users_data[existing_user_id]['tanggal_lahir']
    else:
        birth_date = input("Masukkan tanggal lahir (contoh: 15/08/2000): ").strip()
        if not birth_date:
            print("Tanggal lahir tidak boleh kosong. Registrasi dibatalkan.")
            return
        unique_id = generate_unique_id(users_data)
    
    person_folder = os.path.join(dataset_path, person_name)
    existing_count = check_existing_samples(person_name, dataset_path)
    max_samples = 40
    if existing_count >= max_samples:
        print(f"Data '{person_name}' sudah terdaftar. Registrasi dilewati.")
        return
    
    remaining_slots = max_samples - existing_count
    total_to_capture = min(num_samples, remaining_slots)
    
    if not os.path.exists(person_folder):
        os.makedirs(person_folder)
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Tidak dapat mengakses kamera.")
        return
    
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    count = existing_count
    
    print(f"Mulai registrasi untuk {person_name}. Ambil {total_to_capture} sampel. Tekan 'q' untuk stop.")
    
    captured = 0
    while captured < total_to_capture:
        ret, frame = cap.read()
        if not ret:
            print("Error: Gagal baca frame kamera.")
            break
        
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        for (x, y, w, h) in faces:
            if captured >= total_to_capture:
                break
            count += 1
            captured += 1
            face_img = gray[y:y+h, x:x+w]
            img_path = os.path.join(person_folder, f"{person_name}_{count}.jpg")
            cv2.imwrite(img_path, face_img)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 4)
            cv2.putText(frame, f"Sample {captured}/{total_to_capture}", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            print(f"Sampel {captured} disimpan.")
            time.sleep(0.1)
        
        cv2.imshow('Registrasi', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Registrasi dihentikan pengguna.")
            break

    cap.release()
    cv2.destroyAllWindows()
    
    # Simpan data user jika ada sampel baru dan user baru
    if captured > 0 and not existing_user_id:
        users_data[unique_id] = {
            "nama": person_name,
            "tanggal_lahir": birth_date,
            "folder": person_name
        }
        save_users_data(users_data, users_file)
        print(f"Registrasi berhasil untuk {person_name}, Nomor ID {unique_id}.")
    elif captured > 0 and existing_user_id:
        print(f"Registrasi tambahan berhasil untuk {person_name} (ID: {existing_user_id}).")
    else:
        print("Registrasi gagal: tidak ada sampel yang diambil.")
    
    total_samples = count
    print(f"Total sampel untuk {person_name}: {total_samples} (maksimal {max_samples}).")
