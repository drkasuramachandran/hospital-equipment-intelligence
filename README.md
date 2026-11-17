# Hospital Equipment Readiness & Safety Intelligence

Phase 1 MVP starter. React + Vite frontend, FastAPI backend, SQLite for local development, PostgreSQL-ready configuration.

## Features in this starter
- Demo login and role-aware session shell
- Dashboard summary and equipment readiness overview
- Equipment register, add equipment, search/filter
- Breakdown reporting and work-order creation
- Maintenance/calibration task register
- Safety inspection register
- REST API with OpenAPI docs

## Run on Windows
1. Install Python 3.11+ and Node.js 20+.
2. Extract this ZIP.
3. Open a terminal in the extracted folder.
4. Run `start.bat`.
5. Open `http://127.0.0.1:5173`.

The launcher creates a Python virtual environment, installs dependencies, starts FastAPI and Vite, and opens the browser.

Backend API docs: `http://127.0.0.1:8000/docs`

## Demo access
Email: `admin@hospital.local`
Password: `Hospital@123`

This is a development demo account. Change credentials and configure a strong JWT secret before any deployment.

## Database
By default, the backend uses SQLite at `backend/hospital.db`. Set `DATABASE_URL` to a PostgreSQL SQLAlchemy URL for a PostgreSQL deployment, for example:
`postgresql+psycopg://user:password@localhost:5432/hospital_equipment`

## Important deployment note
This MVP is not yet certified for clinical, regulatory, or production use. Before a hospital pilot, add HTTPS, managed secrets, backups, access reviews, audit-log retention, security testing, tenant isolation, and formal validation of workflows. Do not enter patient-identifiable information; the initial product is designed around equipment and maintenance data.
