import asyncio
import os
import subprocess
from pathlib import Path
from app.config.settings import get_settings

settings = get_settings()


def _ensure_chromium_installed():
    """Install Chromium if not present — handles Render ephemeral filesystem."""
    chromium_path = Path("/opt/render/.cache/ms-playwright")
    
    # Check if chromium executable exists
    chrome_exe = list(chromium_path.glob("**/chrome-linux/chrome"))
    
    if not chrome_exe:
        print("Chromium not found — installing now...")
        try:
            subprocess.run(
                ["python", "-m", "playwright", "install", "chromium"],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["python", "-m", "playwright", "install-deps", "chromium"],
                check=True,
                capture_output=True,
                text=True,
            )
            print("✓ Chromium installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Chromium install failed: {e.stderr}")
            raise RuntimeError(f"Could not install Chromium: {e.stderr}")
    else:
        print(f"✓ Chromium found at {chrome_exe[0]}")


def _ensure_output_dir() -> Path:
    path = Path(settings.PDF_OUTPUT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _render_pdf_sync(html_content: str) -> bytes:
    """Render HTML to PDF using Playwright headless Chromium."""
    # Ensure Chromium is available before launching
    _ensure_chromium_installed()

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
        page.set_viewport_size({"width": 336, "height": 192})
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
    """Generate print-ready PDF. Auto-installs Chromium if wiped by Render."""
    output_dir = _ensure_output_dir()
    filepath = output_dir / f"{order_id}.pdf"

    cleaned_html = html_content.strip()

    loop = asyncio.get_event_loop()
    pdf_bytes = await loop.run_in_executor(
        None, _render_pdf_sync, cleaned_html
    )

    filepath.write_bytes(pdf_bytes)
    return str(filepath)