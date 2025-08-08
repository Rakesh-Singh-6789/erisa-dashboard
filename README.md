## ERISA Assessment

A lightweight web app to analyze insurance claims.

### Tech Stack
- **Backend**: Django 5 (Python)
- **Database**: SQLite
- **Frontend**: HTML/CSS + HTMX + Alpine.js
- **UI**: Minimal, Material-inspired

### Quick Start
1) Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```
2) Install dependencies
```bash
pip install -r requirements.txt
```
3) Apply migrations
```bash
python manage.py migrate
```
4) Run the app
```bash
python manage.py runserver 8000
```
Open `http://localhost:8000`.

### Optional: Load Sample Data
```bash
python manage.py load_claims_data --claims-file claim_list_data.csv --details-file claim_detail_data.csv
```

### Main URLs
- `/` Claims list (search, filter, pagination)
- `/dashboard/` Analytics (totals, flagged, avg underpayment)
- `/upload/` CSV append/overwrite
- `/login/`, `/logout/` Authentication

### Project Structure (brief)
```
erisa-loan-dashboard/
├─ apps/
│  └─ claims/
├─ config/            # settings.py, urls.py, asgi.py, wsgi.py
├─ templates/         # base and app templates
├─ static/            # css, js
├─ manage.py
└─ requirements.txt
```

### Notes
- Single settings file at `config/settings.py`.
- No Docker, no multi-env setup; intended for simple team testing.
- SQLite database file (`claims_db.sqlite3`) is created on first run and is git-ignored.