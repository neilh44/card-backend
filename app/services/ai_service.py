import uuid
import httpx
from app.config.settings import get_settings
from app.models.schemas import UserInfo, CardDesign, DesignStyle

settings = get_settings()

IDEOGRAM_API_URL = "https://api.ideogram.ai/generate"

NEGATIVE_PROMPT = (
    "background, surface, table, desk, environment, grey background, "
    "beige background, colored background, textured background, "
    "shadow behind card, drop shadow, cast shadow, "
    "3D perspective, angled view, tilted card, isometric, "
    "multiple cards, stacked cards, scattered cards, "
    "hands, fingers, props, objects, "
    "portrait orientation, vertical card, square card, "
    "blurry text, distorted text, misspelled text, extra text, "
    "placeholder text, lorem ipsum, watermark, "
    "low resolution, pixelated, photo, photography, lifestyle"
)


def _build_prompt(user_info: UserInfo, style: dict) -> str:
    """Build the complete prompt for each style."""

    email_line = f"Email: {user_info.email}" if user_info.email else ""
    website_line = f"Website: {user_info.website}" if user_info.website else ""
    email_rule = f'"{user_info.email}" must include @ symbol, correct domain spelling.' if user_info.email else ""
    website_rule = f'"{user_info.website}" must be spelled correctly.' if user_info.website else ""

    contact_block = "\n".join(filter(None, [
        f"Phone: {user_info.phone_number}",
        email_line,
        website_line,
        f"Address: {user_info.address}",
    ]))

    return f"""You are a senior graphic designer at a world-class print studio \
specializing in luxury business card design. Your only task is to produce \
a single flat print-ready business card artwork file.

CANVAS AND CARD:
This image IS the business card. The card fills the entire canvas \
completely from edge to edge. There is no background. There is no surface. \
There is no environment. The card edges ARE the image edges. \
Canvas ratio is exactly 3.5 wide by 2 tall — standard landscape business card. \
Think of this as an open flat design file in Illustrator or InDesign, \
not a photo of a card.

DESIGN STYLE:
{style['design_style']}

TYPOGRAPHY AND COLORS:
{style['typography']}

EXACT TEXT — copy every character precisely, no alterations whatsoever:
Name: {user_info.name}
Company: {user_info.company_name}
Phone: {user_info.phone_number}
{email_line}
{website_line}
Address: {user_info.address}

EXACT LAYOUT:
{style['layout']}

TEXT ACCURACY RULES — critical:
- "{user_info.name}" must be spelled with exactly these letters in this order
- "{user_info.company_name}" must be spelled exactly, correct capitalisation
- "{user_info.phone_number}" must show every digit correctly, no substitutions
- {email_rule}
- {website_rule}
- "{user_info.address}" must be spelled correctly
- Do NOT add job title, tagline, social media, QR code, or any text not listed above

ABSOLUTE RULES — these cannot be broken:
- The image canvas equals the card. No grey. No beige. No background. \
No surface. No environment. Nothing outside the card.
- Perfectly flat. Zero angle. Zero tilt. Zero shadow. Zero perspective. \
This is a flat artwork file not a photo.
- Landscape orientation strictly — width must always be greater than height.
- Every character in the text block above must appear exactly as written.
- Final result must look like a print-ready flat design file from a \
premium professional print studio."""


DESIGN_STYLES = [
    {
        "name": "Minimal Gold",
        "theme": "minimal",
        "description": "Off-white card with single gold divider rule, generous whitespace, Swiss precision",
        "design_style": (
            "Minimalist luxury. Off-white card background #F5F4F0. "
            "A single thin horizontal gold rule #C9A84C at exactly the vertical midpoint "
            "divides the card into two equal halves. "
            "Upper half contains name and company. Lower half contains contact details. "
            "Generous whitespace throughout. Swiss design school precision. "
            "Every element placed with surgical intentionality."
        ),
        "typography": (
            "Name: bold serif 44pt similar to Canela or Freight Display, "
            "color #1A1A1A, on one line if the name fits. "
            "Company: 10pt uppercase sans-serif, letter-spacing 0.18em, "
            "color #5A5A5A, directly below name. "
            "Contact details: 8pt regular sans-serif, color #6B6B6B, "
            "line-height 1.7, each item its own line. "
            "Gold divider rule: 1pt weight, color #C9A84C, "
            "spans full card width at 50 percent vertical position."
        ),
        "layout": (
            "Top-left: name in bold serif large, 8mm from left edge, 8mm from top edge. "
            "Below name: company in small uppercase sans-serif with wide letter-spacing. "
            "Center: single thin gold horizontal rule spanning full card width. "
            "Bottom-left: phone number, email, website, address "
            "each stacked on their own line, 8mm from left edge, 10mm from bottom edge. "
            "Bottom-right quadrant: intentionally completely empty white space."
        ),
    },
    {
        "name": "Dark Executive",
        "theme": "bold",
        "description": "Matte black card with metallic gold typography and thin gold border frame",
        "design_style": (
            "Ultra-premium luxury executive. "
            "Deep matte black card background #0A0A0A. "
            "Thin elegant gold rectangular border frame #C9A84C, 0.5pt line weight, "
            "inset 3mm from all four card edges. "
            "A thin gold horizontal rule inside the frame at the vertical midpoint. "
            "All typography in metallic gold. "
            "Communicates exclusivity, authority, and premium positioning. "
            "Think private banking, top-tier law firm, luxury real estate."
        ),
        "typography": (
            "Name: bold serif 20pt similar to Bodoni or Didot, "
            "metallic gold color #C9A84C, letter-spacing 0.05em. "
            "Company: 9pt uppercase sans-serif, gold #C9A84C, "
            "letter-spacing 0.2em, light weight. "
            "Contact details: 7.5pt regular sans-serif, pale gold #D4AF6A, "
            "line-height 1.8, each item on its own line. "
            "Gold border frame: 0.5pt, color #C9A84C, 3mm inset from edges. "
            "Gold divider rule: 0.5pt, color #C9A84C, inside the frame at midpoint."
        ),
        "layout": (
            "Thin gold rectangular border frame inset 3mm from all edges. "
            "Inside frame, top-left: company name in uppercase gold small caps, "
            "6mm from frame edge, near top. "
            "Thin gold horizontal rule below company name. "
            "Name in large bold gold serif, prominent center-left position inside frame. "
            "Thin gold horizontal rule below name. "
            "Contact details in small pale gold text, bottom-left inside frame, "
            "each line stacked vertically: phone, email, website, address. "
            "Right third of card inside frame: intentionally empty — "
            "luxurious negative space, only the gold border frame visible."
        ),
    },
]


async def _generate_image_with_ideogram(
    client: httpx.AsyncClient,
    prompt: str,
) -> str:
    """Send prompt to Ideogram V2 and return image URL."""
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
        timeout=90.0,
    )
    response.raise_for_status()
    data = response.json()
    return data["data"][0]["url"]


async def generate_designs(user_info: UserInfo) -> list[CardDesign]:
    """
    Generate 2 business card designs using Ideogram.ai V2.
    Prompts built directly from user data — no GPT intermediary.
    Each prompt sets full designer context before card specifications.
    """
    designs = []

    async with httpx.AsyncClient() as client:
        for i, style in enumerate(DESIGN_STYLES):
            try:
                prompt = _build_prompt(user_info, style)

                print(f"\nGenerating design {i+1}/{len(DESIGN_STYLES)}: {style['name']}")
                print(f"Prompt length: {len(prompt)} chars")

                image_url = await _generate_image_with_ideogram(client, prompt)

                design_style = DesignStyle(
                    theme=style["theme"],
                    primary_color="#C9A84C",
                    secondary_color="#666666",
                    accent_color="#C9A84C",
                    background_color="#F5F4F0" if style["theme"] == "minimal" else "#0A0A0A",
                    text_color="#1A1A1A" if style["theme"] == "minimal" else "#C9A84C",
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

                print(f"✓ Design {i+1} complete: {image_url[:70]}...")

            except Exception as e:
                print(f"✗ Design {i+1} failed ({style['name']}): {str(e)}")
                continue

    if len(designs) == 0:
        raise ValueError("All Ideogram generations failed. Check API key and quota.")

    print(f"\n✓ Generated {len(designs)}/{len(DESIGN_STYLES)} designs successfully")
    return designs