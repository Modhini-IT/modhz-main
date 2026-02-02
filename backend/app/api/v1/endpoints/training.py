"""
Training and dataset management API endpoints
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
import structlog

from app.services.training_service import TrainingService
from app.services.dataset_processor import DatasetProcessor
from app.services.recognition_engine import RecognitionEngine

logger = structlog.get_logger(__name__)
router = APIRouter()

# Global service instances
training_service = TrainingService()
recognition_engine = RecognitionEngine()


@router.post("/train-from-datasets")
async def train_from_datasets(background_tasks: BackgroundTasks):
    """Train face recognition model from student photo datasets"""
    try:
        # Check if training is already in progress
        if training_service.training_status["is_training"]:
            return {
                "success": False,
                "message": "Training already in progress",
                "status": training_service.training_status
            }
        
        # Start training in background
        background_tasks.add_task(training_service.train_from_datasets)
        
        return {
            "success": True,
            "message": "Training started in background",
            "status": training_service.training_status
        }
        
    except Exception as e:
        logger.error(f"Error starting training: {e}")
        raise HTTPException(status_code=500, detail="Failed to start training")


@router.get("/status")
async def get_training_status():
    """Get current training status and dataset information"""
    try:
        status = await training_service.get_training_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting training status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get training status")


@router.get("/dataset/validate")
async def validate_dataset():
    """Validate dataset structure and provide recommendations"""
    try:
        dataset_processor = DatasetProcessor(recognition_engine)
        validation_results = dataset_processor.validate_dataset_structure()
        
        return {
            "validation_results": validation_results,
            "recommendations": _generate_recommendations(validation_results)
        }
        
    except Exception as e:
        logger.error(f"Error validating dataset: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate dataset")


@router.get("/dataset/statistics")
async def get_dataset_statistics():
    """Get comprehensive dataset statistics"""
    try:
        stats = await training_service.get_dataset_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting dataset statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dataset statistics")


@router.post("/dataset/scan")
async def scan_dataset():
    """Scan dataset directory for student folders and images"""
    try:
        dataset_processor = DatasetProcessor(recognition_engine)
        student_data = dataset_processor.scan_student_folders()
        
        total_students = len(student_data)
        total_images = sum(len(images) for images in student_data.values())
        
        return {
            "success": True,
            "total_students": total_students,
            "total_images": total_images,
            "students": {
                name: {
                    "image_count": len(images),
                    "sample_images": images[:3]  # Show first 3 images as samples
                }
                for name, images in student_data.items()
            }
        }
        
    except Exception as e:
        logger.error(f"Error scanning dataset: {e}")
        raise HTTPException(status_code=500, detail="Failed to scan dataset")


@router.post("/dataset/create-sample")
async def create_sample_dataset():
    """Create sample dataset structure with example folders"""
    try:
        dataset_processor = DatasetProcessor(recognition_engine)
        dataset_processor.create_sample_dataset_structure()
        
        return {
            "success": True,
            "message": "Sample dataset structure created successfully",
            "path": "backend/datasets/students/",
            "instructions": [
                "Add student photos to their respective folders",
                "Use formats: JPG, JPEG, PNG, BMP",
                "Include 5-15 clear face images per student",
                "Ensure good lighting and various angles",
                "Run training after adding photos"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error creating sample dataset: {e}")
        raise HTTPException(status_code=500, detail="Failed to create sample dataset")


@router.post("/model/reload")
async def reload_recognition_model():
    """Reload the recognition model with latest training data"""
    try:
        await training_service._update_recognition_engine()
        
        known_faces_count = len(recognition_engine.known_faces)
        
        return {
            "success": True,
            "message": "Recognition model reloaded successfully",
            "known_faces_count": known_faces_count,
            "threshold": recognition_engine.recognition_threshold
        }
        
    except Exception as e:
        logger.error(f"Error reloading model: {e}")
        raise HTTPException(status_code=500, detail="Failed to reload recognition model")


@router.get("/model/info")
async def get_model_info():
    """Get information about the current recognition model"""
    try:
        return {
            "known_faces_count": len(recognition_engine.known_faces),
            "recognition_threshold": recognition_engine.recognition_threshold,
            "model_loaded": len(recognition_engine.known_faces) > 0,
            "students_in_model": list(recognition_engine.known_faces.keys()),
            "embeddings_per_student": {
                student_id: len(embeddings) 
                for student_id, embeddings in recognition_engine.known_faces.items()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model information")


@router.post("/model/update-threshold")
async def update_recognition_threshold(threshold: float):
    """Update the face recognition threshold"""
    try:
        if not 0.0 <= threshold <= 1.0:
            raise HTTPException(
                status_code=400, 
                detail="Threshold must be between 0.0 and 1.0"
            )
        
        old_threshold = recognition_engine.recognition_threshold
        recognition_engine.recognition_threshold = threshold
        
        return {
            "success": True,
            "message": "Recognition threshold updated successfully",
            "old_threshold": old_threshold,
            "new_threshold": threshold
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating threshold: {e}")
        raise HTTPException(status_code=500, detail="Failed to update recognition threshold")


def _generate_recommendations(validation_results: Dict[str, Any]) -> list:
    """Generate recommendations based on validation results"""
    recommendations = []
    
    if not validation_results["valid"]:
        recommendations.append("Fix validation errors before training")
    
    stats = validation_results["statistics"]
    
    if stats["total_students"] == 0:
        recommendations.append("Add student folders with photos to datasets/students/")
    
    if stats["total_images"] < stats["total_students"] * 5:
        recommendations.append("Add more images per student (recommended: 5-15 images)")
    
    if stats["students_with_insufficient_images"]:
        recommendations.append(
            f"Add more images for students: {', '.join(stats['students_with_insufficient_images'][:3])}"
        )
    
    if stats["students_with_no_faces"]:
        recommendations.append(
            f"Check image quality for students: {', '.join(stats['students_with_no_faces'][:3])}"
        )
    
    if stats["average_images_per_student"] < 5:
        recommendations.append("Increase average images per student to at least 5")
    
    if not recommendations:
        recommendations.append("Dataset looks good! Ready for training.")
    
    return recommendations