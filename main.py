# ======================================================
# ENV SETUP (MUST BE FIRST)
# ======================================================
from dotenv import load_dotenv
load_dotenv()

# ======================================================
# IMPORTS
# ======================================================
from fastapi import FastAPI, UploadFile, File, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from scripts.detect_issue import detect
from scripts.firebase_admin import db
from scripts.pdf_report import generate_issue_pdf
from scripts.gemini_description import generate_ai_insights  # ✅ OK now

import shutil
import uuid
import os
import math
from datetime import datetime

# ======================================================
# APP
# ======================================================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
PDF_DIR = "pdf_reports"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

# ======================================================
# UTILS
# ======================================================
def haversine(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return float("inf")

    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2)
        * math.sin(dlambda / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def assign_department(label: str):
    label = label.lower()
    mapping = {
        "pothole": "Roads Department",
        "damaged road": "Roads Department",
        "garbage": "Sanitation Department",
        "open drain": "Drainage Department",
        "water logging": "Drainage Department",
        "broken streetlight": "Electrical Department",
    }
    for k, v in mapping.items():
        if k in label:
            return v
    return "General Municipal Services"

# ======================================================
# POST /detect
# ======================================================
@app.post("/detect")
async def detect_issue(
    image: UploadFile = File(...),
    latitude: float = Form(None),
    longitude: float = Form(None),
):
    # Save image
    ext = image.filename.split(".")[-1]
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.{ext}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    detections = detect(file_path)
    os.remove(file_path)

    if not detections:
        return {
            "detections": [],
            "primary_issue": "Unknown",
            "ai": {
                "description_en": "No clear civic issue detected.",
                "description_hi": "Koi spasht civic issue nahi mila.",
                "why_it_matters": "Issue unclear.",
                "severity_level": "Low",
            },
            "duplicate": None,
        }

    primary = max(detections, key=lambda x: x["severity"])

    # 🔥 Gemini AI insights
    ai_insights = generate_ai_insights(
        issue_label=primary["label"],
        severity_score=primary["severity"],
    )

    # AI-only response (no DB)
    if latitude is None or longitude is None:
        return {
            "detections": detections,
            "primary_issue": primary["label"],
            "ai": ai_insights,
            "duplicate": None,
        }

    # Duplicate detection
    duplicate_doc = None
    duplicate_distance = None

    for doc in db.collection("issues").stream():
        data = doc.to_dict()
        if data.get("issueType") != primary["label"]:
            continue

        d = haversine(latitude, longitude, data.get("latitude"), data.get("longitude"))
        if d <= 100:
            duplicate_doc = doc
            duplicate_distance = int(d)
            break

    if duplicate_doc:
        data = duplicate_doc.to_dict()
        votes = data.get("votes", 1) + 1

        db.collection("issues").document(duplicate_doc.id).update({
            "votes": votes,
            "updatedAt": datetime.utcnow(),
        })

        return {
            "detections": detections,
            "primary_issue": primary["label"],
            "ai": ai_insights,
            "duplicate": {
                "issueId": duplicate_doc.id,
                "distanceMeters": duplicate_distance,
                "reportCount": votes,
            },
        }

    # New issue
    new_issue = {
        "issueType": primary["label"],
        "severity": primary["severity"],
        "confidence": primary["confidence"],
        "detections": detections,
        "latitude": latitude,
        "longitude": longitude,
        "votes": 1,
        "voters": [],
        "status": "open",
        "department": assign_department(primary["label"]),
        "ai": ai_insights,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
    }

    doc_ref = db.collection("issues").add(new_issue)

    return {
        "detections": detections,
        "primary_issue": primary["label"],
        "ai": ai_insights,
        "issueId": doc_ref[1].id,
        "votes": 1,
    }
