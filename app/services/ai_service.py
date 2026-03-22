import uuid
import httpx
from app.config.settings import get_settings
from app.models.schemas import UserInfo, CardDesign, DesignStyle

settings = get_settings()

IDEOGRAM_API_URL = "https://api.ideogram.ai/generate"

NEGATIVE_PROMPT = "background objects, bowl, plate, dish, table, wood, marble, fabric, props, decorative objects, multiple cards, stacked cards, scattered cards, hands, fingers, shadows behind card, 3D perspective, angled view, tilted, lifestyle photography, realistic photography, texture background, colored background, gradient background, dark background, any objects outside the card"


def _build_prompt(user_info: UserInfo, style: dict) -> str:
    """Build precise Ideogram prompt directly from user data."""

    lines = [
        f'"{user_info.name}"',
        f'"{user_info.company_name}"',
        f'"{user_info.phone_number}"',
    ]
    if user_info.email:
        lines.append(f'"{user_info.email}"')
    if user_info.website:
        lines.append(f'"{user_info.website}"')
    lines.append(f'"{user_info.address}"')

    text_block = ", ".join(lines)

    return f"""Professional business card graphic design, card fills entire image frame edge to edge.

Exact card dimensions: 3.5 inches wide by 2 inches tall, standard business card size, landscape orientation, horizontal layout.

Card design style: {style['style_instruction']}
Colors: {style['color_instruction']}
Typography: {style['typography_instruction']}
Layout: {style['layout_instruction']}

Text to display on card exactly as written, correct spelling guaranteed:
{text_block}

REQUIREMENTS:
- Business card fills 100% of the image, no background visible outside the card
- Card edges go to image borders, full bleed design
- Perfectly flat top-down view, zero perspective, zero angle, zero tilt
- All text spelled exactly as provided, no changes, no hallucinated text
- Clean flat graphic design, print-ready quality 300dpi
- Standard business card 3.5 x 2 inch proportions strictly maintained
- No props, no background, no shadows, card only"""


DESIGN_STYLES = [
    {
        "name": "Minimal White",
        "theme": "minimal",
        "description": "Clean white background with a single thin gold accent line",
        "style_instruction": "ultra-minimalist clean white business card, premium paper texture feel",
        "color_instruction": "pure white background #FFFFFF, dark charcoal text #1C1C1C, single thin gold accent line #C9A84C",
        "typography_instruction": "elegant serif font for name large and bold, clean sans-serif small for contact details, generous letter spacing",
        "layout_instruction": "name top-left large bold, company name below in medium weight, thin horizontal gold line divider across full width at midpoint, contact details bottom-right in small clean text columns",
    },
    {
        "name": "Dark Executive",
        "theme": "bold",
        "description": "Matte black with metallic gold typography, luxury executive feel",
        "style_instruction": "luxury matte black business card with gold foil typography effect",
        "color_instruction": "matte black background #0A0A0A, all text in metallic gold #C9A84C, thin gold border frame",
        "typography_instruction": "bold serif font for name in large gold, elegant sans-serif for company in medium gold, small light text for contact details in pale gold",
        "layout_instruction": "thin gold rectangular border frame inside card edges, company name large centered top third, name bold prominent center-left, thin gold divider line, contact details bottom in two columns",
    },
    {
        "name": "Navy Professional",
        "theme": "corporate",
        "description": "Deep navy background, white and gold typography, authoritative",
        "style_instruction": "deep navy blue professional corporate business card",
        "color_instruction": "deep navy background #0D1B3E, name in gold #C9A84C, all other text white #FFFFFF, thin gold accent",
        "typography_instruction": "bold sans-serif for name in gold, medium weight for company in white, small regular for contact details in white",
        "layout_instruction": "bold gold name top-left large, company in white below name, vertical thin gold line left side accent bar 8px wide, contact details bottom-left stacked vertically in white small text",
    },
    {
        "name": "Luxury Cream",
        "theme": "elegant",
        "description": "Warm cream, burgundy typography, delicate border frame, sophisticated",
        "style_instruction": "sophisticated luxury cream business card with refined elegant styling and decorative border",
        "color_instruction": "warm cream background #F5F0E8, deep burgundy text #5C1A1A, thin burgundy decorative border frame",
        "typography_instruction": "classic serif font throughout, name in large bold burgundy, company medium serif, contact info in small elegant serif",
        "layout_instruction": "thin elegant rectangular decorative border frame inset from edges, name centered upper area large bold serif, company centered below with thin line separator, contact details centered lower area in small columns",
    },
    {
        "name": "Tech Slate",
        "theme": "tech",
        "description": "Dark slate with electric blue left accent stripe, modern tech feel",
        "style_instruction": "modern tech business card dark slate with geometric electric blue accent",
        "color_instruction": "dark slate background #1A1F2E, electric blue accent stripe #3B82F6, white text #FFFFFF, light gray secondary text #94A3B8",
        "typography_instruction": "geometric modern sans-serif, name bold white large, company in electric blue medium, contact details in light gray small",
        "layout_instruction": "solid electric blue vertical stripe left 18% of card width, white space right 82%, name top-right area bold white, company below in blue, thin white horizontal line, contact details bottom-right in light gray stacked",
    },
    {
        "name": "Bold Split",
        "theme": "creative",
        "description": "White and coral horizontal color block split, bold and modern",
        "style_instruction": "bold modern horizontal color block split business card design",
        "color_instruction": "top 55% white #FFFFFF with dark text #1C1C1C, bottom 45% coral red #E85D4A with white text #FFFFFF",
        "typography_instruction": "bold modern sans-serif throughout, name large dark on white section, contact details white on coral section",
        "layout_instruction": "clean horizontal split halfway down card, name and company top white section left-aligned bold dark, phone email website address bottom coral section left-aligned white small text, sharp clean dividing line between sections",
    },
]


async def _generate_image_with_ideogram(
    client: httpx.AsyncClient,
    prompt: str,
) -> str:
    """Send prompt to Ideogram with negative prompt and return image URL."""
    response = await client.post(
        IDEOGRAM_API_URL,
        headers={
            "Api-Key": settings.IDEOGRAM_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "image_request": {
                "prompt": prompt,
                "negative_prompt": NEGATIVE_PROMPT,
                "aspect_ratio": "ASPECT_3_2",
                "model": "V_2",
                "magic_prompt_option": "OFF",
                "style_type": "DESIGN",
            }
        },
        timeout=60.0,
    )
    response.raise_for_status()
    data = response.json()
    return data["data"][0]["url"]


async def generate_designs(user_info: UserInfo) -> list[CardDesign]:
    """
    Generate 6 business card designs using Ideogram.ai.
    Prompts built directly from user data with no GPT intermediary.
    """
    designs = []

    async with httpx.AsyncClient() as client:
        for i, style in enumerate(DESIGN_STYLES):
            try:
                prompt = _build_prompt(user_info, style)

                print(f"Generating design {i+1}/6: {style['name']}")

                image_url = await _generate_image_with_ideogram(
                    client, prompt
                )

                design_style = DesignStyle(
                    theme=style["theme"],
                    primary_color="#000000",
                    secondary_color="#666666",
                    accent_color="#C9A84C",
                    background_color="#ffffff",
                    text_color="#000000",
                    font_family="Georgia",
                    layout="classic",
                    design_name=style["name"],
                    description=style["description"],
                )

                designs.append(CardDesign(
                    id=str(uuid.uuid4()),
                    style=design_style,
                    html_content=image_url,
                ))

                print(f"✓ Design {i+1} done")

            except Exception as e:
                print(f"✗ Design {i+1} failed: {e}")
                continue

    if len(designs) == 0:
        raise ValueError("All Ideogram generations failed")

    print(f"Generated {len(designs)}/6 designs successfully")
    return designs