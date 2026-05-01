import cv2
import face_recognition
import pickle
import os
import requests
import numpy as np

class DeliveryVision:
    def __init__(self, target, speak):
        self.target = target
        self.speak = speak
        base_dir = os.path.dirname(os.path.abspath(__file__))
        enc_path = os.path.join(base_dir, "encodings.pickle")

        with open(enc_path, "rb") as f:
            self.data = pickle.load(f)

    def run(self, stream_url="http://192.168.31.99:8080/stream"):
        try:
            stream = requests.get(stream_url, stream=True, timeout=10)
            if stream.status_code != 200: return False
        except Exception: return False

        bytes_data = bytes()
        for chunk in stream.iter_content(chunk_size=1024):
            bytes_data += chunk
            a = bytes_data.find(b'\xff\xd8')
            b = bytes_data.find(b'\xff\xd9')

            if a != -1 and b != -1:
                jpg = bytes_data[a:b+2]
                bytes_data = bytes_data[b+2:]
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                if frame is None: continue

                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

                boxes = face_recognition.face_locations(rgb)
                encodings = face_recognition.face_encodings(rgb, boxes)

                for encoding in encodings:
                    matches = face_recognition.compare_faces(self.data["encodings"], encoding)
                    if True in matches:
                        matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                        counts = {}
                        for i in matchedIdxs:
                            name = self.data["names"][i]
                            counts[name] = counts.get(name, 0) + 1
                        name = max(counts, key=counts.get)

                        if name.lower() == self.target.lower():
                            self.speak(f"{self.target} found")
                            cv2.destroyAllWindows()
                            return True
        return False
