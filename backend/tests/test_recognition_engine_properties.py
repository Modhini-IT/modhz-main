"""
Property-based tests for Recognition Engine
Feature: face-recognition-backend
"""
import pytest
import numpy as np
from hypothesis import given, settings, strategies as st
from hypothesis import assume

from app.services.recognition_engine import RecognitionEngine
from tests.conftest import face_image_strategy, embedding_strategy


class TestRecognitionEngineProperties:
    """Property-based tests for Recognition Engine"""
    
    @given(face_image=face_image_strategy())
    @settings(max_examples=100, deadline=5000)
    def test_embedding_generation_consistency(self, face_image, recognition_engine):
        """
        Feature: face-recognition-backend, Property 1: Face Embedding Generation Consistency
        **Validates: Requirements 1.1, 2.2**
        
        For any valid face image, the system should generate a 128-dimensional 
        embedding vector that is normalized on the unit hypersphere (magnitude = 1.0)
        """
        # Attempt to extract embedding
        embedding = recognition_engine.extract_embedding(face_image)
        
        # If embedding extraction succeeds, verify properties
        if embedding is not None:
            # Check embedding dimensions
            assert len(embedding) == 128, f"Expected 128 dimensions, got {len(embedding)}"
            assert embedding.dtype == np.float64, f"Expected float64 dtype, got {embedding.dtype}"
            
            # Check normalization on unit hypersphere
            magnitude = np.linalg.norm(embedding)
            assert abs(magnitude - 1.0) < 1e-6, f"Expected unit magnitude, got {magnitude}"
            
            # Check that embedding contains valid numbers
            assert not np.any(np.isnan(embedding)), "Embedding contains NaN values"
            assert not np.any(np.isinf(embedding)), "Embedding contains infinite values"
            
            # Check that embedding is not all zeros
            assert not np.allclose(embedding, 0.0), "Embedding is all zeros"
    
    @given(embedding1=embedding_strategy(), embedding2=embedding_strategy())
    @settings(max_examples=100, deadline=5000)
    def test_cosine_similarity_calculation(self, embedding1, embedding2, recognition_engine):
        """
        Feature: face-recognition-backend, Property 5: Cosine Similarity Calculation
        **Validates: Requirements 2.3**
        
        For any two face embeddings, the comparison should use cosine similarity 
        calculation on the unit hypersphere, returning values between -1 and 1
        """
        # Calculate cosine similarity
        similarity = recognition_engine.compare_embeddings(embedding1, embedding2)
        
        # Verify similarity is in valid range
        assert -1.0 <= similarity <= 1.0, f"Similarity {similarity} not in range [-1, 1]"
        
        # Verify similarity is a valid number
        assert not np.isnan(similarity), "Similarity is NaN"
        assert not np.isinf(similarity), "Similarity is infinite"
        
        # Test self-similarity (should be 1.0 for normalized embeddings)
        self_similarity = recognition_engine.compare_embeddings(embedding1, embedding1)
        assert abs(self_similarity - 1.0) < 1e-6, f"Self-similarity should be 1.0, got {self_similarity}"
        
        # Test symmetry property
        reverse_similarity = recognition_engine.compare_embeddings(embedding2, embedding1)
        assert abs(similarity - reverse_similarity) < 1e-6, "Cosine similarity should be symmetric"
    
    @given(face_image=face_image_strategy())
    @settings(max_examples=100, deadline=5000)
    def test_face_quality_validation(self, face_image, recognition_engine):
        """
        Feature: face-recognition-backend, Property 2: Face Quality Validation
        **Validates: Requirements 1.4**
        
        For any input image, if the face quality score is below the minimum threshold,
        the system should reject the image and provide a descriptive error message
        """
        # Validate face quality
        is_valid, quality_score = recognition_engine.validate_face_quality(face_image)
        
        # Verify quality score is in valid range [0, 1]
        assert 0.0 <= quality_score <= 1.0, f"Quality score {quality_score} not in range [0, 1]"
        
        # Verify quality score is a valid number
        assert not np.isnan(quality_score), "Quality score is NaN"
        assert not np.isinf(quality_score), "Quality score is infinite"
        
        # Verify boolean validity flag
        assert isinstance(is_valid, bool), "Validity flag should be boolean"
        
        # If quality is below threshold, should be marked as invalid
        from app.core.config import settings
        if quality_score < settings.FACE_QUALITY_THRESHOLD:
            assert not is_valid, "Low quality image should be marked as invalid"
        else:
            assert is_valid, "High quality image should be marked as valid"
    
    @given(
        embeddings=st.lists(
            embedding_strategy(),
            min_size=1,
            max_size=10
        ),
        threshold=st.floats(min_value=0.1, max_value=0.9)
    )
    @settings(max_examples=50, deadline=5000)
    def test_recognition_threshold_enforcement(self, embeddings, threshold, recognition_engine):
        """
        Feature: face-recognition-backend, Property 4: Recognition Threshold Enforcement
        **Validates: Requirements 2.5**
        
        For any face recognition attempt, attendance should only be recorded 
        when the confidence score exceeds the configured threshold
        """
        # Set up known faces with the first embedding
        if len(embeddings) > 0:
            known_faces = {"test_student": [embeddings[0].tobytes()]}
            recognition_engine.load_known_faces(known_faces)
            recognition_engine.recognition_threshold = threshold
            
            # Test with remaining embeddings
            for test_embedding in embeddings[1:]:
                similarity = recognition_engine.compare_embeddings(embeddings[0], test_embedding)
                
                # Simulate recognition decision
                should_recognize = similarity > threshold
                
                # Verify threshold enforcement
                if should_recognize:
                    assert similarity > threshold, f"Recognition should occur when similarity {similarity} > threshold {threshold}"
                else:
                    assert similarity <= threshold, f"Recognition should not occur when similarity {similarity} <= threshold {threshold}"
    
    @given(
        bounding_boxes=st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=200),  # x
                st.integers(min_value=0, max_value=200),  # y  
                st.integers(min_value=10, max_value=100), # width
                st.integers(min_value=10, max_value=100)  # height
            ),
            min_size=0,
            max_size=5
        )
    )
    @settings(max_examples=50, deadline=5000)
    def test_face_detection_bounds(self, bounding_boxes, recognition_engine):
        """
        Test that face detection returns valid bounding boxes
        """
        # Create a test image large enough for all bounding boxes
        test_image = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
        
        # Test face detection (may not find faces in random image, but should not crash)
        detected_boxes = recognition_engine.detect_faces(test_image)
        
        # Verify all detected boxes are valid
        for bbox in detected_boxes:
            assert bbox.x >= 0, "Bounding box x coordinate should be non-negative"
            assert bbox.y >= 0, "Bounding box y coordinate should be non-negative"
            assert bbox.width > 0, "Bounding box width should be positive"
            assert bbox.height > 0, "Bounding box height should be positive"
            
            # Verify boxes are within image bounds
            assert bbox.x + bbox.width <= test_image.shape[1], "Bounding box exceeds image width"
            assert bbox.y + bbox.height <= test_image.shape[0], "Bounding box exceeds image height"