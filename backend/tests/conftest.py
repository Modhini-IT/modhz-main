"""
Test configuration and fixtures
"""
import pytest
import numpy as np
import cv2
from typing import Generator
from hypothesis import strategies as st

from app.services.recognition_engine import RecognitionEngine


@pytest.fixture
def recognition_engine():
    """Create a recognition engine instance for testing"""
    return RecognitionEngine()


@pytest.fixture
def sample_face_image():
    """Create a sample face image for testing"""
    # Create a simple synthetic face image (64x64 RGB)
    image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
    return image


# Hypothesis strategies for property-based testing
@st.composite
def face_image_strategy(draw):
    """Generate random face images for property-based testing"""
    # Generate random dimensions within reasonable bounds
    height = draw(st.integers(min_value=32, max_value=256))
    width = draw(st.integers(min_value=32, max_value=256))
    
    # Generate random RGB image
    image = draw(st.lists(
        st.integers(min_value=0, max_value=255),
        min_size=height * width * 3,
        max_size=height * width * 3
    ))
    
    # Reshape to image format
    return np.array(image, dtype=np.uint8).reshape((height, width, 3))


@st.composite
def embedding_strategy(draw):
    """Generate random face embeddings for testing"""
    # Generate 128-dimensional embedding
    embedding = draw(st.lists(
        st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        min_size=128,
        max_size=128
    ))
    
    # Convert to numpy array and normalize to unit sphere
    embedding = np.array(embedding, dtype=np.float64)
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    
    return embedding