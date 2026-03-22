import uuid
import httpx
from app.config.settings import get_settings
from app.models.schemas import UserInfo, CardDesign, DesignStyle

settings = get_settings()

IDEOGRAM_API_URL = "https://api.ideogram.ai/generate"

DESIGN_STYLES = [
    {
        "name": "Minimal Elegance",
        "theme": "minimal",
        "description": "Clean white background, single gold accent line, generous whitespace, premium feel",
        "style_prompt": "minimalist white business card, single thin gold accent line, elegant serif typography, lots of white space, premium luxury feel, professional"
    },
    {
        "name": "Dark Executive",
        "theme": "bold",
        "description": "Near-black background with metallic gold typography, dramatic and authoritative",
        "style_prompt": "dark black business card, metallic gold typography, dramatic shadows, executive luxury feel, sophisticated dark background, premium quality"
    },
    {
        "name": "Bold Modern",
        "theme": "creative",
        "description": "Vivid colors, strong geometric shapes, contemporary design",
        "style_prompt": "bold colorful modern business card, vibrant color blocking, strong geometric shapes, contemporary graphic design, eye-catching"
    },
    {
        "name": "Luxury serif",
        "theme": "elegant",
        "description": "Deep jewel tones, serif typography, refined and luxurious",
        "style_prompt": "luxury business card deep jewel tone color, elegant serif font, refined spacing, high-end brand feel, sophisticated layout"
    },
    {
        "name": "Tech Startup",
        "theme": "tech",
        "description": "Gradient background, geometric accents, sleek and modern",
        "style_prompt": "tech startup business card, subtle gradient background, geometric accent shapes, sleek modern sans-serif font, innovative feel"
    },
    {
        "name": "Corporate Classic",
        "theme": "corporate",
        "description": "Navy and white, traditional layout, trustworthy and professional",
        "style_prompt": "corporate professional business card, navy blue and white color scheme, traditional clean layout, trustworthy business feel, classic typography"
    },
]


def _build_ideogram_prompt(user_info: UserInfo, style: dict) -> str:
    return f"""Professional business card design for {user_info.name}, {user_info.company_name}.
Style: {style['style_prompt']}.
Include text: "{user_info.name}", "{user_info.company_name}", "{user_info.phone_number}"{f', "{user_info.email}"' if user_info.email else ''}{f', "{user_info.website}"' if user_info.website else ''}, "{user_info.address}".
Landscape orientation, standard business card dimensions 3.5x2 inches, photorealistic print-ready design, high resolution, no extra elements outside card borders."""


async def generate_designs(user_info: UserInfo) -> list[CardDesign]:
    """Generate 6 business card designs using Ideogram.ai image generation."""
    designs = []

    async with httpx.AsyncClient(timeout=60.0) as client:
        for style in DESIGN_STYLES:
            try:
                prompt = _build_ideogram_prompt(user_info, style)

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
                            "magic_prompt_option": "AUTO",
                            "style_type": "REALISTIC"
                        }
                    }
                )

                response.raise_for_status()
                data = response.json()

                image_url = data["data"][0]["url"]
                design_id = str(uuid.uuid4())

                # Build a minimal DesignStyle for compatibility
                design_style = DesignStyle(
                    theme=style["theme"],
                    primary_color="#000000",
                    secondary_color="#666666",
                    accent_color="#c9a84c",
                    background_color="#ffffff",
                    text_color="#000000",
                    font_family="Georgia",
                    layout="classic",
                    design_name=style["name"],
                    description=style["description"],
                )

                # html_content now holds the image URL for frontend rendering
                designs.append(CardDesign(
                    id=design_id,
                    style=design_style,
                    html_content=image_url,   # ← image URL instead of HTML
                ))

            except Exception as e:
                print(f"Ideogram generation failed for style {style['name']}: {e}")
                continue

    if len(designs) == 0:
        raise ValueError("All Ideogram generations failed")

    return designs