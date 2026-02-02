# Face Recognition Backend System

A comprehensive Python backend system for real-time face recognition and attendance monitoring, built with FastAPI, OpenCV, and dlib.

## 🚀 Features

- **Real-time Face Recognition**: Advanced face detection and recognition using OpenCV and dlib
- **Student Management**: Complete CRUD operations for student data
- **Attendance Tracking**: Automated attendance recording with confidence scores
- **Dataset Training**: Process student photo datasets for model training
- **REST API**: Comprehensive API endpoints for frontend integration
- **Database Support**: SQLite for development, PostgreSQL for production
- **Docker Ready**: Containerized deployment with Docker and docker-compose
- **Vercel Compatible**: Ready for serverless deployment on Vercel

## 📋 Prerequisites

- Python 3.11+
- OpenCV
- dlib
- SQLite (development) or PostgreSQL (production)

## 🛠️ Installation

### Local Development

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run the application**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 5001
```

### Docker Deployment

1. **Build and run with Docker Compose**
```bash
docker-compose up --build
```

2. **Access the application**
- API: http://localhost:5001
- Documentation: http://localhost:5001/docs

## 📁 Dataset Structure

Add student photos in the following structure:

```
backend/
└── datasets/
    └── students/
        ├── Pranav_A_067/
        │   ├── image_001.jpg
        │   ├── image_002.jpg
        │   └── image_003.jpg
        ├── Raghuraman_R_072/
        │   ├── image_001.jpg
        │   └── image_002.jpg
        └── ... (more students)
```

### Image Requirements
- **Formats**: JPG, JPEG, PNG, BMP
- **Quantity**: 5-15 images per student (minimum 3)
- **Quality**: Clear, well-lit face images
- **Size**: Face should be clearly visible

## 🔧 API Endpoints

### Students
- `GET /api/v1/students/` - List all students
- `POST /api/v1/students/` - Create new student
- `GET /api/v1/students/{id}` - Get student by ID
- `PUT /api/v1/students/{id}` - Update student
- `DELETE /api/v1/students/{id}` - Delete student
- `POST /api/v1/students/enroll` - Enroll student with images

### Training
- `POST /api/v1/training/train-from-datasets` - Train from photo datasets
- `GET /api/v1/training/status` - Get training status
- `GET /api/v1/training/dataset-stats` - Get dataset statistics
- `POST /api/v1/training/validate-dataset` - Validate dataset structure

### Recognition
- `GET /api/v1/recognition/status` - Get recognition system status
- `POST /api/v1/recognition/recognize` - Recognize faces in image
- `POST /api/v1/recognition/start-session` - Start recognition session
- `POST /api/v1/recognition/stop-session` - Stop recognition session

### Attendance
- `GET /api/v1/attendance/` - Get attendance records
- `GET /api/v1/attendance/student/{id}` - Get student attendance
- `GET /api/v1/attendance/stats/daily` - Daily attendance stats
- `POST /api/v1/attendance/record` - Manual attendance recording

## 🚀 Deployment

### Vercel Deployment

1. **Install Vercel CLI**
```bash
npm i -g vercel
```

2. **Deploy to Vercel**
```bash
vercel --prod
```

3. **Set environment variables in Vercel dashboard**
- `SECRET_KEY`: Your secret key
- `ALLOWED_ORIGINS`: Your frontend URLs
- `DATABASE_URL`: Database connection string

### Docker Production

1. **Build production image**
```bash
docker build -t face-recognition-backend .
```

2. **Run with production settings**
```bash
docker run -p 5001:5001 \
  -e DEBUG=false \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host/db \
  face-recognition-backend
```

## 📊 Usage Workflow

1. **Add Student Photos**: Place student photos in `datasets/students/` folders
2. **Train Model**: Call `POST /api/v1/training/train-from-datasets`
3. **Check Status**: Verify training with `GET /api/v1/training/status`
4. **Start Recognition**: Use `POST /api/v1/recognition/recognize` for face recognition
5. **Monitor Attendance**: View attendance data via attendance endpoints

## 🔒 Security Features

- JWT token authentication
- CORS configuration
- Input validation
- SQL injection prevention
- File upload security
- Rate limiting ready

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `true` |
| `PORT` | Server port | `5001` |
| `DATABASE_URL` | Database connection string | SQLite |
| `SECRET_KEY` | JWT secret key | Required |
| `ALLOWED_ORIGINS` | CORS allowed origins | localhost |
| `FACE_RECOGNITION_THRESHOLD` | Recognition confidence threshold | `0.6` |

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Test specific endpoint
curl http://localhost:5001/health
```

## 📚 API Documentation

Once running, visit:
- Swagger UI: http://localhost:5001/docs
- ReDoc: http://localhost:5001/redoc

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the logs for debugging information

## 🔄 Updates

To update the system:
1. Pull latest changes
2. Update dependencies: `pip install -r requirements.txt`
3. Run database migrations if needed
4. Restart the application