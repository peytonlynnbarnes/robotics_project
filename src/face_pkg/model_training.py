import os
import face_recognition
import pickle
import cv2

def train_model():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(base_dir, "dataset")
    
    knownEncodings = []
    knownNames = []

    for person_name in os.listdir(dataset_path):
        person_dir = os.path.join(dataset_path, person_name)
        if not os.path.isdir(person_dir):
            continue

        for image_name in os.listdir(person_dir):
            image_path = os.path.join(person_dir, image_name)
            image = cv2.imread(image_path)
            if image is None: continue 
            
        
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(rgb, model="hog")
            encodings = face_recognition.face_encodings(rgb, boxes)

            for encoding in encodings:
                knownEncodings.append(encoding)
                knownNames.append(person_name)

    data = {"encodings": knownEncodings, "names": knownNames}
    with open(os.path.join(base_dir, "encodings.pickle"), "wb") as f:
        f.write(pickle.dumps(data))
    print("[INFO] Training complete. Encodings saved.")

if __name__ == "__main__":
    train_model()
