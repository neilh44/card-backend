# CardCraft Backend — FastAPI

AI-powered business card generation API. Generates 6 unique designs via OpenAI,
renders print-ready PDFs, and stores orders in Supabase.

---

## Folder Structure

```
cardcraft-backend/
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── config/
│   │   └── settings.py          # Environment config (pydantic-settings)
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response schemas
│   ├── routes/
│   │   ├── design.py            # POST /api/designs/generate
│   │   ├── order.py             # POST /api/orders/  GET /api/orders/{id}
│   │   └── user.py              # POST /api/auth/signup  signin  GET /me
│   └── services/
│       ├── ai_service.py        # OpenAI GPT-4o integration + HTML rendering
│       ├── render_service.py    # WeasyPrint HTML → PDF (3.5 x 2 inch)
│       └── storage_service.py   # Supabase Storage upload + DB writes
├── supabase_schema.sql          # Run once in Supabase SQL Editor
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## API Endpoints

| Method | Endpoint                  | Description                        |
|--------|---------------------------|------------------------------------|
| GET    | /api/health               | Health check                       |
| POST   | /api/designs/generate     | Generate 6 AI card designs         |
| POST   | /api/orders/              | Create order + generate PDF        |
| GET    | /api/orders/{id}          | Fetch order by ID                  |
| POST   | /api/auth/signup          | Register user                      |
| POST   | /api/auth/signin          | Sign in user                       |
| GET    | /api/auth/me              | Get current user (Bearer token)    |
| GET    | /api/docs                 | Swagger UI (interactive docs)      |

---

## Local Development Setup

### 1. Clone and create virtual environment
```bash
git clone https://github.com/yourname/cardcraft-backend
cd cardcraft-backend
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create .env file
```bash
cp .env.example .env
# Open .env and fill in your keys
```

### 4. Set up Supabase
- Go to supabase.com → your project → SQL Editor
- Paste and run the contents of `supabase_schema.sql`
- Go to Storage → confirm `card-pdfs` bucket exists and is public

### 5. Run the server
```bash
uvicorn app.main:app --reload --port 8000
```

### 6. Test the API
Open: http://localhost:8000/api/docs

---

## Environment Variables

| Variable                  | Required | Description                          |
|---------------------------|----------|--------------------------------------|
| OPENAI_API_KEY            | ✅       | OpenAI API key (GPT-4o access)       |
| SUPABASE_URL              | ✅       | Your Supabase project URL            |
| SUPABASE_SERVICE_ROLE_KEY | ✅       | Service role key (bypasses RLS)      |
| SUPABASE_ANON_KEY         | ✅       | Anon key (for auth endpoints)        |
| SUPABASE_STORAGE_BUCKET   | ✅       | Storage bucket name (card-pdfs)      |
| PDF_OUTPUT_DIR            | ✅       | Temp dir for PDFs (/tmp/cardcraft)   |
| ALLOWED_ORIGINS           | ✅       | JSON array of allowed CORS origins   |
| DEBUG                     | ❌       | Set true for dev (default: false)    |

---

## Render Deployment

### Step 1 — Create Web Service on Render
- Go to render.com → New → Web Service
- Connect your GitHub repo

### Step 2 — Configure Build Settings
```
Runtime:        Python 3.11
Build Command:  pip install -r requirements.txt
Start Command:  uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Step 3 — Add Environment Variables
Add all variables from the table above in the Render dashboard
under Environment → Add Environment Variable.

For ALLOWED_ORIGINS use:
```
["https://designspark-cards.onrender.com"]
```

### Step 4 — Deploy
Click Deploy. Once live, test:
```
https://your-backend.onrender.com/api/health
https://your-backend.onrender.com/api/docs
```

---

## WeasyPrint on Render (Important)

WeasyPrint requires system libraries. Add a `render.yaml` or install
via build command if you hit errors:

```bash
# Build Command (with system deps):
apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
  libgdk-pixbuf2.0-0 libcairo2 libffi-dev && pip install -r requirements.txt
```

Or add a `render.yaml` at the root:
```yaml
services:
  - type: web
    name: cardcraft-backend
    runtime: python
    buildCommand: |
      apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 \
        libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libcairo2 libffi-dev
      pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: OPENAI_API_KEY
        sync: false
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_ROLE_KEY
        sync: false
      - key: SUPABASE_ANON_KEY
        sync: false
      - key: SUPABASE_STORAGE_BUCKET
        value: card-pdfs
      - key: PDF_OUTPUT_DIR
        value: /tmp/cardcraft_pdfs
      - key: ALLOWED_ORIGINS
        value: '["https://designspark-cards.onrender.com"]'
```

---

## Request/Response Examples

### POST /api/designs/generate
```json
// Request
{
  "user_info": {
    "name": "Priya Sharma",
    "company_name": "Sharma Consulting",
    "phone_number": "+91 98765 43210",
    "address": "42 MG Road, Bangalore 560001",
    "business_description": "Business strategy consulting for tech startups",
    "email": "priya@sharmaconsulting.in",
    "website": "www.sharmaconsulting.in"
  }
}

// Response
{
  "session_id": "uuid-here",
  "designs": [
    {
      "id": "uuid-here",
      "style": {
        "theme": "minimal",
        "primary_color": "#1a1a2e",
        "secondary_color": "#6c757d",
        "accent_color": "#e8b86d",
        "background_color": "#ffffff",
        "text_color": "#1a1a2e",
        "font_family": "Playfair Display",
        "font_family_url": "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&display=swap",
        "layout": "classic",
        "tagline": "Strategy that scales",
        "design_name": "Ivory Classic",
        "description": "Clean minimal design with a gold accent for a premium consulting feel"
      },
      "html_content": "<!DOCTYPE html>..."
    }
    // ... 5 more designs
  ]
}
```

### POST /api/orders/
```json
// Request
{
  "session_id": "uuid-here",
  "selected_design_id": "uuid-here",
  "design_html": "<!DOCTYPE html>...",
  "user_info": { ...same as above... },
  "user_id": null
}

// Response
{
  "id": "order-uuid",
  "user_id": null,
  "selected_design_id": "design-uuid",
  "pdf_url": "https://your-project.supabase.co/storage/v1/object/public/card-pdfs/orders/order-uuid.pdf",
  "status": "completed",
  "created_at": "2024-01-15T10:30:00Z"
}
```
