import asyncio
import httpx
from pathlib import Path
from app.config.settings import get_settings

settings = get_settings()

CARD_WIDTH_PX = 1050   # 3.5in at 300dpi
CARD_HEIGHT_PX = 600   # 2in at 300dpi


def _ensure_output_dir() -> Path:
    path = Path(settings.PDF_OUTPUT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _image_bytes_to_pdf(image_bytes: bytes) -> bytes:
    """Convert image bytes to a print-ready PDF at 3.5 x 2 inches."""
    from PIL import Image
    from io import BytesIO
    from xhtml2pdf import pisa

    # Resize image to exact business card dimensions at 300dpi
    img = Image.open(BytesIO(image_bytes))
    img = img.convert("RGB")
    img = img.resize((CARD_WIDTH_PX, CARD_HEIGHT_PX), Image.LANCZOS)

    # Save resized image to bytes
    img_buffer = BytesIO()
    img.save(img_buffer, format="PNG")
    img_buffer.seek(0)

    # Embed image in HTML sized to exact card dimensions
    import base64
    img_b64 = base64.b64encode(img_buffer.read()).decode()

    html = f"""<!DOCTYPE html>
<html>
<head>
<style>
@page {{
    size: 3.5in 2in;
    margin: 0;
}}
body {{
    margin: 0;
    padding: 0;
    width: 3.5in;
    height: 2in;
    overflow: hidden;
}}
img {{
    width: 3.5in;
    height: 2in;
    display: block;
}}
</style>
</head>
<body>
<img src="data:image/png;base64,{img_b64}" />
</body>
</html>"""

    buffer = BytesIO()
    pisa.CreatePDF(html, dest=buffer)
    return buffer.getvalue()


async def generate_pdf(image_url: str, order_id: str) -> str:
    """
    Download image from URL and convert to print-ready PDF.
    Returns local file path.
    """
    output_dir = _ensure_output_dir()
    filepath = output_dir / f"{order_id}.pdf"

    # Download the image
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(image_url)
        response.raise_for_status()
        image_bytes = response.content

    # Convert to PDF in executor
    loop = asyncio.get_event_loop()
    pdf_bytes = await loop.run_in_executor(
        None, _image_bytes_to_pdf, image_bytes
    )

    filepath.write_bytes(pdf_bytes)
    return str(filepath)
