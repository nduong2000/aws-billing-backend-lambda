import sqlite3
import logging

logger = logging.getLogger("db_init")

def initialize_db():
    """Create and initialize the SQLite in-memory database"""
    logger.info("Creating in-memory SQLite database")
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # Create tables with the same structure as PostgreSQL
    cursor.execute('''
    CREATE TABLE patients (
        patient_id INTEGER PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        date_of_birth TEXT NOT NULL,
        address TEXT,
        phone_number TEXT,
        insurance_provider TEXT,
        insurance_policy_number TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE providers (
        provider_id INTEGER PRIMARY KEY,
        provider_name TEXT NOT NULL,
        npi_number TEXT UNIQUE NOT NULL,
        specialty TEXT,
        address TEXT,
        phone_number TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE services (
        service_id INTEGER PRIMARY KEY,
        cpt_code TEXT UNIQUE NOT NULL,
        description TEXT NOT NULL,
        standard_charge REAL NOT NULL CHECK (standard_charge >= 0)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE appointments (
        appointment_id INTEGER PRIMARY KEY,
        patient_id INTEGER NOT NULL,
        provider_id INTEGER NOT NULL,
        appointment_date TEXT NOT NULL,
        reason_for_visit TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients (patient_id),
        FOREIGN KEY (provider_id) REFERENCES providers (provider_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE claims (
        claim_id INTEGER PRIMARY KEY,
        patient_id INTEGER NOT NULL,
        provider_id INTEGER NOT NULL,
        claim_date TEXT NOT NULL,
        total_charge REAL NOT NULL CHECK (total_charge >= 0),
        insurance_paid REAL DEFAULT 0 CHECK (insurance_paid >= 0),
        patient_paid REAL DEFAULT 0 CHECK (patient_paid >= 0),
        status TEXT NOT NULL CHECK (status IN ('Submitted', 'Paid', 'Denied', 'Pending', 'Partial')),
        fraud_score REAL,
        FOREIGN KEY (patient_id) REFERENCES patients (patient_id),
        FOREIGN KEY (provider_id) REFERENCES providers (provider_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE claim_items (
        claim_item_id INTEGER PRIMARY KEY,
        claim_id INTEGER NOT NULL,
        service_id INTEGER NOT NULL,
        charge_amount REAL NOT NULL CHECK (charge_amount >= 0),
        FOREIGN KEY (claim_id) REFERENCES claims (claim_id) ON DELETE CASCADE,
        FOREIGN KEY (service_id) REFERENCES services (service_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE payments (
        payment_id INTEGER PRIMARY KEY,
        claim_id INTEGER NOT NULL,
        payment_date TEXT NOT NULL,
        amount REAL NOT NULL CHECK (amount > 0),
        payment_source TEXT NOT NULL CHECK (payment_source IN ('Insurance', 'Patient')),
        reference_number TEXT,
        FOREIGN KEY (claim_id) REFERENCES claims (claim_id)
    )
    ''')
    
    # Insert sample data
    # Sample Patients
    patients_data = [
        (1, 'John', 'Doe', '1985-03-15', '123 Main St, Anytown, USA', '555-1234', 'BlueCross', 'BCBS123456789'),
        (2, 'Jane', 'Smith', '1992-07-22', '456 Oak Ave, Anytown, USA', '555-5678', 'Aetna', 'AETNA987654321'),
        (3, 'Robert', 'Johnson', '1978-11-01', '789 Pine Ln, Anytown, USA', '555-9101', 'Cigna', 'CIGNA112233445'),
        (4, 'Maria', 'Garcia', '2001-01-30', '101 Maple Dr, Anytown, USA', '555-1121', 'UnitedHealthcare', 'UHC556677889'),
        (5, 'David', 'Miller', '1965-09-10', '202 Birch Rd, Anytown, USA', '555-3141', 'BlueCross', 'BCBS998877665')
    ]
    cursor.executemany('''
    INSERT INTO patients (patient_id, first_name, last_name, date_of_birth, address, phone_number, insurance_provider, insurance_policy_number)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', patients_data)
    
    # Sample Providers
    providers_data = [
        (1, 'Dr. Alice Brown', '1234567890', 'Cardiology', '1 Medical Plaza, Anytown, USA', '555-1000'),
        (2, 'Dr. Bob White', '0987654321', 'Pediatrics', '2 Health Way, Anytown, USA', '555-2000'),
        (3, 'Anytown Clinic', '1122334455', 'General Practice', '3 Wellness Blvd, Anytown, USA', '555-3000')
    ]
    cursor.executemany('''
    INSERT INTO providers (provider_id, provider_name, npi_number, specialty, address, phone_number)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', providers_data)
    
    # Sample Services
    services_data = [
        (1, '99213', 'Office visit, established patient, low complexity', 125.00),
        (2, '99214', 'Office visit, established patient, moderate complexity', 175.00),
        (3, '99203', 'Office visit, new patient, low complexity', 150.00),
        (4, '99395', 'Periodic preventive medicine Px; 18-39 years', 200.00),
        (5, '90686', 'Flu vaccine, quadrivalent, intramuscular', 45.00),
        (6, '80053', 'Comprehensive metabolic panel', 85.00),
        (7, '85025', 'Complete blood count (CBC), automated', 60.00),
        (8, '93000', 'Electrocardiogram (ECG), routine', 75.00)
    ]
    cursor.executemany('''
    INSERT INTO services (service_id, cpt_code, description, standard_charge)
    VALUES (?, ?, ?, ?)
    ''', services_data)
    
    # Sample Appointments
    appointments_data = [
        (1, 1, 1, '2025-03-05 10:00:00', 'Follow-up visit for hypertension'),
        (2, 2, 3, '2025-03-08 14:30:00', 'Annual physical'),
        (3, 3, 1, '2025-03-12 09:15:00', 'Chest pain evaluation'),
        (4, 4, 2, '2025-03-15 11:00:00', 'Well-child check-up'),
        (5, 1, 3, '2025-03-20 16:00:00', 'Flu shot'),
        (6, 5, 1, '2025-03-25 08:45:00', 'Consultation for arrhythmia'),
        (7, 2, 3, '2025-04-02 13:00:00', 'Lab work follow-up'),
        (8, 4, 2, '2025-04-10 15:15:00', 'Sick visit - fever'),
        (9, 3, 3, '2025-04-18 10:30:00', 'General check-up')
    ]
    cursor.executemany('''
    INSERT INTO appointments (appointment_id, patient_id, provider_id, appointment_date, reason_for_visit)
    VALUES (?, ?, ?, ?, ?)
    ''', appointments_data)
    
    # Sample Claims
    claims_data = [
        (1, 1, 1, '2025-03-05', 125.00, 0, 0, 'Submitted', None),
        (2, 2, 3, '2025-03-08', 200.00, 0, 0, 'Submitted', None),
        (3, 3, 1, '2025-03-12', 250.00, 0, 0, 'Pending', None),
        (4, 4, 2, '2025-03-15', 150.00, 0, 0, 'Submitted', None),
        (5, 1, 3, '2025-03-20', 45.00, 0, 0, 'Paid', None),
        (6, 5, 1, '2025-03-25', 175.00, 0, 0, 'Submitted', None),
        (7, 2, 3, '2025-04-02', 145.00, 0, 0, 'Partial', None),
        (8, 4, 2, '2025-04-10', 125.00, 0, 0, 'Denied', None),
        (9, 3, 3, '2025-04-18', 1250000.00, 0, 0, 'Submitted', None),
        (10, 3, 2, '2025-04-18', 125.00, 0, 0, 'Submitted', None)
    ]
    cursor.executemany('''
    INSERT INTO claims (claim_id, patient_id, provider_id, claim_date, total_charge, insurance_paid, patient_paid, status, fraud_score)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', claims_data)
    
    # Sample Claim Items - Fixed the abnormal value in claim 10
    claim_items_data = [
        (1, 1, 1, 125.00),
        (2, 2, 4, 200.00),
        (3, 3, 2, 175.00),
        (4, 3, 8, 75.00),
        (5, 4, 3, 150.00),
        (6, 5, 5, 45.00),
        (7, 6, 2, 175.00),
        (8, 7, 6, 85.00),
        (9, 7, 7, 60.00),
        (10, 8, 1, 125.00),
        (11, 9, 1, 125.00),
        (12, 10, 1, 125.00)  # Fixed charge amount to match the service
    ]
    cursor.executemany('''
    INSERT INTO claim_items (claim_item_id, claim_id, service_id, charge_amount)
    VALUES (?, ?, ?, ?)
    ''', claim_items_data)
    
    # Update claims with payment data
    cursor.execute("UPDATE claims SET insurance_paid = 100.00, patient_paid = 25.00, status = 'Paid' WHERE claim_id = 1")
    cursor.execute("UPDATE claims SET insurance_paid = 180.00, status = 'Partial' WHERE claim_id = 2")
    cursor.execute("UPDATE claims SET insurance_paid = 45.00, status = 'Paid' WHERE claim_id = 5")
    cursor.execute("UPDATE claims SET insurance_paid = 110.00, status = 'Partial' WHERE claim_id = 7")
    
    # Sample Payments
    payments_data = [
        (1, 1, '2025-03-20', 100.00, 'Insurance', 'BCBS_PAY_123'),
        (2, 1, '2025-04-01', 25.00, 'Patient', 'CHECK_456'),
        (3, 2, '2025-03-25', 180.00, 'Insurance', 'AETNA_PAY_789'),
        (4, 5, '2025-03-28', 45.00, 'Insurance', 'BCBS_PAY_101'),
        (5, 7, '2025-04-15', 110.00, 'Insurance', 'UHC_PAY_112')
    ]
    cursor.executemany('''
    INSERT INTO payments (payment_id, claim_id, payment_date, amount, payment_source, reference_number)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', payments_data)
    
    conn.commit()
    logger.info("Database initialized successfully")
    return conn

def print_db_summary(conn):
    """Print a summary of the database contents"""
    cursor = conn.cursor()
    
    print("\n--- Medical Billing System Database Summary ---\n")
    
    # Count patients
    cursor.execute("SELECT COUNT(*) FROM patients")
    patient_count = cursor.fetchone()[0]
    print(f"Total Patients: {patient_count}")
    
    # Count providers
    cursor.execute("SELECT COUNT(*) FROM providers")
    provider_count = cursor.fetchone()[0]
    print(f"Total Providers: {provider_count}")
    
    # Count services
    cursor.execute("SELECT COUNT(*) FROM services")
    service_count = cursor.fetchone()[0]
    print(f"Total Services: {service_count}")
    
    # Count claims
    cursor.execute("SELECT COUNT(*), SUM(total_charge) FROM claims")
    claim_data = cursor.fetchone()
    print(f"Total Claims: {claim_data[0]}, Total Value: ${claim_data[1]:.2f}")
    
    # Claims by status
    print("\nClaims by Status:")
    cursor.execute("SELECT status, COUNT(*), SUM(total_charge) FROM claims GROUP BY status")
    for status, count, total in cursor.fetchall():
        print(f"  {status}: {count} claims (${total:.2f})")
    
    # Payments summary
    cursor.execute("SELECT payment_source, COUNT(*), SUM(amount) FROM payments GROUP BY payment_source")
    print("\nPayments Summary:")
    for source, count, total in cursor.fetchall():
        print(f"  {source}: {count} payments (${total:.2f})")

# Simple test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    conn = initialize_db()
    print_db_summary(conn)
    print("\nDatabase initialization test complete")
    conn.close() 