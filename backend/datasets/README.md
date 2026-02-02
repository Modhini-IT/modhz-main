# Face Recognition Training Datasets

This directory contains training datasets for face recognition. Organize your student face images in the following structure:

## Directory Structure

```
datasets/
├── students/
│   ├── student_001/
│   │   ├── image_001.jpg
│   │   ├── image_002.jpg
│   │   └── image_003.jpg
│   ├── student_002/
│   │   ├── image_001.jpg
│   │   ├── image_002.jpg
│   │   └── image_003.jpg
│   └── ...
├── validation/
│   ├── student_001/
│   │   ├── val_001.jpg
│   │   └── val_002.jpg
│   └── ...
└── test/
    ├── student_001/
    │   └── test_001.jpg
    └── ...
```

## Guidelines

### Image Requirements
- **Format**: JPG, PNG, or JPEG
- **Resolution**: Minimum 224x224 pixels
- **Quality**: High quality, well-lit images
- **Face Size**: Face should occupy at least 30% of the image
- **Multiple Angles**: Include front-facing, slight left/right turns
- **Lighting Conditions**: Various lighting conditions for robustness

### Naming Convention
- **Student Folders**: Use student ID or roll number (e.g., `student_067`, `roll_101`)
- **Image Files**: Use sequential numbering (e.g., `image_001.jpg`, `image_002.jpg`)

### Training Data Requirements
- **Minimum Images per Student**: 5-10 images
- **Recommended Images per Student**: 15-20 images
- **Maximum Images per Student**: 50 images

### Data Quality Checklist
- [ ] Clear, unblurred face images
- [ ] Good lighting (avoid shadows on face)
- [ ] Neutral facial expressions
- [ ] Minimal background distractions
- [ ] Face clearly visible (no sunglasses, masks)
- [ ] Various head poses (front, slight angles)

## Usage

1. **Add Student Images**: Create a folder with student ID and add their face images
2. **Run Training**: Use the enrollment API or training scripts to process images
3. **Validation**: Test recognition accuracy with validation set
4. **Update Model**: Retrain when adding new students or improving accuracy

## Example Student Entry

```
datasets/students/student_067/
├── front_face_001.jpg      # Front-facing image
├── front_face_002.jpg      # Another front-facing image
├── slight_left_001.jpg     # Slight left turn
├── slight_right_001.jpg    # Slight right turn
├── different_lighting.jpg  # Different lighting condition
└── casual_expression.jpg   # Natural expression
```

## Training Scripts

Use the following endpoints to train the model:

- `POST /api/v1/students/enroll` - Enroll a single student with images
- `POST /api/v1/training/batch-enroll` - Batch enroll multiple students
- `GET /api/v1/training/status` - Check training status

## Data Privacy

⚠️ **Important**: This directory contains biometric data. Ensure:
- Proper access controls are in place
- Data is encrypted at rest
- Compliance with privacy regulations (GDPR, etc.)
- Regular data audits and cleanup
- Secure backup procedures