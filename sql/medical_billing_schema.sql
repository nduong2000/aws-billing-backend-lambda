-- Drop tables if they exist (optional, for clean setup)
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS claim_items;
DROP TABLE IF EXISTS claims;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS services;
DROP TABLE IF EXISTS providers;
DROP TABLE IF EXISTS patients;

-- Create patients table
CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    address VARCHAR(255),
    phone_number VARCHAR(20),
    insurance_provider VARCHAR(100),
    insurance_policy_number VARCHAR(100)
);

-- Create providers table
CREATE TABLE providers (
    provider_id SERIAL PRIMARY KEY,
    provider_name VARCHAR(150) NOT NULL,
    npi_number VARCHAR(10) UNIQUE NOT NULL, -- National Provider Identifier
    specialty VARCHAR(100),
    address VARCHAR(255),
    phone_number VARCHAR(20)
);

-- Create services table
CREATE TABLE services (
    service_id SERIAL PRIMARY KEY,
    cpt_code VARCHAR(5) UNIQUE NOT NULL, -- Current Procedural Terminology
    description VARCHAR(255) NOT NULL,
    standard_charge DECIMAL(10, 2) NOT NULL CHECK (standard_charge >= 0)
);

-- Create appointments table
CREATE TABLE appointments (
    appointment_id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL REFERENCES patients(patient_id),
    provider_id INT NOT NULL REFERENCES providers(provider_id),
    appointment_date TIMESTAMP NOT NULL,
    reason_for_visit TEXT
);

-- Create claims table
CREATE TABLE claims (
    claim_id SERIAL PRIMARY KEY,
    patient_id INT NOT NULL REFERENCES patients(patient_id),
    provider_id INT NOT NULL REFERENCES providers(provider_id),
    claim_date DATE NOT NULL,
    total_charge DECIMAL(10, 2) NOT NULL CHECK (total_charge >= 0),
    insurance_paid DECIMAL(10, 2) DEFAULT 0 CHECK (insurance_paid >= 0),
    patient_paid DECIMAL(10, 2) DEFAULT 0 CHECK (patient_paid >= 0),
    status VARCHAR(50) NOT NULL CHECK (status IN ('Submitted', 'Paid', 'Denied', 'Pending', 'Partial')),
    fraud_score DECIMAL(5, 2) NULL -- Added fraud score column
);

-- Create claim_items table (linking claims to services)
CREATE TABLE claim_items (
    claim_item_id SERIAL PRIMARY KEY,
    claim_id INT NOT NULL REFERENCES claims(claim_id) ON DELETE CASCADE,
    service_id INT NOT NULL REFERENCES services(service_id),
    charge_amount DECIMAL(10, 2) NOT NULL CHECK (charge_amount >= 0)
);

-- Create payments table
CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    claim_id INT NOT NULL REFERENCES claims(claim_id),
    payment_date DATE NOT NULL,
    amount DECIMAL(10, 2) NOT NULL CHECK (amount > 0),
    payment_source VARCHAR(50) NOT NULL CHECK (payment_source IN ('Insurance', 'Patient')),
    reference_number VARCHAR(100) -- e.g., check number, transaction ID
);

-- --- Sample Data Insertion ---

-- Sample Patients
INSERT INTO patients (first_name, last_name, date_of_birth, address, phone_number, insurance_provider, insurance_policy_number) VALUES
('John', 'Doe', '1985-03-15', '123 Main St, Anytown, USA', '555-1234', 'BlueCross', 'BCBS123456789'),
('Jane', 'Smith', '1992-07-22', '456 Oak Ave, Anytown, USA', '555-5678', 'Aetna', 'AETNA987654321'),
('Robert', 'Johnson', '1978-11-01', '789 Pine Ln, Anytown, USA', '555-9101', 'Cigna', 'CIGNA112233445'),
('Maria', 'Garcia', '2001-01-30', '101 Maple Dr, Anytown, USA', '555-1121', 'UnitedHealthcare', 'UHC556677889'),
('David', 'Miller', '1965-09-10', '202 Birch Rd, Anytown, USA', '555-3141', 'BlueCross', 'BCBS998877665');

-- Sample Providers
INSERT INTO providers (provider_name, npi_number, specialty, address, phone_number) VALUES
('Dr. Alice Brown', '1234567890', 'Cardiology', '1 Medical Plaza, Anytown, USA', '555-1000'),
('Dr. Bob White', '0987654321', 'Pediatrics', '2 Health Way, Anytown, USA', '555-2000'),
('Anytown Clinic', '1122334455', 'General Practice', '3 Wellness Blvd, Anytown, USA', '555-3000');

-- Sample Services
INSERT INTO services (cpt_code, description, standard_charge) VALUES
('99213', 'Office visit, established patient, low complexity', 125.00),
('99214', 'Office visit, established patient, moderate complexity', 175.00),
('99203', 'Office visit, new patient, low complexity', 150.00),
('99395', 'Periodic preventive medicine Px; 18-39 years', 200.00),
('90686', 'Flu vaccine, quadrivalent, intramuscular', 45.00),
('80053', 'Comprehensive metabolic panel', 85.00),
('85025', 'Complete blood count (CBC), automated', 60.00),
('93000', 'Electrocardiogram (ECG), routine', 75.00);

-- Sample Appointments (Updated to March/April 2025)
INSERT INTO appointments (patient_id, provider_id, appointment_date, reason_for_visit) VALUES
(1, 1, '2025-03-05 10:00:00', 'Follow-up visit for hypertension'),
(2, 3, '2025-03-08 14:30:00', 'Annual physical'),
(3, 1, '2025-03-12 09:15:00', 'Chest pain evaluation'),
(4, 2, '2025-03-15 11:00:00', 'Well-child check-up'),
(1, 3, '2025-03-20 16:00:00', 'Flu shot'),
(5, 1, '2025-03-25 08:45:00', 'Consultation for arrhythmia'),
(2, 3, '2025-04-02 13:00:00', 'Lab work follow-up'),
(4, 2, '2025-04-10 15:15:00', 'Sick visit - fever'),
(3, 3, '2025-04-18 10:30:00', 'General check-up');

-- Sample Claims (Based on Appointments, updated dates)
-- Claim 1 (John Doe, Dr. Brown, March 5th)
INSERT INTO claims (patient_id, provider_id, claim_date, total_charge, status) VALUES
(1, 1, '2025-03-05', 125.00, 'Submitted');
INSERT INTO claim_items (claim_id, service_id, charge_amount) VALUES
(1, 1, 125.00); -- 99213

-- Claim 2 (Jane Smith, Anytown Clinic, March 8th)
INSERT INTO claims (patient_id, provider_id, claim_date, total_charge, status) VALUES
(2, 3, '2025-03-08', 200.00, 'Submitted');
INSERT INTO claim_items (claim_id, service_id, charge_amount) VALUES
(2, 4, 200.00); -- 99395

-- Claim 3 (Robert Johnson, Dr. Brown, March 12th)
INSERT INTO claims (patient_id, provider_id, claim_date, total_charge, status) VALUES
(3, 1, '2025-03-12', 250.00, 'Pending'); -- Office visit + ECG
INSERT INTO claim_items (claim_id, service_id, charge_amount) VALUES
(3, 2, 175.00), -- 99214
(3, 8, 75.00);  -- 93000

-- Claim 4 (Maria Garcia, Dr. White, March 15th)
INSERT INTO claims (patient_id, provider_id, claim_date, total_charge, status) VALUES
(4, 2, '2025-03-15', 150.00, 'Submitted');
INSERT INTO claim_items (claim_id, service_id, charge_amount) VALUES
(4, 3, 150.00); -- 99203 (Assuming new patient visit)

-- Claim 5 (John Doe, Anytown Clinic, March 20th)
INSERT INTO claims (patient_id, provider_id, claim_date, total_charge, status) VALUES
(1, 3, '2025-03-20', 45.00, 'Paid');
INSERT INTO claim_items (claim_id, service_id, charge_amount) VALUES
(5, 5, 45.00); -- 90686

-- Claim 6 (David Miller, Dr. Brown, March 25th)
INSERT INTO claims (patient_id, provider_id, claim_date, total_charge, status) VALUES
(5, 1, '2025-03-25', 175.00, 'Submitted');
INSERT INTO claim_items (claim_id, service_id, charge_amount) VALUES
(6, 2, 175.00); -- 99214

-- Claim 7 (Jane Smith, Anytown Clinic, April 2nd)
INSERT INTO claims (patient_id, provider_id, claim_date, total_charge, status) VALUES
(2, 3, '2025-04-02', 145.00, 'Partial'); -- Lab work (Metabolic + CBC)
INSERT INTO claim_items (claim_id, service_id, charge_amount) VALUES
(7, 6, 85.00),  -- 80053
(7, 7, 60.00);  -- 85025

-- Claim 8 (Maria Garcia, Dr. White, April 10th)
INSERT INTO claims (patient_id, provider_id, claim_date, total_charge, status) VALUES
(4, 2, '2025-04-10', 125.00, 'Denied');
INSERT INTO claim_items (claim_id, service_id, charge_amount) VALUES
(8, 1, 125.00); -- 99213

-- Claim 9 (Robert Johnson, Anytown Clinic, April 18th)
INSERT INTO claims (patient_id, provider_id, claim_date, total_charge, status) VALUES
(3, 3, '2025-04-18', 125.00, 'Submitted');
INSERT INTO claim_items (claim_id, service_id, charge_amount) VALUES
(9, 1, 125.00); -- 99213


-- Sample Payments (Assume some payments received in late March / April 2025)
-- Payment for Claim 1 (Insurance)
UPDATE claims SET insurance_paid = 100.00, status = 'Partial' WHERE claim_id = 1;
INSERT INTO payments (claim_id, payment_date, amount, payment_source, reference_number) VALUES
(1, '2025-03-20', 100.00, 'Insurance', 'BCBS_PAY_123');

-- Payment for Claim 1 (Patient - remaining balance)
UPDATE claims SET patient_paid = 25.00, status = 'Paid' WHERE claim_id = 1;
INSERT INTO payments (claim_id, payment_date, amount, payment_source, reference_number) VALUES
(1, '2025-04-01', 25.00, 'Patient', 'CHECK_456');

-- Payment for Claim 2 (Insurance)
UPDATE claims SET insurance_paid = 180.00, status = 'Partial' WHERE claim_id = 2;
INSERT INTO payments (claim_id, payment_date, amount, payment_source, reference_number) VALUES
(2, '2025-03-25', 180.00, 'Insurance', 'AETNA_PAY_789');
-- Note: Patient balance remaining

-- Payment for Claim 5 (Insurance - Paid in Full)
UPDATE claims SET insurance_paid = 45.00, status = 'Paid' WHERE claim_id = 5;
INSERT INTO payments (claim_id, payment_date, amount, payment_source, reference_number) VALUES
(5, '2025-03-28', 45.00, 'Insurance', 'BCBS_PAY_101');

-- Payment for Claim 7 (Insurance - partial for labs)
UPDATE claims SET insurance_paid = 110.00, status = 'Partial' WHERE claim_id = 7;
INSERT INTO payments (claim_id, payment_date, amount, payment_source, reference_number) VALUES
(7, '2025-04-15', 110.00, 'Insurance', 'UHC_PAY_112');
-- Note: Patient balance remaining


-- Final check on claim statuses based on payments (Manual update examples)
-- Claim 1: 125 total, 100 ins paid, 25 patient paid -> Paid
-- Claim 2: 200 total, 180 ins paid -> Partial (20 patient balance)
-- Claim 3: 250 total, 0 paid -> Pending
-- Claim 4: 150 total, 0 paid -> Submitted
-- Claim 5: 45 total, 45 ins paid -> Paid
-- Claim 6: 175 total, 0 paid -> Submitted
-- Claim 7: 145 total, 110 ins paid -> Partial (35 patient balance)
-- Claim 8: 125 total, 0 paid -> Denied
-- Claim 9: 125 total, 0 paid -> Submitted

SELECT 'Database schema and sample data created successfully.' AS status; 