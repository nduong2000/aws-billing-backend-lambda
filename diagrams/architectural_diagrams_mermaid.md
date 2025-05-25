# Medical Billing System - Architectural Diagrams (Mermaid)

## 1. High-Level System Architecture

```mermaid
graph LR
    A[Web Browser] <-->|HTTP/HTTPS| B[Frontend App]
    B <-->|API Calls| C[API Backend]
    C -->|Queries| D[(PostgreSQL DB)]
    C -->|AI Processing| E[AWS Bedrock AI/ML]
    E -->|Results| C
    
    style A fill:#f9f9f9,stroke:#333,stroke-width:2px
    style B fill:#d5e8d4,stroke:#82b366,stroke-width:2px
    style C fill:#dae8fc,stroke:#6c8ebf,stroke-width:2px
    style D fill:#fff2cc,stroke:#d6b656,stroke-width:2px
    style E fill:#ffe6cc,stroke:#d79b00,stroke-width:2px
```

## 2. AWS Deployment Architecture

```mermaid
graph TD
    subgraph AWS Cloud
        A[Route 53 DNS] -->|DNS Resolution| B[Elastic Load Balancer]
        B -->|Traffic Distribution| C[Elastic Beanstalk]
        C -->|Database Queries| D[(RDS PostgreSQL)]
        C -->|AI Processing| E[AWS Bedrock]
        F[S3 Bucket] -->|Static Files| B
    end
    
    Browser[Web Browser] -->|HTTPS Request| A
    
    style A fill:#f5f5f5,stroke:#666,stroke-width:2px
    style B fill:#d5e8d4,stroke:#82b366,stroke-width:2px
    style C fill:#dae8fc,stroke:#6c8ebf,stroke-width:2px
    style D fill:#fff2cc,stroke:#d6b656,stroke-width:2px
    style E fill:#ffe6cc,stroke:#d79b00,stroke-width:2px
    style F fill:#e1d5e7,stroke:#9673a6,stroke-width:2px
    style Browser fill:#f9f9f9,stroke:#333,stroke-width:2px
```

## 3. Application Component Architecture

```mermaid
graph TD
    subgraph FastAPI Application
        P[Patient Module] 
        PR[Provider Module]
        S[Service Module]
        A[Appointment Module]
        C[Claim Module]
        PM[Payment Module]
        AU[Audit Module with Bedrock AI]
        
        P & PR & S --> A
        P & PR & S --> C
        C --> PM
        C --> AU
        PM --> AU
    end
    
    style P fill:#d5e8d4,stroke:#82b366,stroke-width:2px
    style PR fill:#d5e8d4,stroke:#82b366,stroke-width:2px
    style S fill:#d5e8d4,stroke:#82b366,stroke-width:2px
    style A fill:#dae8fc,stroke:#6c8ebf,stroke-width:2px
    style C fill:#dae8fc,stroke:#6c8ebf,stroke-width:2px
    style PM fill:#dae8fc,stroke:#6c8ebf,stroke-width:2px
    style AU fill:#ffe6cc,stroke:#d79b00,stroke-width:2px
```

## 4. Data Flow Diagram

```mermaid
graph LR
    P[Patient Data] --> A[Appointment Data]
    PR[Provider Data] --> A
    S[Service Data] --> A
    
    P --> C[Claim Processing]
    PR --> C
    S --> C
    A --> C
    
    C --> PM[Payment Processing]
    C --> AU[Audit System]
    PM --> AU
    
    style P fill:#d5e8d4,stroke:#82b366,stroke-width:2px
    style PR fill:#d5e8d4,stroke:#82b366,stroke-width:2px
    style S fill:#d5e8d4,stroke:#82b366,stroke-width:2px
    style A fill:#dae8fc,stroke:#6c8ebf,stroke-width:2px
    style C fill:#f8cecc,stroke:#b85450,stroke-width:2px
    style PM fill:#ffe6cc,stroke:#d79b00,stroke-width:2px
    style AU fill:#e1d5e7,stroke:#9673a6,stroke-width:2px
```

## 5. Database Schema Diagram

```mermaid
erDiagram
    PATIENTS ||--o{ APPOINTMENTS : has
    PATIENTS ||--o{ CLAIMS : submits
    PROVIDERS ||--o{ APPOINTMENTS : provides
    PROVIDERS ||--o{ CLAIMS : processes
    SERVICES ||--o{ CLAIM_ITEMS : included_in
    CLAIMS ||--o{ CLAIM_ITEMS : contains
    CLAIMS ||--o{ PAYMENTS : receives
    
    PATIENTS {
        int patient_id PK
        string first_name
        string last_name
        date dob
        string address
        string phone
    }
    
    PROVIDERS {
        int provider_id PK
        string provider_name
        string specialty
        string npi_number
        string tax_id
        string address
    }
    
    SERVICES {
        int service_id PK
        string cpt_code
        string description
        float base_price
    }
    
    APPOINTMENTS {
        int appointment_id PK
        int patient_id FK
        int provider_id FK
        date appointment_date
        string appointment_type
        string notes
    }
    
    CLAIMS {
        int claim_id PK
        int patient_id FK
        int provider_id FK
        date claim_date
        float total_amount
        string status
        float fraud_score
    }
    
    CLAIM_ITEMS {
        int item_id PK
        int claim_id FK
        int service_id FK
        int quantity
        float charge_amount
    }
    
    PAYMENTS {
        int payment_id PK
        int claim_id FK
        date payment_date
        float payment_amount
        string payment_method
        string status
    }
```

## 6. Audit Process Flow

```mermaid
graph LR
    A[Claim Submission] -->|Input| B[Format Claim Data for LLM]
    B -->|Formatted Data| C[AWS Bedrock AI Analysis]
    C -->|Analysis Results| D[Calculate Fraud Score]
    D -->|Score & Results| E[ML Fraud Detection]
    E -->|Audit Findings| F[Generate Audit Report]
    F -->|Report| G[Update Claim Status]
    G -->|Final Status| H[Store Audit Results]
    
    style A fill:#d5e8d4,stroke:#82b366,stroke-width:2px
    style B fill:#dae8fc,stroke:#6c8ebf,stroke-width:2px
    style C fill:#ffe6cc,stroke:#d79b00,stroke-width:2px
    style D fill:#e1d5e7,stroke:#9673a6,stroke-width:2px
    style E fill:#f8cecc,stroke:#b85450,stroke-width:2px
    style F fill:#dae8fc,stroke:#6c8ebf,stroke-width:2px
    style G fill:#d5e8d4,stroke:#82b366,stroke-width:2px
    style H fill:#fff2cc,stroke:#d6b656,stroke-width:2px
```

## 7. Deployment Process Flow

```mermaid
graph LR
    A[Local Dev Environment] -->|Code Changes| B[Git Commit Changes]
    B -->|Version Control| C[Create EB App Version]
    C -->|Package| D[Upload to S3 Bucket]
    D -->|App Package| E[EB Environment Setup]
    E -->|Configure Environment| F[Deploy to Elastic Beanstalk]
    F -->|Deploy| G[Configure HTTPS & CORS]
    G -->|Secure Routing| H[Domain Setup]
    
    style A fill:#d5e8d4,stroke:#82b366,stroke-width:2px
    style B fill:#dae8fc,stroke:#6c8ebf,stroke-width:2px
    style C fill:#ffe6cc,stroke:#d79b00,stroke-width:2px
    style D fill:#fff2cc,stroke:#d6b656,stroke-width:2px
    style E fill:#e1d5e7,stroke:#9673a6,stroke-width:2px
    style F fill:#f8cecc,stroke:#b85450,stroke-width:2px
    style G fill:#d5e8d4,stroke:#82b366,stroke-width:2px
    style H fill:#dae8fc,stroke:#6c8ebf,stroke-width:2px
``` 