"""
Attendance management API endpoints
"""
from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
import structlog

from app.core.database import get_db
from app.models.attendance_record import AttendanceRecord
from app.models.student import Student
from app.schemas.attendance import AttendanceResponse, AttendanceStats

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=List[AttendanceResponse])
async def get_attendance_records(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    subject_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get attendance records with optional filters"""
    try:
        query = select(AttendanceRecord).join(Student)
        
        # Apply filters
        if student_id:
            query = query.where(AttendanceRecord.student_id == student_id)
        
        if date_from:
            query = query.where(AttendanceRecord.timestamp >= date_from)
        
        if date_to:
            # Add one day to include the entire end date
            end_date = datetime.combine(date_to, datetime.max.time())
            query = query.where(AttendanceRecord.timestamp <= end_date)
        
        if subject_code:
            query = query.where(AttendanceRecord.subject_code == subject_code)
        
        # Order by timestamp descending and apply pagination
        query = query.order_by(desc(AttendanceRecord.timestamp)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        records = result.scalars().all()
        
        # Convert to response format with student info
        response_records = []
        for record in records:
            record_dict = record.to_dict()
            record_dict["student_name"] = record.student.name
            record_dict["student_roll_number"] = record.student.roll_number
            response_records.append(AttendanceResponse(**record_dict))
        
        return response_records
        
    except Exception as e:
        logger.error(f"Error fetching attendance records: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch attendance records")


@router.get("/student/{student_id}", response_model=List[AttendanceResponse])
async def get_student_attendance(
    student_id: str,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get attendance records for a specific student"""
    try:
        # Verify student exists
        student_query = select(Student).where(Student.id == student_id, Student.is_active == True)
        student_result = await db.execute(student_query)
        student = student_result.scalar_one_or_none()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Build attendance query
        query = select(AttendanceRecord).where(AttendanceRecord.student_id == student_id)
        
        if date_from:
            query = query.where(AttendanceRecord.timestamp >= date_from)
        
        if date_to:
            end_date = datetime.combine(date_to, datetime.max.time())
            query = query.where(AttendanceRecord.timestamp <= end_date)
        
        query = query.order_by(desc(AttendanceRecord.timestamp))
        
        result = await db.execute(query)
        records = result.scalars().all()
        
        # Convert to response format
        response_records = []
        for record in records:
            record_dict = record.to_dict()
            record_dict["student_name"] = student.name
            record_dict["student_roll_number"] = student.roll_number
            response_records.append(AttendanceResponse(**record_dict))
        
        return response_records
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student attendance: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch student attendance")


@router.get("/stats/daily")
async def get_daily_attendance_stats(
    target_date: Optional[date] = Query(default_factory=date.today),
    db: AsyncSession = Depends(get_db)
):
    """Get daily attendance statistics"""
    try:
        # Get start and end of the target date
        start_date = datetime.combine(target_date, datetime.min.time())
        end_date = datetime.combine(target_date, datetime.max.time())
        
        # Total students
        total_students_query = select(func.count(Student.id)).where(Student.is_active == True)
        total_result = await db.execute(total_students_query)
        total_students = total_result.scalar()
        
        # Students present today
        present_query = select(func.count(func.distinct(AttendanceRecord.student_id))).where(
            and_(
                AttendanceRecord.timestamp >= start_date,
                AttendanceRecord.timestamp <= end_date,
                AttendanceRecord.status == "present"
            )
        )
        present_result = await db.execute(present_query)
        students_present = present_result.scalar()
        
        # Students late today
        late_query = select(func.count(func.distinct(AttendanceRecord.student_id))).where(
            and_(
                AttendanceRecord.timestamp >= start_date,
                AttendanceRecord.timestamp <= end_date,
                AttendanceRecord.status == "late"
            )
        )
        late_result = await db.execute(late_query)
        students_late = late_result.scalar()
        
        # Calculate attendance percentage
        attendance_percentage = (students_present / total_students * 100) if total_students > 0 else 0
        
        # Subject-wise attendance
        subject_query = select(
            AttendanceRecord.subject_code,
            func.count(func.distinct(AttendanceRecord.student_id)).label('count')
        ).where(
            and_(
                AttendanceRecord.timestamp >= start_date,
                AttendanceRecord.timestamp <= end_date,
                AttendanceRecord.subject_code.isnot(None)
            )
        ).group_by(AttendanceRecord.subject_code)
        
        subject_result = await db.execute(subject_query)
        subject_attendance = {subject: count for subject, count in subject_result.all()}
        
        return {
            "date": target_date.isoformat(),
            "total_students": total_students,
            "students_present": students_present,
            "students_late": students_late,
            "students_absent": total_students - students_present - students_late,
            "attendance_percentage": round(attendance_percentage, 2),
            "subject_wise_attendance": subject_attendance
        }
        
    except Exception as e:
        logger.error(f"Error fetching daily attendance stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch attendance statistics")


@router.get("/stats/summary")
async def get_attendance_summary(
    days: int = Query(default=7, description="Number of days to include in summary"),
    db: AsyncSession = Depends(get_db)
):
    """Get attendance summary for the last N days"""
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = start_date - timedelta(days=days-1)
        
        # Total attendance records in period
        total_records_query = select(func.count(AttendanceRecord.id)).where(
            AttendanceRecord.timestamp >= start_date
        )
        total_result = await db.execute(total_records_query)
        total_records = total_result.scalar()
        
        # Average daily attendance
        daily_attendance_query = select(
            func.date(AttendanceRecord.timestamp).label('date'),
            func.count(func.distinct(AttendanceRecord.student_id)).label('count')
        ).where(
            AttendanceRecord.timestamp >= start_date
        ).group_by(func.date(AttendanceRecord.timestamp))
        
        daily_result = await db.execute(daily_attendance_query)
        daily_attendance = daily_result.all()
        
        avg_daily_attendance = sum(count for _, count in daily_attendance) / len(daily_attendance) if daily_attendance else 0
        
        # Most active students
        active_students_query = select(
            Student.name,
            Student.roll_number,
            func.count(AttendanceRecord.id).label('attendance_count')
        ).join(AttendanceRecord).where(
            AttendanceRecord.timestamp >= start_date
        ).group_by(Student.id, Student.name, Student.roll_number).order_by(
            desc(func.count(AttendanceRecord.id))
        ).limit(10)
        
        active_result = await db.execute(active_students_query)
        most_active = [
            {"name": name, "roll_number": roll, "attendance_count": count}
            for name, roll, count in active_result.all()
        ]
        
        return {
            "period_days": days,
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "total_attendance_records": total_records,
            "average_daily_attendance": round(avg_daily_attendance, 2),
            "daily_breakdown": [
                {"date": date.isoformat(), "count": count}
                for date, count in daily_attendance
            ],
            "most_active_students": most_active
        }
        
    except Exception as e:
        logger.error(f"Error fetching attendance summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch attendance summary")


@router.post("/record")
async def record_attendance_manually(
    student_id: str,
    subject_code: Optional[str] = None,
    period: Optional[str] = None,
    status: str = "present",
    confidence_score: float = 1.0,
    db: AsyncSession = Depends(get_db)
):
    """Manually record attendance for a student"""
    try:
        # Verify student exists
        student_query = select(Student).where(Student.id == student_id, Student.is_active == True)
        student_result = await db.execute(student_query)
        student = student_result.scalar_one_or_none()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Create attendance record
        attendance_record = AttendanceRecord(
            student_id=student_id,
            confidence_score=confidence_score,
            subject_code=subject_code,
            period=period,
            status=status,
            location="Manual Entry"
        )
        
        db.add(attendance_record)
        await db.commit()
        await db.refresh(attendance_record)
        
        logger.info(f"Manually recorded attendance for student {student.name}")
        
        # Return response with student info
        record_dict = attendance_record.to_dict()
        record_dict["student_name"] = student.name
        record_dict["student_roll_number"] = student.roll_number
        
        return {
            "message": "Attendance recorded successfully",
            "record": AttendanceResponse(**record_dict)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error recording manual attendance: {e}")
        raise HTTPException(status_code=500, detail="Failed to record attendance")