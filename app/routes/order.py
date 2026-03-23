import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.models.schemas import CreateOrderRequest, OrderResponse, GetOrderResponse
from app.services import render_service, storage_service

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse)
async def create_order(payload: CreateOrderRequest):
    order_id = str(uuid.uuid4())
    clean_html = payload.design_html.strip()

    design_style = {
        "theme": payload.selected_design_id,
        "background_color": "#FFFFFF",
        "text_color": "#1A1A1A",
        "accent_color": "#C9A84C",
        "secondary_color": "#666666",
        "name": payload.user_info.name,
        "company_name": payload.user_info.company_name,
        "contact_items": list(filter(None, [
            payload.user_info.phone_number,
            payload.user_info.email,
            payload.user_info.website,
            payload.user_info.address,
        ])),
    }

    try:
        local_pdf_path = await render_service.generate_pdf(
            clean_html, order_id, design_style
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    try:
        pdf_url = await storage_service.upload_pdf(local_pdf_path, order_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF upload failed: {str(e)}")

    now = datetime.now(timezone.utc)
    order_record = {
        "id": order_id,
        "user_id": payload.user_id,
        "session_id": payload.session_id,
        "selected_design_id": payload.selected_design_id,
        "pdf_url": pdf_url,
        "status": "completed",
        "user_info": payload.user_info.model_dump(),
        "design_html": clean_html,
        "created_at": now.isoformat(),
    }

    try:
        await storage_service.save_order(order_record)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order save failed: {str(e)}")

    return OrderResponse(
        id=order_id,
        user_id=payload.user_id,
        selected_design_id=payload.selected_design_id,
        pdf_url=pdf_url,
        status="completed",
        created_at=now,
    )


@router.post("/{order_id}/print-sheet")
async def generate_print_sheet(order_id: str):
    order = await storage_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    design_html = order.get("design_html", "")
    if not design_html:
        raise HTTPException(status_code=400, detail="No card HTML found. Please recreate the order.")

    try:
        local_path = await render_service.generate_print_sheet(design_html, order_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Print sheet failed: {str(e)}")

    try:
        sheet_url = await storage_service.upload_pdf(local_path, f"{order_id}_print_sheet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    return {
        "order_id": order_id,
        "print_sheet_url": sheet_url,
        "cards_per_sheet": 24,
        "columns": 3,
        "rows": 8,
        "sheet_size": "12x18 inches",
        "card_size": "3.5x2 inches",
        "resolution": "300 DPI",
    }


@router.get("/{order_id}", response_model=GetOrderResponse)
async def get_order(order_id: str):
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