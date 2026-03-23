import uuid
from app.models.schemas import UserInfo, CardDesign, DesignStyle


def _render_html(user_info: UserInfo, style: dict) -> str:
    """Render a complete self-contained business card HTML."""
    font_import = f'@import url("{style["font_url"]}");' if style.get("font_url") else ""
    email = f'<div class="contact-item">{user_info.email}</div>' if user_info.email else ""
    website = f'<div class="contact-item">{user_info.website}</div>' if user_info.website else ""
    body = style["render"](user_info, style)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
{font_import}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{
  width: 3.5in;
  height: 2in;
  overflow: hidden;
  font-family: {style['font_family']};
}}
</style>
</head>
<body>{body}</body>
</html>"""


# ── Layout Renderers ──────────────────────────────────────────────────────────

def _render_minimal_gold(u: UserInfo, s: dict) -> str:
    email = f'<div class="contact-item">{u.email}</div>' if u.email else ""
    website = f'<div class="contact-item">{u.website}</div>' if u.website else ""
    return f"""
<div style="
  width:3.5in; height:2in;
  background:#F5F4F0;
  padding: 0.22in 0.28in;
  display:flex; flex-direction:column;
  justify-content:space-between;
  position:relative;
">
  <!-- Top: Name + Company -->
  <div>
    <div style="
      font-family:'Playfair Display',Georgia,serif;
      font-size:28px; font-weight:700;
      color:#1A1A1A; letter-spacing:-0.3px;
      line-height:1.15;
    ">{u.name}</div>
    <div style="
      font-family:'DM Sans',Arial,sans-serif;
      font-size:8.5px; font-weight:500;
      color:#8A8A8A; letter-spacing:0.18em;
      text-transform:uppercase; margin-top:6px;
    ">{u.company_name}</div>
  </div>

  <!-- Gold Divider -->
  <div style="
    position:absolute; left:0; right:0;
    top:50%; height:0.7px;
    background:linear-gradient(90deg, transparent 0%, #C9A84C 8%, #C9A84C 92%, transparent 100%);
  "></div>

  <!-- Bottom: Contact -->
  <div style="
    font-family:'DM Sans',Arial,sans-serif;
    font-size:7.5px; color:#6B6B6B;
    line-height:1.75;
  ">
    <div>{u.phone_number}</div>
    {email}
    {website}
    <div>{u.address}</div>
  </div>
</div>"""


def _render_dark_executive(u: UserInfo, s: dict) -> str:
    email = f'<div style="margin-top:3px">{u.email}</div>' if u.email else ""
    website = f'<div style="margin-top:3px">{u.website}</div>' if u.website else ""
    return f"""
<div style="
  width:3.5in; height:2in;
  background:#0A0A0A;
  position:relative; overflow:hidden;
">
  <!-- Gold border frame -->
  <div style="
    position:absolute; inset:10px;
    border:0.6px solid #C9A84C;
    pointer-events:none; z-index:1;
  "></div>
  <div style="
    position:absolute; inset:13px;
    border:0.3px solid rgba(201,168,76,0.3);
    pointer-events:none; z-index:1;
  "></div>

  <!-- Content -->
  <div style="
    position:absolute; inset:0;
    padding:0.2in 0.22in 0.18in;
    display:flex; flex-direction:column;
    justify-content:space-between; z-index:2;
  ">
    <!-- Top -->
    <div>
      <div style="
        font-family:'DM Sans',Arial,sans-serif;
        font-size:7px; font-weight:500;
        color:#C9A84C; letter-spacing:0.22em;
        text-transform:uppercase;
      ">{u.company_name}</div>
      <div style="
        width:100%; height:0.5px;
        background:#C9A84C; opacity:0.5;
        margin:8px 0;
      "></div>
      <div style="
        font-family:'Playfair Display',Georgia,serif;
        font-size:22px; font-weight:700;
        color:#C9A84C; letter-spacing:0.03em;
        line-height:1.2;
      ">{u.name}</div>
    </div>

    <!-- Bottom -->
    <div>
      <div style="
        width:100%; height:0.5px;
        background:#C9A84C; opacity:0.4;
        margin-bottom:10px;
      "></div>
      <div style="
        font-family:'DM Sans',Arial,sans-serif;
        font-size:7px; color:#D4AF6A;
        line-height:1.8;
      ">
        <div>{u.phone_number}</div>
        {email}
        {website}
        <div>{u.address}</div>
      </div>
    </div>
  </div>
</div>"""


def _render_navy_corporate(u: UserInfo, s: dict) -> str:
    email = f'<div style="margin-top:3px">{u.email}</div>' if u.email else ""
    website = f'<div style="margin-top:3px">{u.website}</div>' if u.website else ""
    return f"""
<div style="
  width:3.5in; height:2in;
  background:#0D2144;
  display:flex; overflow:hidden;
  position:relative;
">
  <!-- Gold left bar -->
  <div style="width:7px; background:#C9A84C; flex-shrink:0; height:100%;"></div>

  <!-- Content -->
  <div style="
    flex:1; padding:0.2in 0.2in 0.18in 0.18in;
    display:flex; flex-direction:column;
    justify-content:space-between;
  ">
    <!-- Name + Company -->
    <div>
      <div style="
        font-family:'Playfair Display',Georgia,serif;
        font-size:22px; font-weight:700;
        color:#C9A84C; line-height:1.2;
      ">{u.name}</div>
      <div style="
        font-family:'DM Sans',Arial,sans-serif;
        font-size:8px; font-weight:500;
        color:#FFFFFF; letter-spacing:0.14em;
        text-transform:uppercase; margin-top:5px;
      ">{u.company_name}</div>
    </div>

    <!-- Divider -->
    <div style="height:0.5px; background:rgba(255,255,255,0.2); margin:0 0;"></div>

    <!-- Contact -->
    <div style="
      font-family:'DM Sans',Arial,sans-serif;
      font-size:7px; color:rgba(200,215,235,0.85);
      line-height:1.8;
    ">
      <div>· {u.phone_number}</div>
      {'<div>· ' + u.email + '</div>' if u.email else ''}
      {'<div>· ' + u.website + '</div>' if u.website else ''}
      <div>· {u.address}</div>
    </div>
  </div>
</div>"""


def _render_cream_luxury(u: UserInfo, s: dict) -> str:
    email = f'<div>{u.email}</div>' if u.email else ""
    website = f'<div>{u.website}</div>' if u.website else ""
    return f"""
<div style="
  width:3.5in; height:2in;
  background:#F4EFE4;
  position:relative; overflow:hidden;
">
  <!-- Decorative border -->
  <div style="
    position:absolute; inset:8px;
    border:0.8px solid #6B1E2E;
    pointer-events:none;
  "></div>
  <!-- Corner ornaments -->
  <div style="position:absolute;top:14px;left:14px;width:8px;height:8px;border-top:1px solid #C9A84C;border-left:1px solid #C9A84C;"></div>
  <div style="position:absolute;top:14px;right:14px;width:8px;height:8px;border-top:1px solid #C9A84C;border-right:1px solid #C9A84C;"></div>
  <div style="position:absolute;bottom:14px;left:14px;width:8px;height:8px;border-bottom:1px solid #C9A84C;border-left:1px solid #C9A84C;"></div>
  <div style="position:absolute;bottom:14px;right:14px;width:8px;height:8px;border-bottom:1px solid #C9A84C;border-right:1px solid #C9A84C;"></div>

  <!-- Content centered -->
  <div style="
    position:absolute; inset:0;
    display:flex; flex-direction:column;
    align-items:center; justify-content:center;
    text-align:center; padding:0.2in;
  ">
    <div style="
      font-family:'Playfair Display',Georgia,serif;
      font-size:22px; font-weight:700;
      color:#1A1A1A; letter-spacing:0.02em;
    ">{u.name}</div>
    <div style="
      font-family:'Playfair Display',Georgia,serif;
      font-size:9px; font-style:italic;
      color:#6B1E2E; margin-top:4px; letter-spacing:0.06em;
    ">{u.company_name}</div>

    <!-- Gold ornament -->
    <div style="
      display:flex; align-items:center;
      gap:8px; margin:10px 0;
    ">
      <div style="width:30px;height:0.5px;background:#C9A84C;"></div>
      <div style="width:4px;height:4px;background:#C9A84C;transform:rotate(45deg);"></div>
      <div style="width:30px;height:0.5px;background:#C9A84C;"></div>
    </div>

    <!-- Contact -->
    <div style="
      font-family:'DM Sans',Arial,sans-serif;
      font-size:7px; color:#5C5249;
      line-height:1.8; text-align:center;
    ">
      <div>{u.phone_number}</div>
      {email}
      {website}
      <div>{u.address}</div>
    </div>
  </div>
</div>"""


def _render_tech_slate(u: UserInfo, s: dict) -> str:
    email = f'<div>{u.email}</div>' if u.email else ""
    website = f'<div>{u.website}</div>' if u.website else ""
    return f"""
<div style="
  width:3.5in; height:2in;
  background:#1A1F2E;
  display:flex; overflow:hidden;
  position:relative;
">
  <!-- Electric blue left stripe -->
  <div style="width:6px; background:#4F8EF7; flex-shrink:0; height:100%;"></div>

  <!-- Large faint background circle -->
  <div style="
    position:absolute; right:-40px; bottom:-40px;
    width:160px; height:160px;
    border-radius:50%;
    border:1px solid rgba(79,142,247,0.12);
    pointer-events:none;
  "></div>
  <div style="
    position:absolute; right:-20px; bottom:-20px;
    width:100px; height:100px;
    border-radius:50%;
    border:1px solid rgba(79,142,247,0.08);
    pointer-events:none;
  "></div>

  <!-- Content -->
  <div style="
    flex:1; padding:0.2in 0.18in 0.18in 0.16in;
    display:flex; flex-direction:column;
    justify-content:space-between; position:relative; z-index:1;
  ">
    <!-- Name + Company -->
    <div>
      <div style="
        font-family:'DM Sans',Arial,sans-serif;
        font-size:20px; font-weight:700;
        color:#FFFFFF; line-height:1.15; letter-spacing:-0.2px;
      ">{u.name}</div>
      <div style="
        font-family:'DM Sans',Arial,sans-serif;
        font-size:8px; font-weight:500;
        color:#4F8EF7; letter-spacing:0.1em;
        margin-top:5px;
      ">{u.company_name}</div>
    </div>

    <!-- Blue divider -->
    <div style="height:0.5px; background:rgba(79,142,247,0.35);"></div>

    <!-- Contact -->
    <div style="
      font-family:'DM Sans',Arial,sans-serif;
      font-size:7px; color:#94A3B8;
      line-height:1.8; letter-spacing:0.01em;
    ">
      <div>{u.phone_number}</div>
      {email}
      {website}
      <div>{u.address}</div>
    </div>
  </div>
</div>"""


def _render_bold_split(u: UserInfo, s: dict) -> str:
    email = f'<div>{u.email}</div>' if u.email else ""
    website = f'<div>{u.website}</div>' if u.website else ""
    return f"""
<div style="
  width:3.5in; height:2in;
  display:flex; flex-direction:column;
  overflow:hidden; position:relative;
">
  <!-- White top half -->
  <div style="
    flex:1; background:#FFFFFF;
    padding:0.18in 0.22in 0.1in;
    display:flex; flex-direction:column;
    justify-content:center;
  ">
    <div style="
      font-family:'DM Sans',Arial,sans-serif;
      font-size:22px; font-weight:800;
      color:#1C1C1C; line-height:1.1;
      letter-spacing:-0.3px;
    ">{u.name}</div>
    <div style="
      font-family:'DM Sans',Arial,sans-serif;
      font-size:8px; font-weight:600;
      color:#D95F43; letter-spacing:0.12em;
      text-transform:uppercase; margin-top:5px;
    ">{u.company_name}</div>
  </div>

  <!-- Sharp divider -->
  <div style="height:2px; background:#D95F43;"></div>

  <!-- Coral bottom half -->
  <div style="
    flex:1; background:#D95F43;
    padding:0.1in 0.22in 0.18in;
    display:flex; flex-direction:column;
    justify-content:center; position:relative; overflow:hidden;
  ">
    <!-- Subtle circle decoration -->
    <div style="
      position:absolute; right:-20px; bottom:-30px;
      width:100px; height:100px; border-radius:50%;
      background:rgba(255,255,255,0.08);
    "></div>
    <div style="
      font-family:'DM Sans',Arial,sans-serif;
      font-size:7px; color:rgba(255,255,255,0.92);
      line-height:1.75; position:relative; z-index:1;
    ">
      <div>{u.phone_number}</div>
      {email}
      {website}
      <div>{u.address}</div>
    </div>
  </div>
</div>"""


# ── Design Definitions ────────────────────────────────────────────────────────

DESIGN_STYLES = [
    {
        "name": "Minimal Gold",
        "theme": "minimal",
        "description": "Off-white with single gold divider rule, Swiss precision, generous whitespace",
        "font_family": "'Playfair Display', 'DM Sans', Georgia, sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap",
        "primary_color": "#1A1A1A",
        "accent_color": "#C9A84C",
        "bg_color": "#F5F4F0",
        "render": _render_minimal_gold,
    },
    {
        "name": "Dark Executive",
        "theme": "bold",
        "description": "Matte black with gold border frame and metallic typography",
        "font_family": "'Playfair Display', 'DM Sans', Georgia, sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap",
        "primary_color": "#C9A84C",
        "accent_color": "#C9A84C",
        "bg_color": "#0A0A0A",
        "render": _render_dark_executive,
    },
    {
        "name": "Navy Corporate",
        "theme": "corporate",
        "description": "Deep navy with gold left accent bar, authoritative and professional",
        "font_family": "'Playfair Display', 'DM Sans', Georgia, sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap",
        "primary_color": "#C9A84C",
        "accent_color": "#C9A84C",
        "bg_color": "#0D2144",
        "render": _render_navy_corporate,
    },
    {
        "name": "Cream Luxury",
        "theme": "elegant",
        "description": "Warm cream with burgundy border, corner ornaments, centered layout",
        "font_family": "'Playfair Display', 'DM Sans', Georgia, sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap",
        "primary_color": "#1A1A1A",
        "accent_color": "#C9A84C",
        "bg_color": "#F4EFE4",
        "render": _render_cream_luxury,
    },
    {
        "name": "Tech Slate",
        "theme": "tech",
        "description": "Dark slate with electric blue accent stripe and geometric circles",
        "font_family": "'DM Sans', Arial, sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap",
        "primary_color": "#FFFFFF",
        "accent_color": "#4F8EF7",
        "bg_color": "#1A1F2E",
        "render": _render_tech_slate,
    },
    {
        "name": "Bold Split",
        "theme": "creative",
        "description": "White and coral color-block split, bold modern energy",
        "font_family": "'DM Sans', Arial, sans-serif",
        "font_url": "https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;800&display=swap",
        "primary_color": "#1C1C1C",
        "accent_color": "#D95F43",
        "bg_color": "#FFFFFF",
        "render": _render_bold_split,
    },
]


# ── Main Entry Point ──────────────────────────────────────────────────────────

async def generate_designs(user_info: UserInfo) -> list[CardDesign]:
    """
    Generate 6 business card designs using HTML/CSS rendering.
    Zero hallucination — text is injected directly from user data.
    Instant generation — no external API calls.
    Each design is a complete self-contained HTML document.
    """
    designs = []

    for style in DESIGN_STYLES:
        try:
            design_id = str(uuid.uuid4())
            html = _render_html(user_info, style)

            design_style = DesignStyle(
                theme=style["theme"],
                primary_color=style["primary_color"],
                secondary_color="#666666",
                accent_color=style["accent_color"],
                background_color=style["bg_color"],
                text_color=style["primary_color"],
                font_family=style["font_family"],
                layout="classic",
                design_name=style["name"],
                description=style["description"],
            )

            designs.append(CardDesign(
                id=design_id,
                style=design_style,
                html_content=html,
            ))

            print(f"✓ Generated: {style['name']}")

        except Exception as e:
            print(f"✗ Failed: {style['name']} — {str(e)}")
            continue

    if len(designs) == 0:
        raise ValueError("All design generations failed.")

    print(f"✓ Generated {len(designs)}/6 designs")
    return designs