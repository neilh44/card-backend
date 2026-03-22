import json
import uuid
from openai import AsyncOpenAI
from app.config.settings import get_settings
from app.models.schemas import UserInfo, CardDesign, DesignStyle

settings = get_settings()
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT = """You are an expert business card designer. Generate exactly 6 unique, 
professional business card designs as structured JSON. Each design must be visually distinct 
with different color schemes, typography, and layouts. Return ONLY valid JSON, no markdown."""

DESIGN_PROMPT = """Create 6 unique business card designs for:
- Name: {name}
- Company: {company_name}
- Phone: {phone_number}
- Address: {address}
- Business: {business_description}
- Email: {email}
- Website: {website}

Return a JSON object with key "designs" containing an array of exactly 6 items.
Each item must follow this exact schema:
{{
  "theme": "one of: minimal|bold|elegant|tech|creative|corporate",
  "primary_color": "#hexcode",
  "secondary_color": "#hexcode",
  "accent_color": "#hexcode",
  "background_color": "#hexcode",
  "text_color": "#hexcode",
  "font_family": "Google Font name",
  "font_family_url": "https://fonts.googleapis.com/css2?family=...",
  "layout": "one of: classic|left-accent|top-banner|split|centered|diagonal",
  "tagline": "short optional tagline for the business",
  "design_name": "creative name for this design style",
  "description": "one sentence describing the aesthetic"
}}

Make all 6 designs truly diverse:
1. Minimal — white/cream background, single accent line, lots of space
2. Dark/Dramatic — near-black background, metallic gold typography
3. Bold/Modern — vivid color, strong contrast, contemporary feel
4. Elegant/Luxury — deep color, serif-inspired, refined spacing
5. Tech/Startup — gradient tones, geometric feel, sleek sans-serif
6. Corporate/Classic — navy or charcoal, traditional, trustworthy

Ensure text contrast is readable in all designs."""


def _render_classic(u: UserInfo, s: DesignStyle) -> str:
    tagline = f'<p style="color:{s.accent_color};font-size:8px;letter-spacing:2px;text-transform:uppercase;margin-top:2px">{s.tagline}</p>' if s.tagline else ""
    email = f'<p style="font-size:8px;margin-top:2px;color:{s.secondary_color}">{u.email}</p>' if u.email else ""
    website = f'<p style="font-size:8px;color:{s.secondary_color}">{u.website}</p>' if u.website else ""
    return f"""
<div style="width:100%;height:100%;padding:22px 24px;display:flex;flex-direction:column;justify-content:space-between;">
  <div>
    <div style="width:32px;height:3px;background:{s.primary_color};margin-bottom:10px;"></div>
    <h1 style="font-size:16px;font-weight:700;color:{s.primary_color};letter-spacing:0.5px">{u.name}</h1>
    {tagline}
    <p style="font-size:9px;color:{s.secondary_color};margin-top:4px;font-weight:500">{u.company_name}</p>
  </div>
  <div>
    <div style="width:100%;height:1px;background:{s.accent_color};opacity:0.3;margin-bottom:8px"></div>
    <p style="font-size:8px;margin-bottom:2px">{u.phone_number}</p>
    {email}
    {website}
    <p style="font-size:7px;color:{s.secondary_color};margin-top:3px">{u.address}</p>
  </div>
</div>"""


def _render_left_accent(u: UserInfo, s: DesignStyle) -> str:
    email = f'<p style="font-size:7.5px;margin-top:2px">{u.email}</p>' if u.email else ""
    website = f'<p style="font-size:7.5px">{u.website}</p>' if u.website else ""
    tagline = f'<p style="font-size:7px;opacity:0.8;margin-top:2px;font-style:italic">{s.tagline}</p>' if s.tagline else ""
    return f"""
<div style="width:100%;height:100%;display:flex;">
  <div style="width:8px;background:{s.primary_color};height:100%;flex-shrink:0;"></div>
  <div style="flex:1;padding:16px 18px;display:flex;flex-direction:column;justify-content:center;">
    <h1 style="font-size:15px;font-weight:800;color:{s.primary_color}">{u.name}</h1>
    <p style="font-size:8.5px;font-weight:600;color:{s.accent_color};letter-spacing:1.5px;text-transform:uppercase;margin-top:2px">{u.company_name}</p>
    {tagline}
    <div style="width:24px;height:1.5px;background:{s.accent_color};margin:8px 0"></div>
    <p style="font-size:8px">{u.phone_number}</p>
    {email}
    {website}
    <p style="font-size:7px;color:{s.secondary_color};margin-top:4px">{u.address}</p>
  </div>
</div>"""


def _render_top_banner(u: UserInfo, s: DesignStyle) -> str:
    email = f'<span style="margin-left:10px">{u.email}</span>' if u.email else ""
    website = f'<p style="font-size:7.5px;color:{s.secondary_color};margin-top:2px">{u.website}</p>' if u.website else ""
    return f"""
<div style="width:100%;height:100%;display:flex;flex-direction:column;">
  <div style="background:{s.primary_color};padding:14px 18px;">
    <h1 style="font-size:15px;font-weight:700;color:#fff">{u.name}</h1>
    <p style="font-size:8px;color:{s.accent_color};letter-spacing:2px;text-transform:uppercase;margin-top:2px">{u.company_name}</p>
  </div>
  <div style="flex:1;padding:12px 18px;display:flex;flex-direction:column;justify-content:center;background:{s.background_color}">
    <p style="font-size:8px;margin-bottom:3px;color:{s.text_color}">{u.phone_number}{email}</p>
    {website}
    <p style="font-size:7px;color:{s.secondary_color};margin-top:5px">{u.address}</p>
  </div>
</div>"""


def _render_split(u: UserInfo, s: DesignStyle) -> str:
    initials = "".join(w[0].upper() for w in u.name.split()[:2])
    email = f'<p style="font-size:7.5px;margin-top:2px">{u.email}</p>' if u.email else ""
    website = f'<p style="font-size:7.5px">{u.website}</p>' if u.website else ""
    return f"""
<div style="width:100%;height:100%;display:flex;">
  <div style="width:42%;background:{s.primary_color};padding:16px 14px;display:flex;flex-direction:column;align-items:center;justify-content:center;">
    <div style="width:44px;height:44px;border-radius:50%;border:2px solid {s.accent_color};display:flex;align-items:center;justify-content:center;color:#fff;font-size:16px;font-weight:700">{initials}</div>
    <p style="color:#fff;font-size:7.5px;text-align:center;margin-top:8px;opacity:0.9;font-weight:600">{u.company_name}</p>
  </div>
  <div style="flex:1;padding:14px 16px;display:flex;flex-direction:column;justify-content:center;">
    <h1 style="font-size:14px;font-weight:700;color:{s.primary_color}">{u.name}</h1>
    <div style="width:20px;height:2px;background:{s.accent_color};margin:6px 0"></div>
    <p style="font-size:8px;margin-bottom:2px">{u.phone_number}</p>
    {email}
    {website}
    <p style="font-size:7px;color:{s.secondary_color};margin-top:4px">{u.address}</p>
  </div>
</div>"""


def _render_centered(u: UserInfo, s: DesignStyle) -> str:
    tagline = f'<p style="font-size:7px;color:{s.accent_color};letter-spacing:2px;text-transform:uppercase;margin-top:3px">{s.tagline}</p>' if s.tagline else ""
    contact = f'{u.phone_number}'
    if u.email:
        contact += f' &nbsp;·&nbsp; {u.email}'
    website = f'<p style="font-size:7.5px;color:{s.secondary_color};margin-top:2px">{u.website}</p>' if u.website else ""
    return f"""
<div style="width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:16px;">
  <h1 style="font-size:17px;font-weight:700;color:{s.primary_color};letter-spacing:1px">{u.name}</h1>
  {tagline}
  <p style="font-size:8.5px;font-weight:500;color:{s.secondary_color};margin-top:4px">{u.company_name}</p>
  <div style="width:40px;height:1.5px;background:{s.accent_color};margin:10px auto"></div>
  <p style="font-size:7.5px;color:{s.text_color}">{contact}</p>
  {website}
  <p style="font-size:7px;color:{s.secondary_color};margin-top:4px">{u.address}</p>
</div>"""


def _render_diagonal(u: UserInfo, s: DesignStyle) -> str:
    email = f'<p style="font-size:7.5px;margin-top:2px;color:{s.text_color}">{u.email}</p>' if u.email else ""
    website = f'<p style="font-size:7.5px;color:{s.secondary_color}">{u.website}</p>' if u.website else ""
    return f"""
<div style="width:100%;height:100%;position:relative;overflow:hidden;background:{s.background_color}">
  <div style="position:absolute;top:-30px;right:-40px;width:200px;height:200px;background:{s.primary_color};transform:rotate(20deg);opacity:0.9;"></div>
  <div style="position:absolute;bottom:-40px;left:-20px;width:120px;height:120px;background:{s.accent_color};transform:rotate(15deg);opacity:0.15;"></div>
  <div style="position:absolute;inset:0;padding:18px 20px;display:flex;flex-direction:column;justify-content:space-between;">
    <div>
      <h1 style="font-size:16px;font-weight:800;color:{s.text_color}">{u.name}</h1>
      <p style="font-size:8px;letter-spacing:1.5px;text-transform:uppercase;color:{s.accent_color};margin-top:3px">{u.company_name}</p>
    </div>
    <div>
      <p style="font-size:8px;color:{s.text_color}">{u.phone_number}</p>
      {email}
      {website}
      <p style="font-size:7px;color:{s.secondary_color};margin-top:3px">{u.address}</p>
    </div>
  </div>
</div>"""


LAYOUT_RENDERERS = {
    "classic": _render_classic,
    "left-accent": _render_left_accent,
    "top-banner": _render_top_banner,
    "split": _render_split,
    "centered": _render_centered,
    "diagonal": _render_diagonal,
}


def render_card_html(user_info: UserInfo, style: DesignStyle) -> str:
    """Render a business card as a complete self-contained HTML document."""
    font_import = f'@import url("{style.font_family_url}");' if style.font_family_url else ""
    renderer = LAYOUT_RENDERERS.get(style.layout, _render_classic)
    body = renderer(user_info, style)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
{font_import}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  width: 3.5in;
  height: 2in;
  font-family: '{style.font_family}', Georgia, sans-serif;
  background: {style.background_color};
  color: {style.text_color};
  overflow: hidden;
  position: relative;
}}
</style>
</head>
<body>{body}</body>
</html>"""


async def generate_designs(user_info: UserInfo) -> list[CardDesign]:
    """Call OpenAI GPT-4o to generate 6 design specs, then render HTML for each."""
    prompt = DESIGN_PROMPT.format(
        name=user_info.name,
        company_name=user_info.company_name,
        phone_number=user_info.phone_number,
        address=user_info.address,
        business_description=user_info.business_description,
        email=user_info.email or "N/A",
        website=user_info.website or "N/A",
    )

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.85,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)

    designs_raw = data.get("designs", [])
    if not isinstance(designs_raw, list) or len(designs_raw) == 0:
        raise ValueError("AI did not return a valid designs array")

    designs = []
    for item in designs_raw[:6]:
        design_id = str(uuid.uuid4())
        style = DesignStyle(**item)
        html = render_card_html(user_info, style)
        designs.append(CardDesign(id=design_id, style=style, html_content=html))

    return designs
