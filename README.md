# Quimby Construction — private beta

An authenticated Flask operations workspace for customers, inquiries/jobs, scheduling, estimates, inspection checklists, photos, audit history, and professional job reports.

## Current state

The job-report workflow supports:

- customer/job metadata, report date, services performed, findings, and recommendations;
- reusable editable templates with one optional default;
- selection and captioning of photos that belong to the report's job;
- draft preview, finalization/locking, and reopening;
- branded browser printing and downloadable PDF generation;
- a safe email-delivery preview and delivery history that **does not send email**;
- audit entries for report and template changes.

Estimate values remain entirely user-entered. The application does not infer or invent Quimby pricing.

## Run locally

1. Install Python 3.11 or 3.12 and create a virtual environment.
2. Run `pip install -r requirements.txt`.
3. Set a strong `SECRET_KEY` and any environment variables in your shell. Flask does not load a `.env` file unless a dotenv runner is installed.
4. Run `flask --app app db upgrade`.
5. Run `flask --app app seed-report-templates` if you want the starter report template.
6. Run `flask --app app create-admin`.
7. Run `flask --app app run` and visit `http://127.0.0.1:5000`.

Run the automated suite with `python -m pytest -q`.

## Existing hosted database migration

The hosted application predates Alembic migrations. Do not run the baseline migration directly against its populated database because the six original tables already exist.

After taking and verifying a database backup, an operator should:

1. confirm the database contains the original `user`, `customer`, `job`, `estimate`, `photo`, and `audit` tables and does not contain any report tables;
2. run `flask --app app db stamp 0001_existing_schema` once;
3. run `flask --app app db upgrade` to add only the report tables;
4. run `flask --app app seed-report-templates` if desired;
5. verify report creation, PDF download, and rollback/restore procedures on staging before production.

Fresh databases should only run `flask --app app db upgrade`. Do not mix `init-db` with migrations. No hosted environment or production configuration was changed by this branch.

## Hosting and security boundaries

Use separate staging and production databases, secrets, and integration credentials. Hosted environments require persistent PostgreSQL, HTTPS, backup/restore testing, and persistent private object/file storage. The current local upload directory is ephemeral on a default Render filesystem and is not safe as the only copy of job photographs.

Before real customer use, address these known risks:

- migrate photos to durable private storage with authorization, malware scanning, retention, and backups;
- add login rate limiting, password recovery, account roles, session revocation, and security-event monitoring;
- remove `BOOTSTRAP_ADMIN_*` environment variables immediately after the first account is created;
- establish tested database backups, restore drills, data retention, and an incident-response process;
- add a real transactional email provider only after explicit approval, with delivery failures and consent handled safely.

Not implemented: public inquiry form, two-way SMS, Google Calendar, QuickBooks sync, customer portal, payments, invoices, or real email delivery. Use synthetic records during evaluation and do not replace Jobber yet.
