import uuid
import json
import httpx
from openai import AsyncOpenAI
from app.config.settings import get_settings
from app.models.schemas import UserInfo, CardDesign, DesignStyle

settings = get_settings()
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

IDEOGRAM_API_URL = "https://api.ideogram.ai/generate"

# ── Step 1: ChatGPT generates 6 tailored Ideogram prompts ────────────────────

GPT_SYSTEM_PROMPT = """You are an expert business card designer and AI image prompt engineer.
Your job is to create highly detailed, specific Ideogram.ai image generation prompts 
for professional business card designs.

Each prompt must:
- Be highly specific about colors, typography style, layout, and visual elements
- Match the business type and industry
- Create a photorealistic, print-ready business card
- Include the exact text to appear on the card
- Specify landscape orientation and business card dimensions
- Be unique and visually distinct from the other 5 prompts

Return ONLY a valid JSON object with key "prompts" containing array of exactly 6 objects.
Each object must have:
- "prompt": the full Ideogram image generation prompt
- "design_name": creative name for this design
- "theme": one of minimal|bold|elegant|tech|creative|corporate
- "description": one sentence describing the aesthetic"""

GPT_USER_TEMPLATE = """Create 6 unique Ideogram.ai business card design prompts for:

Name: {name}
Company: {company_name}
Phone: {phone_number}
Email: {email}
Website: {website}
Address: {address}
Business Type: {business_description}

The 6 designs must be completely different styles:
1. Minimal/Clean — white or cream, single accent, lots of space
2. Dark/Luxury — dark background, gold or silver accents, premium feel  
3. Bold/Colorful — vivid colors, strong personality, modern
4. Elegant/Sophisticated — refined, serif typography, jewel tones
5. Tech/Modern — gradients, geometric shapes, innovative feel
6. Corporate/Professional — classic, trustworthy, traditional

For each prompt:
- Specify exact colors (hex or descriptive)
- Describe typography style (serif/sans-serif, weight, size hierarchy)
- Describe layout (where name, company, contact info are positioned)
- Include all contact details that should appear on the card
- Mention photorealistic, print-ready, high resolution, 300dpi
- End with: "landscape orientation, standard business card 3.5x2 inches, isolated on clean background"

Make prompts industry-appropriate for: {business_description}"""


async def _generate_prompts_with_gpt(user_info: UserInfo) -> list[dict]:
    """Use ChatGPT to generate 6 tailored Ideogram prompts."""
    user_message = GPT_USER_TEMPLATE.format(
        name=user_info.name,
        company_name=user_info.company_name,
        phone_number=user_info.phone_number,
        email=user_info.email or "N/A",
        website=user_info.website or "N/A",
        address=user_info.address,
        business_description=user_info.business_description,
    )

    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": GPT_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.9,
        response_format={"type": "json_object"},
    )

    data = json.loads(response.choices[0].message.content)
    prompts = data.get("prompts", [])

    if not isinstance(prompts, list) or len(prompts) == 0:
        raise ValueError("GPT did not return valid prompts array")

    return prompts[:6]


# ── Step 2: Send each prompt to Ideogram ─────────────────────────────────────

async def _generate_image_with_ideogram(
    client: httpx.AsyncClient,
    prompt: str
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
                "magic_prompt_option": "OFF",  # OFF because GPT already wrote the prompt
                "style_type": "REALISTIC",
            }
        },
        timeout=60.0,
    )
    response.raise_for_status()
    data = response.json()
    return data["data"][0]["url"]


# ── Main function ─────────────────────────────────────────────────────────────

async def generate_designs(user_info: UserInfo) -> list[CardDesign]:
    """
    Two-step generation:
    1. ChatGPT writes 6 tailored Ideogram prompts based on user business info
    2. Ideogram generates 6 photorealistic business card images
    """

    # Step 1: Get prompts from ChatGPT
    print(f"Generating prompts with ChatGPT for: {user_info.name}")
    prompt_configs = await _generate_prompts_with_gpt(user_info)
    print(f"Got {len(prompt_configs)} prompts from ChatGPT")

    # Step 2: Generate images with Ideogram
    designs = []
    async with httpx.AsyncClient() as client:
        for i, config in enumerate(prompt_configs):
            try:
                print(f"Generating Ideogram image {i+1}/6: {config.get('design_name')}")
                image_url = await _generate_image_with_ideogram(
                    client,
                    config["prompt"]
                )

                design_style = DesignStyle(
                    theme=config.get("theme", "minimal"),
                    primary_color="#000000",
                    secondary_color="#666666",
                    accent_color="#c9a84c",
                    background_color="#ffffff",
                    text_color="#000000",
                    font_family="Georgia",
                    layout="classic",
                    design_name=config.get("design_name", f"Design {i+1}"),
                    description=config.get("description", ""),
                )

                designs.append(CardDesign(
                    id=str(uuid.uuid4()),
                    style=design_style,
                    html_content=image_url,
                ))

                print(f"✓ Design {i+1} generated successfully")

            except Exception as e:
                print(f"✗ Failed to generate design {i+1}: {e}")
                continue

    if len(designs) == 0:
        raise ValueError("All design generations failed")

    print(f"Successfully generated {len(designs)} designs")
    return designs