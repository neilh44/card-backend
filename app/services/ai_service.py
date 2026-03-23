import uuid
import httpx
from app.config.settings import get_settings
from app.models.schemas import UserInfo, CardDesign, DesignStyle

settings = get_settings()

IDEOGRAM_API_URL = "https://api.ideogram.ai/generate"

NEGATIVE_PROMPT = (
    "background objects, bowl, plate, dish, table surface, wood grain, marble texture, "
    "fabric, linen, props, decorative objects, plants, flowers, pen, pencil, "
    "multiple cards, stacked cards, scattered cards, overlapping cards, "
    "hands, fingers, people, person, "
    "heavy drop shadow, cast shadow, 3D perspective, angled view, tilted card, "
    "isometric view, floating card effect, "
    "lifestyle photography, realistic photography, photo background, "
    "colored background, gradient background, dark background, textured background, "
    "busy background, pattern background, "
    "blurry text, unreadable text, distorted text, misspelled text, "
    "extra text, random letters, watermark, logo placeholder, "
    "low resolution, pixelated, jpeg artifacts"
)

DESIGN_STYLES = [
    {
        "name": "Minimal White",
        "theme": "minimal",
        "description": "Ultra-clean white card with a single hairline gold accent and generous whitespace",
        "style_instruction": (
            "Ultra-minimalist Scandinavian-inspired business card. "
            "Extreme whitespace, sparse layout, every element placed with surgical precision. "
            "The card feels expensive through restraint not decoration. "
            "Think Swiss graphic design, Dieter Rams design philosophy."
        ),
        "color_instruction": (
            "Card background: pure white #FFFFFF. "
            "Primary text name: near-black charcoal #1C1C1C. "
            "Secondary text company and contact: medium dark grey #4A4A4A. "
            "Single accent element: hairline gold #C9A84C. "
            "No other colours, no gradients, no tints."
        ),
        "typography_instruction": (
            "Name: large 22pt bold serif typeface similar to Freight Display or Canela, "
            "tight letter-spacing. "
            "Company: 10pt light sans-serif uppercase, letter-spacing 0.15em. "
            "Contact details: 7.5pt regular sans-serif, line-height 1.6. "
            "All text left-aligned."
        ),
        "layout_instruction": (
            "Name starts 8mm from left edge, 8mm from top. "
            "Company name 4mm below the name. "
            "A single hairline horizontal gold rule 0.5pt weight "
            "spans full card width at exactly 50 percent vertical midpoint. "
            "Contact details start 8mm from left, 8mm below the gold rule, "
            "each piece of info on its own line. "
            "Right side of card is intentionally empty whitespace."
        ),
        "style_reference": (
            "Reference: Muji stationery, Apple product cards, "
            "luxury Swiss watchmaker business cards."
        ),
    },
    {
        "name": "Dark Executive",
        "theme": "bold",
        "description": "Matte black with metallic gold foil typography, ultra-premium executive feel",
        "style_instruction": (
            "Ultra-premium luxury executive business card. "
            "Matte black card stock with metallic gold foil typography effect. "
            "Communicates exclusivity, authority, and premium positioning. "
            "Think private banking, top-tier law firm, luxury real estate."
        ),
        "color_instruction": (
            "Card background: deep matte black #0A0A0A. "
            "All text and graphic elements: metallic gold #C9A84C with subtle sheen. "
            "Accent border: ultra-thin gold hairline #B8960C. "
            "No white, no grey, no other colours."
        ),
        "typography_instruction": (
            "Name: large 20pt bold luxury serif similar to Bodoni or Didot, "
            "gold metallic colour, letter-spacing 0.05em. "
            "Company: 9pt uppercase sans-serif, gold, letter-spacing 0.2em, light weight. "
            "Contact: 7pt sans-serif, pale gold #D4AF6A, line-height 1.8."
        ),
        "layout_instruction": (
            "Thin gold rectangular border frame 3mm inset from all card edges, 0.5pt line weight. "
            "Inside the frame: company name uppercase gold small caps top-left 6mm from frame. "
            "Thin horizontal gold rule below company name. "
            "Name in large bold gold serif prominent center-left. "
            "Another thin gold rule below name. "
            "Contact details in small pale gold text bottom-left stacked vertically. "
            "Right third of card intentionally empty with only the gold border frame visible."
        ),
        "style_reference": (
            "Reference: Amex Centurion card, Goldman Sachs executive card, "
            "Rolex boutique business card."
        ),
    },
    {
        "name": "Navy Corporate",
        "theme": "corporate",
        "description": "Deep navy with white text and gold name, professional and authoritative",
        "style_instruction": (
            "Classic authoritative corporate business card in deep navy. "
            "Trustworthy, established, professional. "
            "The card exchanged at board meetings and C-suite introductions. "
            "Think McKinsey, Goldman Sachs, top-tier consulting firms."
        ),
        "color_instruction": (
            "Card background: deep Oxford navy #0D2144. "
            "Name text: warm gold #C9A84C. "
            "Company and contact text: clean white #FFFFFF. "
            "Left accent bar: solid gold #C9A84C."
        ),
        "typography_instruction": (
            "Name: 18pt bold sans-serif similar to Gotham Bold, gold colour. "
            "Company: 9pt medium sans-serif white uppercase letter-spacing 0.12em. "
            "Contact: 7.5pt regular sans-serif white opacity 90 percent line-height 1.7."
        ),
        "layout_instruction": (
            "Solid gold vertical bar full card height 6mm wide flush left edge. "
            "Content area starts 14mm from left edge. "
            "Name top area large bold gold text 9mm from top. "
            "Company directly below name in white uppercase with tracking. "
            "Thin white horizontal rule 1px at card midpoint spanning remaining width. "
            "Contact details below rule in white small text each item on own line "
            "with small gold dot bullet point preceding each line. "
            "Bottom-right corner subtle lighter navy geometric accent shape."
        ),
        "style_reference": (
            "Reference: investment bank business cards, "
            "Fortune 500 executive cards, blue chip corporate identity."
        ),
    },
    {
        "name": "Cream Luxury",
        "theme": "elegant",
        "description": "Warm Italian cream with burgundy serif typography and elegant decorative border",
        "style_instruction": (
            "Old-world European luxury business card. "
            "Warm cream card stock with refined burgundy and charcoal typography. "
            "Elegant, heritage, artisan quality. "
            "Think Italian fashion house, Michelin-starred restaurant, bespoke Savile Row tailor."
        ),
        "color_instruction": (
            "Card background: warm Italian cream #F4EFE4. "
            "Name text: deep charcoal #1A1A1A. "
            "Company text: deep burgundy #6B1E2E. "
            "Contact text: medium warm grey #5C5249. "
            "Decorative border and rules: burgundy #6B1E2E very thin. "
            "Small accent ornament: gold #C9A84C."
        ),
        "typography_instruction": (
            "Name: 19pt bold elegant serif similar to Cormorant Garamond Bold, "
            "charcoal, letter-spacing 0.03em. "
            "Company: 10pt medium serif italic burgundy letter-spacing 0.05em. "
            "Contact: 7pt serif regular warm grey line-height 1.8. "
            "Old-style numerals for phone number."
        ),
        "layout_instruction": (
            "Thin elegant rectangular border: burgundy hairline 0.4pt "
            "4mm inset from all card edges with small ornamental corner flourishes at all 4 corners. "
            "Name centered upper 40 percent of card large and proud. "
            "Company name centered below name in burgundy italic. "
            "Small decorative gold ornament or fleuron centered between name and contact area. "
            "Thin burgundy horizontal rule spanning 60 percent of card width centered. "
            "Contact details centered below rule each on own row small warm grey serif text. "
            "Fully symmetrical centered layout throughout."
        ),
        "style_reference": (
            "Reference: Hermes Paris business cards, Cartier boutique cards, "
            "five-star hotel concierge cards, fine dining restaurant owner cards."
        ),
    },
    {
        "name": "Tech Slate",
        "theme": "tech",
        "description": "Dark slate with electric blue geometric accent stripe, modern tech startup energy",
        "style_instruction": (
            "Modern technology startup business card with dark sophisticated palette. "
            "Clean, precise, forward-looking. Geometric design language, data-driven aesthetic. "
            "Think Stripe, Linear, Vercel, Figma — premium tech product companies. "
            "Dark but not heavy. Technical but not cold."
        ),
        "color_instruction": (
            "Card background: dark blue-slate #1A1F2E. "
            "Name text: pure white #FFFFFF. "
            "Company text: electric blue #4F8EF7. "
            "Contact text: light cool grey #94A3B8. "
            "Left accent stripe: electric blue #4F8EF7. "
            "Subtle background geometric element: white at 6 percent opacity."
        ),
        "typography_instruction": (
            "Name: 17pt bold geometric sans-serif similar to Inter Bold or SF Pro Display Bold, white. "
            "Company: 9pt medium sans-serif electric blue letter-spacing 0.08em. "
            "Contact: 7pt regular sans-serif cool grey #94A3B8 "
            "monospaced feel line-height 1.7."
        ),
        "layout_instruction": (
            "Solid electric blue vertical stripe full card height 5mm wide flush left edge. "
            "Content area starts 14mm from left edge. "
            "Name large bold white text 8mm from top. "
            "Company 5mm below name in electric blue. "
            "Thin 1px horizontal line in electric blue at 45 percent card height "
            "spanning from 14mm to right edge. "
            "Contact details in cool grey below line each item on own line small and precise. "
            "Bottom-right: large subtle geometric circle outline in white at 5 percent opacity "
            "partially cropped by card edge as background decoration."
        ),
        "style_reference": (
            "Reference: Stripe engineering team cards, Linear app team cards, "
            "Y Combinator founder cards, modern SaaS startup identity."
        ),
    },
    {
        "name": "Bold Split",
        "theme": "creative",
        "description": "Confident white and deep coral color-block split, bold modern creative energy",
        "style_instruction": (
            "Bold contemporary color-block business card. "
            "Confident, creative, memorable. "
            "Strong horizontal split between white and a vibrant bold colour. "
            "Think creative agency, brand consultant, design studio principal. "
            "Makes an immediate visual impact when handed over."
        ),
        "color_instruction": (
            "Top half of card: clean white #FFFFFF. "
            "Bottom half of card: deep coral #D95F43. "
            "Name text on white: near-black #1C1C1C. "
            "Company text on white: coral #D95F43. "
            "Contact text on coral: pure white #FFFFFF. "
            "Hard edge between sections no gradient no blur."
        ),
        "typography_instruction": (
            "Name: 20pt bold modern sans-serif similar to Neue Haas Grotesk Bold, "
            "dark on white left-aligned. "
            "Company: 9pt medium sans-serif coral uppercase letter-spacing 0.1em. "
            "Contact: 7.5pt regular sans-serif white on coral line-height 1.6 left-aligned."
        ),
        "layout_instruction": (
            "Exactly 50 percent white top half and 50 percent coral bottom half. "
            "Hard straight horizontal line at exact vertical midpoint no gradient no blur no feathering. "
            "White top section: name starts 10mm from left 9mm from top large bold dark. "
            "Company in coral 5mm below name medium uppercase. "
            "Small thin dark horizontal rule 3mm below company spanning 40 percent from left margin. "
            "Coral bottom section: all contact details in white "
            "starting 10mm from left 10mm from the color split line. "
            "Phone email website address each on own line compact and clean. "
            "Bottom-right of coral section: abstract white geometric quarter circle "
            "at 15 percent opacity as subtle decoration."
        ),
        "style_reference": (
            "Reference: Pentagram design studio cards, Wolff Olins creative director cards, "
            "modern branding agency business cards, award-winning design conference speaker cards."
        ),
    },
]


def _build_prompt(user_info: UserInfo, style: dict) -> str:
    contact_lines = [user_info.phone_number]
    if user_info.email:
        contact_lines.append(user_info.email)
    if user_info.website:
        contact_lines.append(user_info.website)
    contact_lines.append(user_info.address)
    contact_text = "  |  ".join(contact_lines)

    email_rule = f'Email "{user_info.email}" must include the @ symbol and be spelled correctly.' if user_info.email else ""
    website_rule = f'Website "{user_info.website}" must be spelled correctly.' if user_info.website else ""

    return f"""SUBJECT: A single professional business card, flat graphic design only.

COMPOSITION:
- Business card fills the ENTIRE image frame edge to edge, no background visible outside card
- Card proportions: exactly 3.5 inches wide by 2 inches tall, landscape horizontal orientation
- Top-down perfectly flat view, zero rotation, zero perspective, zero tilt, zero angle
- Subtle 2mm rounded corner radius on card corners only

DESIGN STYLE:
{style['style_instruction']}

COLOR PALETTE:
{style['color_instruction']}

TYPOGRAPHY:
{style['typography_instruction']}

LAYOUT STRUCTURE:
{style['layout_instruction']}

TEXT CONTENT — reproduce every character exactly as written, no changes allowed:
- PERSON NAME (largest most prominent text): {user_info.name}
- COMPANY NAME (second in hierarchy): {user_info.company_name}
- PHONE NUMBER: {user_info.phone_number}
{f"- EMAIL ADDRESS: {user_info.email}" if user_info.email else ""}
{f"- WEBSITE: {user_info.website}" if user_info.website else ""}
- ADDRESS: {user_info.address}

TEXT ACCURACY — CRITICAL RULES:
- Spell "{user_info.name}" with exactly these letters in exactly this order
- Spell "{user_info.company_name}" with exactly these letters, correct capitalisation
- Phone "{user_info.phone_number}" must show every digit correctly, no substitutions
- {email_rule}
- {website_rule}
- Address "{user_info.address}" must be spelled correctly
- Do NOT invent taglines, slogans, job titles, or any extra text not listed above
- Do NOT add placeholder text, lorem ipsum, or sample text
- Every word on the card must come from the text content list above

PRINT SPECIFICATIONS:
- 300 DPI print-ready resolution
- Crisp sharp edges on all text and graphic elements
- Flat solid colours suitable for CMYK offset printing
- No anti-aliasing artifacts, no blurry soft edges
- Final result must look like a real professionally printed premium business card

STYLE REFERENCE:
{style['style_reference']}"""


async def _generate_image_with_ideogram(
    client: httpx.AsyncClient,
    prompt: str,
) -> str:
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
    designs = []

    async with httpx.AsyncClient() as client:
        for i, style in enumerate(DESIGN_STYLES[:1]):
            try:
                prompt = _build_prompt(user_info, style)
                print(f"Generating {i+1}/{len(DESIGN_STYLES)}: {style['name']}")

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

                print(f"✓ Design {i+1} done")

            except Exception as e:
                print(f"✗ Design {i+1} failed: {str(e)}")
                continue

    if len(designs) == 0:
        raise ValueError("All Ideogram generations failed. Check API key and quota.")

    print(f"Generated {len(designs)}/{len(DESIGN_STYLES)} designs")
    return designs