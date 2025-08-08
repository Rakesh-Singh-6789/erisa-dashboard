## ERISA Assessment

A lightweight web app to analyze insurance claims.

### Tech Stack
- **Backend**: Django 5 (Python)
- **Database**: SQLite
- **Frontend**: HTML/CSS + HTMX + Alpine.js
- **UI**: Minimal, Material-inspired

### Links
- GitHub: [repo](https://github.com/Rakesh-Singh-6789/erisa-dashboard)
- Replit: [live workspace](https://replit.com/join/ogmkyhgfni-feenicks62)


### Quick Start (Local)
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

### Seed data (optional)
```bash
python manage.py load_claims_data --claims-file claim_list_data.csv --details-file claim_detail_data.csv
```

### Replit (one-click)
- Open the Replit project: [Repl here](https://replit.com/join/ogmkyhgfni-feenicks62)
- Click Run. If the environment needs python/pip, Replit will rebuild from `replit.nix`.
- Default run command (configured in Replit): click on run and see the preview.
```bash
python3 -m venv .venv && source .venv/bin/activate && python -m pip install --upgrade pip && pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate && python manage.py runserver 0.0.0.0:8000
```

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

### Known Issues on replit:
- Real time flagging not working on replit because of how replit works, it uses iframes for the preview. Working fine in localhost.
- I can implement additional features if required.