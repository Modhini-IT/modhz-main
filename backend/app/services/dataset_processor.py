"""
Dataset processor for training face recognition from student photo folders
"""
import os
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import structlog
from PIL import Image

from app.services.recognition_engine import RecognitionEngine
from app.core.config import settings

logger = structlog.get_logger(__name__)


class DatasetProcessor:
    """Process student photo datasets for face recognition training"""
    
    def __init__(self, recognition_engine: RecognitionEngine):
        """Initialize dataset processor"""
        self.recognition_engine = recognition_engine
        self.datasets_path = Path("datasets")
        self.students_path = self.datasets_path / "students"
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp'}
        
    def scan_student_folders(self) -> Dict[str, List[str]]:
        """
        Scan the datasets/students directory for student folders and their images
        
        Returns:
            Dictionary mapping student names to list of image paths
        """
        student_data = {}
        
        try:
            if not self.students_path.exists():
                logger.warning(f"Students directory not found: {self.students_path}")
                return student_data
            
            # Iterate through student folders
            for student_folder in self.students_path.iterdir():
                if not student_folder.is_dir():
                    continue
                
                student_name = student_folder.name
                image_paths = []
                
                # Find all image files in student folder
                for image_file in student_folder.iterdir():
                    if image_file.suffix.lower() in self.supported_formats:
                        image_paths.append(str(image_file))
                
                if image_paths:
                    student_data[student_name] = image_paths
                    logger.info(f"Found {len(image_paths)} images for student: {student_name}")
                else:
                    logger.warning(f"No valid images found for student: {student_name}")
            
            logger.info(f"Scanned {len(student_data)} student folders with images")
            return student_data
            
        except Exception as e:
            logger.error(f"Error scanning student folders: {e}")
            return {}
    
    def load_and_preprocess_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Load and preprocess an image for face recognition
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Preprocessed image array or None if loading fails
        """
        try:
            # Load image using OpenCV
            image = cv2.imread(image_path)
            if image is None:
                logger.warning(f"Could not load image: {image_path}")
                return None
            
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Resize if image is too large (for performance)
            height, width = image_rgb.shape[:2]
            max_dimension = 1024
            
            if max(height, width) > max_dimension:
                scale = max_dimension / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image_rgb = cv2.resize(image_rgb, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            return image_rgb
            
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {e}")
            return None
    
    def extract_face_from_image(self, image: np.ndarray, image_path: str) -> List[Tuple[np.ndarray, float]]:
        """
        Extract face regions from an image with quality scores
        
        Args:
            image: Input image array
            image_path: Path to the image (for logging)
            
        Returns:
            List of tuples containing (face_image, quality_score)
        """
        faces_with_quality = []
        
        try:
            # Convert RGB to BGR for OpenCV processing
            bgr_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # Detect faces
            bounding_boxes = self.recognition_engine.detect_faces(bgr_image)
            
            if not bounding_boxes:
                logger.warning(f"No faces detected in image: {image_path}")
                return faces_with_quality
            
            for bbox in bounding_boxes:
                # Extract face region
                face_region = bgr_image[
                    bbox.y:bbox.y + bbox.height,
                    bbox.x:bbox.x + bbox.width
                ]
                
                if face_region.size == 0:
                    continue
                
                # Validate face quality
                is_valid, quality_score = self.recognition_engine.validate_face_quality(face_region)
                
                if is_valid:
                    faces_with_quality.append((face_region, quality_score))
                    logger.debug(f"Extracted face with quality {quality_score:.3f} from {image_path}")
                else:
                    logger.warning(f"Low quality face (score: {quality_score:.3f}) in {image_path}")
            
            return faces_with_quality
            
        except Exception as e:
            logger.error(f"Error extracting faces from {image_path}: {e}")
            return []
    
    def process_student_images(self, student_name: str, image_paths: List[str]) -> List[np.ndarray]:
        """
        Process all images for a student and extract face embeddings
        
        Args:
            student_name: Name of the student
            image_paths: List of image file paths
            
        Returns:
            List of face embeddings for the student
        """
        embeddings = []
        processed_faces = 0
        
        logger.info(f"Processing {len(image_paths)} images for student: {student_name}")
        
        for image_path in image_paths:
            # Load and preprocess image
            image = self.load_and_preprocess_image(image_path)
            if image is None:
                continue
            
            # Extract faces from image
            faces_with_quality = self.extract_face_from_image(image, image_path)
            
            for face_region, quality_score in faces_with_quality:
                # Extract embedding
                embedding = self.recognition_engine.extract_embedding(face_region)
                
                if embedding is not None:
                    embeddings.append(embedding)
                    processed_faces += 1
                    logger.debug(f"Generated embedding for {student_name} from {os.path.basename(image_path)}")
        
        logger.info(f"Generated {len(embeddings)} embeddings from {processed_faces} faces for {student_name}")
        return embeddings
    
    def process_all_students(self) -> Dict[str, List[np.ndarray]]:
        """
        Process all student folders and generate embeddings
        
        Returns:
            Dictionary mapping student names to their face embeddings
        """
        all_embeddings = {}
        
        # Scan for student folders
        student_data = self.scan_student_folders()
        
        if not student_data:
            logger.warning("No student data found to process")
            return all_embeddings
        
        # Process each student
        for student_name, image_paths in student_data.items():
            try:
                embeddings = self.process_student_images(student_name, image_paths)
                
                if embeddings:
                    all_embeddings[student_name] = embeddings
                    logger.info(f"Successfully processed {len(embeddings)} embeddings for {student_name}")
                else:
                    logger.warning(f"No valid embeddings generated for {student_name}")
                    
            except Exception as e:
                logger.error(f"Error processing student {student_name}: {e}")
                continue
        
        logger.info(f"Dataset processing complete. Processed {len(all_embeddings)} students")
        return all_embeddings
    
    def validate_dataset_structure(self) -> Dict[str, any]:
        """
        Validate the dataset directory structure and provide statistics
        
        Returns:
            Dictionary containing validation results and statistics
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {
                "total_students": 0,
                "total_images": 0,
                "students_with_insufficient_images": [],
                "students_with_no_faces": [],
                "average_images_per_student": 0
            }
        }
        
        try:
            if not self.students_path.exists():
                validation_results["valid"] = False
                validation_results["errors"].append(f"Students directory not found: {self.students_path}")
                return validation_results
            
            student_data = self.scan_student_folders()
            validation_results["statistics"]["total_students"] = len(student_data)
            
            if not student_data:
                validation_results["valid"] = False
                validation_results["errors"].append("No student folders found")
                return validation_results
            
            total_images = 0
            min_images_required = 3
            
            for student_name, image_paths in student_data.items():
                num_images = len(image_paths)
                total_images += num_images
                
                # Check minimum images requirement
                if num_images < min_images_required:
                    validation_results["warnings"].append(
                        f"Student {student_name} has only {num_images} images (minimum {min_images_required} recommended)"
                    )
                    validation_results["statistics"]["students_with_insufficient_images"].append(student_name)
                
                # Quick check for faces in first image
                if image_paths:
                    first_image = self.load_and_preprocess_image(image_paths[0])
                    if first_image is not None:
                        bgr_image = cv2.cvtColor(first_image, cv2.COLOR_RGB2BGR)
                        faces = self.recognition_engine.detect_faces(bgr_image)
                        if not faces:
                            validation_results["warnings"].append(
                                f"No faces detected in sample image for student {student_name}"
                            )
                            validation_results["statistics"]["students_with_no_faces"].append(student_name)
            
            validation_results["statistics"]["total_images"] = total_images
            validation_results["statistics"]["average_images_per_student"] = (
                total_images / len(student_data) if student_data else 0
            )
            
            logger.info(f"Dataset validation complete: {validation_results['statistics']}")
            
        except Exception as e:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Validation error: {str(e)}")
            logger.error(f"Dataset validation failed: {e}")
        
        return validation_results
    
    def create_sample_dataset_structure(self) -> None:
        """Create sample dataset structure with example folders"""
        try:
            # Create main directories
            self.students_path.mkdir(parents=True, exist_ok=True)
            
            # Create sample student folders
            sample_students = [
                "Pranav_A_067",
                "Raghuraman_R_072", 
                "Shivani_T_101",
                "Kumar_S_068",
                "Priya_M_069"
            ]
            
            for student in sample_students:
                student_dir = self.students_path / student
                student_dir.mkdir(exist_ok=True)
                
                # Create a README file in each student folder
                readme_path = student_dir / "README.txt"
                readme_content = f"""Student: {student}
                
Add face images for this student in this folder.
Supported formats: JPG, JPEG, PNG, BMP

Recommended:
- 5-15 clear face images
- Good lighting conditions
- Various angles (front, slight left/right)
- High quality, unblurred images

Example filenames:
- front_face_001.jpg
- front_face_002.jpg
- slight_left_001.jpg
- slight_right_001.jpg
"""
                readme_path.write_text(readme_content)
            
            logger.info(f"Created sample dataset structure with {len(sample_students)} student folders")
            
        except Exception as e:
            logger.error(f"Error creating sample dataset structure: {e}")