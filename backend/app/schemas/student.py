"""
Pydantic schemas for student data validation
"""
from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class StudentBase(BaseModel):
    """Base student schema"""
    name: str
    email: Optional[EmailStr] = None
    student_number: Optional[str] = None
    roll_number: Optional[str] = None
    department: Optional[str] = None
    year: Optional[int] = None
    section: Optional[str] = None
    phone: Optional[str] = None


class StudentCreate(StudentBase):
    """Schema for creating a new student"""
    pass


class StudentUpdate(BaseModel):
    """Schema for updating a student"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    student_number: Optional[str] = None
    roll_number: Optional[str] = None
    department: Optional[str] = None
    year: Optional[int] = None
    section: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class StudentResponse(StudentBase):
    """Schema for student response"""
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool
    
    class Config:
        from_attributes = True