import asyncio
from io import BytesIO
from pathlib import Path
from app.config.settings import get_settings

settings = get_settings()

# Business card at 300 DPI
CARD_W_PX = 1050  # 3.5in x 300dpi
CARD_H_PX = 600   # 2.0in x 300dpi
DPI = 300


def _ensure_output_dir() -> Path:
    path = Path(settings.PDF_OUTPUT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# PILLOW RENDERER — Free Tier
# No system dependencies, works on Render free tier
# ─────────────────────────────────────────────────────────────────────────────

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
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf",
    ]
    paths_regular = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
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


def _in_to_px(inches: float) -> int:
    return int(inches * DPI)


def _render_pillow(design_style: dict) -> bytes:
    from PIL import Image, ImageDraw

    theme = design_style.get("theme", "minimal")
    bg = _hex_to_rgb(design_style.get("background_color", "#FFFFFF"), (255, 255, 255))
    name_color = _hex_to_rgb(design_style.get("text_color", "#1A1A1A"), (28, 28, 28))
    accent = _hex_to_rgb(design_style.get("accent_color", "#C9A84C"), (201, 168, 76))
    contact_color = (107, 107, 107)

    img = Image.new("RGB", (CARD_W_PX, CARD_H_PX), color=bg)
    draw = ImageDraw.Draw(img)

    left_offset = 0

    # ── Decorative elements per theme ─────────────────────────────────────

    if theme == "bold":
        # Matte black + double gold border frame
        m = 28
        draw.rectangle([m, m, CARD_W_PX - m, CARD_H_PX - m],
                       outline=accent, width=2)
        i = m + 7
        draw.rectangle([i, i, CARD_W_PX - i, CARD_H_PX - i],
                       outline=(*accent, 60), width=1)
        mid = CARD_H_PX // 2
        draw.line([(m + 10, mid), (CARD_W_PX - m - 10, mid)],
                  fill=accent, width=1)
        name_color = accent
        contact_color = _hex_to_rgb("#D4AF6A", (212, 175, 106))

    elif theme == "corporate":
        # Navy + gold left bar + white rule
        bar_w = _in_to_px(0.08)
        draw.rectangle([0, 0, bar_w, CARD_H_PX], fill=accent)
        mid = CARD_H_PX // 2
        draw.line([(bar_w + 18, mid), (CARD_W_PX - 28, mid)],
                  fill=(255, 255, 255), width=1)
        left_offset = _in_to_px(0.12)
        name_color = accent
        contact_color = (190, 210, 235)

    elif theme == "elegant":
        # Cream + burgundy border + gold corner ornaments + diamond
        bur = _hex_to_rgb("#6B1E2E", (107, 30, 46))
        m = 22
        draw.rectangle([m, m, CARD_W_PX - m, CARD_H_PX - m],
                       outline=bur, width=2)
        orn = 24
        ins = 40
        for (x, y, dx, dy) in [
            (ins, ins, 1, 1), (CARD_W_PX - ins, ins, -1, 1),
            (ins, CARD_H_PX - ins, 1, -1),
            (CARD_W_PX - ins, CARD_H_PX - ins, -1, -1),
        ]:
            draw.line([(x, y), (x + dx * orn, y)], fill=accent, width=2)
            draw.line([(x, y), (x, y + dy * orn)], fill=accent, width=2)
        mid = CARD_H_PX // 2
        draw.line([(m + 10, mid), (CARD_W_PX - m - 10, mid)],
                  fill=bur, width=1)
        cx = CARD_W_PX // 2
        d = 10
        draw.polygon([(cx, mid - d), (cx + d, mid),
                      (cx, mid + d), (cx - d, mid)], fill=accent)
        contact_color = _hex_to_rgb("#5C5249", (92, 82, 73))

    elif theme == "tech":
        # Slate + electric blue bar + rule + faint circle
        bar_w = _in_to_px(0.06)
        draw.rectangle([0, 0, bar_w, CARD_H_PX], fill=accent)
        rule_y = int(CARD_H_PX * 0.45)
        draw.line([(bar_w + 18, rule_y), (CARD_W_PX - 28, rule_y)],
                  fill=accent, width=1)
        left_offset = _in_to_px(0.12)
        name_color = (255, 255, 255)
        contact_color = _hex_to_rgb("#94A3B8", (148, 163, 184))

    elif theme == "creative":
        # White top + coral bottom split
        coral = _hex_to_rgb("#D95F43", (217, 95, 67))
        split_y = CARD_H_PX // 2
        draw.rectangle([0, split_y, CARD_W_PX, CARD_H_PX], fill=coral)
        draw.line([(0, split_y), (CARD_W_PX, split_y)], fill=coral, width=3)
        name_color = (28, 28, 28)
        contact_color = (255, 255, 255)

    else:
        # Minimal: single gold horizontal rule
        mid = CARD_H_PX // 2
        draw.line([(0, mid), (CARD_W_PX, mid)], fill=accent, width=2)
        contact_color = (107, 107, 107)

    # ── Text rendering ─────────────────────────────────────────────────────

    ml = _in_to_px(0.22) + left_offset
    mt = _in_to_px(0.18)
    mb = _in_to_px(0.18)

    font_name = _get_font(72, bold=True)
    font_company = _get_font(30)
    font_contact = _get_font(26)

    name_text = design_style.get("name", "")
    company_text = design_style.get("company_name", "")
    contact_items = design_style.get("contact_items", [])

    if theme == "elegant":
        # Centered layout
        def centered_x(text, font):
            bbox = draw.textbbox((0, 0), text, font=font)
            return (CARD_W_PX - (bbox[2] - bbox[0])) // 2

        draw.text((centered_x(name_text, font_name), mt + 15),
                  name_text, font=font_name, fill=name_color)
        draw.text((centered_x(company_text, font_company), mt + 105),
                  company_text, font=font_company,
                  fill=_hex_to_rgb("#6B1E2E", (107, 30, 46)))
        cy = CARD_H_PX - mb - (len(contact_items) * 36)
        for item in contact_items:
            draw.text((centered_x(item, font_contact), cy),
                      item, font=font_contact, fill=contact_color)
            cy += 36

    elif theme == "bold":
        # Company at top, then name, then contact bottom
        font_label = _get_font(22)
        draw.text((ml, mt + 15), company_text.upper(),
                  font=font_label, fill=accent)
        draw.text((ml, mt + 55), name_text,
                  font=font_name, fill=name_color)
        cy = CARD_H_PX - mb - (len(contact_items) * 34)
        for item in contact_items:
            draw.text((ml, cy), item, font=font_contact, fill=contact_color)
            cy += 34

    else:
        # Standard left-aligned layout
        draw.text((ml, mt), name_text, font=font_name, fill=name_color)
        nm_bbox = draw.textbbox((0, 0), name_text, font=font_name)
        nm_h = nm_bbox[3] - nm_bbox[1]

        company_fill = accent if theme in ["corporate", "tech"] else (
            _hex_to_rgb("#D95F43", (217, 95, 67)) if theme == "creative"
            else (102, 102, 102)
        )
        draw.text((ml, mt + nm_h + 12), company_text,
                  font=font_company, fill=company_fill)

        cy = CARD_H_PX - mb - (len(contact_items) * 34)
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


# ─────────────────────────────────────────────────────────────────────────────
# PLAYWRIGHT RENDERER — Premium Tier
# Pixel-perfect browser rendering, full CSS + Google Fonts support
# ─────────────────────────────────────────────────────────────────────────────

def _render_playwright(html_content: str) -> bytes:
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


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT — Routes to correct renderer based on PDF_RENDERER setting
# ─────────────────────────────────────────────────────────────────────────────

async def generate_pdf(
    html_content: str,
    order_id: str,
    design_style: dict = None,
) -> str:
    """
    Generate print-ready PDF.

    FREE TIER  (PDF_RENDERER=pillow):
      Uses Pillow + img2pdf — no system deps, works on Render free tier.
      Renders decorative elements + text using Python drawing.

    PREMIUM TIER (PDF_RENDERER=playwright):
      Uses Playwright headless Chromium — pixel-perfect browser rendering.
      Full CSS, Google Fonts, absolute positioning support.
    """
    output_dir = _ensure_output_dir()
    filepath = output_dir / f"{order_id}.pdf"
    renderer = settings.PDF_RENDERER.lower()

    print(f"PDF Renderer: {renderer}")

    loop = asyncio.get_event_loop()

    if renderer == "playwright":
        # Premium: full browser rendering
        pdf_bytes = await loop.run_in_executor(
            None, _render_playwright, html_content.strip()
        )
        filepath.write_bytes(pdf_bytes)

    else:
        # Free: Pillow rendering
        png_bytes = await loop.run_in_executor(
            None, _render_pillow, design_style or {}
        )
        pdf_bytes = await loop.run_in_executor(
            None, _png_to_pdf, png_bytes
        )
        filepath.write_bytes(pdf_bytes)

    print(f"✓ PDF saved: {filepath}")
    return str(filepath)


# ─────────────────────────────────────────────────────────────────────────────
# PRINT SHEET GENERATOR — 12×18 inch sheet with multiple cards
# ─────────────────────────────────────────────────────────────────────────────

# Sheet specifications
SHEET_W_IN = 12.0
SHEET_H_IN = 18.0
CARD_W_IN = 3.5
CARD_H_IN = 2.0
COLS = 3
ROWS = 8
GAP_IN = 0.15          # gap between cards (bleed/cut guide)
MARGIN_IN = 0.25       # sheet outer margin

SHEET_DPI = 300
SHEET_W_PX = int(SHEET_W_IN * SHEET_DPI)   # 3600px
SHEET_H_PX = int(SHEET_H_IN * SHEET_DPI)   # 5400px
CARD_W_S_PX = int(CARD_W_IN * SHEET_DPI)   # 1050px
CARD_H_S_PX = int(CARD_H_IN * SHEET_DPI)   # 600px
GAP_PX = int(GAP_IN * SHEET_DPI)            # 45px
MARGIN_PX = int(MARGIN_IN * SHEET_DPI)      # 75px


def _render_print_sheet_sync(html_content: str) -> bytes:
    """
    Render a 12x18 inch print sheet containing 24 business cards
    arranged in 3 columns x 8 rows at 300 DPI.
    Uses Playwright to render each card then assembles the sheet.
    """
    from PIL import Image
    from playwright.sync_api import sync_playwright

    print(f"Rendering print sheet: {COLS}x{ROWS} = {COLS*ROWS} cards")

    # Step 1: Render single card as image using Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--single-process",
        ])
        page = browser.new_page()
        page.set_viewport_size({
            "width": CARD_W_S_PX,
            "height": CARD_H_S_PX
        })
        page.set_content(html_content, wait_until="networkidle")
        page.wait_for_timeout(2500)

        # Screenshot the card at exact dimensions
        card_png = page.screenshot(
            full_page=False,
            clip={
                "x": 0, "y": 0,
                "width": CARD_W_S_PX,
                "height": CARD_H_S_PX
            }
        )
        browser.close()

    print(f"✓ Card rendered: {len(card_png)} bytes")

    # Step 2: Open card image
    from io import BytesIO
    card_img = Image.open(BytesIO(card_png)).convert("RGB")
    card_img = card_img.resize((CARD_W_S_PX, CARD_H_S_PX), Image.LANCZOS)

    # Step 3: Create white sheet canvas
    sheet = Image.new("RGB", (SHEET_W_PX, SHEET_H_PX), color=(255, 255, 255))

    # Step 4: Calculate total grid dimensions and center it
    grid_w = COLS * CARD_W_S_PX + (COLS - 1) * GAP_PX
    grid_h = ROWS * CARD_H_S_PX + (ROWS - 1) * GAP_PX

    # Center the grid on the sheet
    start_x = (SHEET_W_PX - grid_w) // 2
    start_y = (SHEET_H_PX - grid_h) // 2

    print(f"Grid: {grid_w}x{grid_h}px, starting at ({start_x},{start_y})")

    # Step 5: Place cards on sheet
    from PIL import ImageDraw
    draw = ImageDraw.Draw(sheet)

    for row in range(ROWS):
        for col in range(COLS):
            x = start_x + col * (CARD_W_S_PX + GAP_PX)
            y = start_y + row * (CARD_H_S_PX + GAP_PX)

            # Paste card
            sheet.paste(card_img, (x, y))

            # Draw cut guides (thin grey lines around each card)
            cut_color = (180, 180, 180)
            cut_len = 20   # guide line length in pixels
            cut_offset = 5  # offset from card edge

            # Top-left corner
            draw.line([(x - cut_offset, y), (x - cut_offset - cut_len, y)],
                      fill=cut_color, width=1)
            draw.line([(x, y - cut_offset), (x, y - cut_offset - cut_len)],
                      fill=cut_color, width=1)
            # Top-right corner
            draw.line([(x + CARD_W_S_PX + cut_offset, y),
                       (x + CARD_W_S_PX + cut_offset + cut_len, y)],
                      fill=cut_color, width=1)
            draw.line([(x + CARD_W_S_PX, y - cut_offset),
                       (x + CARD_W_S_PX, y - cut_offset - cut_len)],
                      fill=cut_color, width=1)
            # Bottom-left corner
            draw.line([(x - cut_offset, y + CARD_H_S_PX),
                       (x - cut_offset - cut_len, y + CARD_H_S_PX)],
                      fill=cut_color, width=1)
            draw.line([(x, y + CARD_H_S_PX + cut_offset),
                       (x, y + CARD_H_S_PX + cut_offset + cut_len)],
                      fill=cut_color, width=1)
            # Bottom-right corner
            draw.line([(x + CARD_W_S_PX + cut_offset, y + CARD_H_S_PX),
                       (x + CARD_W_S_PX + cut_offset + cut_len, y + CARD_H_S_PX)],
                      fill=cut_color, width=1)
            draw.line([(x + CARD_W_S_PX, y + CARD_H_S_PX + cut_offset),
                       (x + CARD_W_S_PX, y + CARD_H_S_PX + cut_offset + cut_len)],
                      fill=cut_color, width=1)

    print(f"✓ {COLS * ROWS} cards placed on sheet")

    # Step 6: Save sheet as PNG
    sheet_buf = BytesIO()
    sheet.save(sheet_buf, format="PNG", dpi=(SHEET_DPI, SHEET_DPI))
    sheet_buf.seek(0)
    return sheet_buf.read()


def _sheet_png_to_pdf(png_bytes: bytes) -> bytes:
    """Convert 12x18 sheet PNG to PDF at exact dimensions."""
    import img2pdf
    layout = img2pdf.get_fixed_dpi_layout_fun((SHEET_DPI, SHEET_DPI))
    page_size = (
        img2pdf.in_to_pt(SHEET_W_IN),
        img2pdf.in_to_pt(SHEET_H_IN)
    )
    return img2pdf.convert(png_bytes, layout_fun=layout, pagesize=page_size)


async def generate_print_sheet(html_content: str, order_id: str) -> str:
    """
    Generate a 12x18 inch print-ready sheet PDF.
    Contains 3 columns x 8 rows = 24 business cards at 300 DPI.
    Each card has crop/cut marks for the printer.
    Returns local file path.
    """
    output_dir = _ensure_output_dir()
    filepath = output_dir / f"{order_id}_print_sheet.pdf"

    loop = asyncio.get_event_loop()

    # Render the sheet
    sheet_png = await loop.run_in_executor(
        None, _render_print_sheet_sync, html_content.strip()
    )
    print(f"✓ Sheet PNG: {len(sheet_png)} bytes")

    # Convert to PDF
    pdf_bytes = await loop.run_in_executor(
        None, _sheet_png_to_pdf, sheet_png
    )

    filepath.write_bytes(pdf_bytes)
    print(f"✓ Print sheet saved: {filepath}")
    return str(filepath)