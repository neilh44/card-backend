from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from supabase import create_client
from app.config.settings import get_settings

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Auth"])


class SignUpRequest(BaseModel):
    email: str
    password: str


class SignInRequest(BaseModel):
    email: str
    password: str


def _get_client():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


@router.post("/signup")
async def sign_up(payload: SignUpRequest):
    """Register a new user via Supabase Auth."""
    supabase = _get_client()
    try:
        result = supabase.auth.sign_up({
            "email": payload.email,
            "password": payload.password
        })
        return {
            "user_id": result.user.id,
            "message": "Registration successful. Check your email to confirm."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/signin")
async def sign_in(payload: SignInRequest):
    """Sign in an existing user via Supabase Auth."""
    supabase = _get_client()
    try:
        result = supabase.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password
        })
        return {
            "access_token": result.session.access_token,
            "user_id": result.user.id,
            "email": result.user.email,
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid email or password")


@router.get("/me")
async def get_current_user(authorization: str = Header(...)):
    """Get current authenticated user from Bearer token."""
    supabase = _get_client()
    token = authorization.replace("Bearer ", "").strip()
    try:
        user = supabase.auth.get_user(token)
        return {
            "user_id": user.user.id,
            "email": user.user.email
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
