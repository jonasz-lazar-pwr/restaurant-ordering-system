from fastapi import APIRouter
from pydantic import BaseModel
from api.services.sns import publish_notification

router = APIRouter()

class NotificationRequest(BaseModel):
    message: str
    subject: str = "Notification"

@router.post("/notify")
def send_notification(payload: NotificationRequest):
    return publish_notification(payload.message, payload.subject)
