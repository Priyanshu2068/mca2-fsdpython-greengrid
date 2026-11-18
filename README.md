# GreenGrid: Smart Energy Management for Tomorrow's Needs (P02)

**Author:** Priyanshu  
**Project Type:** Individual Academic Project (90 Hours)  
**Repository:** [https://github.com/Priyanshu2068/mca2-fsdpython-greengrid.git](https://github.com/Priyanshu2068/mca2-fsdpython-greengrid.git)

---

## 1. Project Overview
GreenGrid is a web-based Energy Management Information System (EMIS) tailored for Indian commercial facilities. It collects 15-minute sub-metered energy readings (grid, diesel generators, solar PV, water, gas; categorised by HVAC, lighting, IT, and auxiliary pump loads) and converts high-frequency operational telemetry into actionable analytics, benchmarks, billing audit reconciliation, automated anomaly alerts, and rule-based energy conservation measures (ECMs) with rupee (₹) savings.

Meter hardware is out of scope. Data arrives via a high-throughput idempotent ingestion API supported by synthetic seed fixtures, an automated environmental simulator driven by NASA POWER hourly solar irradiance and temperature data, CSV batch uploads, and manual entry forms.

---

## 2. Technical Stack
- **Language & Runtime:** Python 3.11+
- **Backend Framework:** Django 4.2 LTS & Django REST Framework (DRF)
- **Database Engine:** PostgreSQL 16 using `psycopg 3`
- **Query & Storage Optimisation:** `ON CONFLICT` upserts, `date_trunc` aggregate rollups, BRIN indices on reading timestamps
- **API Documentation & Filtering:** `drf-spectacular` (OpenAPI 3.0 / Swagger UI at `/api/docs/`), `django-filter`
- **Authentication & Security:** Django built-in Session Authentication with strict CSRF protection (no JWT) and SHA-256 hashed device API keys (`X-API-Key`)
- **Background Orchestration:** Re-runnable Django management commands (modular, cron-friendly, no Celery/Redis dependencies)
- **Testing & Quality Assurance:** `pytest` and `pytest-django` with isolated database fixtures
- **Environment Management:** `django-environ` reading local `.env` files

---

## 3. Project Review & Evaluation Directory

This section provides direct navigation to project milestones, design artifacts, and architectural documentation for academic evaluation.

### Release Tags & Milestones
| Milestone Tag | Phase Scope | Focus Areas | Status |
| :--- | :--- | :--- | :--- |
| **`v0.1.0`** | Phase 0 | Architecture, Workflows, ERD, SQL DDL, API Spec, User Stories | Complete |
| **`v0.2.0`** | Phase 1 | Foundation, Ingestion API, Simulator, Rollups, Anomalies | Upcoming |
| **`v0.3.0`** | Phase 2 | Analytics Dashboard APIs, Utility Billing Reconciliation, Benchmarks | Upcoming |
| **`v1.0.0`** | Phase 3 | Recommendation Engine (ECMs), Renewables & Grid, Final Release | Upcoming |

### Design Documentation Index
All foundational engineering documents reside in the `docs/` and `database/` directories:

| Document | File Path | Description |
| :--- | :--- | :--- |
| **Operational Workflows** | [`docs/workflow.md`](docs/workflow.md) | Mermaid flowcharts for end-to-end ingestion, 15-minute reading validation, and role-based workflows |
| **System Architecture** | [`docs/architecture.md`](docs/architecture.md) | Component architecture, modular monolith app structure, layer conventions, authentication flows, and ADRs |
| **Entity-Relationship Model** | [`docs/er-diagram.md`](docs/er-diagram.md) | Complete Mermaid ER diagram illustrating relational structures, constraints, and cardinalities |
| **Relational Database DDL** | [`database/schema.sql`](database/schema.sql) | Production PostgreSQL 16 schema with table definitions, constraints, foreign keys, and BRIN indexes |
| **Seed Data Fixtures** | [`database/seed_data.sql`](database/seed_data.sql) | Comprehensive Indian commercial facility dataset (2024–2026) with master records, readings, and edge cases |
| **REST API Specification** | [`docs/api-spec.md`](docs/api-spec.md) | Comprehensive endpoint catalog covering all 8 modules, payload schemas, and response formats |
| **Agile Backlog & Stories** | [`docs/user-stories.md`](docs/user-stories.md) | Granular user stories (P02-US01 to P02-US23) with acceptance criteria, priority, and 90-hour work allocation |

---

## 4. Local Installation & Setup Guide

### Prerequisites
- Python 3.11 or higher
- PostgreSQL 16
- Git

### Setup Steps
1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Priyanshu2068/mca2-fsdpython-greengrid.git
   cd mca2-fsdpython-greengrid
   ```

2. **Set Up Python Virtual Environment:**
   ```bash
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   # Modify .env with your local PostgreSQL credentials
   ```

5. **Initialize Database & Run Migrations:**
   ```bash
   cd backend
   python manage.py migrate
   ```

6. **Seed Initial Master and Telemetry Data:**
   ```bash
   psql -U greengrid_user -d greengrid_db -f ../database/seed_data.sql
   ```

7. **Run the Development Server:**
   ```bash
   python manage.py runserver
   ```
   Access the interactive Swagger UI documentation at: `http://127.0.0.1:8000/api/docs/`

8. **Execute Test Suite:**
   ```bash
   pytest
   ```
