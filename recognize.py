import cv2
import os
import json

def load_users_data(users_file='dataset/users.json'):
    if os.path.exists(users_file):
        with open(users_file, 'r') as f:
            return json.load(f)
    return {}

def recognize_face(label_dict, model_path='trainer.yml'):
    if not os.path.exists(model_path):
        print("Error: Model belum ada.")
        return
    
    users_data = load_users_data()
    
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(model_path)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened(0):
        print("Error: Tidak bisa mengakses kamera.")
        return
    
    print("Mulai recognition. Tekan 'q' untuk berhenti.")
    offset_y_below_box = 30  
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        for (x, y, w, h) in faces:
            face_img = gray[y:y+h, x:x+w]
            id, confidence = recognizer.predict(face_img)
            
            if confidence < 50:
                name = label_dict.get(id, "Unknown")
                unique_id = "Unknown"
                for uid, data in users_data.items():
                    if data['nama'] == name:
                        unique_id = uid
                        break
                cv2.putText(frame, name, (x, y - 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                cv2.putText(frame, f"ID: {unique_id}", (x, y + h + offset_y_below_box),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "Unknown", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 4)
        
        cv2.imshow('Recognition', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("Recognition selesai.")
