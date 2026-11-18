# GreenGrid Agile User Stories & Work Breakdown Structure

**Project:** GreenGrid: Smart Energy Management for Tomorrow's Needs (P02)  
**Total Allocation:** 90 Hours (Individual Academic Project)  
**Phases Breakdown:**
- **Phase 0:** Workflow & Architecture Design (6 Hours) — Completed (`v0.1.0`)
- **Phase 1:** Backend Foundation & Ingestion (28 Hours) — Target `v0.2.0`
- **Phase 2:** Insight Modules & Billing (28 Hours) — Target `v0.3.0`
- **Phase 3:** Intelligence, Renewables & Release (28 Hours) — Target `v1.0.0`

---

## Summary Matrix

| Story ID | Module | Title | Phase | Est. Hours | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **P02-US01** | `core` | Django Project Foundation, Error Handler & Health Check | Phase 1 | 2.5 h | High |
| **P02-US02** | `accounts` | Custom User Model, Session Auth & CSRF Lifecycle | Phase 1 | 3.0 h | High |
| **P02-US03** | `accounts` | Admin User Management & Audit Logging | Phase 1 | 2.0 h | Medium |
| **P02-US04** | `facilities` | Facility & Building Hierarchy Management | Phase 1 | 2.5 h | High |
| **P02-US05** | `facilities` | Meter Inventory & Hashed DataSource API Keys | Phase 1 | 2.5 h | High |
| **P02-US06** | `ingestion` | High-Throughput Bulk 15-Minute Readings API | Phase 1 | 3.5 h | Critical |
| **P02-US07** | `ingestion` | Batch CSV Upload Pipeline & Error Reporting | Phase 1 | 2.5 h | Medium |
| **P02-US08** | `simulator` | Environmental Simulator via NASA POWER Replay | Phase 1 | 2.5 h | Medium |
| **P02-US09** | `analytics` | Incremental 48-Hour Hourly Rollup Management Command | Phase 1 | 2.5 h | High |
| **P02-US10** | `analytics` | Daily Energy Rollup & Peak Demand Pipeline | Phase 1 | 2.0 h | High |
| **P02-US11** | `analytics` | Rule-based Anomaly Detection & AnomalyAlerts | Phase 1 | 2.5 h | Critical |
| **P02-US12** | `dashboard` | Executive KPI Summary API (<1s Response) | Phase 2 | 4.0 h | High |
| **P02-US13** | `dashboard` | 24-Hour & 30-Day Trends with Load Breakdown | Phase 2 | 4.5 h | High |
| **P02-US14** | `billing` | Utility Provider & Indian Tariff Slabs Management | Phase 2 | 4.0 h | Medium |
| **P02-US15** | `billing` | Utility Bill Tracking & Effective Cost Per kWh | Phase 2 | 4.5 h | High |
| **P02-US16** | `billing` | Metered vs. Billed Variance Reconciliation Engine | Phase 2 | 5.5 h | Critical |
| **P02-US17** | `benchmarking` | Facility EUI ($\text{kWh/m}^2/\text{yr}$) & Star Ratings | Phase 2 | 5.5 h | High |
| **P02-US18** | `recommendations` | Deterministic Energy Conservation Measures (ECMs) | Phase 3 | 5.5 h | Critical |
| **P02-US19** | `recommendations` | ECM Lifecycle (Accept/Dismiss) & Savings Tracking | Phase 3 | 4.5 h | High |
| **P02-US20** | `renewables` | Solar PV Asset Monitoring & Generation Tracking | Phase 3 | 4.5 h | High |
| **P02-US21** | `renewables` | Solar Self-Consumption & Grid Outage Management | Phase 3 | 4.5 h | High |
| **P02-US22** | `renewables` | Source-specific Carbon Emissions Accounting | Phase 3 | 4.5 h | High |
| **P02-US23** | `release` | End-to-End System Verification, OpenAPI & Release | Phase 3 | 4.5 h | Critical |
| **Total** | | **Comprehensive 23 Stories across 3 Delivery Phases** | | **84.0 h + 6 h P0 = 90 h** | |

---

## Detailed User Stories Specification

### Phase 1: Backend Foundation & Ingestion (28 Hours)

#### P02-US01: Django Project Foundation, Error Handler & Health Check
- **App:** `core` | **Phase:** Phase 1 | **Estimate:** 2.5 Hours | **Role:** System Architect
- **Goal:** As a system integrator, I want a robust Django 4.2 project scaffold with PostgreSQL 16 connectivity, OpenAPI documentation, and a unified error handler envelope.
- **Acceptance Criteria:**
  1. Django settings load environment configuration using `django-environ` from `.env`.
  2. `GET /api/v1/health/` returns `{"status": "healthy", "database": "connected", "time": "..."}` with HTTP 200.
  3. Interactive Swagger UI is live and accessible at `/api/docs/` powered by `drf-spectacular`.
  4. All uncaught exceptions and DRF validation errors return the standardized error envelope: `{"error": {"status": int, "code": str, "message": str, "details": dict}}`.
  5. Pytest suite tests the health endpoint and error handling.

#### P02-US02: Custom User Model, Session Auth & CSRF Lifecycle
- **App:** `accounts` | **Phase:** Phase 1 | **Estimate:** 3.0 Hours | **Role:** Web User (Customer / Field Engineer / Admin)
- **Goal:** As a web user, I want to authenticate securely using my email and password via session cookies and CSRF protection (without JWTs).
- **Acceptance Criteria:**
  1. Custom `CustomUser` model inherits from `AbstractBaseUser` with email as unique username identifier.
  2. Roles enum contains `'admin'`, `'customer'`, `'field_engineer'`.
  3. `GET /api/v1/accounts/csrf/` sets the `csrftoken` cookie.
  4. `POST /api/v1/accounts/login/` validates credentials, sets `sessionid` cookie, and returns user details and role.
  5. `POST /api/v1/accounts/logout/` invalidates session and clears cookies.
  6. `GET /api/v1/accounts/me/` returns current authenticated profile and assigned facility IDs.
  7. Automated tests verify login success, wrong password rejection, and CSRF token enforcement.

#### P02-US03: Admin User Management & Audit Logging
- **App:** `accounts` | **Phase:** Phase 1 | **Estimate:** 2.0 Hours | **Role:** Administrator
- **Goal:** As an admin, I want to create user accounts, assign roles, and inspect security audit logs.
- **Acceptance Criteria:**
  1. `GET /api/v1/accounts/users/` allows only `admin` users to list users with filtering by role.
  2. `POST /api/v1/accounts/users/` allows `admin` to create customer or field engineer users.
  3. Non-admin users attempting access receive HTTP 403.
  4. Security actions (logins, user creations, key rotations) produce an entry in `accounts_auditlog`.
  5. `GET /api/v1/accounts/audit-logs/` returns paginated audit records for admin review.

#### P02-US04: Facility & Building Hierarchy Management
- **App:** `facilities` | **Phase:** Phase 1 | **Estimate:** 2.5 Hours | **Role:** Administrator & Customer
- **Goal:** As a facility manager, I want to organize facilities and buildings with gross floor areas and sanctioned demand limits.
- **Acceptance Criteria:**
  1. `Facility` model stores Indian commercial metadata (facility_type, GFA in sqm, sanctioned kVA, city, state, pin code).
  2. `Building` model links to facility with floor area and total floors.
  3. `facilities_userfacilityassignment` maps customers and field engineers to specific facilities.
  4. Facility scoping rule: Customers only see their organization's facilities; engineers only see assigned facilities; out-of-scope facility access returns HTTP 404.
  5. CRUD endpoints available under `/api/v1/facilities/`.

#### P02-US05: Meter Inventory & Hashed DataSource API Keys
- **App:** `facilities` | **Phase:** Phase 1 | **Estimate:** 2.5 Hours | **Role:** Field Engineer & IoT Gateway
- **Goal:** As a field engineer, I want to register sub-meters (categorized by load: HVAC, lighting, IT, pumps; and source: grid, DG, solar) and provision hashed API keys for edge devices.
- **Acceptance Criteria:**
  1. `Meter` model enforces unique `meter_identifier`, `energy_source`, and `load_category` choices.
  2. `DataSource` model stores SHA-256 hashed API key (`key_hash`) and plain prefix (`key_prefix`).
  3. API key generation endpoint `POST /api/v1/facilities/{id}/datasources/` returns unhashed secret once (`gg_live_...`).
  4. `POST /api/v1/facilities/datasources/{id}/rotate-key/` replaces hash and invalidates old credentials.
  5. Device requests with `X-API-Key` authenticate via SHA-256 lookup in `DataSource`.

#### P02-US06: High-Throughput Bulk 15-Minute Readings API
- **App:** `ingestion` | **Phase:** Phase 1 | **Estimate:** 3.5 Hours | **Role:** IoT Gateway / Ingestion Script
- **Goal:** As an edge data logger, I want to post batches of up to 5000 15-minute readings idempotently via HTTP header `X-API-Key`.
- **Acceptance Criteria:**
  1. Endpoint `POST /api/v1/ingestion/readings/bulk/` accepts array of readings.
  2. Enforces maximum batch limit $\le 5000$; rejects oversize batches with HTTP 400.
  3. Validates energy constraint: `energy_kwh >= 0`, `power_factor BETWEEN 0.0 AND 1.0`, `voltage_v >= 0`.
  4. Idempotency: `UNIQUE(meter_id, timestamp)` constraint in DB combined with `ON CONFLICT DO NOTHING`.
  5. Duplicate readings within or across batches are silently ignored without raising errors.
  6. Returns response payload detailing `total_received`, `accepted`, `duplicates_ignored`, and `rejected`.
  7. Rejection details isolate malformed items without aborting valid readings.
  8. Automated tests verify idempotency, batch limit rejection, and validation edge cases.

#### P02-US07: Batch CSV Upload Pipeline & Error Reporting
- **App:** `ingestion` | **Phase:** Phase 1 | **Estimate:** 2.5 Hours | **Role:** Field Engineer
- **Goal:** As a field engineer, I want to upload historical or offline CSV reading files and receive a detailed status report.
- **Acceptance Criteria:**
  1. `POST /api/v1/ingestion/readings/upload-csv/` accepts `multipart/form-data` with CSV file.
  2. Validates CSV header format: `meter_identifier,timestamp,energy_kwh,active_power_kw,power_factor,voltage_v`.
  3. Parses rows in chunks using `ingestion.services.bulk_insert_readings`.
  4. Records an `ingestion_batchlog` entry with source type `csv_upload` and execution duration.
  5. Returns comprehensive upload summary with row-level error reasons for invalid lines.

#### P02-US08: Environmental Simulator via NASA POWER Replay
- **App:** `simulator` | **Phase:** Phase 1 | **Estimate:** 2.5 Hours | **Role:** System Demonstrator
- **Goal:** As a system evaluator, I want a simulator script driven by NASA POWER hourly solar irradiance and temperature to generate realistic 15-minute loads for commercial facilities.
- **Acceptance Criteria:**
  1. Management command `python manage.py run_simulator --facility-id=1 --days=30` fetches NASA POWER hourly data (or uses cached fallback).
  2. Generates 15-minute interpolated load profiles for HVAC (temperature correlated), Solar PV (irradiance correlated), Lighting, and IT.
  3. Posts generated readings into the ingestion bulk API endpoint via HTTP with `X-API-Key`.
  4. Supports offline replay mode without requiring live external internet connectivity.

#### P02-US09: Incremental 48-Hour Hourly Rollup Management Command
- **App:** `analytics` | **Phase:** Phase 1 | **Estimate:** 2.5 Hours | **Role:** Background Task
- **Goal:** As the analytics pipeline, I want an incremental hourly rollup command that recomputes the last 48 hours to absorb delayed readings cleanly.
- **Acceptance Criteria:**
  1. Management command `rollup_hourly` groups raw readings into 1-hour buckets via `date_trunc('hour', timestamp)`.
  2. Computes `total_energy_kwh` ($\sum$), `peak_demand_kw` ($\max$), `min_demand_kw` ($\min$), and `avg_power_factor`.
  3. Recomputes rolling 48-hour window and upserts into `analytics_hourlyrollup` via `ON CONFLICT (meter_id, bucket_start) DO UPDATE`.
  4. Command execution is idempotent and re-runnable without duplicate rows.
  5. Automated test verifies rollup accuracy against raw 15-minute readings.

#### P02-US10: Daily Energy Rollup & Peak Demand Pipeline
- **App:** `analytics` | **Phase:** Phase 1 | **Estimate:** 2.0 Hours | **Role:** Background Task
- **Goal:** As the analytics pipeline, I want a daily rollup command that compiles hourly aggregates into daily consumption, peak demand timestamp, and peak/off-peak breakdown.
- **Acceptance Criteria:**
  1. Management command `rollup_daily` aggregates hourly rollups per meter into `analytics_dailyrollup`.
  2. Segregates off-peak energy (22:00 - 06:00) and peak energy (18:00 - 22:00) according to Indian DISCOM standard windows.
  3. Stores daily maximum peak demand (kW) and exact peak timestamp.
  4. Upserts on `(meter_id, rollup_date)`.
  5. Automated tests verify daily calculations.

#### P02-US11: Rule-based Anomaly Detection & AnomalyAlerts
- **App:** `analytics` | **Phase:** Phase 1 | **Estimate:** 2.5 Hours | **Role:** Energy Analyst
- **Goal:** As an energy analyst, I want automated detection of energy spikes (>1.3× 4-week hour-of-week median), low power factor (<0.9), DG running with active grid, and silent meters (>2h).
- **Acceptance Criteria:**
  1. Management command `detect_anomalies` executes 4 distinct detection rules:
     - Rule A: Consumption spike (> 1.3× median of same hour-of-week over past 4 weeks and > min kWh threshold).
     - Rule B: Power factor below 0.900 threshold.
     - Rule C: DG running (`active_power_kw > 0`) while primary grid incomer voltage is nominal ($\ge 400\text{V}$).
     - Rule D: Meter silent with no readings received for $> 120$ minutes.
  2. Generates `analytics_anomalyalert` with severity, human-readable reason, observed vs baseline values, and deviation factor.
  3. Prevents duplicate open alerts for the same meter and condition.
  4. `GET /api/v1/analytics/alerts/` and `PATCH /api/v1/analytics/alerts/{id}/` allow acknowledging and resolving alerts.
  5. Tests cover each anomaly condition with edge case fixtures.

---

### Phase 2: Insight Modules & Billing (28 Hours)

#### P02-US12: Executive KPI Summary API (<1s Response)
- **App:** `dashboard` | **Phase:** Phase 2 | **Estimate:** 4.0 Hours | **Role:** Customer / Facility Executive
- **Goal:** As a facility executive, I want an executive summary dashboard showing today's energy, yesterday's comparison, MTD consumption, and peak demand in under 1 second.
- **Acceptance Criteria:**
  1. `GET /api/v1/dashboard/summary/?facility_id=1` queries exclusively from `analytics_hourlyrollup` and `analytics_dailyrollup` (zero raw reading scans).
  2. Returns today's cumulative kWh, yesterday same time kWh, percentage variance, MTD kWh, current peak demand kW, and sanctioned demand utilization %.
  3. Response time benchmarked strictly $< 1.0$ second.
  4. Scoped to authorized facilities only; unassigned facility returns HTTP 404.

#### P02-US13: 24-Hour & 30-Day Trends with Load Breakdown
- **App:** `dashboard` | **Phase:** Phase 2 | **Estimate:** 4.5 Hours | **Role:** Energy Manager
- **Goal:** As an energy manager, I want 24-hour hourly trend profiles, 30-day daily trends, energy source mix, and sub-metered load breakdown (HVAC, lighting, IT, pumps).
- **Acceptance Criteria:**
  1. `GET /api/v1/dashboard/trends/?facility_id=1&range=24h` returns 24 hourly data points.
  2. `GET /api/v1/dashboard/energy-mix/?facility_id=1` returns percentage and kWh breakdown by source (Grid, DG, Solar).
  3. `GET /api/v1/dashboard/load-breakdown/?facility_id=1` aggregates sub-meters by `load_category` (`hvac`, `lighting`, `it_infrastructure`, `auxiliary_pumps`).
  4. Response formats structured cleanly for frontend charting libraries (Chart.js / Recharts).

#### P02-US14: Utility Provider & Indian Tariff Slabs Management
- **App:** `billing` | **Phase:** Phase 2 | **Estimate:** 4.0 Hours | **Role:** Administrator
- **Goal:** As an administrator, I want to manage Indian DISCOM utility providers and commercial HT tariff structures.
- **Acceptance Criteria:**
  1. `billing_utilityprovider` manages state DISCOMs (BESCOM, MSEDCL, DHBVN, TANGEDCO, TSSPDCL).
  2. `billing_tariffstructure` models base energy rates (₹/kWh), peak-hour surcharge rates, off-peak discount rates, demand charges (₹/kVA), and PF penalty rates.
  3. CRUD endpoints under `/api/v1/billing/tariffs/` with role checks (`admin` write, `customer` read).

#### P02-US15: Utility Bill Tracking & Effective Cost Per kWh
- **App:** `billing` | **Phase:** Phase 2 | **Estimate:** 4.5 Hours | **Role:** Facility Accountant
- **Goal:** As an accountant, I want to record monthly utility bills, track payment status, and automatically calculate effective blended cost per kWh.
- **Acceptance Criteria:**
  1. `billing_utilitybill` stores billed kWh, billed maximum demand kVA, and total invoice amount in ₹.
  2. Auto-computes `effective_cost_per_kwh_inr = billed_amount_inr / billed_kwh`.
  3. Validates billing cycle date ranges (`billing_cycle_end >= billing_cycle_start`).
  4. Endpoints `GET` and `POST` at `/api/v1/billing/bills/` with filtering by facility and fiscal year.

#### P02-US16: Metered vs. Billed Variance Reconciliation Engine
- **App:** `billing` | **Phase:** Phase 2 | **Estimate:** 5.5 Hours | **Role:** Energy Auditor
- **Goal:** As an energy auditor, I want an automated reconciliation engine that compares utility billed kWh against internal check meter aggregates and flags financial variances.
- **Acceptance Criteria:**
  1. Reconciliation service sums `analytics_dailyrollup` total kWh for the main incomer meter across the exact billing cycle dates.
  2. Computes `discrepancy_kwh = billed_kwh - metered_kwh`.
  3. Computes `discrepancy_percentage = (discrepancy_kwh / billed_kwh) * 100`.
  4. Computes `variance_cost_inr = discrepancy_kwh * effective_cost_per_kwh`.
  5. Assigns status:
     - `verified_within_tolerance` if $|\text{discrepancy \%}| \le 1.0\%$
     - `variance_minor` if $1.0\% < |\text{discrepancy \%}| \le 2.5\%$
     - `variance_action_required` if $|\text{discrepancy \%}| > 2.5\%$
  6. Endpoint `GET /api/v1/billing/reconciliations/` returns comprehensive audit reports.

#### P02-US17: Facility EUI ($\text{kWh/m}^2/\text{yr}$) & Star Ratings
- **App:** `benchmarking` | **Phase:** Phase 2 | **Estimate:** 5.5 Hours | **Role:** Sustainability Officer
- **Goal:** As a sustainability officer, I want to compute our building's Energy Use Intensity (EUI in $\text{kWh/m}^2/\text{year}$), compare against national BEE benchmarks, and determine star ratings.
- **Acceptance Criteria:**
  1. Management command `compute_benchmarks` calculates annual energy consumption for facility.
  2. Computes $\text{EUI} = \text{Annual Energy (kWh)} / \text{Gross Floor Area (sqm)}$.
  3. Evaluates EUI against `benchmarking_buildingbenchmark` percentile thresholds for the facility type.
  4. Assigns BEE Star Rating from 1 to 5 stars.
  5. `GET /api/v1/benchmarking/scores/` and `GET /api/v1/benchmarking/ranking/` return percentile distributions.

---

### Phase 3: Intelligence, Renewables & Release (28 Hours)

#### P02-US18: Deterministic Energy Conservation Measures (ECMs)
- **App:** `recommendations` | **Phase:** Phase 3 | **Estimate:** 5.5 Hours | **Role:** Facility Manager
- **Goal:** As a facility manager, I want automated, explainable ECM recommendations calculated from our actual telemetry data with quantified ₹ savings.
- **Acceptance Criteria:**
  1. Management command `generate_recommendations` implements 5 distinct deterministic rules:
     - Rule 1 (Peak Demand Shaving): Recommends chiller pre-cooling when peak demand approaches sanctioned limit during evening peak tariff window.
     - Rule 2 (Power Factor Penalty Elimination): Recommends APFC capacitor bank servicing when monthly PF $< 0.90$.
     - Rule 3 (HVAC Setback Optimization): Detects chiller runtime during non-working weekend hours.
     - Rule 4 (Baseload Leakage Reduction): Flags weekend night base-load $>25\%$ of daytime load.
     - Rule 5 (DG Displacement): Calculates diesel fuel wasted when DG operated alongside healthy grid power.
  2. Each generated recommendation stores title, description, concrete action plan, estimated annual kWh savings, and annual ₹ savings based on active tariff rates.
  3. Computes estimated simple payback period in months.

#### P02-US19: ECM Lifecycle (Accept/Dismiss) & Savings Tracking
- **App:** `recommendations` | **Phase:** Phase 3 | **Estimate:** 4.5 Hours | **Role:** Customer
- **Goal:** As a customer, I want to accept or dismiss energy recommendations and provide feedback reasons.
- **Acceptance Criteria:**
  1. `GET /api/v1/recommendations/` returns active, accepted, and dismissed recommendations for scoped facilities.
  2. `PATCH /api/v1/recommendations/{id}/` allows changing status to `accepted` or `dismissed`.
  3. If status is `dismissed`, `dismissal_reason` field is mandatory.
  4. Stores timestamp `actioned_at`.
  5. Dashboard shows total projected ₹ savings from all `accepted` ECMs.

#### P02-US20: Solar PV Asset Monitoring & Generation Tracking
- **App:** `renewables` | **Phase:** Phase 3 | **Estimate:** 4.5 Hours | **Role:** Green Energy Officer
- **Goal:** As a green energy officer, I want to monitor rooftop and carport solar PV capacity, generation telemetry, and inverter performance ratio.
- **Acceptance Criteria:**
  1. `renewables_solarasset` models solar installations with rated capacity (kWp), tilt, azimuth, and inverter make.
  2. `renewables_solargenerationreading` tracks 15-minute generation (kWh), solar irradiance ($\text{W/m}^2$), ambient temperature, and performance ratio (PR).
  3. `GET /api/v1/renewables/solar-assets/` and `GET /api/v1/renewables/generation/` provide solar analytics.
  4. Validates performance ratio $0.00 \le \text{PR} \le 1.00$.

#### P02-US21: Solar Self-Consumption & Grid Outage Management
- **App:** `renewables` | **Phase:** Phase 3 | **Estimate:** 4.5 Hours | **Role:** Facility Engineer
- **Goal:** As a facility engineer, I want to track solar self-consumption percentage and log grid outage events with diesel fuel consumption.
- **Acceptance Criteria:**
  1. Calculates `self_consumption_pct = min(100, (solar_generation_kwh / total_facility_consumption_kwh) * 100)`.
  2. `renewables_gridevent` logs grid outage start/end timestamps, outage duration in minutes, and litres of diesel consumed.
  3. Endpoints `GET /api/v1/renewables/self-consumption/` and `GET /api/v1/renewables/grid-events/`.

#### P02-US22: Source-specific Carbon Emissions Accounting
- **App:** `renewables` | **Phase:** Phase 3 | **Estimate:** 4.5 Hours | **Role:** ESG Compliance Officer
- **Goal:** As an ESG officer, I want automated Scope 2 greenhouse gas emissions calculations based on CEA India emission factors.
- **Acceptance Criteria:**
  1. `renewables_carbonemissionfactor` stores verified India CEA factors: Grid ($0.82\text{ kg CO}_2/\text{kWh}$), DG ($0.68\text{ kg CO}_2/\text{kWh}$), Natural Gas ($0.49\text{ kg CO}_2/\text{kWh}$), Solar ($0.00$).
  2. Endpoint `GET /api/v1/renewables/emissions/?facility_id=1&month=YYYY-MM` aggregates monthly energy by source and multiplies by factor.
  3. Calculates avoided carbon emissions in $\text{kg CO}_2$ attributed to on-site solar PV generation.
  4. Returns emissions breakdown and total metric tonnes of $\text{CO}_2\text{e}$.

#### P02-US23: Comprehensive Verification, Test Suite & Release Deployment
- **App:** `release` | **Phase:** Phase 3 | **Estimate:** 4.5 Hours | **Role:** Senior Backend Engineer
- **Goal:** As the senior engineer, I want full regression testing across all modules, OpenAPI validation, test coverage documentation, and the final v1.0.0 release.
- **Acceptance Criteria:**
  1. Comprehensive pytest suite passing 100% of unit and integration tests across all 8 modules.
  2. Complete test execution and coverage report documented in `docs/test-report.md`.
  3. Final sprint review document in `docs/sprint-3-review.md`.
  4. Swagger documentation at `/api/docs/` verified complete with all schemas and response codes.
  5. Release branch `release/v1.0.0` merged into `main`, tagged `v1.0.0`, and pushed to GitHub.
