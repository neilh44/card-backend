from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── User Info ────────────────────────────────────────────────────────────────

class UserInfo(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    company_name: str = Field(..., min_length=1, max_length=150)
    phone_number: str = Field(..., min_length=5, max_length=30)
    address: str = Field(..., min_length=1, max_length=300)
    business_description: str = Field(..., min_length=10, max_length=500)
    email: Optional[str] = None
    website: Optional[str] = None


# ── Design ───────────────────────────────────────────────────────────────────

class DesignStyle(BaseModel):
    theme: str
    primary_color: str
    secondary_color: str
    accent_color: str
    background_color: str
    text_color: str
    font_family: str
    font_family_url: Optional[str] = None
    layout: str
    tagline: Optional[str] = None
    design_name: str
    description: str


class CardDesign(BaseModel):
    id: str
    style: DesignStyle
    html_content: str


class GenerateDesignsRequest(BaseModel):
    user_info: UserInfo


class GenerateDesignsResponse(BaseModel):
    designs: list[CardDesign]
    session_id: str


# ── Order ────────────────────────────────────────────────────────────────────

class CreateOrderRequest(BaseModel):
    session_id: str
    selected_design_id: str
    user_info: UserInfo
    design_html: str
    user_id: Optional[str] = None


class OrderResponse(BaseModel):
    id: str
    user_id: Optional[str]
    selected_design_id: str
    pdf_url: str
    status: str
    created_at: datetime


class GetOrderResponse(BaseModel):
    id: str
    selected_design: dict
    pdf_url: str
    status: str
    created_at: datetime
    user_info: dict
