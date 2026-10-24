# Quimby Construction — private beta v0.1

Flask prototype with login, customer records, inquiry/job creation, manual scheduling, estimating, inspection checklist, authenticated photo retrieval, and audit log.

## Run locally

1. Install Python 3.11 or 3.12 and create a virtual environment.
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env`; set a strong `SECRET_KEY` and environment variables (use a shell or dotenv runner; Flask does not automatically load `.env` without python-dotenv).
4. `flask --app app init-db`
5. `flask --app app create-admin`
6. `flask --app app run`
7. Visit http://127.0.0.1:5000 and sign in.

## Hosting / staging

Use a **private** GitHub repository. Deploy a separate staging service with `APP_ENV=staging`, a strong `SECRET_KEY`, managed persistent PostgreSQL (`DATABASE_URL`), and a persistent private upload directory (`UPLOAD_FOLDER`). Configure HTTPS, backups and restore tests before real customer data. Set the start command to `gunicorn app:app --bind 0.0.0.0:$PORT`. Run `flask --app app init-db` and `flask --app app create-admin` through a secure service shell after provisioning. Do not use ephemeral disks for uploaded photos. For production, replace `db.create_all` with managed schema migrations.

**Not implemented:** public inquiry form, two-way SMS, Google Calendar, QuickBooks sync, customer portal, payments, production-grade file scanning, password recovery, rate-limited login, account roles, and automated backups. Do not use real customer data or replace Jobber yet. The quote formula and text are placeholders, not verified Quimby prices.

The app is not deployed by this package. Staging and production should use different databases, secrets, and integration credentials.
