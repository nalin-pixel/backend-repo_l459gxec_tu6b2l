import os
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Patient, Provider, Appointment

app = FastAPI(title="Hospital CRM MVP", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers
class IdModel(BaseModel):
    id: str


def to_public(doc):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc


@app.get("/")
def read_root():
    return {"message": "Hospital CRM Backend Running"}


# Schema discovery for DB viewer
@app.get("/schema")
def get_schema():
    return {
        "patient": Patient.model_json_schema(),
        "provider": Provider.model_json_schema(),
        "appointment": Appointment.model_json_schema(),
    }


# Patients
@app.post("/api/v1/patients")
def create_patient(payload: Patient):
    new_id = create_document("patient", payload)
    return {"id": new_id}


@app.get("/api/v1/patients")
def list_patients(q: Optional[str] = None, limit: int = 50):
    filt = {}
    if q:
        filt = {"$or": [
            {"first_name": {"$regex": q, "$options": "i"}},
            {"last_name": {"$regex": q, "$options": "i"}},
            {"phone": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}},
        ]}
    docs = get_documents("patient", filt, limit)
    return [to_public(d) for d in docs]


@app.get("/api/v1/patients/{patient_id}")
def get_patient(patient_id: str):
    doc = db["patient"].find_one({"_id": ObjectId(patient_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Patient not found")
    return to_public(doc)


# Providers
@app.post("/api/v1/providers")
def create_provider(payload: Provider):
    new_id = create_document("provider", payload)
    return {"id": new_id}


@app.get("/api/v1/providers")
def list_providers(q: Optional[str] = None, limit: int = 100):
    filt = {}
    if q:
        filt = {"name": {"$regex": q, "$options": "i"}}
    docs = get_documents("provider", filt, limit)
    return [to_public(d) for d in docs]


# Appointments
class AppointmentCreate(Appointment):
    pass


@app.post("/api/v1/appointments")
def create_appointment(payload: AppointmentCreate):
    # simple overlap check for provider
    overlap = db["appointment"].find_one({
        "provider_id": payload.provider_id,
        "$or": [
            {"start_time": {"$lt": payload.end_time}, "end_time": {"$gt": payload.start_time}}
        ]
    })
    if overlap:
        raise HTTPException(status_code=409, detail="Time slot overlaps with another appointment")
    new_id = create_document("appointment", payload)
    return {"id": new_id}


@app.get("/api/v1/appointments")
def list_appointments(patient_id: Optional[str] = None, provider_id: Optional[str] = None, start: Optional[str] = None, end: Optional[str] = None, limit: int = 100):
    filt = {}
    if patient_id:
        filt["patient_id"] = patient_id
    if provider_id:
        filt["provider_id"] = provider_id
    if start and end:
        try:
            s = datetime.fromisoformat(start)
            e = datetime.fromisoformat(end)
            filt["start_time"] = {"$gte": s}
            filt["end_time"] = {"$lte": e}
        except Exception:
            pass
    docs = get_documents("appointment", filt, limit)
    return [to_public(d) for d in docs]


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = os.getenv("DATABASE_NAME") or "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
