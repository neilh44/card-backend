import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.models.schemas import CreateOrderRequest, OrderResponse, GetOrderResponse
from app.services import render_service, storage_service

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse)
async def create_order(payload: CreateOrderRequest):
    """
    Create a print-ready order:
    1. Render PDF from selected design HTML
    2. Upload PDF to Supabase Storage
    3. Save order record to database
    Returns order details including the PDF download URL.
    """
    order_id = str(uuid.uuid4())

    # Step 1: Generate PDF
    try:
        local_pdf_path = await render_service.generate_pdf(
            payload.design_html, order_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {str(e)}"
        )

    # Step 2: Upload to Supabase Storage
    try:
        pdf_url = await storage_service.upload_pdf(local_pdf_path, order_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF upload failed: {str(e)}"
        )

    # Step 3: Save order record
    now = datetime.now(timezone.utc)
    order_record = {
        "id": order_id,
        "user_id": payload.user_id,
        "session_id": payload.session_id,
        "selected_design_id": payload.selected_design_id,
        "pdf_url": pdf_url,
        "status": "completed",
        "user_info": payload.user_info.model_dump(),
        "created_at": now.isoformat(),
    }

    try:
        await storage_service.save_order(order_record)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Order save failed: {str(e)}"
        )

    return OrderResponse(
        id=order_id,
        user_id=payload.user_id,
        selected_design_id=payload.selected_design_id,
        pdf_url=pdf_url,
        status="completed",
        created_at=now,
    )


@router.get("/{order_id}", response_model=GetOrderResponse)
async def get_order(order_id: str):
    """Fetch a specific order by ID."""
    order = await storage_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return GetOrderResponse(
        id=order["id"],
        selected_design={"id": order["selected_design_id"]},
        pdf_url=order["pdf_url"],
        status=order["status"],
        created_at=order["created_at"],
        user_info=order["user_info"],
    )
