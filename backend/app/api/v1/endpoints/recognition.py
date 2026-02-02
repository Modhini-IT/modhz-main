"""
Face recognition API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog
import asyncio
import json
from datetime import datetime

from app.core.database import get_db
from app.models.student import Student
from app.models.attendance_record import AttendanceRecord
from app.services.recognition_engine import RecognitionEngine
from app.services.training_service import TrainingService

logger = structlog.get_logger(__name__)
router = APIRouter()

# Global instances
recognition_engine = RecognitionEngine()
training_service = TrainingService()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()


@router.get("/status")
async def get_recognition_status():
    """Get current recognition system status"""
    try:
        # Check if recognition engine has loaded faces
        known_faces_count = len(recognition_engine.known_faces)
        
        # Get training status
        training_status = await training_service.get_training_status()
        
        return {
            "status": "online" if known_faces_count > 0 else "no_training_data",
            "known_faces_count": known_faces_count,
            "recognition_threshold": recognition_engine.recognition_threshold,
            "active_websocket_connections": len(manager.active_connections),
            "training_status": training_status["status"],
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting recognition status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recognition status")


@router.post("/start")
async def start_recognition_session(
    session_id: Optional[str] = None,
    location: Optional[str] = None,
    subject_code: Optional[str] = None,
    period: Optional[str] = None
):
    """Start a new recognition session"""
    try:
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Ensure recognition engine has training data
        if len(recognition_engine.known_faces) == 0:
            # Try to load from database
            await training_service._update_recognition_engine()
            
            if len(recognition_engine.known_faces) == 0:
                raise HTTPException(
                    status_code=400, 
                    detail="No training data available. Please train the model first."
                )
        
        # Broadcast session start to connected clients
        session_data = {
            "type": "session_started",
            "session_id": session_id,
            "location": location,
            "subject_code": subject_code,
            "period": period,
            "timestamp": datetime.now().isoformat()
        }
        
        await manager.broadcast(json.dumps(session_data))
        
        logger.info(f"Started recognition session: {session_id}")
        
        return {
            "message": "Recognition session started",
            "session_id": session_id,
            "location": location,
            "subject_code": subject_code,
            "period": period,
            "known_faces_count": len(recognition_engine.known_faces)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting recognition session: {e}")
        raise HTTPException(status_code=500, detail="Failed to start recognition session")


@router.post("/stop")
async def stop_recognition_session(session_id: str):
    """Stop a recognition session"""
    try:
        # Broadcast session stop to connected clients
        session_data = {
            "type": "session_stopped",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        await manager.broadcast(json.dumps(session_data))
        
        logger.info(f"Stopped recognition session: {session_id}")
        
        return {
            "message": "Recognition session stopped",
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Error stopping recognition session: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop recognition session")


@router.post("/simulate")
async def simulate_recognition(
    session_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Simulate face recognition for testing (generates mock recognition events)"""
    try:
        if not session_id:
            session_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get some students from database for simulation
        stmt = select(Student).where(Student.is_active == True).limit(5)
        result = await db.execute(stmt)
        students = result.scalars().all()
        
        if not students:
            raise HTTPException(status_code=400, detail="No students found for simulation")
        
        # Simulate recognition events
        import random
        simulated_recognitions = []
        
        for _ in range(random.randint(1, 3)):  # Simulate 1-3 recognitions
            student = random.choice(students)
            confidence = random.uniform(0.7, 0.95)  # Random confidence score
            
            # Create attendance record
            attendance_record = AttendanceRecord(
                student_id=student.id,
                confidence_score=confidence,
                session_id=session_id,
                location="Simulation",
                status="present"
            )
            
            db.add(attendance_record)
            await db.commit()
            await db.refresh(attendance_record)
            
            recognition_data = {
                "type": "face_recognized",
                "student_id": student.id,
                "student_name": student.name,
                "roll_number": student.roll_number,
                "confidence": confidence,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "attendance_id": attendance_record.id
            }
            
            simulated_recognitions.append(recognition_data)
            
            # Broadcast recognition event
            await manager.broadcast(json.dumps(recognition_data))
            
            # Small delay between recognitions
            await asyncio.sleep(0.5)
        
        logger.info(f"Simulated {len(simulated_recognitions)} recognition events")
        
        return {
            "message": "Face recognition simulation completed",
            "session_id": session_id,
            "recognitions": simulated_recognitions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in recognition simulation: {e}")
        raise HTTPException(status_code=500, detail="Failed to simulate recognition")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time recognition updates"""
    await manager.connect(websocket)
    try:
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "Connected to face recognition system",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                elif message.get("type") == "get_status":
                    status = await get_recognition_status()
                    await websocket.send_text(json.dumps({
                        "type": "status_update",
                        "data": status,
                        "timestamp": datetime.now().isoformat()
                    }))
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.get("/connections")
async def get_active_connections():
    """Get number of active WebSocket connections"""
    return {
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }


@router.post("/broadcast")
async def broadcast_message(message: str, message_type: str = "announcement"):
    """Broadcast a message to all connected WebSocket clients"""
    try:
        broadcast_data = {
            "type": message_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        await manager.broadcast(json.dumps(broadcast_data))
        
        return {
            "message": "Message broadcasted successfully",
            "recipients": len(manager.active_connections),
            "data": broadcast_data
        }
        
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast message")