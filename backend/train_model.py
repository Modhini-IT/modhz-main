#!/usr/bin/env python3
"""
Face Recognition Model Training Script
Processes student dataset and creates face embeddings for recognition
"""

import os
import sys
import cv2
import numpy as np
import face_recognition
from pathlib import Path
import json
import logging
from typing import Dict, List
import sqlite3
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import engine, SessionLocal
from app.models.student import Student
from app.models.face_embedding import FaceEmbedding
from sqlalchemy.orm import Session

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FaceTrainer:
    """Face recognition model trainer"""
    
    def __init__(self, dataset_path: str = "datasets/students"):
        self.dataset_path = Path(dataset_path)
        self.model = "hog"  # Use HOG for CPU training
        self.embeddings_data = {}
        
    def load_student_images(self) -> Dict[str, List[str]]:
        """Load all student images from dataset directory"""
        student_images = {}
        
        if not self.dataset_path.exists():
            logger.error(f"Dataset path {self.dataset_path} does not exist")
            return student_images
        
        for student_dir in self.dataset_path.iterdir():
            if student_dir.is_dir() and not student_dir.name.startswith('.'):
                student_id = student_dir.name
                image_files = []
                
                # Find all image files
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
                    image_files.extend(student_dir.glob(ext))
                    image_files.extend(student_dir.glob(ext.upper()))
                
                if image_files:
                    student_images[student_id] = [str(f) for f in image_files]
                    logger.info(f"Found {len(image_files)} images for student {student_id}")
        
        return student_images
    
    def extract_face_embeddings(self, image_path: str) -> List[np.ndarray]:
        """Extract face embeddings from an image"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                logger.warning(f"Could not load image: {image_path}")
                return []
            
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Find face locations and encodings
            face_locations = face_recognition.face_locations(rgb_image, model=self.model)
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations, model="large")
            
            if not face_encodings:
                logger.warning(f"No faces found in image: {image_path}")
                return []
            
            logger.info(f"Extracted {len(face_encodings)} face(s) from {image_path}")
            return face_encodings
            
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            return []
    
    def train_student_embeddings(self, student_images: Dict[str, List[str]]) -> Dict[str, List[np.ndarray]]:
        """Train face embeddings for all students"""
        student_embeddings = {}
        
        for student_id, image_paths in student_images.items():
            logger.info(f"Processing student: {student_id}")
            embeddings = []
            
            for image_path in image_paths:
                face_embeddings = self.extract_face_embeddings(image_path)
                embeddings.extend(face_embeddings)
            
            if embeddings:
                student_embeddings[student_id] = embeddings
                logger.info(f"Created {len(embeddings)} embeddings for {student_id}")
            else:
                logger.warning(f"No valid embeddings created for {student_id}")
        
        return student_embeddings
    
    def save_to_database(self, student_embeddings: Dict[str, List[np.ndarray]]):
        """Save student data and embeddings to database"""
        db = SessionLocal()
        
        try:
            for student_id, embeddings in student_embeddings.items():
                # Parse student info from directory name (format: Name_Initial_RollNo)
                parts = student_id.split('_')
                if len(parts) >= 3:
                    name = parts[0]
                    roll_number = parts[-1]
                else:
                    name = student_id
                    roll_number = student_id
                
                # Check if student already exists
                existing_student = db.query(Student).filter(Student.roll_number == roll_number).first()
                
                if existing_student:
                    logger.info(f"Student {roll_number} already exists, updating embeddings")
                    student = existing_student
                    # Delete existing embeddings
                    db.query(FaceEmbedding).filter(FaceEmbedding.student_id == student.id).delete()
                else:
                    # Create new student
                    student = Student(
                        name=name,
                        roll_number=roll_number,
                        email=f"{roll_number}@student.edu",
                        is_active=True
                    )
                    db.add(student)
                    db.flush()  # Get the student ID
                    logger.info(f"Created new student: {name} ({roll_number})")
                
                # Save embeddings
                for i, embedding in enumerate(embeddings):
                    face_embedding = FaceEmbedding(
                        student_id=student.id,
                        embedding_data=embedding.tobytes(),
                        confidence_score=1.0,
                        created_at=datetime.utcnow()
                    )
                    db.add(face_embedding)
                
                logger.info(f"Saved {len(embeddings)} embeddings for {name}")
            
            db.commit()
            logger.info("Successfully saved all data to database")
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def save_embeddings_json(self, student_embeddings: Dict[str, List[np.ndarray]], output_path: str = "face_embeddings.json"):
        """Save embeddings to JSON file for backup"""
        try:
            # Convert numpy arrays to lists for JSON serialization
            json_data = {}
            for student_id, embeddings in student_embeddings.items():
                json_data[student_id] = [embedding.tolist() for embedding in embeddings]
            
            with open(output_path, 'w') as f:
                json.dump(json_data, f, indent=2)
            
            logger.info(f"Saved embeddings to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving embeddings to JSON: {e}")
    
    def run_training(self):
        """Run the complete training process"""
        logger.info("Starting face recognition training...")
        
        # Load student images
        student_images = self.load_student_images()
        if not student_images:
            logger.error("No student images found!")
            return False
        
        logger.info(f"Found {len(student_images)} students with images")
        
        # Extract embeddings
        student_embeddings = self.train_student_embeddings(student_images)
        if not student_embeddings:
            logger.error("No embeddings created!")
            return False
        
        # Save to database
        try:
            self.save_to_database(student_embeddings)
        except Exception as e:
            logger.error(f"Failed to save to database: {e}")
            return False
        
        # Save backup JSON
        self.save_embeddings_json(student_embeddings)
        
        logger.info("Training completed successfully!")
        return True

def main():
    """Main training function"""
    # Initialize database tables
    from app.models import student, face_embedding, attendance_record
    from app.core.database import Base
    
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Run training
    trainer = FaceTrainer()
    success = trainer.run_training()
    
    if success:
        logger.info("✅ Face recognition model training completed successfully!")
        print("\n🎉 Training Complete!")
        print("Your face recognition system is ready to use.")
        print("Run 'python -m uvicorn app.main:app --reload' to start the server.")
    else:
        logger.error("❌ Training failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()