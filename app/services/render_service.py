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

    # Clean the HTML — remove newlines and whitespace that corrupt the render
    html_clean = html_content.strip()

    # Add print page size CSS
    page_css = """
    <style>
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
    </style>
    """

    # Inject page CSS before closing </head> tag
    if "</head>" in html_clean:
        html_clean = html_clean.replace("</head>", f"{page_css}</head>")
    else:
        html_clean = page_css + html_clean

    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(
        html_clean,
        dest=buffer,
        encoding="utf-8",
    )

    if pisa_status.err:
        raise RuntimeError(f"xhtml2pdf error: {pisa_status.err}")

    return buffer.getvalue()


async def generate_pdf(html_content: str, order_id: str) -> str:
    """
    Generate a print-ready PDF from HTML card content.
    Cleans the HTML string before processing.
    Returns local file path.
    """
    output_dir = _ensure_output_dir()
    filepath = output_dir / f"{order_id}.pdf"

    # Strip whitespace and newlines from the content
    cleaned_html = html_content.strip().replace("\r\n", "\n").replace("\r", "\n")

    loop = asyncio.get_event_loop()
    pdf_bytes = await loop.run_in_executor(
        None, _render_pdf_sync, cleaned_html
    )

    filepath.write_bytes(pdf_bytes)
    return str(filepath)