# FitPulse — Multi-Tenant Fitness Coaching SaaS Platform

FitPulse is an all-in-one multi-tenant Software-as-a-Service (SaaS) platform built for independent fitness coaches, personal trainers, and nutritionists. Each coach is provided with an isolated, secure workspace to manage clients, customized meal plans, structured workout regimes, body measurement logs, and consent-verified client transformations.

The platform owner (Super Admin) monetizes the software through recurring coach subscriptions, while coaches manage their own paying clients independently.

---

## Phase 1: Foundation & Architecture

In accordance with the project roadmap, **Phase 1** establishes the foundation:
- Application structure and environment configuration
- Flask application factory with blueprint architecture
- Base Jinja2 layout and responsive CSS design system
- Strict Top Bar Contract and Zero-Pill typography
- High-impact fitness visual assets with accessibility fallbacks
- Interactive instant demo for the Free Food Alternatives tool
- Git version control configuration and Render deployment files

---

## 1. Directory Structure

```text
fitpulse/
├── app.py                      # Flask Application Factory & Entry Point
├── config.py                   # Multi-environment configuration (Dev/Test/Prod)
├── requirements.txt            # Python dependencies (Flask, SQLAlchemy, etc.)
├── Procfile                    # Render/Heroku production process configuration
├── .env.example                # Template of environment variables & secrets
├── .gitignore                  # Git ignore rules for virtualenvs, keys & SQLite
├── README.md                   # Complete architectural guide & setup manual
│
├── models/                     # Database Models (Phase 2 readiness)
│   └── __init__.py             # SQLAlchemy & Flask-Migrate instance init
│
├── routes/                     # Blueprint Route Controllers
│   ├── __init__.py             # Route package exports
│   └── public.py               # Public pages, health check & meta endpoints
│
├── services/                   # Business Logic & Validation
│   └── __init__.py             # Services package definition
│
├── templates/                  # Jinja2 HTML Templates
│   ├── base.html               # Master layout (3-zone nav, footer, mobile bar)
│   ├── public/
│   │   └── index.html          # Phase 1 Responsive SaaS Landing Page
│   └── errors/
│       ├── 400.html            # Bad Request error view
│       ├── 403.html            # Tenant Violation / Access Prohibited view
│       ├── 404.html            # Resource Not Found view
│       └── 500.html            # Internal Server Error view (No stack traces)
│
├── static/                     # Static Web Assets
│   ├── css/
│   │   └── styles.css          # Fitness-Tech Design System & CSS Variables
│   ├── js/
│   │   └── main.js             # Mobile nav drawer & Interactive Demo logic
│   ├── images/
│   │   ├── hero.jpg            # Hero section athletic coaching visual
│   │   ├── showcase.jpg        # Client transformation showcase visual
│   │   └── nutrition.jpg       # Balanced meal prep & nutrition visual
│   └── uploads/                # Directory for tenant files (Ignored in Git)
│       └── .gitkeep
```

---

## 2. Local Environment Setup

### Prerequisites
- Python 3.10 or higher
- Git

### Step 1: Clone or Enter the Repository
```bash
cd fitpulse
```

### Step 2: Create a Python Virtual Environment
On macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows (Command Prompt):
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy the template `.env.example` into a local `.env`:
```bash
cp .env.example .env
```
Ensure `FLASK_ENV=development` and configure a development `SECRET_KEY`.

---

## 3. Running the Application Locally

### Using Flask Development Server
```bash
python app.py
```
Or via the Flask CLI:
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
```
Open your browser and navigate to: `http://localhost:5000`

### Testing Production Server Locally (Gunicorn)
On Unix/Linux:
```bash
gunicorn app:app --workers 2 --bind 0.0.0.0:5000
```

---

## 4. Git & GitHub Repository Setup

To push this codebase to a fresh GitHub repository:

```bash
# 1. Initialize git
git init

# 2. Stage all Phase 1 files
git add .

# 3. Create the initial commit
git commit -m "feat(phase-1): initial foundation, landing page, and design system"

# 4. Set main branch
git branch -M main

# 5. Link your remote GitHub repository
git remote add origin https://github.com/YOUR_USERNAME/fitpulse-saas.git

# 6. Push to GitHub
git push -u origin main
```

---

## 5. Render & PostgreSQL Cloud Deployment Guide

When deploying to **Render**:

1. **Connect GitHub Repo**: Link your GitHub repository in the Render dashboard.
2. **Create Managed PostgreSQL**:
   - Create a PostgreSQL database instance on Render.
   - Copy the **Internal Database URL**.
3. **Create Web Service**:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --workers 4 --threads 2 --bind 0.0.0.0:$PORT`
4. **Configure Environment Variables in Render**:
   - `FLASK_ENV` = `production`
   - `DATABASE_URL` = Paste your Render PostgreSQL connection string
   - `SECRET_KEY` = Generate a 64-character random hex string (`python -c "import secrets; print(secrets.token_hex(32))"`)
   - `PORT` = `10000` (Render defaults)

`config.py` automatically detects Render's `postgres://` URLs and standardizes them for SQLAlchemy 2.0 (`postgresql://`).

---

## 6. Explanation of Key Phase 1 Files

| File | Purpose & Architecture |
|---|---|
| `app.py` | **Application Factory**: Configures Flask, hooks security headers (`X-Frame-Options`, `nosniff`), registers blueprints, and registers clean HTTP 400, 403, 404, 500 error handlers that prevent stack traces in production. |
| `config.py` | **Configuration Classes**: Manages `DevelopmentConfig` (SQLite default), `ProductionConfig` (PostgreSQL and SSL cookies), and `TestingConfig` (in-memory SQLite). |
| `requirements.txt` | **Pinned Dependencies**: Includes Flask 3, SQLAlchemy 2, Flask-Migrate, psycopg2-binary, python-dotenv, gunicorn, plus scikit-learn/pandas prepared for Phase 10. |
| `.env.example` | **Security Blueprint**: Provides sample configuration without exposing production secrets. |
| `.gitignore` | **Exclusion Rules**: Prevents tracking of virtual environments, cache files, `.sqlite` databases, user uploads, and secrets. |
| `Procfile` | **Cloud Process Specification**: Defines the Gunicorn WSGI startup command for Render web service instances. |
| `models/__init__.py` | **Database Extensibility**: Initializes SQLAlchemy `db` and Flask-Migrate `migrate` ready for multi-tenant entity mapping in Phase 2. |
| `routes/public.py` | **Public Blueprint**: Serves the homepage, service `/health` probe, and metadata endpoints. |
| `templates/base.html` | **Jinja2 Master Layout**: Implements the strict 3-zone Top Bar Contract, typography hierarchy, footer, and touch-friendly mobile bottom bar. |
| `templates/public/index.html` | **Phase 1 SaaS Homepage**: Renders the Hero, Platform Capabilities Bento Grid, 100% Free Tools Showcase with interactive live demo, transformations, and coach directory (clearly labeled DEMO DATA). |
| `static/css/styles.css` | **Design System**: Contains fitness-tech CSS variables (`--primary`, `--secondary`, `--background`, `--surface-card`), responsive layout rules, and zero-pill typography. |
| `static/js/main.js` | **Frontend Interactivity**: Drives responsive mobile menu drawer and live client-side food craving swap demo. |
| `templates/errors/*.html` | **Safe Error Pages**: Professional error UI preventing stack trace disclosure for 400, 403, 404, and 500 errors. |

---

## Next Step: Phase 2 — Database Models & Multi-Tenant Schema

Once you review and approve Phase 1, we will proceed to **Phase 2**, where we will define the complete SQLAlchemy relational schema:
- `users` (multi-role: admin, coach, client)
- `coaches` (business profile, specializations, experience, isolation key)
- `clients` (coach foreign key, baseline metrics)
- `subscription_plans` and `subscriptions`
- `diet_plans` and `diet_items`
- `workout_plans` and `workout_exercises`
- `progress` and `measurements`
- `transformations` and `transformation_consents`
- `support_tickets`, `audit_logs`, and database migrations
