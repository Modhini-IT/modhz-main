"""
Face Recognition Engine using face_recognition library (no dlib dependency)
"""
import cv2
import numpy as np
import face_recognition
from typing import List, Optional, Dict, Tuple
import structlog
from dataclasses import dataclass
import hashlib

from app.core.config import settings

logger = structlog.get_logger(__name__)


@dataclass
class BoundingBox:
    """Face bounding box coordinates"""
    x: int
    y: int
    width: int
    height: int


@dataclass
class RecognitionResult:
    """Face recognition result"""
    student_id: Optional[str]
    confidence: float
    bounding_box: BoundingBox
    embedding: np.ndarray
    timestamp: str


class RecognitionEngine:
    """Core face recognition engine using face_recognition library"""
    
    def __init__(self, model: str = "hog"):
        """Initialize the recognition engine"""
        self.model = model  # "hog" for CPU, "cnn" for GPU
        self.known_faces: Dict[str, List[np.ndarray]] = {}
        self.recognition_threshold = getattr(settings, 'FACE_RECOGNITION_THRESHOLD', 0.6)
        
        logger.info(f"Recognition engine initialized with {model} model")
    
    def detect_faces(self, frame: np.ndarray) -> List[BoundingBox]:
        """
        Detect faces in a frame using face_recognition library
        
        Args:
            frame: Input image frame
            
        Returns:
            List of bounding boxes for detected faces
        """
        try:
            # Convert BGR to RGB for face_recognition
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect face locations
            face_locations = face_recognition.face_locations(rgb_frame, model=self.model)
            
            bounding_boxes = []
            for (top, right, bottom, left) in face_locations:
                bbox = BoundingBox(
                    x=left,
                    y=top,
                    width=right - left,
                    height=bottom - top
                )
                bounding_boxes.append(bbox)
            
            logger.debug(f"Detected {len(bounding_boxes)} faces")
            return bounding_boxes
            
        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            return []
    
    def extract_embedding(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract 128-dimensional face embedding using face_recognition library
        
        Args:
            face_image: Cropped face image
            
        Returns:
            128-dimensional face embedding or None if extraction fails
        """
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            
            # Extract face encodings
            encodings = face_recognition.face_encodings(rgb_image, model=self.model)
            
            if len(encodings) > 0:
                embedding = encodings[0]
                
                # Normalize to unit hypersphere
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
                
                logger.debug(f"Extracted embedding with shape: {embedding.shape}")
                return embedding
            else:
                logger.warning("No face encoding found in image")
                return None
                
        except Exception as e:
            logger.error(f"Embedding extraction failed: {e}")
            return None
    
    def compare_embeddings(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compare two face embeddings using Euclidean distance
        
        Args:
            embedding1: First face embedding
            embedding2: Second face embedding
            
        Returns:
            Similarity score (higher = more similar)
        """
        try:
            # Calculate Euclidean distance
            distance = np.linalg.norm(embedding1 - embedding2)
            
            # Convert distance to similarity (0-1 scale, 1 = identical)
            # face_recognition typically uses 0.6 as threshold
            similarity = max(0.0, 1.0 - (distance / 0.6))
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Embedding comparison failed: {e}")
            return 0.0
    
    def recognize_face(self, frame: np.ndarray) -> List[RecognitionResult]:
        """
        Recognize faces in a frame
        
        Args:
            frame: Input image frame
            
        Returns:
            List of recognition results
        """
        results = []
        
        try:
            # Detect faces
            bounding_boxes = self.detect_faces(frame)
            
            for bbox in bounding_boxes:
                # Extract face region
                face_region = frame[
                    bbox.y:bbox.y + bbox.height,
                    bbox.x:bbox.x + bbox.width
                ]
                
                # Extract embedding
                embedding = self.extract_embedding(face_region)
                if embedding is None:
                    continue
                
                # Find best match
                best_match_id = None
                best_confidence = 0.0
                
                for student_id, known_embeddings in self.known_faces.items():
                    for known_embedding in known_embeddings:
                        similarity = self.compare_embeddings(embedding, known_embedding)
                        
                        if similarity > best_confidence and similarity > self.recognition_threshold:
                            best_confidence = similarity
                            best_match_id = student_id
                
                # Create result
                result = RecognitionResult(
                    student_id=best_match_id,
                    confidence=best_confidence,
                    bounding_box=bbox,
                    embedding=embedding,
                    timestamp=str(np.datetime64('now'))
                )
                
                results.append(result)
                
                if best_match_id:
                    logger.info(f"Recognized student {best_match_id} with confidence {best_confidence:.3f}")
                else:
                    logger.debug(f"Unknown face detected with max confidence {best_confidence:.3f}")
            
            return results
            
        except Exception as e:
            logger.error(f"Face recognition failed: {e}")
            return []
    
    def load_known_faces(self, student_embeddings: Dict[str, List[bytes]]) -> None:
        """
        Load known face embeddings for recognition
        
        Args:
            student_embeddings: Dictionary mapping student IDs to their face embeddings
        """
        try:
            self.known_faces.clear()
            
            for student_id, embedding_bytes_list in student_embeddings.items():
                embeddings = []
                for embedding_bytes in embedding_bytes_list:
                    # Deserialize numpy array from bytes
                    embedding = np.frombuffer(embedding_bytes, dtype=np.float64)
                    embeddings.append(embedding)
                
                self.known_faces[student_id] = embeddings
            
            total_faces = sum(len(embeddings) for embeddings in self.known_faces.values())
            logger.info(f"Loaded {total_faces} face embeddings for {len(self.known_faces)} students")
            
        except Exception as e:
            logger.error(f"Failed to load known faces: {e}")
    
    def validate_face_quality(self, face_image: np.ndarray) -> Tuple[bool, float]:
        """
        Validate face image quality
        
        Args:
            face_image: Face image to validate
            
        Returns:
            Tuple of (is_valid, quality_score)
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            
            # Calculate Laplacian variance (blur detection)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Normalize quality score (higher is better)
            quality_score = min(laplacian_var / 1000.0, 1.0)
            
            # Check if quality meets threshold
            quality_threshold = getattr(settings, 'FACE_QUALITY_THRESHOLD', 0.1)
            is_valid = quality_score >= quality_threshold
            
            logger.debug(f"Face quality score: {quality_score:.3f}, valid: {is_valid}")
            
            return is_valid, quality_score
            
        except Exception as e:
            logger.error(f"Face quality validation failed: {e}")
            return False, 0.0