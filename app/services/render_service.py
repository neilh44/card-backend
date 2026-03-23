import asyncio
import os
from pathlib import Path
from app.config.settings import get_settings

settings = get_settings()

# Set Playwright browser path explicitly for Render environment
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/render/.cache/ms-playwright")


def _ensure_output_dir() -> Path:
    path = Path(settings.PDF_OUTPUT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _render_pdf_sync(html_content: str) -> bytes:
    """Render HTML to PDF using Playwright headless Chromium."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
            ]
        )
        page = browser.new_page()

        # Set viewport to exact business card size at 96dpi
        page.set_viewport_size({"width": 336, "height": 192})

        # Load HTML and wait for fonts
        page.set_content(html_content, wait_until="networkidle")
        page.wait_for_timeout(2500)

        pdf_bytes = page.pdf(
            width="3.5in",
            height="2in",
            print_background=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        )

        browser.close()
        return pdf_bytes


async def generate_pdf(html_content: str, order_id: str) -> str:
    """
    Generate print-ready PDF using Playwright headless Chromium.
    Renders exactly as seen in browser — full CSS support.
    Returns local file path.
    """
    output_dir = _ensure_output_dir()
    filepath = output_dir / f"{order_id}.pdf"

    cleaned_html = html_content.strip()

    loop = asyncio.get_event_loop()
    pdf_bytes = await loop.run_in_executor(
        None, _render_pdf_sync, cleaned_html
    )

    filepath.write_bytes(pdf_bytes)
    return str(filepath)