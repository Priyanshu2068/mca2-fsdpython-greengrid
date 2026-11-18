# GreenGrid Database Entity-Relationship Model

This document outlines the complete relational schema design for the GreenGrid Energy Management Information System (EMIS).

---

## 1. Entity-Relationship Diagram

```mermaid
erDiagram
    users_customuser ||--o{ accounts_auditlog : "triggers"
    users_customuser ||--o{ facilities_userfacilityassignment : "assigned_to"
    facilities_facility ||--o{ facilities_userfacilityassignment : "grants_access"
    facilities_facility ||--o{ facilities_building : "contains"
    facilities_facility ||--o{ facilities_datasource : "operates"
    facilities_facility ||--o{ facilities_meter : "monitors"
    facilities_building ||--o{ facilities_meter : "houses"
    
    facilities_datasource ||--o{ ingestion_batchlog : "submits"
    facilities_meter ||--o{ ingestion_rawreading : "records"
    ingestion_batchlog ||--o{ ingestion_rawreading : "contains"
    
    facilities_meter ||--o{ analytics_hourlyrollup : "aggregates_hourly"
    facilities_meter ||--o{ analytics_dailyrollup : "aggregates_daily"
    facilities_facility ||--o{ analytics_anomalyalert : "flags_anomalies_at"
    facilities_meter ||--o{ analytics_anomalyalert : "triggers_alert_for"
    
    benchmarking_buildingbenchmark ||--o{ benchmarking_facilitybenchmarkscore : "evaluates_against"
    facilities_facility ||--o{ benchmarking_facilitybenchmarkscore : "receives_score"
    
    billing_utilityprovider ||--o{ billing_tariffstructure : "defines"
    billing_tariffstructure ||--o{ billing_utilitybill : "bills_under"
    facilities_facility ||--o{ billing_utilitybill : "incurred_by"
    billing_utilitybill ||--o{ billing_billreconciliation : "reconciles"
    
    recommendations_ecmrule ||--o{ recommendations_recommendation : "instantiates"
    facilities_facility ||--o{ recommendations_recommendation : "recommends_for"
    facilities_meter ||--o{ recommendations_recommendation : "applies_to"
    
    facilities_facility ||--o{ renewables_solarasset : "hosts"
    renewables_solarasset ||--o{ renewables_solargenerationreading : "generates"
    facilities_facility ||--o{ renewables_gridevent : "experiences"
    renewables_carbonemissionfactor ||--o{ renewables_solargenerationreading : "offsets_using"

    users_customuser {
        bigint id PK
        varchar email UK
        varchar role "admin | customer | field_engineer"
        varchar first_name
        varchar last_name
        boolean is_active
        timestamptz date_joined
    }

    facilities_facility {
        bigint id PK
        varchar name
        varchar code UK
        varchar facility_type "commercial_office | tech_park | hospital | retail_mall"
        numeric gross_floor_area_sqm
        varchar address
        varchar city
        varchar state
        varchar pin_code
        timestamptz created_at
    }

    facilities_building {
        bigint id PK
        bigint facility_id FK
        varchar name
        integer total_floors
        numeric floor_area_sqm
    }

    facilities_meter {
        bigint id PK
        bigint facility_id FK
        bigint building_id FK "nullable"
        varchar meter_identifier UK
        varchar name
        varchar energy_source "grid | diesel_generator | solar | water | gas"
        varchar load_category "hvac | lighting | it_infrastructure | auxiliary_pumps | main_incomer"
        varchar physical_location
        boolean is_active
    }

    facilities_datasource {
        bigint id PK
        bigint facility_id FK
        varchar name
        varchar key_prefix
        varchar key_hash UK
        boolean is_active
        timestamptz last_used_at
    }

    ingestion_rawreading {
        bigint id PK
        bigint meter_id FK
        bigint batch_id FK "nullable"
        timestamptz timestamp
        numeric energy_kwh
        numeric active_power_kw
        numeric reactive_power_kvar
        numeric apparent_power_kva
        numeric voltage_v
        numeric current_a
        numeric power_factor
        numeric frequency_hz
    }

    analytics_hourlyrollup {
        bigint id PK
        bigint meter_id FK
        timestamptz bucket_start
        numeric total_energy_kwh
        numeric peak_demand_kw
        numeric min_demand_kw
        numeric avg_power_factor
        integer reading_count
    }

    analytics_dailyrollup {
        bigint id PK
        bigint meter_id FK
        date rollup_date
        numeric total_energy_kwh
        numeric peak_demand_kw
        numeric off_peak_energy_kwh
        numeric peak_energy_kwh
        numeric avg_power_factor
    }

    analytics_anomalyalert {
        bigint id PK
        bigint facility_id FK
        bigint meter_id FK
        timestamptz detected_at
        varchar anomaly_type "spike | low_power_factor | dg_grid_clash | meter_silent"
        varchar severity "low | medium | high | critical"
        text reason
        numeric deviation_factor
        varchar status "open | acknowledged | resolved"
    }

    billing_tariffstructure {
        bigint id PK
        bigint provider_id FK
        varchar tariff_code UK
        varchar tariff_name
        numeric base_energy_rate_inr
        numeric peak_hour_rate_inr
        numeric demand_charge_inr_per_kva
        numeric pf_penalty_threshold
        numeric pf_penalty_rate_inr
    }

    billing_utilitybill {
        bigint id PK
        bigint facility_id FK
        bigint tariff_id FK
        date billing_cycle_start
        date billing_cycle_end
        numeric billed_kwh
        numeric billed_max_demand_kva
        numeric billed_amount_inr
        numeric effective_cost_per_kwh_inr
    }

    billing_billreconciliation {
        bigint id PK
        bigint bill_id FK UK
        numeric metered_kwh
        numeric discrepancy_kwh
        numeric discrepancy_percentage
        numeric variance_cost_inr
        varchar reconciliation_status "verified | variance_minor | variance_action_required"
    }

    recommendations_recommendation {
        bigint id PK
        bigint rule_id FK
        bigint facility_id FK
        bigint meter_id FK "nullable"
        varchar title
        text description
        numeric estimated_annual_savings_inr
        numeric estimated_payback_months
        varchar status "active | accepted | dismissed"
    }

    renewables_solarasset {
        bigint id PK
        bigint facility_id FK
        varchar array_identifier
        numeric rated_capacity_kwp
        numeric tilt_degrees
        varchar inverter_model
    }

    renewables_solargenerationreading {
        bigint id PK
        bigint asset_id FK
        timestamptz timestamp
        numeric generation_kwh
        numeric irradiation_wm2
        numeric performance_ratio
    }
```
