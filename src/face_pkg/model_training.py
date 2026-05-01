import os
import face_recognition
import pickle
import cv2

def train_model():
    # Use absolute path for dataset folder
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(base_dir, "dataset")
    
    knownEncodings = []
    knownNames = []

    # Loop through each folder in the dataset
    for person_name in os.listdir(dataset_path):
        person_dir = os.path.join(dataset_path, person_name)
        if not os.path.isdir(person_dir):
            continue

        # Process every image found in the person's specific folder
        for image_name in os.listdir(person_dir):
            image_path = os.path.join(person_dir, image_name)
            image = cv2.imread(image_path)
            if image is None: continue # Skip files that aren't valid images
            
            # Convert BGR (OpenCV default) to RGB 
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            # Locate the coordinates of faces in the image using the HOG model
            boxes = face_recognition.face_locations(rgb, model="hog")
            # Turn the visual face data into a 128-dimension mathematical vector (encoding)
            encodings = face_recognition.face_encodings(rgb, boxes)

            for encoding in encodings:
                # Map the mathematical encoding to the person's name
                knownEncodings.append(encoding)
                knownNames.append(person_name)

    # Bundle the encodings and names into a dictionary for storage
    data = {"encodings": knownEncodings, "names": knownNames}
    # Save the data to a pickle file, prevents unnecessary retraining 
    with open(os.path.join(base_dir, "encodings.pickle"), "wb") as f:
        f.write(pickle.dumps(data))
    print("[INFO] Training complete. Encodings saved.")

if __name__ == "__main__":
    train_model()