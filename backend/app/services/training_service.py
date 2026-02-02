"""
Training service for processing datasets and training face recognition models
"""
import asyncio
from typing import Dict, List, Optional
import structlog
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.dataset_processor import DatasetProcessor
from app.services.recognition_engine import RecognitionEngine
from app.models.student import Student
from app.models.face_embedding import FaceEmbedding
from app.core.database import AsyncSessionLocal

logger = structlog.get_logger(__name__)


class TrainingService:
    """Service for training face recognition models from datasets"""
    
    def __init__(self):
        """Initialize training service"""
        self.recognition_engine = RecognitionEngine()
        self.dataset_processor = DatasetProcessor(self.recognition_engine)
        self.training_status = {
            "is_training": False,
            "current_student": None,
            "progress": 0,
            "total_students": 0,
            "errors": [],
            "completed_students": []
        }
    
    async def train_from_datasets(self) -> Dict[str, any]:
        """
        Train face recognition model from student photo datasets
        
        Returns:
            Training results and statistics
        """
        if self.training_status["is_training"]:
            return {
                "success": False,
                "message": "Training already in progress",
                "status": self.training_status
            }
        
        try:
            # Reset training status
            self.training_status = {
                "is_training": True,
                "current_student": None,
                "progress": 0,
                "total_students": 0,
                "errors": [],
                "completed_students": []
            }
            
            logger.info("Starting face recognition training from datasets")
            
            # Validate dataset structure
            validation_results = self.dataset_processor.validate_dataset_structure()
            if not validation_results["valid"]:
                self.training_status["is_training"] = False
                return {
                    "success": False,
                    "message": "Dataset validation failed",
                    "validation_results": validation_results
                }
            
            # Process all student datasets
            all_embeddings = self.dataset_processor.process_all_students()
            
            if not all_embeddings:
                self.training_status["is_training"] = False
                return {
                    "success": False,
                    "message": "No valid embeddings generated from datasets"
                }
            
            self.training_status["total_students"] = len(all_embeddings)
            
            # Store embeddings in database
            training_results = await self._store_embeddings_in_database(all_embeddings)
            
            # Update recognition engine with new embeddings
            await self._update_recognition_engine()
            
            self.training_status["is_training"] = False
            
            logger.info(f"Training completed successfully for {len(all_embeddings)} students")
            
            return {
                "success": True,
                "message": "Training completed successfully",
                "results": training_results,
                "validation_results": validation_results,
                "status": self.training_status
            }
            
        except Exception as e:
            self.training_status["is_training"] = False
            self.training_status["errors"].append(str(e))
            logger.error(f"Training failed: {e}")
            
            return {
                "success": False,
                "message": f"Training failed: {str(e)}",
                "status": self.training_status
            }
    
    async def _store_embeddings_in_database(self, all_embeddings: Dict[str, List[np.ndarray]]) -> Dict[str, any]:
        """
        Store face embeddings in database
        
        Args:
            all_embeddings: Dictionary mapping student names to embeddings
            
        Returns:
            Storage results and statistics
        """
        results = {
            "students_created": 0,
            "students_updated": 0,
            "embeddings_stored": 0,
            "errors": []
        }
        
        async with AsyncSessionLocal() as session:
            try:
                for student_name, embeddings in all_embeddings.items():
                    self.training_status["current_student"] = student_name
                    
                    try:
                        # Check if student already exists
                        stmt = select(Student).where(Student.name == student_name)
                        result = await session.execute(stmt)
                        existing_student = result.scalar_one_or_none()
                        
                        if existing_student:
                            # Update existing student
                            student = existing_student
                            student.is_active = True
                            results["students_updated"] += 1
                            
                            # Remove old embeddings
                            for old_embedding in student.face_embeddings:
                                await session.delete(old_embedding)
                            
                        else:
                            # Create new student
                            # Extract additional info from folder name if available
                            name_parts = student_name.replace('_', ' ').split()
                            roll_number = None
                            clean_name = student_name
                            
                            # Try to extract roll number from name
                            if name_parts and name_parts[-1].isdigit():
                                roll_number = name_parts[-1]
                                clean_name = ' '.join(name_parts[:-1])
                            
                            student = Student(
                                name=clean_name,
                                student_number=roll_number,
                                roll_number=roll_number,
                                is_active=True
                            )
                            session.add(student)
                            results["students_created"] += 1
                        
                        # Store embeddings
                        for i, embedding in enumerate(embeddings):
                            # Serialize embedding to bytes
                            embedding_bytes = embedding.astype(np.float64).tobytes()
                            
                            face_embedding = FaceEmbedding(
                                student_id=student.id,
                                embedding=embedding_bytes,
                                quality_score=0.8  # Default quality score
                            )
                            session.add(face_embedding)
                            results["embeddings_stored"] += 1
                        
                        await session.commit()
                        
                        self.training_status["completed_students"].append(student_name)
                        self.training_status["progress"] = len(self.training_status["completed_students"])
                        
                        logger.info(f"Stored {len(embeddings)} embeddings for student: {student_name}")
                        
                    except Exception as e:
                        await session.rollback()
                        error_msg = f"Error storing data for student {student_name}: {str(e)}"
                        results["errors"].append(error_msg)
                        self.training_status["errors"].append(error_msg)
                        logger.error(error_msg)
                        continue
                
                logger.info(f"Database storage complete: {results}")
                return results
                
            except Exception as e:
                await session.rollback()
                error_msg = f"Database storage failed: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
                raise
    
    async def _update_recognition_engine(self) -> None:
        """Update recognition engine with latest embeddings from database"""
        try:
            async with AsyncSessionLocal() as session:
                # Load all active students with their embeddings
                stmt = select(Student).where(Student.is_active == True)
                result = await session.execute(stmt)
                students = result.scalars().all()
                
                student_embeddings = {}
                
                for student in students:
                    embeddings_bytes = []
                    for face_embedding in student.face_embeddings:
                        embeddings_bytes.append(face_embedding.embedding)
                    
                    if embeddings_bytes:
                        student_embeddings[student.id] = embeddings_bytes
                
                # Load embeddings into recognition engine
                self.recognition_engine.load_known_faces(student_embeddings)
                
                logger.info(f"Updated recognition engine with {len(student_embeddings)} students")
                
        except Exception as e:
            logger.error(f"Failed to update recognition engine: {e}")
            raise
    
    async def get_training_status(self) -> Dict[str, any]:
        """Get current training status"""
        return {
            "status": self.training_status,
            "dataset_info": self.dataset_processor.validate_dataset_structure()
        }
    
    async def enroll_single_student(self, student_name: str, image_files: List[bytes]) -> Dict[str, any]:
        """
        Enroll a single student with provided image files
        
        Args:
            student_name: Name of the student
            image_files: List of image file bytes
            
        Returns:
            Enrollment results
        """
        try:
            logger.info(f"Enrolling single student: {student_name}")
            
            # Process images and extract embeddings
            embeddings = []
            
            for i, image_bytes in enumerate(image_files):
                try:
                    # Convert bytes to numpy array
                    nparr = np.frombuffer(image_bytes, np.uint8)
                    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if image is None:
                        logger.warning(f"Could not decode image {i} for student {student_name}")
                        continue
                    
                    # Extract faces and embeddings
                    faces_with_quality = self.dataset_processor.extract_face_from_image(
                        cv2.cvtColor(image, cv2.COLOR_BGR2RGB), 
                        f"upload_{i}"
                    )
                    
                    for face_region, quality_score in faces_with_quality:
                        embedding = self.recognition_engine.extract_embedding(face_region)
                        if embedding is not None:
                            embeddings.append(embedding)
                    
                except Exception as e:
                    logger.error(f"Error processing image {i} for student {student_name}: {e}")
                    continue
            
            if not embeddings:
                return {
                    "success": False,
                    "message": "No valid face embeddings could be extracted from provided images"
                }
            
            # Store in database
            embedding_dict = {student_name: embeddings}
            results = await self._store_embeddings_in_database(embedding_dict)
            
            # Update recognition engine
            await self._update_recognition_engine()
            
            return {
                "success": True,
                "message": f"Successfully enrolled student {student_name}",
                "embeddings_count": len(embeddings),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Single student enrollment failed: {e}")
            return {
                "success": False,
                "message": f"Enrollment failed: {str(e)}"
            }
    
    async def get_dataset_statistics(self) -> Dict[str, any]:
        """Get comprehensive dataset statistics"""
        try:
            # Scan filesystem
            student_data = self.dataset_processor.scan_student_folders()
            
            # Get database statistics
            async with AsyncSessionLocal() as session:
                stmt = select(Student).where(Student.is_active == True)
                result = await session.execute(stmt)
                db_students = result.scalars().all()
                
                db_stats = {
                    "total_students_in_db": len(db_students),
                    "total_embeddings_in_db": sum(len(s.face_embeddings) for s in db_students),
                    "students_in_db": [s.name for s in db_students]
                }
            
            # Filesystem statistics
            fs_stats = {
                "total_student_folders": len(student_data),
                "total_images_in_folders": sum(len(images) for images in student_data.values()),
                "students_in_folders": list(student_data.keys()),
                "images_per_student": {name: len(images) for name, images in student_data.items()}
            }
            
            # Validation results
            validation = self.dataset_processor.validate_dataset_structure()
            
            return {
                "filesystem": fs_stats,
                "database": db_stats,
                "validation": validation,
                "training_status": self.training_status
            }
            
        except Exception as e:
            logger.error(f"Error getting dataset statistics: {e}")
            return {
                "error": str(e),
                "training_status": self.training_status
            }