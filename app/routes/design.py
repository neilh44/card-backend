import uuid
from fastapi import APIRouter, HTTPException
from app.models.schemas import GenerateDesignsRequest, GenerateDesignsResponse
from app.services import ai_service

router = APIRouter(prefix="/designs", tags=["Designs"])


@router.post("/generate", response_model=GenerateDesignsResponse)
async def generate_designs(payload: GenerateDesignsRequest):
    """
    Generate 6 unique AI-powered business card designs.
    Calls OpenAI GPT-4o, renders HTML for each design, returns all 6.
    """
    try:
        designs = await ai_service.generate_designs(payload.user_info)
        return GenerateDesignsResponse(
            designs=designs,
            session_id=str(uuid.uuid4())
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Design generation failed: {str(e)}"
        )
