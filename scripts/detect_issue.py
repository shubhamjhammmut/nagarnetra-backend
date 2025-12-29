import sys
sys.path.append("../GroundingDINO")

from groundingdino.util.inference import load_model, load_image, predict

# Paths
CONFIG_PATH = "models/GroundingDINO_SwinT_OGC.py"
WEIGHTS_PATH = "models/groundingdino_swint_ogc.pth"

# Load model (CPU only)
model = load_model(CONFIG_PATH, WEIGHTS_PATH)


def severity_score(label, confidence):
    base = {
        "pothole": 8,
        "garbage pile": 6,
        "broken streetlight": 5,
        "open drain": 9,
        "water logging": 7,
        "damaged road": 7
    }
    return min(10, int(base.get(label, 4) * confidence))


def detect(image_path):
    image_source, image = load_image(image_path)

    # Improved civic prompt
    TEXT_PROMPT = (
        "pothole on road, garbage pile on street, trash dumping, "
        "broken streetlight pole, open drainage, water logging on road"
    )

    boxes, scores, labels = predict(
        model=model,
        image=image,
        caption=TEXT_PROMPT,
        box_threshold=0.45,
        text_threshold=0.35,
        device="cpu"   # required on macOS
    )

    results = []
    h, w, _ = image_source.shape

    for box, score, label in zip(boxes, scores, labels):
        if score < 0.4:
            continue

        x1 = int(box[0] * w)
        y1 = int(box[1] * h)
        x2 = int(box[2] * w)
        y2 = int(box[3] * h)

        results.append({
            "label": label,
            "confidence": float(score),
            "severity": severity_score(label, score),
            "bbox": {
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2
            }
        })

    # Remove duplicate labels (keep highest confidence)
    unique = {}
    for r in results:
        if r["label"] not in unique or r["confidence"] > unique[r["label"]]["confidence"]:
            unique[r["label"]] = r

    return list(unique.values())


if __name__ == "__main__":
    print(detect("test.jpg"))
from scripts.firebase_admin import db
import math
from datetime import datetime, timedelta


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))


def check_duplicate(lat, lon, label):
    since = datetime.utcnow() - timedelta(hours=24)

    issues = db.collection("issues") \
        .where("title", "==", label) \
        .where("createdAt", ">", since) \
        .stream()

    count = 0
    for issue in issues:
        data = issue.to_dict()
        dist = haversine(lat, lon, data["latitude"], data["longitude"])
        if dist < 100:
            count += 1

    return count
