# GreenGrid Operational Workflows Specification

This document details the system workflows for GreenGrid, covering end-to-end telemetry flow, the idempotent 15-minute ingestion lifecycle, and role-specific operational user journeys.

---

## 1. End-to-End System Flow

The diagram below illustrates the comprehensive lifecycle of energy data—from external sources and simulation scripts through ingestion, storage, scheduled analytical rollups, and user-facing intelligence interfaces.

```mermaid
flowchart TD
    subgraph Sources["1. Telemetry & Data Acquisition Sources"]
        S1["NASA POWER API\n(Hourly Irradiance & Temp)"]
        S2["Environmental Simulator\n(Replay past weather & loads)"]
        S3["Field CSV Upload\n(Offline data logging)"]
        S4["Edge Gateways & Data Sources\n(Direct HTTP Post)"]
        S5["Manual Web Entry\n(Customer / Engineer portal)"]
    end

    subgraph Ingestion["2. Ingestion & Security Boundary"]
        I1["API Gateway / DRF Ingestion Endpoint\n/api/v1/ingestion/readings/bulk/"]
        I2{"Authentication Check\n(Session CSRF or X-API-Key)"}
        I3{"Payload Validation\n(Schema, Batch <= 5000, Types)"}
        I4["Idempotent Staging & De-duplication\n(ON CONFLICT DO NOTHING)"]
    end

    subgraph Storage["3. High-Performance PostgreSQL 16 Storage"]
        D1[("raw_readings\nBRIN Index on timestamp\nUNIQUE (meter_id, timestamp)")]
        D2[("facility_meters\nMaster metadata & load categories")]
        D3[("audit_logs\nIngestion batches & user actions")]
    end

    subgraph Jobs["4. Incremental Scheduled Jobs (Management Commands)"]
        J1["rollup_hourly\n(Incremental 48-hr recompute with date_trunc)"]
        J2["rollup_daily\n(Aggregates hourly rollups per meter/source)"]
        J3["detect_anomalies\n(4-week hour-of-week median baseline, PF < 0.9, DG grid clash)"]
        J4["compute_benchmarks\n(EUI kWh/sqm/yr and building type percentiles)"]
        J5["generate_recommendations\n(5-6 deterministic rules with INR savings)"]
    end

    subgraph AggregatedStorage["5. Analytics & Intelligence Datastores"]
        A1[("hourly_rollups & daily_rollups")]
        A2[("anomaly_alerts\n(Reason, severity, status)")]
        A3[("recommendations\n(Status: active/accepted/dismissed)")]
        A4[("utility_bills & reconciliations")]
    end

    subgraph Interfaces["6. Presentation & User Experience (<1s read time)"]
        P1["M3: Executive Dashboard & Load Breakdown"]
        P2["M2: Anomaly Alerts & Telemetry Diagnostics"]
        P3["M5: Utility Bill Audit & Discrepancy Reporting"]
        P4["M4: Benchmark Rankings & Peer Comparison"]
        P5["M6: Rule-based ECMs with INR Savings"]
        P6["M7: Solar PV Generation & Self-consumption"]
    end

    subgraph Users["7. User Actions & Closed-Loop Outcomes"]
        U1["Customer: Accept/Dismiss ECMs & Approve Bills"]
        U2["Field Engineer: Resolve Meter Drift & Recalibrate"]
        U3["Admin: Reconfigure Tariffs & Provision Facilities"]
    end

    S1 --> S2
    S2 --> I1
    S3 --> I1
    S4 --> I1
    S5 --> I1

    I1 --> I2
    I2 -- "Valid" --> I3
    I2 -- "Invalid Auth" --> R1["HTTP 401 / 403 Forbidden"]
    I3 -- "Pass" --> I4
    I3 -- "Malformed / >5000" --> R2["HTTP 400 Bad Request with Details"]
    I4 --> D1
    I4 --> D3
    D2 -.-> I3

    D1 --> J1
    J1 --> A1
    A1 --> J2
    J2 --> A1

    D1 --> J3
    A1 --> J3
    J3 --> A2

    A1 --> J4
    J4 --> Interfaces

    A1 --> J5
    A2 --> J5
    J5 --> A3

    A1 --> P1
    A2 --> P2
    A4 --> P3
    A3 --> P5
    A1 --> P6

    P5 --> U1
    P2 --> U2
    P3 --> U1
    Interfaces --> U3
```

---

## 2. 15-Minute Reading Ingestion & Validation Workflow

Every 15-minute telemetry packet undergoes rigorous syntax, security, and integrity checks prior to persistence. Idempotency guarantees that re-transmitting payloads will never duplicate metrics or corrupt downstream aggregates.

```mermaid
flowchart TD
    Start(["Client submits POST /api/v1/ingestion/readings/bulk/"]) --> AuthCheck{"Has X-API-Key Header?"}

    AuthCheck -- "Yes" --> HashKey["Compute SHA-256 hash of API key"]
    HashKey --> QuerySource["Lookup DataSource by key_hash"]
    QuerySource --> SourceActive{"DataSource exists\nand is_active == True?"}
    SourceActive -- "No" --> Ret401["Return HTTP 401 Unauthorized\n{'error': {'code': 'INVALID_API_KEY'}}"]
    SourceActive -- "Yes" --> ScopedFacility["Extract authorized facility_id"]

    AuthCheck -- "No" --> SessionCheck{"Active User Session\nwith valid CSRF token?"}
    SessionCheck -- "No" --> Ret403["Return HTTP 403 Forbidden\n{'error': {'code': 'AUTHENTICATION_REQUIRED'}}"]
    SessionCheck -- "Yes" --> CheckUserRole{"User has role\nADMIN or FIELD_ENGINEER?"}
    CheckUserRole -- "No" --> RetRoleDenied["Return HTTP 403 Forbidden\n{'error': {'code': 'INSUFFICIENT_PERMISSIONS'}}"]
    CheckUserRole -- "Yes" --> ScopedFacilitySession["Extract accessible facility_ids"]

    ScopedFacility --> BatchCheck{"Batch size > 0\nand <= 5000?"}
    ScopedFacilitySession --> BatchCheck

    BatchCheck -- "No" --> Ret400Batch["Return HTTP 400 Bad Request\n{'error': {'code': 'INVALID_BATCH_SIZE'}}"]
    BatchCheck -- "Yes" --> LoopInit["Initialize Staging Queues:\nValidList = [], Rejections = []"]

    LoopInit --> ForEach["For each reading in batch"]
    ForEach --> SchemaVal{"Validate item schema:\nmeter_id (UUID/int),\ntimestamp (ISO UTC),\nenergy_kwh (Decimal >= 0),\nvoltage, current, pf, freq"}

    SchemaVal -- "Failed" --> AddRejection["Record rejection item:\n{index, error_code, reason}"]
    SchemaVal -- "Passed" --> MeterScopeCheck{"Does meter exist and\nbelong to authorized facility?"}

    MeterScopeCheck -- "No" --> AddScopeReject["Record rejection item:\n{index, error_code: 'METER_NOT_FOUND_OR_FORBIDDEN'}"]
    MeterScopeCheck -- "Yes" --> AddValid["Stage in ValidList for bulk execution"]

    AddRejection --> MoreItems{"More items in batch?"}
    AddScopeReject --> MoreItems
    AddValid --> MoreItems

    MoreItems -- "Yes" --> ForEach
    MoreItems -- "No" --> AnyValid{"ValidList count > 0?"}

    AnyValid -- "Yes" --> BulkUpsert["Execute PostgreSQL Bulk Insert:\nINSERT INTO raw_readings\n(meter_id, timestamp, energy_kwh, ...)\nVALUES (...)\nON CONFLICT (meter_id, timestamp) DO NOTHING"]
    BulkUpsert --> CountInserted["Calculate:\nInserted = rows_affected\nDuplicates = len(ValidList) - rows_affected"]

    AnyValid -- "No" --> CountZero["Inserted = 0, Duplicates = 0"]

    CountInserted --> LogAudit["Write IngestionAuditLog record"]
    CountZero --> LogAudit

    LogAudit --> ResponsePayload["Construct Response:\n{\n  'status': 'processed',\n  'total_received': N,\n  'accepted': Inserted,\n  'duplicates_ignored': Duplicates,\n  'rejected': len(Rejections),\n  'rejection_details': Rejections\n}"]

    ResponsePayload --> Done(["Return HTTP 201 Created (or 207 Multi-Status if partial)"])
```

---

## 3. Per-Role Operational Workflows

GreenGrid enforces strict Role-Based Access Control (RBAC) across three distinct user personas: **Administrator**, **Customer**, and **Field Engineer**.

```mermaid
flowchart TD
    subgraph AdminWF["Administrator Workflow (System Governance)"]
        A_Start(["Admin Logs In"]) --> A_Mgt["User Management\n(Create Customer / Engineer accounts)"]
        A_Mgt --> A_Fac["Facility & Sub-meter Provisioning\n(Assign square footage, load categories, building types)"]
        A_Fac --> A_Tariff["Utility Tariff Configuration\n(Define slabs, peak hours, demand charges, PF penalties)"]
        A_Tariff --> A_Audit["System Audit & Anomaly Tuning\n(Configure thresholds, review system ingestion health)"]
    end

    subgraph CustomerWF["Customer Workflow (Facility Energy Management)"]
        C_Start(["Customer Logs In"]) --> C_Scope["System scopes view to\nauthorized facilities only"]
        C_Scope --> C_Dash["View Real-time Executive Dashboard\n(<1s load from pre-aggregated rollups)"]
        C_Dash --> C_DeepDive{"User Action"}
        C_DeepDive -- "Monitor Mix" --> C_Mix["Inspect Energy Mix\n(Grid, Solar, DG, Gas breakdown)"]
        C_DeepDive -- "Billing Audit" --> C_Bill["Review Monthly Utility Bill\n(Metered vs. Billed variance report)"]
        C_DeepDive -- "Benchmarks" --> C_Bench["Compare Energy Use Intensity (EUI)\nagainst Indian building benchmarks"]
        C_DeepDive -- "ECMs" --> C_Rec["Review Rule-based Recommendations\n(Evaluate ₹ savings per year)"]
        C_Rec --> C_Action{"Decision"}
        C_Action -- "Approve" --> C_Accept["Mark Recommendation 'ACCEPTED'\n(Schedule maintenance/retrofit)"]
        C_Action -- "Dismiss" --> C_Dismiss["Mark Recommendation 'DISMISSED'\n(Store dismissal justification)"]
    end

    subgraph FieldEngWF["Field Engineer Workflow (Operations & Field Deployment)"]
        F_Start(["Field Engineer Logs In"]) --> F_Scope["Scope limited to\nassigned facilities"]
        F_Scope --> F_Action{"Operational Task"}
        F_Action -- "Register Hardware" --> F_Meter["Register New Meter\n(Assign serial number, load type, source)"]
        F_Meter --> F_Key["Generate or Rotate DataSource API Key\n(Copy unhashed secret once, SHA-256 stored)"]
        F_Action -- "Offline Ingestion" --> F_Upload["Upload Historical CSV Readings\n(Validate headers, progress tracking)"]
        F_Upload --> F_ErrReview["Review Ingestion Error Log\n(Fix timestamp offsets, re-upload)"]
        F_Action -- "Diagnostics" --> F_Alerts["Inspect Anomaly Alerts\n(PF < 0.9, meter silent > 2h, DG clash)"]
        F_Alerts --> F_Ack["Acknowledge & Clear Field Alerts"]
    end
```
