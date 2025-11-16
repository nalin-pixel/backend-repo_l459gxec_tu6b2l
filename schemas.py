"""
Database Schemas for Hospital CRM MVP

Each Pydantic model represents a collection in MongoDB. Collection name = class name lowercased.
"""
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

class Patient(BaseModel):
    mrn: Optional[str] = Field(None, description="Medical Record Number")
    first_name: str
    last_name: str
    dob: Optional[str] = Field(None, description="Date of birth (YYYY-MM-DD)")
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[dict] = Field(default=None, description="Address object {line1, line2, city, state, zip}")
    preferred_language: Optional[str] = None
    consent_sms: bool = Field(default=False)
    consent_email: bool = Field(default=False)

class Provider(BaseModel):
    name: str
    specialty: Optional[str] = None
    location: Optional[str] = None
    npi: Optional[str] = None

class Appointment(BaseModel):
    patient_id: str
    provider_id: str
    start_time: datetime
    end_time: datetime
    type: Optional[str] = Field(default="Consult")
    status: str = Field(default="scheduled", description="scheduled|checked_in|completed|cancelled")
    reason: Optional[str] = None
