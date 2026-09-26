from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.database import db
from app.models.settings import ReferenceEmailCreate

router = APIRouter(prefix="/api/reference-emails", tags=["reference_emails"])

@router.get("", response_model=List[Dict[str, Any]])
async def get_reference_emails():
    return await db.get_reference_emails()

@router.post("", response_model=Dict[str, Any])
async def add_reference_email(req: ReferenceEmailCreate):
    return await db.create_reference_email({
        "subject": req.subject,
        "body": req.body,
        "style_notes": req.style_notes
    })

@router.delete("/{email_id}")
async def delete_reference_email(email_id: str):
    await db.delete_reference_email(email_id)
    return {"status": "deleted", "id": email_id}
