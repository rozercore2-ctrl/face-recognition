import cv2
import os
import numpy as np
from PIL import Image

def create_dataset_folder(dataset_path='dataset/'):
    if not os.path.exists(dataset_path):
        os.makedirs(dataset_path)

def train_model(dataset_path='dataset/', model_path='trainer.yml'):
    create_dataset_folder(dataset_path)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    
    faces = []
    ids = []
    label_dict = {}
    label_id = 0
    
    for person_name in os.listdir(dataset_path):
        person_folder = os.path.join(dataset_path, person_name)
        if os.path.isdir(person_folder) and person_name != 'users.json': 
            label_dict[label_id] = person_name
            for img_name in os.listdir(person_folder):
                img_path = os.path.join(person_folder, img_name)
                img = Image.open(img_path).convert('L')
                img_np = np.array(img, 'uint8')
                faces.append(img_np)
                ids.append(label_id)
            label_id += 1
    
    if len(faces) == 0:
        print("Error: Tidak ada data di dataset.")
        return None
    
    recognizer.train(faces, np.array(ids))
    recognizer.save(model_path)
    print(f"Training selesai. Model disimpan di {model_path}.")
    return label_dict

def load_label_dict(dataset_path='dataset/'):
    label_dict = {}
    label_id = 0
    for person_name in os.listdir(dataset_path):
        person_folder = os.path.join(dataset_path, person_name)
        if os.path.isdir(person_folder) and person_name != 'users.json':
            label_dict[label_id] = person_name
            label_id += 1
    return label_dict if label_dict else None