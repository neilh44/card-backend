import asyncio
from pathlib import Path
from app.config.settings import get_settings

settings = get_settings()


def _ensure_output_dir() -> Path:
    path = Path(settings.PDF_OUTPUT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _render_pdf_sync(html_content: str) -> bytes:
    """Convert HTML to PDF bytes using xhtml2pdf."""
    from io import BytesIO
    from xhtml2pdf import pisa

    # Add page size to HTML
    sized_html = html_content.replace(
        "<style>",
        """<style>
        @page {
            size: 3.5in 2in;
            margin: 0;
        }
        body {
            width: 3.5in;
            height: 2in;
            margin: 0;
            padding: 0;
            overflow: hidden;
        }
        """,
        1
    )

    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(sized_html, dest=buffer)

    if pisa_status.err:
        raise RuntimeError(f"PDF generation error: {pisa_status.err}")

    return buffer.getvalue()


async def generate_pdf(html_content: str, order_id: str) -> str:
    """
    Generate a print-ready PDF from HTML and save to disk.
    Returns the local file path.
    """
    output_dir = _ensure_output_dir()
    filepath = output_dir / f"{order_id}.pdf"

    loop = asyncio.get_event_loop()
    pdf_bytes = await loop.run_in_executor(
        None, _render_pdf_sync, html_content
    )

    filepath.write_bytes(pdf_bytes)
    return str(filepath)