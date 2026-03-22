import asyncio
from pathlib import Path
from app.config.settings import get_settings

settings = get_settings()


def _ensure_output_dir() -> Path:
    path = Path(settings.PDF_OUTPUT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _render_pdf_sync(html_content: str) -> bytes:
    """Synchronously render HTML to PDF bytes using WeasyPrint."""
    try:
        from weasyprint import HTML, CSS
    except ImportError:
        raise RuntimeError(
            "weasyprint is not installed. Add it to requirements.txt"
        )

    page_css = CSS(string="""
        @page {
            size: 3.5in 2in;
            margin: 0;
        }
        html, body {
            width: 3.5in;
            height: 2in;
            margin: 0;
            padding: 0;
            overflow: hidden;
        }
    """)

    return HTML(string=html_content).write_pdf(stylesheets=[page_css])


async def generate_pdf(html_content: str, order_id: str) -> str:
    """
    Generate a print-ready PDF from HTML and save to disk.
    Returns the local file path.
    Runs WeasyPrint in a thread executor to avoid blocking the event loop.
    """
    output_dir = _ensure_output_dir()
    filepath = output_dir / f"{order_id}.pdf"

    loop = asyncio.get_event_loop()
    pdf_bytes = await loop.run_in_executor(
        None, _render_pdf_sync, html_content
    )

    filepath.write_bytes(pdf_bytes)
    return str(filepath)
