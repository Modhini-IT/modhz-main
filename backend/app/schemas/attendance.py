"""
Pydantic schemas for attendance data validation
"""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class AttendanceBase(BaseModel):
    """Base attendance schema"""
    student_id: str
    confidence_score: float
    location: Optional[str] = None
    session_id: Optional[str] = None
    subject_code: Optional[str] = None
    period: Optional[str] = None
    status: str = "present"


class AttendanceCreate(AttendanceBase):
    """Schema for creating attendance record"""
    pass


class AttendanceResponse(AttendanceBase):
    """Schema for attendance response"""
    id: str
    timestamp: datetime
    image_path: Optional[str] = None
    student_name: Optional[str] = None
    student_roll_number: Optional[str] = None
    
    class Config:
        from_attributes = True


class AttendanceStats(BaseModel):
    """Schema for attendance statistics"""
    total_students: int
    students_present: int
    students_late: int
    students_absent: int
    attendance_percentage: float
    date: str