import asyncio
from io import BytesIO
from pathlib import Path
from app.config.settings import get_settings

settings = get_settings()

CARD_W_PX = 1050
CARD_H_PX = 600
DPI = 300

SHEET_W_IN = 12.0
SHEET_H_IN = 18.0
COLS = 3
ROWS = 8
GAP_IN = 0.15
SHEET_DPI = 300
SHEET_W_PX = int(SHEET_W_IN * SHEET_DPI)
SHEET_H_PX = int(SHEET_H_IN * SHEET_DPI)
CARD_W_S_PX = int(3.5 * SHEET_DPI)
CARD_H_S_PX = int(2.0 * SHEET_DPI)
GAP_PX = int(GAP_IN * SHEET_DPI)


def _ensure_output_dir() -> Path:
    path = Path(settings.PDF_OUTPUT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


# ── Playwright Renderer ───────────────────────────────────────────────────────

def _render_playwright(html_content: str) -> bytes:
    """Render HTML to PDF using Playwright. Raises on failure."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--single-process",
        ])
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


def _screenshot_playwright(html_content: str) -> bytes:
    """Screenshot card as PNG using Playwright. Raises on failure."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--single-process",
        ])
        page = browser.new_page()
        page.set_viewport_size({"width": CARD_W_S_PX, "height": CARD_H_S_PX})
        page.set_content(html_content, wait_until="networkidle")
        page.wait_for_timeout(2500)
        png = page.screenshot(
            full_page=False,
            clip={"x": 0, "y": 0, "width": CARD_W_S_PX, "height": CARD_H_S_PX}
        )
        browser.close()
        return png


# ── Pillow Renderer (Fallback) ────────────────────────────────────────────────

def _hex_to_rgb(hex_color: str, fallback=(0, 0, 0)) -> tuple:
    try:
        h = hex_color.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        return fallback


def _get_font(size: int, bold: bool = False):
    from PIL import ImageFont
    paths_bold = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    ]
    paths_regular = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in (paths_bold if bold else paths_regular):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def _render_pillow(design_style: dict) -> bytes:
    from PIL import Image, ImageDraw

    theme = design_style.get("theme", "minimal")
    bg = _hex_to_rgb(design_style.get("background_color", "#FFFFFF"), (255, 255, 255))
    accent = _hex_to_rgb(design_style.get("accent_color", "#C9A84C"), (201, 168, 76))
    name_color = _hex_to_rgb(design_style.get("text_color", "#1A1A1A"), (28, 28, 28))
    contact_color = (107, 107, 107)

    img = Image.new("RGB", (CARD_W_PX, CARD_H_PX), color=bg)
    draw = ImageDraw.Draw(img)
    left_offset = 0

    def in_to_px(i): return int(i * DPI)

    if theme == "bold":
        m = 28
        draw.rectangle([m, m, CARD_W_PX-m, CARD_H_PX-m], outline=accent, width=2)
        draw.line([(m+10, CARD_H_PX//2), (CARD_W_PX-m-10, CARD_H_PX//2)], fill=accent, width=1)
        name_color = accent
        contact_color = _hex_to_rgb("#D4AF6A", (212, 175, 106))
    elif theme == "corporate":
        bar_w = in_to_px(0.08)
        draw.rectangle([0, 0, bar_w, CARD_H_PX], fill=accent)
        draw.line([(bar_w+18, CARD_H_PX//2), (CARD_W_PX-28, CARD_H_PX//2)], fill=(255,255,255), width=1)
        left_offset = in_to_px(0.12)
        name_color = accent
        contact_color = (190, 210, 235)
    elif theme == "elegant":
        bur = _hex_to_rgb("#6B1E2E", (107, 30, 46))
        draw.rectangle([22, 22, CARD_W_PX-22, CARD_H_PX-22], outline=bur, width=2)
        for (x, y, dx, dy) in [(40,40,1,1),(CARD_W_PX-40,40,-1,1),(40,CARD_H_PX-40,1,-1),(CARD_W_PX-40,CARD_H_PX-40,-1,-1)]:
            draw.line([(x,y),(x+dx*24,y)], fill=accent, width=2)
            draw.line([(x,y),(x,y+dy*24)], fill=accent, width=2)
        mid = CARD_H_PX//2
        draw.line([(32, mid),(CARD_W_PX-32, mid)], fill=bur, width=1)
        cx = CARD_W_PX//2
        draw.polygon([(cx,mid-10),(cx+10,mid),(cx,mid+10),(cx-10,mid)], fill=accent)
        contact_color = (92, 82, 73)
    elif theme == "tech":
        bar_w = in_to_px(0.06)
        draw.rectangle([0, 0, bar_w, CARD_H_PX], fill=accent)
        draw.line([(bar_w+18, int(CARD_H_PX*0.45)), (CARD_W_PX-28, int(CARD_H_PX*0.45))], fill=accent, width=1)
        left_offset = in_to_px(0.12)
        name_color = (255, 255, 255)
        contact_color = (148, 163, 184)
    elif theme == "creative":
        coral = _hex_to_rgb("#D95F43", (217, 95, 67))
        draw.rectangle([0, CARD_H_PX//2, CARD_W_PX, CARD_H_PX], fill=coral)
        name_color = (28, 28, 28)
        contact_color = (255, 255, 255)
    else:
        draw.line([(0, CARD_H_PX//2), (CARD_W_PX, CARD_H_PX//2)], fill=accent, width=2)

    ml = in_to_px(0.22) + left_offset
    mt = in_to_px(0.18)
    mb = in_to_px(0.18)

    font_name = _get_font(72, bold=True)
    font_company = _get_font(30)
    font_contact = _get_font(26)

    name_text = design_style.get("name", "")
    company_text = design_style.get("company_name", "")
    contact_items = design_style.get("contact_items", [])

    if theme == "elegant":
        def cx_text(t, f):
            b = draw.textbbox((0,0), t, font=f)
            return (CARD_W_PX-(b[2]-b[0]))//2
        draw.text((cx_text(name_text, font_name), mt+15), name_text, font=font_name, fill=name_color)
        draw.text((cx_text(company_text, font_company), mt+105), company_text, font=font_company, fill=_hex_to_rgb("#6B1E2E",(107,30,46)))
        cy = CARD_H_PX - mb - (len(contact_items)*36)
        for item in contact_items:
            draw.text((cx_text(item, font_contact), cy), item, font=font_contact, fill=contact_color)
            cy += 36
    elif theme == "bold":
        font_label = _get_font(22)
        draw.text((ml, mt+15), company_text.upper(), font=font_label, fill=accent)
        draw.text((ml, mt+55), name_text, font=font_name, fill=name_color)
        cy = CARD_H_PX - mb - (len(contact_items)*34)
        for item in contact_items:
            draw.text((ml, cy), item, font=font_contact, fill=contact_color)
            cy += 34
    else:
        draw.text((ml, mt), name_text, font=font_name, fill=name_color)
        nb = draw.textbbox((0,0), name_text, font=font_name)
        company_fill = accent if theme in ["corporate","tech"] else (_hex_to_rgb("#D95F43",(217,95,67)) if theme=="creative" else (102,102,102))
        draw.text((ml, mt+(nb[3]-nb[1])+12), company_text, font=font_company, fill=company_fill)
        cy = CARD_H_PX - mb - (len(contact_items)*34)
        for item in contact_items:
            draw.text((ml, cy), item, font=font_contact, fill=contact_color)
            cy += 34

    buf = BytesIO()
    img.save(buf, format="PNG", dpi=(DPI, DPI))
    buf.seek(0)
    return buf.read()


def _png_to_pdf(png_bytes: bytes) -> bytes:
    import img2pdf
    layout = img2pdf.get_fixed_dpi_layout_fun((DPI, DPI))
    page_size = (img2pdf.in_to_pt(3.5), img2pdf.in_to_pt(2))
    return img2pdf.convert(png_bytes, layout_fun=layout, pagesize=page_size)


# ── Main PDF Generator ────────────────────────────────────────────────────────

async def generate_pdf(
    html_content: str,
    order_id: str,
    design_style: dict = None,
) -> str:
    """
    Generate print-ready PDF.
    Tries Playwright first, falls back to Pillow if Playwright fails.
    """
    output_dir = _ensure_output_dir()
    filepath = output_dir / f"{order_id}.pdf"
    renderer = settings.PDF_RENDERER.lower()
    loop = asyncio.get_event_loop()

    print(f"PDF Renderer: {renderer}")

    if renderer == "playwright":
        try:
            print("Trying Playwright renderer...")
            pdf_bytes = await loop.run_in_executor(
                None, _render_playwright, html_content.strip()
            )
            filepath.write_bytes(pdf_bytes)
            print("✓ Playwright PDF generated")
            return str(filepath)
        except Exception as e:
            print(f"✗ Playwright failed: {e} — falling back to Pillow")

    # Pillow fallback
    print("Using Pillow renderer...")
    png_bytes = await loop.run_in_executor(
        None, _render_pillow, design_style or {}
    )
    pdf_bytes = await loop.run_in_executor(None, _png_to_pdf, png_bytes)
    filepath.write_bytes(pdf_bytes)
    print("✓ Pillow PDF generated")
    return str(filepath)


# ── Print Sheet Generator ─────────────────────────────────────────────────────

def _render_print_sheet_sync(html_content: str) -> bytes:
    """Render 12x18 print sheet with 24 cards. Tries Playwright, falls back to Pillow."""
    from PIL import Image, ImageDraw

    card_img = None

    # Try Playwright screenshot first
    try:
        print("Print sheet: trying Playwright screenshot...")
        png_bytes = _screenshot_playwright(html_content)
        card_img = Image.open(BytesIO(png_bytes)).convert("RGB")
        card_img = card_img.resize((CARD_W_S_PX, CARD_H_S_PX), Image.LANCZOS)
        print("✓ Playwright screenshot done")
    except Exception as e:
        print(f"✗ Playwright screenshot failed: {e} — using Pillow")
        card_img = None

    # Pillow fallback for card image
    if card_img is None:
        png_bytes = _render_pillow({})
        card_img = Image.open(BytesIO(png_bytes)).convert("RGB")
        card_img = card_img.resize((CARD_W_S_PX, CARD_H_S_PX), Image.LANCZOS)

    # Create sheet
    sheet = Image.new("RGB", (SHEET_W_PX, SHEET_H_PX), color=(255, 255, 255))
    draw = ImageDraw.Draw(sheet)

    grid_w = COLS * CARD_W_S_PX + (COLS - 1) * GAP_PX
    grid_h = ROWS * CARD_H_S_PX + (ROWS - 1) * GAP_PX
    start_x = (SHEET_W_PX - grid_w) // 2
    start_y = (SHEET_H_PX - grid_h) // 2

    cut_color = (180, 180, 180)
    cut_len = 20
    cut_off = 5

    for row in range(ROWS):
        for col in range(COLS):
            x = start_x + col * (CARD_W_S_PX + GAP_PX)
            y = start_y + row * (CARD_H_S_PX + GAP_PX)
            sheet.paste(card_img, (x, y))

            # Cut marks
            for (lx1,ly1,lx2,ly2) in [
                (x-cut_off,y,x-cut_off-cut_len,y),
                (x,y-cut_off,x,y-cut_off-cut_len),
                (x+CARD_W_S_PX+cut_off,y,x+CARD_W_S_PX+cut_off+cut_len,y),
                (x+CARD_W_S_PX,y-cut_off,x+CARD_W_S_PX,y-cut_off-cut_len),
                (x-cut_off,y+CARD_H_S_PX,x-cut_off-cut_len,y+CARD_H_S_PX),
                (x,y+CARD_H_S_PX+cut_off,x,y+CARD_H_S_PX+cut_off+cut_len),
                (x+CARD_W_S_PX+cut_off,y+CARD_H_S_PX,x+CARD_W_S_PX+cut_off+cut_len,y+CARD_H_S_PX),
                (x+CARD_W_S_PX,y+CARD_H_S_PX+cut_off,x+CARD_W_S_PX,y+CARD_H_S_PX+cut_off+cut_len),
            ]:
                draw.line([(lx1,ly1),(lx2,ly2)], fill=cut_color, width=1)

    buf = BytesIO()
    sheet.save(buf, format="PNG", dpi=(SHEET_DPI, SHEET_DPI))
    buf.seek(0)
    return buf.read()


def _sheet_png_to_pdf(png_bytes: bytes) -> bytes:
    import img2pdf
    layout = img2pdf.get_fixed_dpi_layout_fun((SHEET_DPI, SHEET_DPI))
    page_size = (img2pdf.in_to_pt(SHEET_W_IN), img2pdf.in_to_pt(SHEET_H_IN))
    return img2pdf.convert(png_bytes, layout_fun=layout, pagesize=page_size)


async def generate_print_sheet(html_content: str, order_id: str) -> str:
    """
    Generate 12x18 inch print sheet PDF.
    3 columns x 8 rows = 24 cards with cut marks.
    """
    output_dir = _ensure_output_dir()
    filepath = output_dir / f"{order_id}_print_sheet.pdf"
    loop = asyncio.get_event_loop()

    sheet_png = await loop.run_in_executor(
        None, _render_print_sheet_sync, html_content.strip()
    )
    pdf_bytes = await loop.run_in_executor(None, _sheet_png_to_pdf, sheet_png)
    filepath.write_bytes(pdf_bytes)
    print(f"✓ Print sheet saved: {filepath}")
    return str(filepath)