-- ==============================================================================
-- GreenGrid Energy Management Information System (EMIS)
-- Comprehensive Indian Enterprise Seed Dataset (2024–2026)
-- Currencies in INR (₹), Timestamps in UTC, Parents before Children
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. Master Data: Users and Access Control (M8)
-- ------------------------------------------------------------------------------

-- Passwords hashed using Django default PBKDF2 SHA-256 placeholder (Password: 'GreenGrid@2026')
INSERT INTO users_customuser (id, email, password, first_name, last_name, role, phone, is_active, is_staff, is_superuser, date_joined) VALUES
(1, 'admin@greengrid.in', 'pbkdf2_sha256$600000$demohashplaceholder$Z9pXy7WqK3vLm8Rt1Ns4Pq6AbCdEfGhIjKlMnOpQrSt=', 'Vikram', 'Aditya', 'admin', '+919876543210', TRUE, TRUE, TRUE, '2024-01-01 00:00:00+00'),
(2, 'customer.blr@alphatech.in', 'pbkdf2_sha256$600000$demohashplaceholder$Z9pXy7WqK3vLm8Rt1Ns4Pq6AbCdEfGhIjKlMnOpQrSt=', 'Rajesh', 'Sharma', 'customer', '+919876543211', TRUE, FALSE, FALSE, '2024-01-05 04:30:00+00'),
(3, 'customer.pune@infocity.in', 'pbkdf2_sha256$600000$demohashplaceholder$Z9pXy7WqK3vLm8Rt1Ns4Pq6AbCdEfGhIjKlMnOpQrSt=', 'Pooja', 'Kulkarni', 'customer', '+919876543212', TRUE, FALSE, FALSE, '2024-01-10 05:00:00+00'),
(4, 'customer.delhi@dlfcyber.in', 'pbkdf2_sha256$600000$demohashplaceholder$Z9pXy7WqK3vLm8Rt1Ns4Pq6AbCdEfGhIjKlMnOpQrSt=', 'Amit', 'Verma', 'customer', '+919876543213', TRUE, FALSE, FALSE, '2024-01-15 05:30:00+00'),
(5, 'customer.mum@metrohub.in', 'pbkdf2_sha256$600000$demohashplaceholder$Z9pXy7WqK3vLm8Rt1Ns4Pq6AbCdEfGhIjKlMnOpQrSt=', 'Sanjay', 'Mehta', 'customer', '+919876543214', TRUE, FALSE, FALSE, '2024-02-01 06:00:00+00'),
(6, 'customer.hyd@hitower.in', 'pbkdf2_sha256$600000$demohashplaceholder$Z9pXy7WqK3vLm8Rt1Ns4Pq6AbCdEfGhIjKlMnOpQrSt=', 'Kavita', 'Reddy', 'customer', '+919876543215', TRUE, FALSE, FALSE, '2024-02-10 06:30:00+00'),
(7, 'customer.chn@tideltower.in', 'pbkdf2_sha256$600000$demohashplaceholder$Z9pXy7WqK3vLm8Rt1Ns4Pq6AbCdEfGhIjKlMnOpQrSt=', 'Anand', 'Subramaniam', 'customer', '+919876543216', TRUE, FALSE, FALSE, '2024-02-15 07:00:00+00'),
(8, 'engineer.blr@greengrid.in', 'pbkdf2_sha256$600000$demohashplaceholder$Z9pXy7WqK3vLm8Rt1Ns4Pq6AbCdEfGhIjKlMnOpQrSt=', 'Karthik', 'Nair', 'field_engineer', '+919876543217', TRUE, FALSE, FALSE, '2024-01-02 04:00:00+00'),
(9, 'engineer.pune@greengrid.in', 'pbkdf2_sha256$600000$demohashplaceholder$Z9pXy7WqK3vLm8Rt1Ns4Pq6AbCdEfGhIjKlMnOpQrSt=', 'Rohan', 'Deshmukh', 'field_engineer', '+919876543218', TRUE, FALSE, FALSE, '2024-01-03 04:30:00+00'),
(10, 'engineer.north@greengrid.in', 'pbkdf2_sha256$600000$demohashplaceholder$Z9pXy7WqK3vLm8Rt1Ns4Pq6AbCdEfGhIjKlMnOpQrSt=', 'Deepak', 'Yadav', 'field_engineer', '+919876543219', TRUE, FALSE, FALSE, '2024-01-04 05:00:00+00');

SELECT setval('users_customuser_id_seq', 10);

-- ------------------------------------------------------------------------------
-- 2. Master Data: Facilities & Buildings (M1)
-- ------------------------------------------------------------------------------

INSERT INTO facilities_facility (id, name, code, facility_type, gross_floor_area_sqm, operating_hours_per_week, address, city, state, pin_code, latitude, longitude, sanctioned_demand_kva) VALUES
(1, 'Alpha Tech Park', 'FAC-BLR-01', 'tech_park', 45000.00, 65.00, 'Outer Ring Road, Bellandur', 'Bengaluru', 'Karnataka', '560103', 12.927923, 77.681122, 2500.00),
(2, 'Infotech Cyber City', 'FAC-PUN-01', 'tech_park', 38000.00, 60.00, 'Phase 1, Hinjewadi IT Park', 'Pune', 'Maharashtra', '411057', 18.591272, 73.738907, 2000.00),
(3, 'DLF Cyber Horizon', 'FAC-GUR-01', 'commercial_office', 52000.00, 70.00, 'DLF Phase 2, Sector 24', 'Gurugram', 'Haryana', '122002', 28.490515, 77.089455, 3000.00),
(4, 'Mumbai Metro Business Hub', 'FAC-MUM-01', 'commercial_office', 32000.00, 55.00, 'Bandra Kurla Complex (BKC)', 'Mumbai', 'Maharashtra', '400051', 19.065718, 72.868378, 1800.00),
(5, 'HiTech Knowledge Park', 'FAC-HYD-01', 'tech_park', 60000.00, 70.00, 'HITEC City, Madhapur', 'Hyderabad', 'Telangana', '500081', 17.447412, 78.376230, 3200.00),
(6, 'Tidel Grand Towers', 'FAC-CHN-01', 'commercial_office', 28000.00, 50.00, 'Rajiv Gandhi Salai, Taramani', 'Chennai', 'Tamil Nadu', '600113', 12.989201, 80.245842, 1500.00),
(7, 'Noida Eco World Tower', 'FAC-NOI-01', 'commercial_office', 35000.00, 60.00, 'Sector 62, Institutional Area', 'Noida', 'Uttar Pradesh', '201309', 28.627981, 77.364853, 2100.00),
(8, 'City Care Multispeciality Hospital', 'FAC-BLR-02', 'hospital', 22000.00, 168.00, 'Old Airport Road, Kodihalli', 'Bengaluru', 'Karnataka', '560008', 12.960012, 77.649231, 1600.00),
(9, 'Phoenix Mall of the East', 'FAC-KOL-01', 'retail_mall', 48000.00, 84.00, 'EM Bypass, Salt Lake', 'Kolkata', 'West Bengal', '700098', 22.572645, 88.406830, 2800.00),
(10, 'Avenue Grand Luxury Hotel', 'FAC-AHM-01', 'hotel', 26000.00, 168.00, 'SG Highway, Bodakdev', 'Ahmedabad', 'Gujarat', '380054', 23.045812, 72.508392, 1750.00);

SELECT setval('facilities_facility_id_seq', 10);

-- User Facility Assignments
INSERT INTO facilities_userfacilityassignment (user_id, facility_id) VALUES
(2, 1), (3, 2), (4, 3), (5, 4), (6, 5), (7, 6),
(8, 1), (8, 8), -- Karthik assigned to Bengaluru facilities
(9, 2), (9, 4), -- Rohan assigned to Pune & Mumbai facilities
(10, 3), (10, 7); -- Deepak assigned to NCR facilities

-- Buildings
INSERT INTO facilities_building (id, facility_id, name, code, total_floors, floor_area_sqm) VALUES
(1, 1, 'Tower Alpha (North)', 'BLD-BLR-A', 12, 25000.00),
(2, 1, 'Tower Beta (South)', 'BLD-BLR-B', 10, 20000.00),
(3, 2, 'Synergy Block 1', 'BLD-PUN-01', 8, 20000.00),
(4, 2, 'Synergy Block 2', 'BLD-PUN-02', 8, 18000.00),
(5, 3, 'Tower One', 'BLD-GUR-01', 16, 30000.00),
(6, 3, 'Tower Two', 'BLD-GUR-02', 12, 22000.00),
(7, 4, 'Bandra Central Tower', 'BLD-MUM-01', 14, 32000.00),
(8, 5, 'Knowledge Block A', 'BLD-HYD-01', 18, 35000.00),
(9, 5, 'Knowledge Block B', 'BLD-HYD-02', 14, 25000.00),
(10, 6, 'Tidel Core Tower', 'BLD-CHN-01', 9, 28000.00),
(11, 8, 'Hospital Main Inpatient Wing', 'BLD-BLR-H1', 7, 15000.00),
(12, 8, 'Diagnostics and OT Wing', 'BLD-BLR-H2', 4, 7000.00);

SELECT setval('facilities_building_id_seq', 12);

-- Meters (Covering Grid, DG, Solar, HVAC, Lighting, IT, Pumps)
INSERT INTO facilities_meter (id, facility_id, building_id, meter_identifier, name, energy_source, load_category, meter_make, meter_model, ct_ratio, pt_ratio, physical_location, is_active) VALUES
(1, 1, 1, 'MTR-BLR-01-INC', 'Alpha Main Incomer 1 (BESCOM HT)', 'grid', 'main_incomer', 'Schneider Electric', 'EM6400NG', 400.00, 1.00, 'Main Substation Room 1', TRUE),
(2, 1, 1, 'MTR-BLR-01-HVAC', 'Alpha Central Chiller Plant', 'grid', 'hvac', 'Schneider Electric', 'PM5350', 200.00, 1.00, 'Basement 1 Plant Room', TRUE),
(3, 1, 1, 'MTR-BLR-01-IT', 'Alpha Data Center Server Floor', 'grid', 'it_infrastructure', 'Schneider Electric', 'PM8000', 100.00, 1.00, 'Floor 3 Server Hall', TRUE),
(4, 1, 1, 'MTR-BLR-01-LGT', 'Alpha Tower A Common Lighting', 'grid', 'lighting', 'L&T Electrical', 'ER300P', 50.00, 1.00, 'Riser Electrical Shaft 1', TRUE),
(5, 1, 1, 'MTR-BLR-01-PMP', 'Alpha Water & Fire Booster Pumps', 'grid', 'auxiliary_pumps', 'L&T Electrical', 'ER300P', 50.00, 1.00, 'Basement 2 Pump Room', TRUE),
(6, 1, 1, 'MTR-BLR-01-DG', 'Alpha 1500kVA Cummins DG Backup', 'diesel_generator', 'main_incomer', 'Deep Sea Electronics', 'DSE7320', 300.00, 1.00, 'DG Yard 1', TRUE),
(7, 1, 1, 'MTR-BLR-01-SOL', 'Alpha Rooftop Solar PV Inverter', 'solar', 'main_incomer', 'Sungrow', 'SG110CX', 100.00, 1.00, 'Rooftop Solar Substation', TRUE),
(8, 2, 3, 'MTR-PUN-01-INC', 'Pune Synergy Incomer (MSEDCL)', 'grid', 'main_incomer', 'Schneider Electric', 'EM6400NG', 350.00, 1.00, 'Primary Substation', TRUE),
(9, 2, 3, 'MTR-PUN-01-HVAC', 'Pune Chiller & AHU System', 'grid', 'hvac', 'Schneider Electric', 'PM5350', 150.00, 1.00, 'Basement HVAC Utility', TRUE),
(10, 2, 3, 'MTR-PUN-01-IT', 'Pune Enterprise IT & Labs', 'grid', 'it_infrastructure', 'Schneider Electric', 'PM8000', 80.00, 1.00, 'Block 1 Floor 2 Lab', TRUE),
(11, 3, 5, 'MTR-GUR-01-INC', 'Gurugram Cyber Incomer (DHBVN)', 'grid', 'main_incomer', 'Schneider Electric', 'EM6400NG', 500.00, 1.00, 'Main Receiving Substation', TRUE),
(12, 3, 5, 'MTR-GUR-01-HVAC', 'Gurugram Chiller Bank 1', 'grid', 'hvac', 'Schneider Electric', 'PM5350', 250.00, 1.00, 'HVAC Plant Room Ground', TRUE),
(13, 8, 11, 'MTR-BLR-HOS-INC', 'Hospital 24x7 Critical Incomer', 'grid', 'main_incomer', 'Schneider Electric', 'PM8000', 300.00, 1.00, 'Hospital Substation', TRUE),
(14, 8, 12, 'MTR-BLR-HOS-DG', 'Hospital Life-Support DG Set', 'diesel_generator', 'main_incomer', 'Deep Sea Electronics', 'DSE8610', 250.00, 1.00, 'Critical DG Bay', TRUE);

SELECT setval('facilities_meter_id_seq', 14);

-- DataSources (Hashed API Keys)
-- Pre-hashed SHA-256 strings for secure header authentication
INSERT INTO facilities_datasource (id, facility_id, name, key_prefix, key_hash, is_active, last_used_at, expires_at) VALUES
(1, 1, 'Alpha Tech IoT Gateway Primary', 'gg_live_blr01', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', TRUE, '2026-03-31 12:00:00+00', '2027-12-31 00:00:00+00'),
(2, 2, 'Pune Synergy Schneider Gateway', 'gg_live_pun01', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', TRUE, '2026-03-31 12:00:00+00', '2027-12-31 00:00:00+00'),
(3, 3, 'Gurugram Cyber Moxa Gateway', 'gg_live_gur01', 'b5a2c96250612366ac8b2731f8899b47e307a540c913f7de226e768d9a9e9ab0', TRUE, '2026-03-31 12:00:00+00', '2027-12-31 00:00:00+00'),
(4, 4, 'Mumbai Metro BACnet Logger', 'gg_live_mum01', '38b060a751ac96384cd9327eb1b1e36a21fdb71114be07434c0cc7bf63f6e1da', TRUE, '2026-03-31 12:00:00+00', '2027-12-31 00:00:00+00'),
(5, 5, 'Hyderabad HiTech Siemens S7 Gateway', 'gg_live_hyd01', '60303ae22b998861bce3b28f33eec1be758a213c86c93c076dbe9f508c36f8e1', TRUE, '2026-03-31 12:00:00+00', '2027-12-31 00:00:00+00'),
(6, 6, 'Chennai Tidel Advantech Logger', 'gg_live_chn01', 'fd5cb8035e3843ac9840da700030eb23d40e46c163b0ac4132acd345c08192f3', TRUE, '2026-03-31 12:00:00+00', '2027-12-31 00:00:00+00'),
(7, 8, 'Hospital IoT Secure Gateway', 'gg_live_blr02', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', TRUE, '2026-03-31 12:00:00+00', '2027-12-31 00:00:00+00'),
(8, 1, 'Alpha Simulator Automation Feed', 'gg_sim_blr01', '4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a', TRUE, '2026-03-31 12:00:00+00', '2027-12-31 00:00:00+00');

SELECT setval('facilities_datasource_id_seq', 8);

-- ------------------------------------------------------------------------------
-- 3. Master Data: Utility Providers & Tariffs (M5)
-- ------------------------------------------------------------------------------

INSERT INTO billing_utilityprovider (id, name, code, state, website, customer_care_phone) VALUES
(1, 'Bangalore Electricity Supply Company Limited', 'BESCOM', 'Karnataka', 'https://bescom.karnataka.gov.in', '1912'),
(2, 'Maharashtra State Electricity Distribution Co.', 'MSEDCL', 'Maharashtra', 'https://www.mahadiscom.in', '1800-212-3435'),
(3, 'Dakshin Haryana Bijli Vitran Nigam', 'DHBVN', 'Haryana', 'https://www.dhbvn.org.in', '1800-180-4334'),
(4, 'Tamil Nadu Generation and Distribution Corp.', 'TANGEDCO', 'Tamil Nadu', 'https://www.tangedco.gov.in', '94987 94987'),
(5, 'Telangana State Southern Power Distribution Co.', 'TSSPDCL', 'Telangana', 'https://www.tssouthernpower.com', '1912');

SELECT setval('billing_utilityprovider_id_seq', 5);

INSERT INTO billing_tariffstructure (id, provider_id, tariff_code, tariff_name, effective_from, base_energy_rate_inr, peak_hour_rate_inr, off_peak_rate_inr, demand_charge_inr_per_kva, pf_penalty_threshold, pf_penalty_rate_inr, fixed_charge_monthly_inr) VALUES
(1, 1, 'BESCOM-HT-2A', 'BESCOM HT-2(a) Commercial IT Parks', '2024-04-01', 7.4500, 9.5000, 6.2000, 310.00, 0.900, 0.5000, 15000.00),
(2, 2, 'MSEDCL-HT-COMM', 'MSEDCL HT-II Commercial & Tech Hubs', '2024-04-01', 8.1000, 10.2500, 6.8000, 360.00, 0.900, 0.6000, 20000.00),
(3, 3, 'DHBVN-HT-COMM', 'DHBVN Bulk Supply Commercial (Above 50kW)', '2024-04-01', 7.8000, 9.8000, 6.5000, 290.00, 0.900, 0.4500, 12000.00),
(4, 4, 'TANGEDCO-HT-3', 'TANGEDCO HT Tariff III Commercial Complex', '2024-04-01', 7.2000, 9.0000, 6.0000, 350.00, 0.900, 0.5500, 18000.00),
(5, 5, 'TSSPDCL-HT-2', 'TSSPDCL HT Category II Others & IT', '2024-04-01', 7.6000, 9.6000, 6.4000, 320.00, 0.900, 0.5000, 16000.00);

SELECT setval('billing_tariffstructure_id_seq', 5);

-- ------------------------------------------------------------------------------
-- 4. Master Data: Benchmarks, ECM Rules, and Carbon Factors (M4, M6, M7)
-- ------------------------------------------------------------------------------

INSERT INTO benchmarking_buildingbenchmark (id, facility_type, median_eui_kwh_sqm_year, top_20_percentile_eui, bottom_20_percentile_eui, benchmark_standard) VALUES
(1, 'tech_park', 185.00, 140.00, 235.00, 'Bureau of Energy Efficiency (BEE) IT Park Baseline 2024'),
(2, 'commercial_office', 165.00, 125.00, 210.00, 'BEE Commercial Buildings Energy Conservation Code (ECBC)'),
(3, 'hospital', 320.00, 250.00, 410.00, 'BEE Hospital 24x7 Continuous Healthcare Standard'),
(4, 'retail_mall', 280.00, 215.00, 360.00, 'BEE Retail Centers HVAC & Lighting Baseline'),
(5, 'hotel', 240.00, 180.00, 310.00, 'BEE Hospitality Industry Star Standard'),
(6, 'educational_campus', 95.00, 70.00, 130.00, 'BEE Academic & Educational Institutional Guideline');

SELECT setval('benchmarking_buildingbenchmark_id_seq', 6);

INSERT INTO recommendations_ecmrule (id, rule_code, name, category, description, is_active) VALUES
(1, 'ECM-PEAK-SHAVE', 'Peak Demand Shaving & Chiller Staggering', 'peak_shaving', 'Detects instantaneous demand approaching 90% of sanctioned kVA during peak tariff windows (18:00 - 22:00) and recommends pre-cooling and load shedding.', TRUE),
(2, 'ECM-PF-CORRECT', 'Low Power Factor Capacitor Bank Tuning', 'power_factor_correction', 'Flags average monthly power factor below 0.92 to prevent DISCOM low-PF penalties and recommends APFC capacitor bank maintenance.', TRUE),
(3, 'ECM-HVAC-SCHED', 'HVAC Night & Weekend Setback Optimization', 'hvac_scheduling', 'Identifies unnecessary chiller/AHU operation during non-occupancy hours (22:00 - 06:00) and recommends thermostat setbacks.', TRUE),
(4, 'ECM-BASELOAD-LEAK', 'After-Hours Base-Load Leakage Mitigation', 'baseload_reduction', 'Detects base-load consumption exceeding 25% of daytime average during weekends/holidays caused by uncurbed IT and lighting circuits.', TRUE),
(5, 'ECM-DG-OPTIM', 'DG Idle-Running & Grid Overlap Elimination', 'dg_displacement', 'Detects diesel generator operation while primary grid voltage is stable, preventing costly diesel generation at ₹28-35/kWh.', TRUE);

SELECT setval('recommendations_ecmrule_id_seq', 5);

INSERT INTO renewables_carbonemissionfactor (id, energy_source, co2_kg_per_kwh, source_reference) VALUES
(1, 'grid', 0.8200, 'Central Electricity Authority (CEA) India Baseline CO2 Database Version 19'),
(2, 'diesel_generator', 0.6800, 'Intergovernmental Panel on Climate Change (IPCC) Diesel Engine Stationary Combustion'),
(3, 'natural_gas', 0.4900, 'CEA Natural Gas Turbine Emission Factors 2024'),
(4, 'solar', 0.0000, 'Zero Direct Operational Scope 2 Greenhouse Emissions');

SELECT setval('renewables_carbonemissionfactor_id_seq', 4);

INSERT INTO renewables_solarasset (id, facility_id, array_identifier, name, rated_capacity_kwp, panel_technology, inverter_model, tilt_degrees, azimuth_degrees, commissioned_date, is_active) VALUES
(1, 1, 'SOL-BLR-01-ROOF', 'Alpha Tower A & B Rooftop Solar Array', 250.00, 'Monocrystalline Perc', 'Sungrow SG110CX (2x110kW)', 13.0, 180.0, '2024-01-15', TRUE),
(2, 2, 'SOL-PUN-01-CARPORT', 'Pune Synergy Solar Carport', 180.00, 'Bifacial Monocrystalline', 'ABB TRIO-50.0', 18.0, 180.0, '2024-02-01', TRUE),
(3, 3, 'SOL-GUR-01-ROOF', 'Gurugram Horizon Rooftop Array', 300.00, 'Monocrystalline Silicon', 'SMA Sunny Tripower CORE2', 28.0, 180.0, '2024-03-01', TRUE);

SELECT setval('renewables_solarasset_id_seq', 3);

-- ------------------------------------------------------------------------------
-- 5. Transaction Data: Ingestion Batches & Raw Readings (M1)
-- ------------------------------------------------------------------------------

INSERT INTO ingestion_batchlog (id, datasource_id, uploaded_by, batch_reference, source_type, total_records, accepted_records, duplicate_records, rejected_records, ingestion_duration_ms, created_at) VALUES
(1, 1, NULL, 'BATCH-20260330-001', 'api_bulk', 96, 96, 0, 0, 48, '2026-03-30 00:00:00+00'),
(2, 1, NULL, 'BATCH-20260330-002', 'api_bulk', 96, 96, 0, 0, 52, '2026-03-30 08:00:00+00'),
(3, 2, NULL, 'BATCH-20260330-003', 'api_bulk', 96, 96, 0, 0, 45, '2026-03-30 08:00:00+00'),
(4, NULL, 8, 'BATCH-CSV-20260330-BLR', 'csv_upload', 96, 94, 2, 0, 120, '2026-03-30 18:00:00+00');

SELECT setval('ingestion_batchlog_id_seq', 4);

-- 15-Minute Raw Readings (Master meter 1 - Alpha Main Incomer, Day 2026-03-30)
INSERT INTO ingestion_rawreading (meter_id, batch_id, timestamp, energy_kwh, active_power_kw, reactive_power_kvar, apparent_power_kva, voltage_v, current_a, power_factor, frequency_hz) VALUES
-- Normal Nighttime Baseload readings
(1, 1, '2026-03-30 00:00:00+00', 45.2500, 181.0000, 59.5000, 190.5200, 415.20, 265.10, 0.950, 49.98),
(1, 1, '2026-03-30 00:15:00+00', 44.8000, 179.2000, 58.9000, 188.6300, 415.50, 262.40, 0.950, 50.01),
(1, 1, '2026-03-30 00:30:00+00', 44.5000, 178.0000, 58.5000, 187.3600, 415.10, 260.70, 0.950, 50.00),
(1, 1, '2026-03-30 00:45:00+00', 44.1000, 176.4000, 58.0000, 185.6800, 415.30, 258.30, 0.950, 49.99),
(1, 1, '2026-03-30 01:00:00+00', 43.8000, 175.2000, 57.6000, 184.4200, 415.60, 256.50, 0.950, 50.02),
(1, 1, '2026-03-30 01:15:00+00', 43.5000, 174.0000, 57.2000, 183.1500, 415.40, 254.80, 0.950, 50.01),
(1, 1, '2026-03-30 01:30:00+00', 43.2000, 172.8000, 56.8000, 181.8900, 415.70, 253.00, 0.950, 50.00),
(1, 1, '2026-03-30 01:45:00+00', 43.0000, 172.0000, 56.5000, 181.0500, 415.50, 251.90, 0.950, 49.98),
(1, 1, '2026-03-30 02:00:00+00', 42.8000, 171.2000, 56.3000, 180.2100, 415.80, 250.70, 0.950, 50.03),
(1, 1, '2026-03-30 02:15:00+00', 42.5000, 170.0000, 55.9000, 178.9400, 415.90, 248.90, 0.950, 50.01),
(1, 1, '2026-03-30 02:30:00+00', 42.4000, 169.6000, 55.8000, 178.5200, 415.70, 248.30, 0.950, 50.00),
(1, 1, '2026-03-30 02:45:00+00', 42.2000, 168.8000, 55.5000, 177.6800, 416.00, 247.10, 0.950, 49.99),
(1, 1, '2026-03-30 03:00:00+00', 45.0000, 180.0000, 59.2000, 189.4700, 415.80, 263.50, 0.950, 50.00),
(1, 1, '2026-03-30 03:15:00+00', 65.5000, 262.0000, 86.1000, 275.7800, 415.20, 383.80, 0.950, 49.98),
-- Morning ramp up (09:00 AM IST = 03:30 UTC)
(1, 1, '2026-03-30 03:30:00+00', 125.0000, 500.0000, 164.3000, 526.3100, 414.50, 733.20, 0.950, 49.97),
(1, 1, '2026-03-30 03:45:00+00', 185.0000, 740.0000, 243.2000, 778.9400, 413.80, 1087.20, 0.950, 49.95),
(1, 2, '2026-03-30 04:00:00+00', 245.0000, 980.0000, 322.1000, 1031.5700, 413.00, 1442.30, 0.950, 49.94),
(1, 2, '2026-03-30 04:15:00+00', 310.0000, 1240.0000, 407.5000, 1305.2600, 412.50, 1827.10, 0.950, 49.92),
(1, 2, '2026-03-30 04:30:00+00', 360.0000, 1440.0000, 473.2000, 1515.7800, 412.00, 2124.20, 0.950, 49.91),
(1, 2, '2026-03-30 04:45:00+00', 390.0000, 1560.0000, 512.7000, 1642.1000, 411.80, 2302.50, 0.950, 49.90),
-- Daytime Business Hours Peak (11:00 AM - 04:00 PM IST = 05:30 - 10:30 UTC)
(1, 2, '2026-03-30 05:00:00+00', 410.0000, 1640.0000, 538.9000, 1726.3100, 411.50, 2422.30, 0.950, 49.90),
(1, 2, '2026-03-30 05:15:00+00', 425.0000, 1700.0000, 558.7000, 1789.4700, 411.20, 2513.10, 0.950, 49.89),
(1, 2, '2026-03-30 05:30:00+00', 430.0000, 1720.0000, 565.2000, 1810.5200, 411.00, 2544.20, 0.950, 49.89),
(1, 2, '2026-03-30 05:45:00+00', 435.0000, 1740.0000, 571.8000, 1831.5700, 410.90, 2574.60, 0.950, 49.88),
(1, 2, '2026-03-30 06:00:00+00', 440.0000, 1760.0000, 578.4000, 1852.6300, 410.80, 2605.00, 0.950, 49.88),
(1, 2, '2026-03-30 06:15:00+00', 445.0000, 1780.0000, 584.9000, 1873.6800, 410.70, 2635.40, 0.950, 49.87),
(1, 2, '2026-03-30 06:30:00+00', 442.0000, 1768.0000, 581.0000, 1861.0500, 410.80, 2617.20, 0.950, 49.88),
(1, 2, '2026-03-30 06:45:00+00', 438.0000, 1752.0000, 575.7000, 1844.2100, 411.00, 2592.80, 0.950, 49.89),
(1, 2, '2026-03-30 07:00:00+00', 435.0000, 1740.0000, 571.8000, 1831.5700, 411.20, 2573.40, 0.950, 49.90),
(1, 2, '2026-03-30 07:15:00+00', 430.0000, 1720.0000, 565.2000, 1810.5200, 411.40, 2542.50, 0.950, 49.91),
(1, 2, '2026-03-30 07:30:00+00', 428.0000, 1712.0000, 562.6000, 1802.1000, 411.50, 2530.10, 0.950, 49.91),
(1, 2, '2026-03-30 07:45:00+00', 425.0000, 1700.0000, 558.7000, 1789.4700, 411.60, 2511.80, 0.950, 49.92),
-- Submeter 2: HVAC Chiller Readings corresponding to same periods
(2, 1, '2026-03-30 00:00:00+00', 12.5000, 50.0000, 16.4000, 52.6300, 415.00, 73.20, 0.950, 50.00),
(2, 1, '2026-03-30 00:15:00+00', 12.0000, 48.0000, 15.8000, 50.5200, 415.20, 70.20, 0.950, 50.00),
(2, 1, '2026-03-30 04:00:00+00', 110.0000, 440.0000, 144.6000, 463.1500, 413.00, 647.10, 0.950, 49.94),
(2, 2, '2026-03-30 05:00:00+00', 195.0000, 780.0000, 256.3000, 821.0500, 411.50, 1151.70, 0.950, 49.90),
(2, 2, '2026-03-30 06:00:00+00', 210.0000, 840.0000, 276.1000, 884.2100, 410.80, 1243.30, 0.950, 49.88),
-- Submeter 3: IT Infrastructure Server Hall Readings (Flat steady load)
(3, 1, '2026-03-30 00:00:00+00', 22.0000, 88.0000, 18.0000, 89.8200, 415.00, 125.00, 0.980, 50.00),
(3, 1, '2026-03-30 02:00:00+00', 22.1000, 88.4000, 18.1000, 90.2300, 415.20, 125.50, 0.980, 50.01),
(3, 2, '2026-03-30 05:00:00+00', 24.5000, 98.0000, 20.1000, 100.0500, 411.50, 140.20, 0.980, 49.90),
(3, 2, '2026-03-30 07:00:00+00', 24.2000, 96.8000, 19.8000, 98.8000, 411.20, 138.50, 0.980, 49.90),
-- Submeter 4: Lighting (Daylight harvested, night low)
(4, 1, '2026-03-30 00:00:00+00', 5.0000, 20.0000, 4.1000, 20.4100, 415.00, 28.40, 0.980, 50.00),
(4, 2, '2026-03-30 05:00:00+00', 14.0000, 56.0000, 11.5000, 57.1700, 411.50, 80.10, 0.980, 49.90),
-- Submeter 7: Solar PV Generation Reading (Zero at night, peak at noon)
(7, 1, '2026-03-30 00:00:00+00', 0.0000, 0.0000, 0.0000, 0.0000, 415.00, 0.00, 1.000, 50.00),
(7, 2, '2026-03-30 06:30:00+00', 55.0000, 220.0000, 0.0000, 220.0000, 410.80, 309.40, 1.000, 49.88),
(7, 2, '2026-03-30 07:00:00+00', 58.0000, 232.0000, 0.0000, 232.0000, 411.20, 326.10, 1.000, 49.90);

-- ==============================================================================
-- 5 SPECIFIC EDGE-CASE ROWS (Documented & Tagged)
-- ==============================================================================

-- Edge Case 1: Zero energy reading during total facility maintenance / complete blackout
INSERT INTO ingestion_rawreading (meter_id, batch_id, timestamp, energy_kwh, active_power_kw, reactive_power_kvar, apparent_power_kva, voltage_v, current_a, power_factor, frequency_hz)
VALUES (1, 1, '2026-03-29 02:00:00+00', 0.0000, 0.0000, 0.0000, 0.0000, 0.00, 0.00, 0.000, 50.00);

-- Edge Case 2: Extreme peak demand spike (> 3.5x normal baseline demand due to chiller motor startup locked-rotor failure)
INSERT INTO ingestion_rawreading (meter_id, batch_id, timestamp, energy_kwh, active_power_kw, reactive_power_kvar, apparent_power_kva, voltage_v, current_a, power_factor, frequency_hz)
VALUES (2, 2, '2026-03-28 14:15:00+00', 780.0000, 3120.0000, 2340.0000, 3900.0000, 385.00, 5847.00, 0.800, 48.90);

-- Edge Case 3: Degraded power factor (< 0.650) triggering maximum utility tariff penalty and APFC bank fault
INSERT INTO ingestion_rawreading (meter_id, batch_id, timestamp, energy_kwh, active_power_kw, reactive_power_kvar, apparent_power_kva, voltage_v, current_a, power_factor, frequency_hz)
VALUES (5, 1, '2026-03-27 18:30:00+00', 35.0000, 140.0000, 170.8000, 220.8000, 410.00, 311.00, 0.634, 49.92);

-- Edge Case 4: Critical DG-Grid clash (Diesel generator running simultaneously with active grid power)
INSERT INTO ingestion_rawreading (meter_id, batch_id, timestamp, energy_kwh, active_power_kw, reactive_power_kvar, apparent_power_kva, voltage_v, current_a, power_factor, frequency_hz)
VALUES (6, 2, '2026-03-26 10:00:00+00', 180.0000, 720.0000, 240.0000, 758.9000, 414.00, 1057.00, 0.948, 50.10);

-- Edge Case 5: Telemetry with near-unity frequency anomaly at permissible safety margin
INSERT INTO ingestion_rawreading (meter_id, batch_id, timestamp, energy_kwh, active_power_kw, reactive_power_kvar, apparent_power_kva, voltage_v, current_a, power_factor, frequency_hz)
VALUES (3, 1, '2026-03-25 04:00:00+00', 23.0000, 92.0000, 18.0000, 93.7400, 438.00, 123.50, 0.981, 52.45);

-- ------------------------------------------------------------------------------
-- 6. Transaction Data: Hourly Rollups (M2)
-- ------------------------------------------------------------------------------

INSERT INTO analytics_hourlyrollup (meter_id, bucket_start, total_energy_kwh, peak_demand_kw, min_demand_kw, avg_power_factor, reading_count) VALUES
(1, '2026-03-30 00:00:00+00', 178.6500, 181.0000, 176.4000, 0.950, 4),
(1, '2026-03-30 01:00:00+00', 174.5000, 175.2000, 172.0000, 0.950, 4),
(1, '2026-03-30 02:00:00+00', 169.9000, 171.2000, 168.8000, 0.950, 4),
(1, '2026-03-30 03:00:00+00', 420.5000, 740.0000, 180.0000, 0.950, 4),
(1, '2026-03-30 04:00:00+00', 1305.0000, 1560.0000, 980.0000, 0.950, 4),
(1, '2026-03-30 05:00:00+00', 1710.0000, 1740.0000, 1640.0000, 0.950, 4),
(1, '2026-03-30 06:00:00+00', 1765.0000, 1780.0000, 1752.0000, 0.950, 4),
(1, '2026-03-30 07:00:00+00', 1718.0000, 1740.0000, 1700.0000, 0.950, 4),
(2, '2026-03-30 00:00:00+00', 49.0000, 50.0000, 48.0000, 0.950, 4),
(2, '2026-03-30 04:00:00+00', 440.0000, 460.0000, 420.0000, 0.950, 4),
(2, '2026-03-30 05:00:00+00', 780.0000, 800.0000, 760.0000, 0.950, 4),
(2, '2026-03-30 06:00:00+00', 840.0000, 860.0000, 820.0000, 0.950, 4),
(3, '2026-03-30 00:00:00+00', 88.2000, 88.5000, 87.8000, 0.980, 4),
(3, '2026-03-30 05:00:00+00', 97.6000, 98.2000, 96.9000, 0.980, 4),
(7, '2026-03-30 06:00:00+00', 215.0000, 230.0000, 195.0000, 1.000, 4),
(7, '2026-03-30 07:00:00+00', 232.0000, 240.0000, 220.0000, 1.000, 4);

-- ------------------------------------------------------------------------------
-- 7. Transaction Data: Daily Rollups (M2)
-- ------------------------------------------------------------------------------

INSERT INTO analytics_dailyrollup (meter_id, rollup_date, total_energy_kwh, peak_demand_kw, peak_timestamp, off_peak_energy_kwh, peak_energy_kwh, avg_power_factor, reading_count) VALUES
(1, '2026-03-29', 18450.0000, 1680.0000, '2026-03-29 06:15:00+00', 6200.0000, 12250.0000, 0.951, 96),
(1, '2026-03-28', 19120.0000, 1720.0000, '2026-03-28 05:45:00+00', 6450.0000, 12670.0000, 0.949, 96),
(1, '2026-03-27', 24650.0000, 1850.0000, '2026-03-27 06:30:00+00', 7100.0000, 17550.0000, 0.948, 96),
(2, '2026-03-29', 7200.0000, 820.0000, '2026-03-29 07:00:00+00', 1800.0000, 5400.0000, 0.950, 96),
(2, '2026-03-28', 7500.0000, 840.0000, '2026-03-28 06:45:00+00', 1900.0000, 5600.0000, 0.950, 96),
(3, '2026-03-29', 2210.0000, 98.0000, '2026-03-29 09:30:00+00', 980.0000, 1230.0000, 0.980, 96),
(7, '2026-03-29', 1420.0000, 245.0000, '2026-03-29 07:15:00+00', 0.0000, 1420.0000, 1.000, 96);

-- ------------------------------------------------------------------------------
-- 8. Transaction Data: Anomaly Alerts (M2)
-- ------------------------------------------------------------------------------

INSERT INTO analytics_anomalyalert (id, facility_id, meter_id, detected_at, anomaly_type, severity, reason, baseline_value, observed_value, deviation_factor, status) VALUES
(1, 1, 2, '2026-03-28 14:15:00+00', 'consumption_spike', 'critical', 'Instantaneous demand breached 3120 kW (>3.5x baseline) during locked-rotor chiller event.', 780.0000, 3120.0000, 4.00, 'resolved'),
(2, 1, 5, '2026-03-27 18:30:00+00', 'low_power_factor', 'high', 'Observed power factor dropped to 0.634 (below DISCOM threshold 0.900) on water booster pumps.', 0.9500, 0.6340, 0.67, 'acknowledged'),
(3, 1, 6, '2026-03-26 10:00:00+00', 'dg_grid_clash', 'critical', 'Diesel generator running while primary grid incomer voltage is nominal (414V). Potential fuel wastage.', 0.0000, 720.0000, 99.99, 'resolved'),
(4, 2, 8, '2026-03-25 11:00:00+00', 'consumption_spike', 'medium', 'Energy consumption 1.45x higher than 4-week median for Thursday 11:00 AM.', 1200.0000, 1740.0000, 1.45, 'open'),
(5, 3, 11, '2026-03-24 22:00:00+00', 'meter_silent', 'high', 'No readings received from Gurugram Main Incomer for > 2 hours (120 minutes). Gateway disconnected.', 1.0000, 0.0000, 0.00, 'resolved');

SELECT setval('analytics_anomalyalert_id_seq', 5);

-- ------------------------------------------------------------------------------
-- 9. Transaction Data: Utility Bills & Reconciliation (M5)
-- ------------------------------------------------------------------------------

INSERT INTO billing_utilitybill (id, facility_id, tariff_id, bill_number, billing_cycle_start, billing_cycle_end, due_date, billed_kwh, billed_max_demand_kva, billed_amount_inr, effective_cost_per_kwh_inr, payment_status) VALUES
(1, 1, 1, 'BILL-BESCOM-2026-01', '2026-01-01', '2026-01-31', '2026-02-15', 585000.00, 2150.00, 5218750.00, 8.9209, 'paid'),
(2, 1, 1, 'BILL-BESCOM-2026-02', '2026-02-01', '2026-02-28', '2026-03-15', 542000.00, 2080.00, 4839800.00, 8.9295, 'paid'),
(3, 1, 1, 'BILL-BESCOM-2026-03', '2026-03-01', '2026-03-31', '2026-04-15', 612000.00, 2280.00, 5472400.00, 8.9418, 'unpaid'),
(4, 2, 2, 'BILL-MSEDCL-2026-01', '2026-01-01', '2026-01-31', '2026-02-18', 475000.00, 1750.00, 4615000.00, 9.7158, 'paid'),
(5, 3, 3, 'BILL-DHBVN-2026-01', '2026-01-01', '2026-01-31', '2026-02-20', 690000.00, 2600.00, 6288000.00, 9.1130, 'paid');

SELECT setval('billing_utilitybill_id_seq', 5);

INSERT INTO billing_billreconciliation (id, bill_id, metered_kwh, discrepancy_kwh, discrepancy_percentage, variance_cost_inr, reconciliation_status, notes) VALUES
(1, 1, 582450.0000, 2550.0000, 0.44, 22748.00, 'verified_within_tolerance', 'Metered data matches utility bill within 0.5% standard transformer loss tolerance.'),
(2, 2, 539800.0000, 2200.0000, 0.41, 19645.00, 'verified_within_tolerance', 'Reconciled successfully.'),
(3, 3, 595200.0000, 16800.0000, 2.75, 150222.00, 'variance_action_required', 'Significant variance (>2.5%) detected between utility bill and internal check meter. Audit dispute raised with BESCOM.');

SELECT setval('billing_billreconciliation_id_seq', 3);

-- ------------------------------------------------------------------------------
-- 10. Transaction Data: Benchmarking Scores & Recommendations (M4, M6)
-- ------------------------------------------------------------------------------

INSERT INTO benchmarking_facilitybenchmarkscore (facility_id, year, annual_energy_kwh, calculated_eui_kwh_sqm_year, national_percentile, star_rating) VALUES
(1, 2025, 7120000.00, 158.22, 78.50, 4),
(2, 2025, 5980000.00, 157.37, 79.20, 4),
(3, 2025, 9650000.00, 185.58, 52.00, 3),
(4, 2025, 5100000.00, 159.38, 77.00, 4),
(8, 2025, 6800000.00, 309.09, 68.00, 3);

INSERT INTO recommendations_recommendation (id, rule_id, facility_id, meter_id, title, description, action_plan, estimated_annual_kwh_savings, estimated_annual_savings_inr, implementation_cost_inr, estimated_payback_months, status) VALUES
(1, 1, 1, 2, 'Pre-cooling & Chiller Setback during BESCOM Peak Hours (18:00 - 22:00)', 'Alpha Tech Park experiences average demand of 1650 kVA during evening peak tariff hours billed at ₹9.50/kWh.', 'Pre-cool building to 22.5°C between 15:00 and 17:30, then raise thermostat to 25.0°C between 18:00 and 21:00.', 115000.0000, 1092500.00, 50000.00, 0.55, 'active'),
(2, 2, 1, 5, 'APFC Capacitor Bank Servicing on Basement Water Booster Pumps', 'Power factor on pump meter MTR-BLR-01-PMP drops to 0.634, risking BESCOM PF penalty surcharge.', 'Replace degraded 25 kVAR capacitor stages in the motor control center panel.', 18000.0000, 185000.00, 45000.00, 2.92, 'accepted'),
(3, 3, 2, 9, 'Weekend AHU Shutdown Optimization for Pune Synergy Blocks', 'AHUs in unoccupied wings run continuously at 40% load on Saturdays and Sundays.', 'Configure automated BMS setback schedule to shut down AHUs on non-working floors on weekends.', 62000.0000, 502200.00, 15000.00, 0.36, 'active'),
(4, 5, 1, 6, 'DG Synchronization Interlock Rectification', '1500kVA DG was recorded running for 4.5 hours in March while grid power was operational.', 'Inspect ATS (Automatic Transfer Switch) feedback contactor to ensure immediate generator shutdown upon grid restoration.', 24000.0000, 480000.00, 20000.00, 0.50, 'accepted');

SELECT setval('recommendations_recommendation_id_seq', 4);

-- ------------------------------------------------------------------------------
-- 11. Transaction Data: Solar Generation & Grid Outages (M7)
-- ------------------------------------------------------------------------------

INSERT INTO renewables_solargenerationreading (asset_id, timestamp, generation_kwh, solar_irradiance_wm2, ambient_temp_celsius, performance_ratio) VALUES
(1, '2026-03-30 05:30:00+00', 42.5000, 680.00, 31.50, 0.82),
(1, '2026-03-30 06:00:00+00', 52.0000, 810.00, 33.00, 0.81),
(1, '2026-03-30 06:30:00+00', 55.0000, 890.00, 34.20, 0.80),
(1, '2026-03-30 07:00:00+00', 58.0000, 940.00, 35.00, 0.79),
(1, '2026-03-30 07:30:00+00', 56.5000, 920.00, 35.50, 0.79),
(1, '2026-03-30 08:00:00+00', 51.0000, 830.00, 35.20, 0.80),
(2, '2026-03-30 06:30:00+00', 38.0000, 850.00, 33.00, 0.83),
(2, '2026-03-30 07:00:00+00', 41.5000, 910.00, 34.00, 0.82);

INSERT INTO renewables_gridevent (facility_id, event_type, start_time, end_time, duration_minutes, fuel_consumed_litres, grid_restored, notes) VALUES
(1, 'grid_outage', '2026-03-24 08:30:00+00', '2026-03-24 10:15:00+00', 105.00, 320.00, TRUE, 'BESCOM feeder trip due to roadside transformer cable breakdown. DG 1 took over load within 12 seconds.'),
(1, 'voltage_sag', '2026-03-22 14:10:00+00', '2026-03-22 14:14:00+00', 4.00, 0.00, TRUE, 'Grid voltage dipped to 365V during industrial switching. Chiller VFDs rode through without tripping.'),
(2, 'grid_outage', '2026-03-18 11:00:00+00', '2026-03-18 12:45:00+00', 105.00, 260.00, TRUE, 'MSEDCL scheduled maintenance power outage in Hinjewadi Phase 1.');
