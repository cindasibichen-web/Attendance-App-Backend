import numpy as np
from PIL import Image
import insightface

try:
    face_app = insightface.app.FaceAnalysis(name="buffalo_l")
    face_app.prepare(ctx_id=0, det_size=(640, 640))
    print("✅ InsightFace loaded successfully")

    img = np.array(Image.open("test_face.jpg").convert("RGB"))  # Use a real image
    faces = face_app.get(img)
    print("Detected faces:", len(faces))

except Exception as e:
    print("⚠️ InsightFace not available:", e)
