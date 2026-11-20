# GreenGrid REST API Specification

This document defines the endpoint contracts, role-based permissions, request payloads, and response schemas across all modules in GreenGrid.

All endpoints are prefixed with `/api/v1/`.

---

## 1. Global Standards & Error Envelope

All error responses across all modules strictly follow the unified error envelope:

```json
{
  "error": {
    "status": 400,
    "code": "VALIDATION_ERROR",
    "message": "Invalid batch payload or constraints violated.",
    "details": {
      "readings": [
        "Item at index 4 violates non-negative energy constraint: energy_kwh must be >= 0."
      ]
    }
  }
}
```

Standard error codes:
- `AUTHENTICATION_REQUIRED` (401)
- `INVALID_API_KEY` (401)
- `PERMISSION_DENIED` (403)
- `RESOURCE_NOT_FOUND` (404)
- `VALIDATION_ERROR` (400)
- `BATCH_LIMIT_EXCEEDED` (400)
- `INTERNAL_SERVER_ERROR` (500)

---

## 2. Core & Accounts Module (M8)

| Method | Endpoint | Allowed Roles | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health/` | Public | System and database health status |
| `GET` | `/api/v1/accounts/csrf/` | Public | Sets `csrftoken` HTTP cookie for SPA session initiation |
| `POST` | `/api/v1/accounts/login/` | Public | Authenticates user credentials and establishes Django session |
| `POST` | `/api/v1/accounts/logout/` | Authenticated | Clears session cookie and invalidates session |
| `GET` | `/api/v1/accounts/me/` | Authenticated | Retrieves current logged-in user profile, role, and facility scopes |
| `POST` | `/api/v1/accounts/change-password/` | Authenticated | Updates account password |
| `GET` | `/api/v1/accounts/users/` | `admin`, `field_engineer` | Lists users with filtering by role. Admins see everyone; field engineers see only customers who share one of their facilities |
| `POST` | `/api/v1/accounts/users/` | `admin`, `field_engineer` | Provisions a user and grants facility access (`facility_ids`). Admins can create customers and field engineers (facilities optional). Field engineers can create customers only, for at least one of their own facilities (404 for any other facility) |
| `PUT` | `/api/v1/accounts/users/{id}/facilities/` | `admin`, `field_engineer` | Replaces a user's facility access within the caller's scope. Access outside the caller's facilities is left untouched. Writes an `UPDATE_FACILITY_ACCESS` audit entry |
| `PATCH` | `/api/v1/accounts/users/{id}/` | `admin` | Updates a profile or activates / deactivates a user |
| `GET` | `/api/v1/accounts/audit-logs/` | `admin` | Ingestion and operational security audit log |

### `POST /api/v1/accounts/login/`
**Request:**
```json
{
  "email": "customer.blr@alphatech.in",
  "password": "StrongPassword@2026"
}
```
**Response (200 OK):**
```json
{
  "id": 2,
  "email": "customer.blr@alphatech.in",
  "first_name": "Rajesh",
  "last_name": "Sharma",
  "role": "customer",
  "facilities": [
    {
      "id": 1,
      "name": "Alpha Tech Park",
      "code": "FAC-BLR-01"
    }
  ]
}
```

---

## 3. Facilities & Meters Module (M1)

| Method | Endpoint | Allowed Roles | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/facilities/` | `admin`, `customer`, `field_engineer` | Lists facilities scoped to user's role |
| `POST` | `/api/v1/facilities/` | `admin` | Provisions a new commercial facility |
| `GET` | `/api/v1/facilities/{id}/` | Scoped Roles | Detailed facility profile, square footage, demand limit |
| `GET` | `/api/v1/facilities/{id}/buildings/` | Scoped Roles | Lists buildings contained in facility |
| `GET` | `/api/v1/facilities/{id}/meters/` | Scoped Roles | Lists sub-meters with source and load category |
| `POST` | `/api/v1/facilities/{id}/meters/` | `admin`, `field_engineer` | Registers a new physical or virtual sub-meter |
| `GET` | `/api/v1/facilities/{id}/datasources/`| `admin`, `field_engineer` | Lists IoT DataSources for facility |
| `POST` | `/api/v1/facilities/{id}/datasources/`| `admin`, `field_engineer` | Generates a new DataSource & raw API key |
| `POST` | `/api/v1/facilities/datasources/{id}/rotate-key/` | `admin`, `field_engineer` | Rotates API key, invalidates old key |

### `POST /api/v1/facilities/{id}/meters/`
**Request:**
```json
{
  "building_id": 1,
  "meter_identifier": "MTR-BLR-01-HVAC-CH2",
  "name": "Alpha Chiller 2 Sub-meter",
  "energy_source": "grid",
  "load_category": "hvac",
  "meter_make": "Schneider Electric",
  "meter_model": "PM5350",
  "ct_ratio": "200.00",
  "pt_ratio": "1.00",
  "physical_location": "Basement 1 Chiller Room Bay 2"
}
```
**Response (201 Created):**
```json
{
  "id": 15,
  "facility_id": 1,
  "building_id": 1,
  "meter_identifier": "MTR-BLR-01-HVAC-CH2",
  "name": "Alpha Chiller 2 Sub-meter",
  "energy_source": "grid",
  "load_category": "hvac",
  "is_active": true,
  "created_at": "2026-03-30T10:00:00Z"
}
```

---

## 4. Telemetry Ingestion Module (M1)

| Method | Endpoint | Allowed Roles / Auth | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/ingestion/readings/bulk/` | `X-API-Key` OR `admin`, `field_engineer` | Ingests up to 5000 15-minute readings idempotently |
| `POST` | `/api/v1/ingestion/readings/upload-csv/` | `admin`, `field_engineer` | Uploads offline CSV file containing readings |
| `GET` | `/api/v1/ingestion/readings/` | Scoped Roles | Paginated query of raw readings with filters |
| `GET` | `/api/v1/ingestion/batches/` | `admin`, `field_engineer` | Audit log of previous ingestion batches |

### `POST /api/v1/ingestion/readings/bulk/`
**Headers:**
`X-API-Key: gg_live_blr01_a93f4e8b2c1d` (or Session Cookie + CSRF)

**Request:**
```json
{
  "readings": [
    {
      "meter_identifier": "MTR-BLR-01-INC",
      "timestamp": "2026-03-30T09:00:00Z",
      "energy_kwh": "425.5000",
      "active_power_kw": "1702.0000",
      "reactive_power_kvar": "558.7000",
      "apparent_power_kva": "1791.5000",
      "voltage_v": "412.50",
      "current_a": "2506.20",
      "power_factor": "0.950",
      "frequency_hz": "49.95"
    }
  ]
}
```
**Response (201 Created):**
```json
{
  "batch_reference": "BATCH-20260330-104928-842",
  "status": "processed",
  "total_received": 1,
  "accepted": 1,
  "duplicates_ignored": 0,
  "rejected": 0,
  "rejection_details": []
}
```

---

## 5. Analytics & Anomaly Detection Module (M2)

| Method | Endpoint | Allowed Roles | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/analytics/rollups/hourly/` | Scoped Roles | Queries hourly rollups per meter or facility |
| `GET` | `/api/v1/analytics/rollups/daily/` | Scoped Roles | Queries daily rollups with peak demand & off-peak split |
| `GET` | `/api/v1/analytics/alerts/` | Scoped Roles | Lists anomaly alerts filtered by severity, status, facility |
| `PATCH` | `/api/v1/analytics/alerts/{id}/` | `admin`, `field_engineer` | Updates alert status (`acknowledged`, `resolved`, `false_positive`) |

### `PATCH /api/v1/analytics/alerts/{id}/`
**Request:**
```json
{
  "status": "acknowledged",
  "resolution_notes": "Technician dispatched to inspect APFC capacitor bank contactors."
}
```
**Response (200 OK):**
```json
{
  "id": 2,
  "status": "acknowledged",
  "resolution_notes": "Technician dispatched to inspect APFC capacitor bank contactors.",
  "resolved_at": null
}
```

---

## 6. Executive Dashboard Module (M3)

All dashboard endpoints read exclusively from pre-aggregated rollups and guarantee response times under 1 second.

| Method | Endpoint | Allowed Roles | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/dashboard/summary/` | Scoped Roles | Today's kWh, yesterday comparison, MTD kWh, current peak kW |
| `GET` | `/api/v1/dashboard/trends/` | Scoped Roles | 24-hour hourly profile and 30-day daily profile |
| `GET` | `/api/v1/dashboard/energy-mix/` | Scoped Roles | Energy consumed by source: Grid vs. DG vs. Solar |
| `GET` | `/api/v1/dashboard/load-breakdown/` | Scoped Roles | Sub-metered breakdown: HVAC, Lighting, IT, Pumps |

### `GET /api/v1/dashboard/summary/?facility_id=1`
**Response (200 OK):**
```json
{
  "facility_id": 1,
  "facility_name": "Alpha Tech Park",
  "as_of": "2026-03-30T10:30:00Z",
  "metrics": {
    "today_consumption_kwh": "14285.5000",
    "yesterday_same_time_kwh": "13950.0000",
    "change_percentage": 2.41,
    "month_to_date_kwh": "595200.0000",
    "current_peak_demand_kw": "1780.0000",
    "sanctioned_demand_kw": "2500.0000",
    "demand_utilization_pct": 71.20,
    "active_anomalies_count": 2
  }
}
```

---

## 7. Facility Benchmarking Module (M4)

| Method | Endpoint | Allowed Roles | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/benchmarking/standards/` | Scoped Roles | Indian commercial building EUI benchmarks ($\text{kWh/m}^2/\text{yr}$) |
| `GET` | `/api/v1/benchmarking/scores/` | Scoped Roles | Historical annual benchmark scores and star ratings |
| `GET` | `/api/v1/benchmarking/ranking/` | Scoped Roles | Peer ranking percentile within building category. Admins see every facility; other roles see their own facilities in full and all other facilities anonymised (`Peer facility #N`, with name, code, id, floor area and absolute energy removed) so they can compare efficiency without learning who the peers are |

### `GET /api/v1/benchmarking/scores/?facility_id=1`
**Response (200 OK):**
```json
{
  "facility_id": 1,
  "facility_name": "Alpha Tech Park",
  "building_type": "tech_park",
  "gross_floor_area_sqm": "45000.00",
  "evaluations": [
    {
      "year": 2025,
      "annual_energy_kwh": "7120000.0000",
      "eui_kwh_sqm_year": "158.22",
      "industry_median_eui": "185.00",
      "national_percentile": 78.50,
      "star_rating": 4,
      "performance_band": "High Efficiency (Top 25% Nationally)"
    }
  ]
}
```

---

## 8. Utility Billing & Reconciliation Module (M5)

| Method | Endpoint | Allowed Roles | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/billing/providers/` | Scoped Roles | Indian electricity supply companies (DISCOMs) |
| `GET` | `/api/v1/billing/tariffs/` | Scoped Roles | Commercial HT tariff rates, peak multipliers, PF penalties |
| `GET` | `/api/v1/billing/bills/` | Scoped Roles | Utility bills list with status and effective cost/kWh |
| `POST` | `/api/v1/billing/bills/` | `admin`, `field_engineer` | Records a new monthly utility bill (manual / emergency entry). Engineers are limited to their assigned facilities (404 otherwise) |
| `GET` | `/api/v1/billing/reconciliations/` | Scoped Roles | Metered vs. billed discrepancy audit records |

### `GET /api/v1/billing/reconciliations/?bill_id=3`
**Response (200 OK):**
```json
{
  "reconciliation_id": 3,
  "bill_id": 3,
  "bill_number": "BILL-BESCOM-2026-03",
  "billing_cycle": {
    "start": "2026-03-01",
    "end": "2026-03-31"
  },
  "utility_billed_kwh": "612000.0000",
  "internal_metered_kwh": "595200.0000",
  "discrepancy_kwh": "16800.0000",
  "discrepancy_percentage": 2.75,
  "financial_variance_inr": "150222.00",
  "status": "variance_action_required",
  "notes": "Significant variance (>2.5%) detected between utility bill and internal check meter. Audit dispute raised with BESCOM."
}
```

---

## 9. Rule-Based Recommendations Module (M6)

| Method | Endpoint | Allowed Roles | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/recommendations/rules/` | Scoped Roles | Catalog of deterministic Energy Conservation Measures (ECMs) |
| `GET` | `/api/v1/recommendations/` | Scoped Roles | Active and historical recommendations with ₹ savings |
| `PATCH` | `/api/v1/recommendations/{id}/` | `customer`, `admin` | Actions recommendation: `accepted` or `dismissed` |

### `PATCH /api/v1/recommendations/{id}/`
**Request:**
```json
{
  "status": "accepted"
}
```
**Response (200 OK):**
```json
{
  "id": 1,
  "rule_code": "ECM-PEAK-SHAVE",
  "title": "Pre-cooling & Chiller Setback during BESCOM Peak Hours (18:00 - 22:00)",
  "estimated_annual_savings_inr": "1092500.00",
  "status": "accepted",
  "actioned_at": "2026-03-30T10:45:00Z"
}
```

---

## 10. Renewables & Grid Events Module (M7)

| Method | Endpoint | Allowed Roles | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/renewables/solar-assets/` | Scoped Roles | Rooftop and ground-mount Solar PV arrays |
| `GET` | `/api/v1/renewables/generation/` | Scoped Roles | Solar generation readings and performance ratio |
| `GET` | `/api/v1/renewables/self-consumption/` | Scoped Roles | Solar self-consumption % vs grid feed-in |
| `GET` | `/api/v1/renewables/grid-events/` | Scoped Roles | Grid outages, voltage dips, and DG failovers |
| `GET` | `/api/v1/renewables/emissions/` | Scoped Roles | Scope 2 carbon footprint accounting ($\text{kg CO}_2\text{e}$) |

### `GET /api/v1/renewables/emissions/?facility_id=1&month=2026-03`
**Response (200 OK):**
```json
{
  "facility_id": 1,
  "period": "2026-03",
  "total_emissions_co2_kg": "492344.00",
  "source_breakdown": [
    {
      "source": "grid",
      "energy_kwh": "595200.0000",
      "emission_factor_kg_per_kwh": "0.8200",
      "emissions_co2_kg": "488064.00",
      "share_percentage": 99.13
    },
    {
      "source": "diesel_generator",
      "energy_kwh": "6294.0000",
      "emission_factor_kg_per_kwh": "0.6800",
      "emissions_co2_kg": "4280.00",
      "share_percentage": 0.87
    },
    {
      "source": "solar",
      "energy_kwh": "42500.0000",
      "emission_factor_kg_per_kwh": "0.0000",
      "emissions_co2_kg": "0.00",
      "avoided_co2_kg": "34850.00"
    }
  ]
}
```
