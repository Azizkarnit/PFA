from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.core.database import get_db
from app.models.app_notification import AppNotification
from app.models.user import User
from app.api.v1.auth import get_current_user
from app.core.websockets import manager
from app.core.security import decode_access_token

router = APIRouter()

@router.get("/")
def get_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Fetch all notifications for the current user, ordered by newest first."""
    notifications = db.query(AppNotification).filter(
        AppNotification.user_id == current_user.id
    ).order_by(AppNotification.created_at.desc()).limit(50).all()
    
    return [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "type": n.type,
            "action_url": n.action_url,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat()
        } for n in notifications
    ]

@router.put("/{notification_id}/read")
def mark_as_read(notification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Mark a specific notification as read."""
    notif = db.query(AppNotification).filter(
        AppNotification.id == notification_id,
        AppNotification.user_id == current_user.id
    ).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"status": "success"}

@router.put("/read-all")
def mark_all_as_read(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Mark all notifications as read for the current user."""
    db.query(AppNotification).filter(
        AppNotification.user_id == current_user.id,
        AppNotification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"status": "success"}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...), db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time notifications."""
    try:
        # Validate token manually since we can't easily use standard Depends for WS
        payload = decode_access_token(token)
        if not payload:
            await websocket.close(code=1008)
            return
            
        user_id_str = payload.get("sub")
        if not user_id_str:
            await websocket.close(code=1008)
            return
            
        user_id = int(user_id_str)
        
        await manager.connect(websocket, user_id)
        try:
            while True:
                # Keep connection alive
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)
            
    except Exception as e:
        await websocket.close(code=1008)
