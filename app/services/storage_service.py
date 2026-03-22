from supabase import create_client, Client
from app.config.settings import get_settings

settings = get_settings()


def _get_client() -> Client:
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY
    )


async def upload_pdf(local_path: str, order_id: str) -> str:
    """
    Upload a PDF file to Supabase Storage.
    Returns the public URL of the uploaded file.
    """
    supabase = _get_client()
    bucket = settings.SUPABASE_STORAGE_BUCKET
    storage_path = f"orders/{order_id}.pdf"

    with open(local_path, "rb") as f:
        pdf_bytes = f.read()

    supabase.storage.from_(bucket).upload(
        path=storage_path,
        file=pdf_bytes,
        file_options={"content-type": "application/pdf"},
    )

    public_url = supabase.storage.from_(bucket).get_public_url(storage_path)
    return public_url


async def save_order(order_data: dict) -> dict:
    """Insert a new order record into the Supabase orders table."""
    supabase = _get_client()
    result = supabase.table("orders").insert(order_data).execute()
    return result.data[0] if result.data else {}


async def get_order(order_id: str) -> dict | None:
    """Fetch a single order by its UUID."""
    supabase = _get_client()
    result = (
        supabase.table("orders")
        .select("*")
        .eq("id", order_id)
        .single()
        .execute()
    )
    return result.data
