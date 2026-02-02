"""
Student management API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import structlog

from app.core.database import get_db
from app.models.student import Student
from app.models.face_embedding import FaceEmbedding
from app.services.training_service import TrainingService
from app.schemas.student import StudentCreate, StudentResponse, StudentUpdate

logger = structlog.get_logger(__name__)
router = APIRouter()

# Global training service instance
training_service = TrainingService()


@router.get("/", response_model=List[StudentResponse])
async def get_students(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get list of students with optional search"""
    try:
        query = select(Student).where(Student.is_active == True)
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Student.name.ilike(search_term)) |
                (Student.student_number.ilike(search_term)) |
                (Student.roll_number.ilike(search_term))
            )
        
        query = query.offset(skip).limit(limit).order_by(Student.name)
        result = await db.execute(query)
        students = result.scalars().all()
        
        return [StudentResponse.from_orm(student) for student in students]
        
    except Exception as e:
        logger.error(f"Error fetching students: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch students")


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(student_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific student by ID"""
    try:
        stmt = select(Student).where(Student.id == student_id, Student.is_active == True)
        result = await db.execute(stmt)
        student = result.scalar_one_or_none()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        return StudentResponse.from_orm(student)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student {student_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch student")


@router.post("/", response_model=StudentResponse)
async def create_student(
    student_data: StudentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new student"""
    try:
        # Check if student already exists
        existing_query = select(Student).where(
            (Student.name == student_data.name) |
            (Student.student_number == student_data.student_number) |
            (Student.roll_number == student_data.roll_number)
        )
        result = await db.execute(existing_query)
        existing_student = result.scalar_one_or_none()
        
        if existing_student:
            raise HTTPException(
                status_code=400, 
                detail="Student with this name, student number, or roll number already exists"
            )
        
        # Create new student
        student = Student(**student_data.dict())
        db.add(student)
        await db.commit()
        await db.refresh(student)
        
        logger.info(f"Created new student: {student.name} (ID: {student.id})")
        return StudentResponse.from_orm(student)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating student: {e}")
        raise HTTPException(status_code=500, detail="Failed to create student")


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: str,
    student_data: StudentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing student"""
    try:
        stmt = select(Student).where(Student.id == student_id, Student.is_active == True)
        result = await db.execute(stmt)
        student = result.scalar_one_or_none()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Update student fields
        update_data = student_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(student, field, value)
        
        await db.commit()
        await db.refresh(student)
        
        logger.info(f"Updated student: {student.name} (ID: {student.id})")
        return StudentResponse.from_orm(student)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating student {student_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update student")


@router.delete("/{student_id}")
async def delete_student(student_id: str, db: AsyncSession = Depends(get_db)):
    """Soft delete a student (mark as inactive)"""
    try:
        stmt = select(Student).where(Student.id == student_id, Student.is_active == True)
        result = await db.execute(stmt)
        student = result.scalar_one_or_none()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Soft delete by marking as inactive
        student.is_active = False
        await db.commit()
        
        logger.info(f"Deleted student: {student.name} (ID: {student.id})")
        return {"message": "Student deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting student {student_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete student")


@router.post("/enroll")
async def enroll_student_with_images(
    name: str = Form(...),
    student_number: Optional[str] = Form(None),
    roll_number: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    section: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    images: List[UploadFile] = File(...)
):
    """Enroll a student with face images for training"""
    try:
        if not images:
            raise HTTPException(status_code=400, detail="At least one image is required")
        
        # Validate image files
        valid_types = {"image/jpeg", "image/jpg", "image/png"}
        image_bytes_list = []
        
        for image in images:
            if image.content_type not in valid_types:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid image type: {image.content_type}. Supported: JPEG, PNG"
                )
            
            content = await image.read()
            if len(content) > 10 * 1024 * 1024:  # 10MB limit
                raise HTTPException(status_code=400, detail="Image file too large (max 10MB)")
            
            image_bytes_list.append(content)
        
        # Enroll student using training service
        result = await training_service.enroll_single_student(name, image_bytes_list)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        logger.info(f"Successfully enrolled student {name} with {len(images)} images")
        
        return {
            "message": f"Student {name} enrolled successfully",
            "embeddings_count": result["embeddings_count"],
            "details": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enrolling student with images: {e}")
        raise HTTPException(status_code=500, detail="Failed to enroll student")


@router.get("/stats/summary")
async def get_student_statistics(db: AsyncSession = Depends(get_db)):
    """Get student statistics summary"""
    try:
        # Total active students
        total_students_query = select(func.count(Student.id)).where(Student.is_active == True)
        total_result = await db.execute(total_students_query)
        total_students = total_result.scalar()
        
        # Students with face embeddings
        students_with_faces_query = select(func.count(func.distinct(FaceEmbedding.student_id)))
        faces_result = await db.execute(students_with_faces_query)
        students_with_faces = faces_result.scalar()
        
        # Total face embeddings
        total_embeddings_query = select(func.count(FaceEmbedding.id))
        embeddings_result = await db.execute(total_embeddings_query)
        total_embeddings = embeddings_result.scalar()
        
        # Students by department
        dept_query = select(Student.department, func.count(Student.id)).where(
            Student.is_active == True
        ).group_by(Student.department)
        dept_result = await db.execute(dept_query)
        departments = {dept: count for dept, count in dept_result.all()}
        
        return {
            "total_students": total_students,
            "students_with_face_data": students_with_faces,
            "total_face_embeddings": total_embeddings,
            "students_by_department": departments,
            "recognition_ready": students_with_faces > 0
        }
        
    except Exception as e:
        logger.error(f"Error fetching student statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")