import uuid
import httpx
from app.config.settings import get_settings
from app.models.schemas import UserInfo, CardDesign, DesignStyle

settings = get_settings()

IDEOGRAM_API_URL = "https://api.ideogram.ai/generate"


def _build_prompt(user_info: UserInfo, style: dict) -> str:
    """Build a precise Ideogram prompt directly from user data — no GPT."""

    email_line = f"Email: {user_info.email}" if user_info.email else ""
    website_line = f"Website: {user_info.website}" if user_info.website else ""

    contact_block = "\n".join(filter(None, [
        f"Phone: {user_info.phone_number}",
        email_line,
        website_line,
        f"Address: {user_info.address}",
    ]))

    return f"""Flat graphic design of a single professional business card.
Style: {style['style_instruction']}

The card must display this exact text with correct spelling:
- Name (largest text): {user_info.name}
- Company (second largest): {user_info.company_name}
- {contact_block}

STRICT VISUAL RULES:
- Single card only, perfectly flat, top-down view, no perspective or angle
- Landscape orientation, business card proportions 3.5 x 2 inches
- Card fills 85% of image frame, centered
- Clean solid neutral background surrounding the card
- All text perfectly legible, correct English spelling, no invented text
- No hands, no table surface, no props, no shadows behind card
- No multiple cards, no stacked cards, no scattered cards
- Flat vector graphic design style, print-ready
- High resolution, clean edges, professional quality
- {style['color_instruction']}
- {style['typography_instruction']}
- {style['layout_instruction']}"""


DESIGN_STYLES = [
    {
        "name": "Minimal White",
        "theme": "minimal",
        "description": "Clean white background with a single thin gold accent line and generous whitespace",
        "style_instruction": "ultra-minimalist clean white business card design",
        "color_instruction": "pure white background #FFFFFF, dark charcoal text #1a1a1a, single thin gold accent line #C9A84C",
        "typography_instruction": "elegant thin serif font for name, light sans-serif for contact details, generous letter spacing",
        "layout_instruction": "name and company top-left, thin horizontal gold divider line in middle, contact info bottom-left, lots of white space",
    },
    {
        "name": "Dark Executive",
        "theme": "bold",
        "description": "Matte black background with metallic gold typography, premium executive feel",
        "style_instruction": "luxury dark executive business card, matte black with gold foil effect",
        "color_instruction": "matte black background #0a0a0a, metallic gold text #C9A84C, thin gold border line",
        "typography_instruction": "bold serif font for name in gold, smaller elegant sans-serif for details in light gold",
        "layout_instruction": "company name large centered top, name prominent center-left, contact details bottom in small clean text, thin gold border frame around entire card",
    },
    {
        "name": "Navy Classic",
        "theme": "corporate",
        "description": "Deep navy background with white text and gold accent, authoritative and trustworthy",
        "style_instruction": "professional navy blue corporate business card",
        "color_instruction": "deep navy background #0f2044, white text #FFFFFF, gold accent #C9A84C for name",
        "typography_instruction": "strong sans-serif bold for name in white, regular weight for company in gold, small light text for contact",
        "layout_instruction": "bold name top-left in white, company below in gold, vertical gold line left accent bar, contact info bottom-left in white small text",
    },
    {
        "name": "Luxury Cream",
        "theme": "elegant",
        "description": "Warm cream background with burgundy typography and delicate border frame",
        "style_instruction": "sophisticated luxury cream business card with refined elegant styling",
        "color_instruction": "warm cream background #F5F0E8, deep burgundy text #5C1A1A, thin burgundy decorative border",
        "typography_instruction": "classic serif font throughout, name in larger bold burgundy serif, contact in small elegant serif",
        "layout_instruction": "thin decorative rectangular border frame, name centered upper area, company below name, horizontal thin line divider, contact details centered lower area",
    },
    {
        "name": "Tech Dark",
        "theme": "tech",
        "description": "Dark slate with electric blue geometric accent stripe, sleek and modern",
        "style_instruction": "modern tech startup business card, dark with electric blue geometric accent",
        "color_instruction": "dark slate background #1a1f2e, electric blue accent #3B82F6, white text #FFFFFF",
        "typography_instruction": "clean modern geometric sans-serif, name bold white, company in blue, details in light gray",
        "layout_instruction": "vertical electric blue stripe on left 20% of card, name and company right side top, contact details right side bottom, clean geometric feel",
    },
    {
        "name": "Bold Color",
        "theme": "creative",
        "description": "Vibrant coral and white color block design, modern and energetic",
        "style_instruction": "bold modern color block business card, vibrant and contemporary",
        "color_instruction": "white background top half #FFFFFF, vibrant coral bottom half #E85D4A, white text on coral",
        "typography_instruction": "bold modern sans-serif, name large dark on white section, company and details white on coral section",
        "layout_instruction": "horizontal color split — white top 55% with name and company in dark text, coral bottom 45% with contact details in white text",
    },
]


async def _generate_image_with_ideogram(
    client: httpx.AsyncClient,
    prompt: str,
) -> str:
    """Send a single prompt to Ideogram and return the image URL."""
    response = await client.post(
        IDEOGRAM_API_URL,
        headers={
            "Api-Key": settings.IDEOGRAM_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "image_request": {
                "prompt": prompt,
                "aspect_ratio": "ASPECT_16_9",
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
    Prompts are built directly from user data — no GPT intermediary.
    """
    designs = []

    async with httpx.AsyncClient() as client:
        for i, style in enumerate(DESIGN_STYLES):
            try:
                prompt = _build_prompt(user_info, style)

                print(f"Generating design {i+1}/6: {style['name']}")
                print(f"Prompt preview: {prompt[:120]}...")

                image_url = await _generate_image_with_ideogram(client, prompt)

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

                print(f"✓ Design {i+1} done: {image_url[:60]}...")

            except Exception as e:
                print(f"✗ Design {i+1} failed: {e}")
                continue

    if len(designs) == 0:
        raise ValueError("All Ideogram generations failed")

    print(f"Successfully generated {len(designs)}/6 designs")
    return designs