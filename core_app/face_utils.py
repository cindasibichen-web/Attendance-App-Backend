# # core_app/face_utils.py
# import torch
# import numpy as np
# from PIL import Image
# from facenet_pytorch import InceptionResnetV1

# # Load pre-trained Facenet model
# DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
# FACENET_MODEL = InceptionResnetV1(pretrained='vggface2').eval().to(DEVICE)
# print("✅ Facenet-PyTorch model loaded successfully")

# # -----------------------------
# # Preprocess Image
# # -----------------------------
# def preprocess_image(image_path):
#     """Load image and preprocess for Facenet"""
#     img = Image.open(image_path).convert("RGB")
#     img = img.resize((160, 160))
#     img_array = np.asarray(img).astype(np.float32)
#     img_array = (img_array - 127.5) / 128.0  # Normalize [-1, 1]
#     img_array = np.transpose(img_array, (2, 0, 1))  # C x H x W
#     img_tensor = torch.tensor(img_array).unsqueeze(0).to(DEVICE)
#     return img_tensor

# # -----------------------------
# # Generate Embedding
# # -----------------------------
# def generate_face_embedding(image_path):
#     """Generate normalized embedding using Facenet-PyTorch"""
#     try:
#         img_tensor = preprocess_image(image_path)
#         with torch.no_grad():
#             embedding = FACENET_MODEL(img_tensor)
#         embedding = embedding / embedding.norm()  # Normalize
#         return embedding.cpu().numpy()[0]
#     except Exception as e:
#         print("❌ Error generating face embedding:", e)
#         return None

# # -----------------------------
# # Compare Faces
# # -----------------------------
# def compare_faces(known_embedding, uploaded_embedding, threshold=0.5):
#     """Compare two embeddings using cosine similarity"""
#     known_vec = np.array(known_embedding)
#     uploaded_vec = np.array(uploaded_embedding)
#     similarity = np.dot(known_vec, uploaded_vec)
#     confidence = round(similarity * 100, 2)
#     return similarity >= threshold, confidence

# core_app/face_utils.py
import torch
import numpy as np
from PIL import Image
from facenet_pytorch import InceptionResnetV1

# Load pre-trained Facenet model once globally
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
FACENET_MODEL = InceptionResnetV1(pretrained='vggface2').eval().to(DEVICE)
print("✅ Facenet-PyTorch model loaded successfully")

# -----------------------------
# Preprocess Image
# -----------------------------
def preprocess_image(image_path):
    """Load and preprocess image for Facenet"""
    img = Image.open(image_path).convert("RGB")
    img = img.resize((160, 160))
    img_array = np.asarray(img).astype(np.float32)
    img_array = (img_array - 127.5) / 128.0  # Normalize to [-1, 1]
    img_array = np.transpose(img_array, (2, 0, 1))  # C x H x W
    img_tensor = torch.tensor(img_array).unsqueeze(0).to(DEVICE)
    return img_tensor


# -----------------------------
# Generate Face Embedding
# -----------------------------
def generate_face_embedding(image_path):
    """Generate normalized face embedding using Facenet-PyTorch"""
    try:
        img_tensor = preprocess_image(image_path)
        with torch.no_grad():
            embedding = FACENET_MODEL(img_tensor)
        # Normalize embedding
        embedding = embedding / embedding.norm()
        return embedding.cpu().numpy()[0].tolist()
    except Exception as e:
        print("❌ Error generating face embedding:", e)
        return None


# -----------------------------
# Compare Faces (Cosine Similarity)
# -----------------------------
def compare_faces(known_embedding, uploaded_embedding, threshold=0.7):
    """
    Compare two face embeddings using cosine similarity.
    Returns (is_match, confidence).
    """
    try:
        known_vec = np.array(known_embedding, dtype=np.float32)
        uploaded_vec = np.array(uploaded_embedding, dtype=np.float32)

        # Normalize both embeddings
        known_vec /= np.linalg.norm(known_vec)
        uploaded_vec /= np.linalg.norm(uploaded_vec)

        # Compute cosine similarity
        similarity = np.dot(known_vec, uploaded_vec)
        confidence = round(float(similarity) * 100, 2)

        is_match = similarity >= threshold
        return is_match, confidence
    except Exception as e:
        print("❌ Error comparing faces:", e)
        return False, 0.0
