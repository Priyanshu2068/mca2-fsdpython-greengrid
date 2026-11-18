-- ==============================================================================
-- GreenGrid Energy Management Information System (EMIS)
-- PostgreSQL 16 Production Relational DDL Schema
-- ==============================================================================

-- Enable UUID extension if required
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------------------------
-- 1. Users and Access Control (Module M8)
-- ------------------------------------------------------------------------------

CREATE TABLE users_customuser (
    id BIGSERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMPTZ,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    email VARCHAR(254) NOT NULL UNIQUE,
    first_name VARCHAR(150) NOT NULL DEFAULT '',
    last_name VARCHAR(150) NOT NULL DEFAULT '',
    role VARCHAR(30) NOT NULL CHECK (role IN ('admin', 'customer', 'field_engineer')),
    phone VARCHAR(20) NOT NULL DEFAULT '',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    date_joined TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_role ON users_customuser (role);
CREATE INDEX idx_users_email ON users_customuser (email);

CREATE TABLE accounts_auditlog (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users_customuser(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(100) NOT NULL DEFAULT '',
    ip_address INET,
    user_agent TEXT NOT NULL DEFAULT '',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_auditlog_timestamp_brin ON accounts_auditlog USING brin (timestamp);
CREATE INDEX idx_auditlog_user ON accounts_auditlog (user_id);

-- ------------------------------------------------------------------------------
-- 2. Facilities, Meters, and Data Sources (Module M1)
-- ------------------------------------------------------------------------------

CREATE TABLE facilities_facility (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    facility_type VARCHAR(50) NOT NULL CHECK (facility_type IN (
        'commercial_office', 'tech_park', 'hospital', 'retail_mall', 'hotel', 'educational_campus'
    )),
    gross_floor_area_sqm NUMERIC(12, 2) NOT NULL CHECK (gross_floor_area_sqm > 0),
    operating_hours_per_week NUMERIC(5, 2) NOT NULL DEFAULT 50.00 CHECK (operating_hours_per_week BETWEEN 0 AND 168),
    address TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    pin_code VARCHAR(20) NOT NULL,
    latitude NUMERIC(9, 6),
    longitude NUMERIC(9, 6),
    sanctioned_demand_kva NUMERIC(10, 2) NOT NULL DEFAULT 500.00 CHECK (sanctioned_demand_kva > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_facilities_city ON facilities_facility (city);
CREATE INDEX idx_facilities_type ON facilities_facility (facility_type);

CREATE TABLE facilities_userfacilityassignment (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users_customuser(id) ON DELETE CASCADE,
    facility_id BIGINT NOT NULL REFERENCES facilities_facility(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_facility_assignment UNIQUE (user_id, facility_id)
);

CREATE TABLE facilities_building (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT NOT NULL REFERENCES facilities_facility(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL,
    total_floors INT NOT NULL DEFAULT 1 CHECK (total_floors > 0),
    floor_area_sqm NUMERIC(12, 2) NOT NULL CHECK (floor_area_sqm > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_facility_building_code UNIQUE (facility_id, code)
);

CREATE TABLE facilities_meter (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT NOT NULL REFERENCES facilities_facility(id) ON DELETE CASCADE,
    building_id BIGINT REFERENCES facilities_building(id) ON DELETE SET NULL,
    meter_identifier VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    energy_source VARCHAR(50) NOT NULL CHECK (energy_source IN (
        'grid', 'diesel_generator', 'solar', 'water', 'gas'
    )),
    load_category VARCHAR(50) NOT NULL CHECK (load_category IN (
        'main_incomer', 'hvac', 'lighting', 'it_infrastructure', 'auxiliary_pumps', 'elevators', 'ev_chargers'
    )),
    meter_make VARCHAR(100) NOT NULL DEFAULT 'Schneider Electric',
    meter_model VARCHAR(100) NOT NULL DEFAULT 'EM6400NG',
    ct_ratio NUMERIC(10, 2) NOT NULL DEFAULT 1.00 CHECK (ct_ratio > 0),
    pt_ratio NUMERIC(10, 2) NOT NULL DEFAULT 1.00 CHECK (pt_ratio > 0),
    physical_location VARCHAR(255) NOT NULL DEFAULT 'Main Electrical Room',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_meter_facility_source ON facilities_meter (facility_id, energy_source);
CREATE INDEX idx_meter_load_category ON facilities_meter (load_category);

CREATE TABLE facilities_datasource (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT NOT NULL REFERENCES facilities_facility(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    key_prefix VARCHAR(16) NOT NULL,
    key_hash VARCHAR(64) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ
);

CREATE INDEX idx_datasource_key_hash ON facilities_datasource (key_hash);

-- ------------------------------------------------------------------------------
-- 3. Telemetry Ingestion (Module M1)
-- ------------------------------------------------------------------------------

CREATE TABLE ingestion_batchlog (
    id BIGSERIAL PRIMARY KEY,
    datasource_id BIGINT REFERENCES facilities_datasource(id) ON DELETE SET NULL,
    uploaded_by BIGINT REFERENCES users_customuser(id) ON DELETE SET NULL,
    batch_reference VARCHAR(100) NOT NULL UNIQUE,
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('api_bulk', 'csv_upload', 'simulator', 'manual')),
    total_records INT NOT NULL CHECK (total_records >= 0),
    accepted_records INT NOT NULL CHECK (accepted_records >= 0),
    duplicate_records INT NOT NULL CHECK (duplicate_records >= 0),
    rejected_records INT NOT NULL CHECK (rejected_records >= 0),
    ingestion_duration_ms INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    error_summary JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE ingestion_rawreading (
    id BIGSERIAL PRIMARY KEY,
    meter_id BIGINT NOT NULL REFERENCES facilities_meter(id) ON DELETE CASCADE,
    batch_id BIGINT REFERENCES ingestion_batchlog(id) ON DELETE SET NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    energy_kwh NUMERIC(14, 4) NOT NULL CHECK (energy_kwh >= 0),
    active_power_kw NUMERIC(12, 4) NOT NULL DEFAULT 0.0000,
    reactive_power_kvar NUMERIC(12, 4) NOT NULL DEFAULT 0.0000,
    apparent_power_kva NUMERIC(12, 4) NOT NULL DEFAULT 0.0000,
    voltage_v NUMERIC(8, 2) NOT NULL DEFAULT 415.00 CHECK (voltage_v >= 0),
    current_a NUMERIC(10, 2) NOT NULL DEFAULT 0.00 CHECK (current_a >= 0),
    power_factor NUMERIC(4, 3) NOT NULL DEFAULT 1.000 CHECK (power_factor BETWEEN 0.000 AND 1.000),
    frequency_hz NUMERIC(5, 2) NOT NULL DEFAULT 50.00 CHECK (frequency_hz BETWEEN 45.00 AND 55.00),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_meter_timestamp UNIQUE (meter_id, timestamp)
);

-- BRIN index on timestamp for ultra-compact time series indexing
CREATE INDEX idx_rawreading_timestamp_brin ON ingestion_rawreading USING brin (timestamp);
-- BTree composite index for analytical lookups
CREATE INDEX idx_rawreading_meter_timestamp ON ingestion_rawreading (meter_id, timestamp DESC);

-- ------------------------------------------------------------------------------
-- 4. Analytical Rollups and Anomaly Detection (Module M2)
-- ------------------------------------------------------------------------------

CREATE TABLE analytics_hourlyrollup (
    id BIGSERIAL PRIMARY KEY,
    meter_id BIGINT NOT NULL REFERENCES facilities_meter(id) ON DELETE CASCADE,
    bucket_start TIMESTAMPTZ NOT NULL,
    total_energy_kwh NUMERIC(14, 4) NOT NULL CHECK (total_energy_kwh >= 0),
    peak_demand_kw NUMERIC(12, 4) NOT NULL DEFAULT 0.0000,
    min_demand_kw NUMERIC(12, 4) NOT NULL DEFAULT 0.0000,
    avg_power_factor NUMERIC(4, 3) NOT NULL DEFAULT 1.000 CHECK (avg_power_factor BETWEEN 0.000 AND 1.000),
    reading_count INT NOT NULL CHECK (reading_count >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_hourly_meter_bucket UNIQUE (meter_id, bucket_start)
);

CREATE INDEX idx_hourlyrollup_bucket_brin ON analytics_hourlyrollup USING brin (bucket_start);
CREATE INDEX idx_hourlyrollup_meter_bucket ON analytics_hourlyrollup (meter_id, bucket_start DESC);

CREATE TABLE analytics_dailyrollup (
    id BIGSERIAL PRIMARY KEY,
    meter_id BIGINT NOT NULL REFERENCES facilities_meter(id) ON DELETE CASCADE,
    rollup_date DATE NOT NULL,
    total_energy_kwh NUMERIC(14, 4) NOT NULL CHECK (total_energy_kwh >= 0),
    peak_demand_kw NUMERIC(12, 4) NOT NULL DEFAULT 0.0000,
    peak_timestamp TIMESTAMPTZ,
    off_peak_energy_kwh NUMERIC(14, 4) NOT NULL DEFAULT 0.0000,
    peak_energy_kwh NUMERIC(14, 4) NOT NULL DEFAULT 0.0000,
    avg_power_factor NUMERIC(4, 3) NOT NULL DEFAULT 1.000 CHECK (avg_power_factor BETWEEN 0.000 AND 1.000),
    reading_count INT NOT NULL CHECK (reading_count >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_daily_meter_date UNIQUE (meter_id, rollup_date)
);

CREATE INDEX idx_dailyrollup_date ON analytics_dailyrollup (rollup_date);
CREATE INDEX idx_dailyrollup_meter_date ON analytics_dailyrollup (meter_id, rollup_date DESC);

CREATE TABLE analytics_anomalyalert (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT NOT NULL REFERENCES facilities_facility(id) ON DELETE CASCADE,
    meter_id BIGINT NOT NULL REFERENCES facilities_meter(id) ON DELETE CASCADE,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    anomaly_type VARCHAR(50) NOT NULL CHECK (anomaly_type IN (
        'consumption_spike', 'low_power_factor', 'dg_grid_clash', 'meter_silent', 'demand_limit_breach'
    )),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    reason TEXT NOT NULL,
    baseline_value NUMERIC(14, 4),
    observed_value NUMERIC(14, 4),
    deviation_factor NUMERIC(8, 2),
    status VARCHAR(30) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'acknowledged', 'resolved', 'false_positive')),
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT NOT NULL DEFAULT ''
);

CREATE INDEX idx_anomaly_facility_status ON analytics_anomalyalert (facility_id, status);
CREATE INDEX idx_anomaly_detected_at ON analytics_anomalyalert (detected_at DESC);

-- ------------------------------------------------------------------------------
-- 5. Facility Benchmarking (Module M4)
-- ------------------------------------------------------------------------------

CREATE TABLE benchmarking_buildingbenchmark (
    id BIGSERIAL PRIMARY KEY,
    facility_type VARCHAR(50) NOT NULL UNIQUE CHECK (facility_type IN (
        'commercial_office', 'tech_park', 'hospital', 'retail_mall', 'hotel', 'educational_campus'
    )),
    median_eui_kwh_sqm_year NUMERIC(8, 2) NOT NULL CHECK (median_eui_kwh_sqm_year > 0),
    top_20_percentile_eui NUMERIC(8, 2) NOT NULL CHECK (top_20_percentile_eui > 0),
    bottom_20_percentile_eui NUMERIC(8, 2) NOT NULL CHECK (bottom_20_percentile_eui > 0),
    benchmark_standard VARCHAR(100) NOT NULL DEFAULT 'BEE India Star Rating Standards',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE benchmarking_facilitybenchmarkscore (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT NOT NULL REFERENCES facilities_facility(id) ON DELETE CASCADE,
    year INT NOT NULL CHECK (year >= 2020),
    annual_energy_kwh NUMERIC(16, 4) NOT NULL CHECK (annual_energy_kwh >= 0),
    calculated_eui_kwh_sqm_year NUMERIC(8, 2) NOT NULL CHECK (calculated_eui_kwh_sqm_year >= 0),
    national_percentile NUMERIC(5, 2) NOT NULL CHECK (national_percentile BETWEEN 0 AND 100),
    star_rating INT NOT NULL CHECK (star_rating BETWEEN 1 AND 5),
    computed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_facility_benchmark_year UNIQUE (facility_id, year)
);

-- ------------------------------------------------------------------------------
-- 6. Utility Tariffs, Bills, and Reconciliation (Module M5)
-- ------------------------------------------------------------------------------

CREATE TABLE billing_utilityprovider (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    state VARCHAR(100) NOT NULL,
    website VARCHAR(255) NOT NULL DEFAULT '',
    customer_care_phone VARCHAR(50) NOT NULL DEFAULT ''
);

CREATE TABLE billing_tariffstructure (
    id BIGSERIAL PRIMARY KEY,
    provider_id BIGINT NOT NULL REFERENCES billing_utilityprovider(id) ON DELETE CASCADE,
    tariff_code VARCHAR(50) NOT NULL UNIQUE,
    tariff_name VARCHAR(255) NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE,
    base_energy_rate_inr NUMERIC(10, 4) NOT NULL CHECK (base_energy_rate_inr >= 0),
    peak_hour_rate_inr NUMERIC(10, 4) NOT NULL CHECK (peak_hour_rate_inr >= 0),
    off_peak_rate_inr NUMERIC(10, 4) NOT NULL CHECK (off_peak_rate_inr >= 0),
    demand_charge_inr_per_kva NUMERIC(10, 2) NOT NULL CHECK (demand_charge_inr_per_kva >= 0),
    pf_penalty_threshold NUMERIC(4, 3) NOT NULL DEFAULT 0.900 CHECK (pf_penalty_threshold BETWEEN 0.500 AND 1.000),
    pf_penalty_rate_inr NUMERIC(10, 4) NOT NULL DEFAULT 0.5000 CHECK (pf_penalty_rate_inr >= 0),
    fixed_charge_monthly_inr NUMERIC(12, 2) NOT NULL DEFAULT 0.00
);

CREATE TABLE billing_utilitybill (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT NOT NULL REFERENCES facilities_facility(id) ON DELETE CASCADE,
    tariff_id BIGINT NOT NULL REFERENCES billing_tariffstructure(id) ON DELETE RESTRICT,
    bill_number VARCHAR(100) NOT NULL UNIQUE,
    billing_cycle_start DATE NOT NULL,
    billing_cycle_end DATE NOT NULL,
    due_date DATE NOT NULL,
    billed_kwh NUMERIC(14, 4) NOT NULL CHECK (billed_kwh >= 0),
    billed_max_demand_kva NUMERIC(10, 2) NOT NULL CHECK (billed_max_demand_kva >= 0),
    billed_amount_inr NUMERIC(14, 2) NOT NULL CHECK (billed_amount_inr >= 0),
    effective_cost_per_kwh_inr NUMERIC(10, 4) NOT NULL CHECK (effective_cost_per_kwh_inr >= 0),
    payment_status VARCHAR(30) NOT NULL DEFAULT 'unpaid' CHECK (payment_status IN ('unpaid', 'paid', 'disputed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_utilitybill_facility_cycle ON billing_utilitybill (facility_id, billing_cycle_start DESC);

CREATE TABLE billing_billreconciliation (
    id BIGSERIAL PRIMARY KEY,
    bill_id BIGINT NOT NULL UNIQUE REFERENCES billing_utilitybill(id) ON DELETE CASCADE,
    metered_kwh NUMERIC(14, 4) NOT NULL CHECK (metered_kwh >= 0),
    discrepancy_kwh NUMERIC(14, 4) NOT NULL,
    discrepancy_percentage NUMERIC(6, 2) NOT NULL,
    variance_cost_inr NUMERIC(14, 2) NOT NULL,
    reconciliation_status VARCHAR(40) NOT NULL CHECK (reconciliation_status IN (
        'verified_within_tolerance', 'variance_minor', 'variance_action_required'
    )),
    reconciled_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT NOT NULL DEFAULT ''
);

-- ------------------------------------------------------------------------------
-- 7. Energy Conservation Recommendations (Module M6)
-- ------------------------------------------------------------------------------

CREATE TABLE recommendations_ecmrule (
    id BIGSERIAL PRIMARY KEY,
    rule_code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN (
        'peak_shaving', 'power_factor_correction', 'hvac_scheduling', 'baseload_reduction', 'dg_displacement'
    )),
    description TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE recommendations_recommendation (
    id BIGSERIAL PRIMARY KEY,
    rule_id BIGINT NOT NULL REFERENCES recommendations_ecmrule(id) ON DELETE RESTRICT,
    facility_id BIGINT NOT NULL REFERENCES facilities_facility(id) ON DELETE CASCADE,
    meter_id BIGINT REFERENCES facilities_meter(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    action_plan TEXT NOT NULL,
    estimated_annual_kwh_savings NUMERIC(14, 4) NOT NULL CHECK (estimated_annual_kwh_savings >= 0),
    estimated_annual_savings_inr NUMERIC(14, 2) NOT NULL CHECK (estimated_annual_savings_inr >= 0),
    implementation_cost_inr NUMERIC(14, 2) NOT NULL DEFAULT 0.00 CHECK (implementation_cost_inr >= 0),
    estimated_payback_months NUMERIC(6, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(30) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'accepted', 'dismissed', 'implemented')),
    dismissal_reason TEXT NOT NULL DEFAULT '',
    generated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actioned_at TIMESTAMPTZ
);

CREATE INDEX idx_recommendation_facility_status ON recommendations_recommendation (facility_id, status);

-- ------------------------------------------------------------------------------
-- 8. Renewables and Carbon Emissions (Module M7)
-- ------------------------------------------------------------------------------

CREATE TABLE renewables_solarasset (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT NOT NULL REFERENCES facilities_facility(id) ON DELETE CASCADE,
    array_identifier VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    rated_capacity_kwp NUMERIC(10, 2) NOT NULL CHECK (rated_capacity_kwp > 0),
    panel_technology VARCHAR(100) NOT NULL DEFAULT 'Monocrystalline Silicon',
    inverter_model VARCHAR(100) NOT NULL DEFAULT 'Sungrow SG110CX',
    tilt_degrees NUMERIC(4, 1) NOT NULL DEFAULT 15.0 CHECK (tilt_degrees BETWEEN 0 AND 90),
    azimuth_degrees NUMERIC(5, 1) NOT NULL DEFAULT 180.0 CHECK (azimuth_degrees BETWEEN 0 AND 360),
    commissioned_date DATE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE renewables_solargenerationreading (
    id BIGSERIAL PRIMARY KEY,
    asset_id BIGINT NOT NULL REFERENCES renewables_solarasset(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    generation_kwh NUMERIC(12, 4) NOT NULL CHECK (generation_kwh >= 0),
    solar_irradiance_wm2 NUMERIC(8, 2) NOT NULL DEFAULT 0.00 CHECK (solar_irradiance_wm2 >= 0),
    ambient_temp_celsius NUMERIC(5, 2) NOT NULL DEFAULT 25.00,
    performance_ratio NUMERIC(5, 2) NOT NULL DEFAULT 0.80 CHECK (performance_ratio BETWEEN 0.00 AND 1.00),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_asset_timestamp UNIQUE (asset_id, timestamp)
);

CREATE INDEX idx_solargeneration_timestamp_brin ON renewables_solargenerationreading USING brin (timestamp);
CREATE INDEX idx_solargeneration_asset_time ON renewables_solargenerationreading (asset_id, timestamp DESC);

CREATE TABLE renewables_gridevent (
    id BIGSERIAL PRIMARY KEY,
    facility_id BIGINT NOT NULL REFERENCES facilities_facility(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN (
        'grid_outage', 'voltage_sag', 'frequency_aberration', 'dg_cut_in', 'dg_cut_out'
    )),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    duration_minutes NUMERIC(8, 2),
    fuel_consumed_litres NUMERIC(10, 2) DEFAULT 0.00 CHECK (fuel_consumed_litres >= 0),
    grid_restored BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE INDEX idx_gridevent_facility_time ON renewables_gridevent (facility_id, start_time DESC);

CREATE TABLE renewables_carbonemissionfactor (
    id BIGSERIAL PRIMARY KEY,
    energy_source VARCHAR(50) NOT NULL UNIQUE CHECK (energy_source IN (
        'grid', 'diesel_generator', 'solar', 'natural_gas'
    )),
    co2_kg_per_kwh NUMERIC(8, 4) NOT NULL CHECK (co2_kg_per_kwh >= 0),
    source_reference VARCHAR(255) NOT NULL DEFAULT 'Central Electricity Authority (CEA) India Baseline CO2 Database Version 19'
);
