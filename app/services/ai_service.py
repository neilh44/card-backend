import uuid
import json
import httpx
import asyncio
from openai import AsyncOpenAI
from app.config.settings import get_settings
from app.models.schemas import UserInfo, CardDesign, DesignStyle

settings = get_settings()
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
IDEOGRAM_API_URL = "https://api.ideogram.ai/generate"

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — IDEOGRAM: Abstract style inspiration images (NO text)
# ─────────────────────────────────────────────────────────────────────────────

STYLE_PROMPTS = [
    {
        "name": "Minimal Gold",
        "theme": "minimal",
        "description": "Off-white with single gold divider, Swiss precision",
        "prompt": (
            "Abstract minimalist business card layout design, pure flat graphic artwork. "
            "Off-white background #F5F4F0, single thin horizontal gold line #C9A84C "
            "dividing the canvas at the exact vertical midpoint. "
            "Upper half clean empty warm off-white space. "
            "Lower half clean empty space. "
            "No text, no words, no letters, no numbers anywhere. "
            "Swiss design school precision, generous whitespace, luxury stationery feel. "
            "Flat vector graphic, fills entire frame edge to edge, "
            "landscape 3.5x2 inch proportions, top-down view, zero perspective."
        ),
    },
    {
        "name": "Dark Executive",
        "theme": "bold",
        "description": "Matte black with gold border frame, luxury executive",
        "prompt": (
            "Abstract luxury executive business card layout design, pure flat graphic artwork. "
            "Deep matte black background #0A0A0A. "
            "Thin elegant gold rectangular border frame #C9A84C inset 3mm from all edges. "
            "Inner thin gold border 2px inside the first. "
            "Single thin gold horizontal rule at vertical midpoint inside the frame. "
            "No text, no words, no letters, no numbers anywhere. "
            "Premium luxury feel, private banking aesthetic. "
            "Flat vector graphic, fills entire frame edge to edge, "
            "landscape 3.5x2 inch proportions, top-down view, zero perspective."
        ),
    },
    {
        "name": "Navy Corporate",
        "theme": "corporate",
        "description": "Deep navy with gold left bar, authoritative professional",
        "prompt": (
            "Abstract corporate business card layout design, pure flat graphic artwork. "
            "Deep navy background #0D2144. "
            "Solid gold vertical stripe #C9A84C on far left, 6mm wide, full card height. "
            "Thin white horizontal rule at 50 percent card height on the right content area. "
            "No text, no words, no letters, no numbers anywhere. "
            "Professional authoritative feel, Fortune 500 aesthetic. "
            "Flat vector graphic, fills entire frame edge to edge, "
            "landscape 3.5x2 inch proportions, top-down view, zero perspective."
        ),
    },
    {
        "name": "Cream Luxury",
        "theme": "elegant",
        "description": "Warm cream with burgundy border and gold corner ornaments",
        "prompt": (
            "Abstract elegant luxury business card layout design, pure flat graphic artwork. "
            "Warm cream background #F4EFE4. "
            "Thin burgundy rectangular border frame #6B1E2E inset 4mm from all edges. "
            "Small decorative corner ornaments in gold #C9A84C at all four corners. "
            "Thin burgundy horizontal rule at vertical midpoint. "
            "Small gold diamond ornament centered on the rule. "
            "No text, no words, no letters, no numbers anywhere. "
            "Old-world European luxury, Hermes Paris aesthetic. "
            "Flat vector graphic, fills entire frame edge to edge, "
            "landscape 3.5x2 inch proportions, top-down view, zero perspective."
        ),
    },
    {
        "name": "Tech Slate",
        "theme": "tech",
        "description": "Dark slate with electric blue accent stripe, tech energy",
        "prompt": (
            "Abstract modern tech business card layout design, pure flat graphic artwork. "
            "Dark slate background #1A1F2E. "
            "Solid electric blue vertical stripe #4F8EF7 on far left, 5mm wide, full card height. "
            "Thin electric blue horizontal rule at 45 percent card height. "
            "Large faint circle outline in white at 5 percent opacity bottom-right partially cropped. "
            "No text, no words, no letters, no numbers anywhere. "
            "Modern tech startup feel, Stripe or Linear aesthetic. "
            "Flat vector graphic, fills entire frame edge to edge, "
            "landscape 3.5x2 inch proportions, top-down view, zero perspective."
        ),
    },
    {
        "name": "Bold Split",
        "theme": "creative",
        "description": "White and coral color-block split, bold creative energy",
        "prompt": (
            "Abstract bold modern business card layout design, pure flat graphic artwork. "
            "Top exactly 50 percent pure white #FFFFFF. "
            "Bottom exactly 50 percent deep coral #D95F43. "
            "Perfectly sharp straight hard horizontal line at exact vertical midpoint, no blur, no gradient. "
            "Subtle white geometric quarter circle at 12 percent opacity bottom-right corner. "
            "No text, no words, no letters, no numbers anywhere. "
            "Bold creative agency aesthetic, Pentagram design studio feel. "
            "Flat vector graphic, fills entire frame edge to edge, "
            "landscape 3.5x2 inch proportions, top-down view, zero perspective."
        ),
    },
]

IDEOGRAM_NEGATIVE = (
    "text, letters, words, numbers, typography, font characters, "
    "name, address, phone, email, website, label, title, heading, "
    "background surface, table, environment, grey background, "
    "shadow, 3D perspective, angled view, tilted, "
    "multiple cards, stacked cards, hands, props, objects, "
    "portrait orientation, square format, photo, photography"
)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — GPT VISION: Extract color palette and mood from Ideogram image
# ─────────────────────────────────────────────────────────────────────────────

GPT_VISION_SYSTEM = """You are a professional color analyst and brand strategist.
Analyze the business card design image and extract its exact color palette and mood.
Return ONLY valid JSON, no markdown, no explanation."""

GPT_VISION_USER = """Analyze this business card design image carefully.
Extract the exact colors used and describe the mood/feel.

Return a JSON object with exactly this structure:
{
  "background_color": "#hexcode",
  "primary_text_color": "#hexcode",
  "secondary_text_color": "#hexcode",
  "accent_color": "#hexcode",
  "decorative_colors": ["#hexcode1", "#hexcode2"],
  "mood": "one paragraph describing the visual mood, feel, and aesthetic of this design",
  "style_keywords": ["keyword1", "keyword2", "keyword3"],
  "has_dark_background": true or false,
  "has_left_bar": true or false,
  "left_bar_color": "#hexcode or null",
  "left_bar_width_px": 0,
  "has_horizontal_rule": true or false,
  "rule_color": "#hexcode or null",
  "rule_position_percent": 50,
  "has_border_frame": true or false,
  "border_color": "#hexcode or null",
  "has_corner_ornaments": true or false,
  "has_color_split": true or false,
  "split_top_color": "#hexcode or null",
  "split_bottom_color": "#hexcode or null",
  "has_circle_decoration": true or false,
  "circle_color": "#hexcode or null"
}"""


async def _extract_colors_with_vision(image_url: str) -> dict:
    """GPT-4 Vision: analyze Ideogram image and extract color palette + mood."""
    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": GPT_VISION_SYSTEM},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url, "detail": "high"},
                    },
                    {"type": "text", "text": GPT_VISION_USER},
                ],
            },
        ],
        max_tokens=800,
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — GPT-4O: Generate complete layout system from color data + user info
# ─────────────────────────────────────────────────────────────────────────────

GPT_LAYOUT_SYSTEM = """You are a world-class typographic layout designer specializing in 
luxury business card design. You receive color palette data and user information, 
and you produce a precise, complete HTML/CSS layout specification.
Return ONLY valid JSON, no markdown, no explanation."""

GPT_LAYOUT_USER = """You are designing a premium business card.

COLOR PALETTE FROM STYLE ANALYSIS:
{color_data}

USER INFORMATION TO DISPLAY:
- Name: {name}
- Company: {company}
- Phone: {phone}
- Email: {email}
- Website: {website}
- Address: {address}

DESIGN MOOD: {mood}
STYLE KEYWORDS: {keywords}

Based on the color palette and mood, design a complete layout system for this business card.
The card is exactly 3.5 inches wide by 2 inches tall (336px x 192px at 96dpi).

Return a JSON object with exactly this structure:
{{
  "layout_name": "descriptive name",
  "background_color": "#hexcode",
  "background_style": "solid|gradient description",

  "name_section": {{
    "top_in": 0.18,
    "left_in": 0.22,
    "font_family": "Playfair Display|DM Sans",
    "font_size_px": 26,
    "font_weight": "700",
    "color": "#hexcode",
    "letter_spacing": "-0.3px",
    "line_height": "1.15",
    "text_transform": "none|uppercase"
  }},

  "company_section": {{
    "margin_top_px": 5,
    "font_family": "DM Sans",
    "font_size_px": 8,
    "font_weight": "500",
    "color": "#hexcode",
    "letter_spacing": "0.18em",
    "text_transform": "uppercase|none"
  }},

  "contact_section": {{
    "bottom_in": 0.18,
    "left_in": 0.22,
    "align": "left|center",
    "font_family": "DM Sans",
    "font_size_px": 7,
    "font_weight": "400",
    "color": "#hexcode",
    "line_height": "1.8"
  }},

  "decorative_elements": [
    {{
      "type": "horizontal_rule|vertical_bar|border_frame|corner_ornaments|color_split|circle",
      "color": "#hexcode",
      "opacity": 1.0,
      "spec": {{}}
    }}
  ],

  "content_left_offset_in": 0.0,
  "google_fonts_url": "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=DM+Sans:wght@300;400;500;600;700&display=swap"
}}

LAYOUT RULES:
- If has_left_bar is true: set content_left_offset_in to 0.12 to clear the bar
- If has_dark_background: use light/gold text colors
- If has_color_split: put name/company on top section, contact on bottom section
- If has_border_frame: keep all content inside the frame with extra padding
- If has_corner_ornaments: include them as decorative_elements
- Typography must create clear visual hierarchy: name largest, company medium, contact small
- All measurements must respect the 3.5in x 2in card boundary
- Design must look like it came from a premium print studio"""


async def _generate_layout_with_gpt4o(
    user_info: UserInfo,
    color_data: dict,
) -> dict:
    """GPT-4o: generate complete layout system from colors + user info."""

    user_message = GPT_LAYOUT_USER.format(
        color_data=json.dumps(color_data, indent=2),
        name=user_info.name,
        company=user_info.company_name,
        phone=user_info.phone_number,
        email=user_info.email or "N/A",
        website=user_info.website or "N/A",
        address=user_info.address,
        mood=color_data.get("mood", "professional and elegant"),
        keywords=", ".join(color_data.get("style_keywords", [])),
    )

    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": GPT_LAYOUT_SYSTEM},
            {"role": "user", "content": user_message},
        ],
        max_tokens=1500,
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — HTML RENDERER: Inject text into layout, produce final card HTML
# ─────────────────────────────────────────────────────────────────────────────

def _render_decorative_elements(elements: list) -> str:
    """Convert layout JSON decorative elements to HTML."""
    html = ""
    for el in elements:
        el_type = el.get("type", "")
        color = el.get("color", "#C9A84C")
        opacity = el.get("opacity", 1.0)
        spec = el.get("spec", {})

        if el_type == "horizontal_rule":
            position = spec.get("position_percent", 50)
            thickness = spec.get("thickness_px", 1)
            html += f"""
<div style="
    position:absolute; left:0; right:0;
    top:{position}%; height:{thickness}px;
    background:{color}; opacity:{opacity};
    z-index:1;
"></div>"""

        elif el_type == "vertical_bar":
            width = spec.get("width_px", 6)
            html += f"""
<div style="
    position:absolute; left:0; top:0; bottom:0;
    width:{width}px; background:{color}; opacity:{opacity};
    z-index:1;
"></div>"""

        elif el_type == "border_frame":
            inset = spec.get("inset_px", 10)
            thickness = spec.get("thickness_px", 1)
            html += f"""
<div style="
    position:absolute; inset:{inset}px;
    border:{thickness}px solid {color}; opacity:{opacity};
    pointer-events:none; z-index:1;
"></div>"""
            # Optional inner frame
            if spec.get("double_frame"):
                inner = inset + 3
                html += f"""
<div style="
    position:absolute; inset:{inner}px;
    border:0.3px solid {color}; opacity:{opacity * 0.4};
    pointer-events:none; z-index:1;
"></div>"""

        elif el_type == "corner_ornaments":
            size = spec.get("size_px", 8)
            inset = spec.get("inset_px", 14)
            for pos_css in [
                f"top:{inset}px;left:{inset}px;border-top:1px solid;border-left:1px solid",
                f"top:{inset}px;right:{inset}px;border-top:1px solid;border-right:1px solid",
                f"bottom:{inset}px;left:{inset}px;border-bottom:1px solid;border-left:1px solid",
                f"bottom:{inset}px;right:{inset}px;border-bottom:1px solid;border-right:1px solid",
            ]:
                html += f"""
<div style="
    position:absolute; {pos_css};
    border-color:{color}; opacity:{opacity};
    width:{size}px; height:{size}px;
    z-index:1;
"></div>"""

        elif el_type == "color_split":
            top_color = spec.get("top_color", "#FFFFFF")
            bottom_color = spec.get("bottom_color", "#D95F43")
            split_percent = spec.get("split_percent", 50)
            html += f"""
<div style="
    position:absolute; inset:0; z-index:0;
    background:linear-gradient(
        to bottom,
        {top_color} 0%,
        {top_color} {split_percent}%,
        {bottom_color} {split_percent}%,
        {bottom_color} 100%
    );
"></div>"""

        elif el_type == "circle":
            size = spec.get("size_px", 120)
            right = spec.get("right_px", -30)
            bottom = spec.get("bottom_px", -30)
            html += f"""
<div style="
    position:absolute; right:{right}px; bottom:{bottom}px;
    width:{size}px; height:{size}px; border-radius:50%;
    border:1px solid {color}; opacity:{opacity};
    pointer-events:none; z-index:1;
"></div>"""

        elif el_type == "diamond_ornament":
            html += f"""
<div style="
    position:absolute; left:50%; top:50%;
    transform:translate(-50%,-50%) rotate(45deg);
    width:5px; height:5px;
    background:{color}; opacity:{opacity};
    z-index:2;
"></div>"""

    return html


def _build_final_html(
    user_info: UserInfo,
    layout: dict,
) -> str:
    """Render the final business card HTML from layout JSON + user data."""

    bg = layout.get("background_color", "#FFFFFF")
    fonts_url = layout.get("google_fonts_url",
        "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=DM+Sans:wght@300;400;500;600;700&display=swap"
    )
    left_offset = layout.get("content_left_offset_in", 0.0)

    # Name section
    ns = layout.get("name_section", {})
    name_top = ns.get("top_in", 0.18)
    name_left = ns.get("left_in", 0.22) + left_offset
    name_font = ns.get("font_family", "Playfair Display")
    name_size = ns.get("font_size_px", 26)
    name_weight = ns.get("font_weight", "700")
    name_color = ns.get("color", "#1A1A1A")
    name_ls = ns.get("letter_spacing", "normal")
    name_lh = ns.get("line_height", "1.15")
    name_transform = ns.get("text_transform", "none")

    # Company section
    cs = layout.get("company_section", {})
    company_mt = cs.get("margin_top_px", 5)
    company_font = cs.get("font_family", "DM Sans")
    company_size = cs.get("font_size_px", 8)
    company_weight = cs.get("font_weight", "500")
    company_color = cs.get("color", "#666666")
    company_ls = cs.get("letter_spacing", "0.1em")
    company_transform = cs.get("text_transform", "uppercase")

    # Contact section
    ct = layout.get("contact_section", {})
    contact_bottom = ct.get("bottom_in", 0.18)
    contact_left = ct.get("left_in", 0.22) + left_offset
    contact_align = ct.get("align", "left")
    contact_font = ct.get("font_family", "DM Sans")
    contact_size = ct.get("font_size_px", 7)
    contact_weight = ct.get("font_weight", "400")
    contact_color = ct.get("color", "#6B6B6B")
    contact_lh = ct.get("line_height", "1.8")

    # Contact positioning
    if contact_align == "center":
        contact_pos_css = f"left:0; right:0; bottom:{contact_bottom}in; text-align:center;"
    else:
        contact_pos_css = f"left:{contact_left}in; bottom:{contact_bottom}in;"

    # Decorative elements
    deco_html = _render_decorative_elements(
        layout.get("decorative_elements", [])
    )

    # Contact lines
    email_line = f"<div>{user_info.email}</div>" if user_info.email else ""
    website_line = f"<div>{user_info.website}</div>" if user_info.website else ""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="{fonts_url}" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{
    width: 3.5in;
    height: 2in;
    overflow: hidden;
    position: relative;
    background: {bg};
}}
</style>
</head>
<body>

<!-- Layer 0: Decorative elements -->
{deco_html}

<!-- Layer 1: Name + Company -->
<div style="
    position: absolute;
    top: {name_top}in;
    left: {name_left}in;
    z-index: 10;
    max-width: 2.8in;
">
    <div style="
        font-family: '{name_font}', Georgia, serif;
        font-size: {name_size}px;
        font-weight: {name_weight};
        color: {name_color};
        letter-spacing: {name_ls};
        line-height: {name_lh};
        text-transform: {name_transform};
    ">{user_info.name}</div>

    <div style="
        font-family: '{company_font}', Arial, sans-serif;
        font-size: {company_size}px;
        font-weight: {company_weight};
        color: {company_color};
        letter-spacing: {company_ls};
        text-transform: {company_transform};
        margin-top: {company_mt}px;
    ">{user_info.company_name}</div>
</div>

<!-- Layer 2: Contact Details -->
<div style="
    position: absolute;
    {contact_pos_css}
    z-index: 10;
    font-family: '{contact_font}', Arial, sans-serif;
    font-size: {contact_size}px;
    font-weight: {contact_weight};
    color: {contact_color};
    line-height: {contact_lh};
">
    <div>{user_info.phone_number}</div>
    {email_line}
    {website_line}
    <div>{user_info.address}</div>
</div>

</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# IDEOGRAM API CALL
# ─────────────────────────────────────────────────────────────────────────────

async def _generate_ideogram_style(
    client: httpx.AsyncClient,
    prompt: str,
) -> str:
    """Generate abstract style inspiration image. Returns image URL."""
    response = await client.post(
        IDEOGRAM_API_URL,
        headers={
            "Api-Key": settings.IDEOGRAM_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "image_request": {
                "prompt": prompt,
                "negative_prompt": IDEOGRAM_NEGATIVE,
                "aspect_ratio": "ASPECT_3_2",
                "model": "V_2",
                "magic_prompt_option": "OFF",
                "style_type": "DESIGN",
            }
        },
        timeout=90.0,
    )
    response.raise_for_status()
    data = response.json()
    return data["data"][0]["url"]


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

async def generate_designs(user_info: UserInfo) -> list[CardDesign]:
    """
    4-step pipeline:
    1. Ideogram  → abstract style inspiration image (no text)
    2. GPT Vision → extract color palette + mood from image
    3. GPT-4o    → generate complete layout system JSON
    4. HTML      → inject user text, render final print-ready card
    """
    designs = []

    async with httpx.AsyncClient() as client:
        for i, style in enumerate(STYLE_PROMPTS):
            try:
                print(f"\n{'='*55}")
                print(f"[{i+1}/{len(STYLE_PROMPTS)}] {style['name']}")
                print(f"{'='*55}")

                # ── Step 1: Ideogram style image ──────────────────────────
                print(f"  Step 1 → Ideogram: generating style inspiration...")
                image_url = await _generate_ideogram_style(
                    client, style["prompt"]
                )
                print(f"  ✓ Image: {image_url[:70]}...")

                # ── Step 2: GPT Vision color extraction ───────────────────
                print(f"  Step 2 → GPT Vision: extracting colors + mood...")
                color_data = await _extract_colors_with_vision(image_url)
                print(f"  ✓ Background: {color_data.get('background_color')}")
                print(f"  ✓ Mood: {color_data.get('mood', '')[:60]}...")

                # ── Step 3: GPT-4o layout system ──────────────────────────
                print(f"  Step 3 → GPT-4o: generating layout system...")
                layout = await _generate_layout_with_gpt4o(
                    user_info, color_data
                )
                print(f"  ✓ Layout: {layout.get('layout_name', 'unnamed')}")
                print(f"  ✓ Elements: {len(layout.get('decorative_elements', []))} decorative")

                # ── Step 4: HTML rendering ────────────────────────────────
                print(f"  Step 4 → HTML Renderer: building final card...")
                html = _build_final_html(user_info, layout)
                print(f"  ✓ HTML: {len(html)} chars rendered")

                design_style = DesignStyle(
                    theme=style["theme"],
                    primary_color=layout.get("name_section", {}).get("color", "#1A1A1A"),
                    secondary_color=layout.get("company_section", {}).get("color", "#666666"),
                    accent_color=color_data.get("accent_color", "#C9A84C"),
                    background_color=layout.get("background_color", "#FFFFFF"),
                    text_color=layout.get("name_section", {}).get("color", "#1A1A1A"),
                    font_family=layout.get("name_section", {}).get("font_family", "Playfair Display"),
                    layout=style["theme"],
                    design_name=style["name"],
                    description=style["description"],
                )

                designs.append(CardDesign(
                    id=str(uuid.uuid4()),
                    style=design_style,
                    html_content=html,
                ))

                print(f"  ✓ Design {i+1} complete!")

            except Exception as e:
                print(f"  ✗ Design {i+1} failed ({style['name']}): {str(e)}")
                continue

    if len(designs) == 0:
        raise ValueError("All design generations failed.")

    print(f"\n✓ Pipeline complete: {len(designs)}/{len(STYLE_PROMPTS)} designs generated")
    return designs