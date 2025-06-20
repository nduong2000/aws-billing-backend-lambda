# Medical Billing System - Architectural Diagrams

## 1. High-Level System Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│   Web Browser   │◄────►│  Frontend App   │◄────►│  API Backend    │
│                 │      │                 │      │                 │
└─────────────────┘      └─────────────────┘      └────────┬────────┘
                                                           │
                                                           ▼
                         ┌─────────────────┐      ┌─────────────────┐
                         │                 │      │                 │
                         │   AWS Bedrock   │◄────►│  PostgreSQL DB  │
                         │   (AI/ML)       │      │                 │
                         └─────────────────┘      └─────────────────┘
```

## 2. AWS Deployment Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                         AWS Cloud                              │
│                                                                │
│  ┌─────────────────┐      ┌─────────────────┐                  │
│  │                 │      │                 │                  │
│  │  Route 53       │─────►│  Elastic        │                  │
│  │  (DNS)          │      │  Load Balancer  │                  │
│  │                 │      │                 │                  │
│  └─────────────────┘      └────────┬────────┘                  │
│                                    │                           │
│                                    ▼                           │
│  ┌─────────────────┐      ┌─────────────────┐                  │
│  │                 │      │                 │                  │
│  │  S3 Bucket      │      │  Elastic        │                  │
│  │  (Static Files) │      │  Beanstalk      │                  │
│  │                 │      │                 │                  │
│  └─────────────────┘      └────────┬────────┘                  │
│                                    │                           │
│                                    ▼                           │
│  ┌─────────────────┐      ┌─────────────────┐                  │
│  │                 │      │                 │                  │
│  │  AWS Bedrock    │◄────►│  RDS            │                  │
│  │  (AI Audit)     │      │  (PostgreSQL)   │                  │
│  │                 │      │                 │                  │
│  └─────────────────┘      └─────────────────┘                  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

## 3. Application Component Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                       FastAPI Application                             │
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐          │
│  │                │  │                │  │                │          │
│  │ Patient Module │  │ Provider Module│  │ Service Module │          │
│  │                │  │                │  │                │          │
│  └────────┬───────┘  └────────┬───────┘  └────────┬───────┘          │
│           │                   │                   │                  │
│           ▼                   ▼                   ▼                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐          │
│  │                │  │                │  │                │          │
│  │ Appointment    │  │ Claim Module   │  │ Payment Module │          │
│  │ Module         │  │                │  │                │          │
│  └────────┬───────┘  └────────┬───────┘  └────────┬───────┘          │
│           │                   │                   │                  │
│           └───────────────────┼───────────────────┘                  │
│                               │                                      │
│                               ▼                                      │
│                     ┌────────────────┐                               │
│                     │                │                               │
│                     │ Audit Module   │                               │
│                     │ (Bedrock AI)   │                               │
│                     │                │                               │
│                     └────────────────┘                               │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## 4. Data Flow Diagram

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│              │     │              │     │              │     │              │
│   Patient    │────►│  Provider    │────►│  Service     │────►│ Appointment  │
│   Data       │     │  Data        │     │  Data        │     │ Data         │
│              │     │              │     │              │     │              │
└──────┬───────┘     └──────────────┘     └──────────────┘     └──────┬───────┘
       │                                                              │
       │                                                              │
       │                                                              ▼
┌──────▼───────┐                                              ┌──────────────┐
│              │                                              │              │
│   Payment    │◄─────────────────────────────────────────────┤   Claim      │
│   Processing │                                              │   Processing │
│              │                                              │              │
└──────┬───────┘                                              └──────┬───────┘
       │                                                              │
       │                                                              │
       │                                                              ▼
       │                                                     ┌──────────────┐
       │                                                     │              │
       └────────────────────────────────────────────────────►│   Audit      │
                                                             │   System     │
                                                             │              │
                                                             └──────────────┘
```

## 5. Database Schema Diagram

```
┌──────────────────┐          ┌──────────────────┐          ┌──────────────────┐
│     patients     │          │    providers     │          │     services     │
├──────────────────┤          ├──────────────────┤          ├──────────────────┤
│ patient_id (PK)  ├──┐       │ provider_id (PK) ├──┐       │ service_id (PK)  │
│ first_name       │  │       │ provider_name    │  │       │ cpt_code         │
│ last_name        │  │       │ specialty        │  │       │ description      │
│ dob              │  │       │ npi_number       │  │       │ base_price       │
│ address          │  │       │ tax_id           │  │       │                  │
│ phone            │  │       │ address          │  │       │                  │
└──────────────────┘  │       └──────────────────┘  │       └─────────┬────────┘
                      │                              │                 │
                      │                              │                 │
                      ▼                              ▼                 │
┌──────────────────┐  │       ┌──────────────────┐  │                 │
│   appointments   │  │       │      claims      │  │                 │
├──────────────────┤  │       ├──────────────────┤  │                 │
│ appointment_id(PK)  │       │ claim_id (PK)    │  │                 │
│ patient_id (FK)  ◄──┘       │ patient_id (FK)  ◄──┘                 │
│ provider_id (FK) ◄──────────┼─ provider_id (FK)│                    │
│ appointment_date │          │ claim_date       │                    │
│ appointment_type │          │ total_amount     │                    │
│ notes            │          │ status           │                    │
└──────────────────┘          │ fraud_score      │                    │
                              └────────┬─────────┘                    │
                                       │                              │
                                       │                              │
                                       ▼                              │
                              ┌──────────────────┐                    │
                              │   claim_items    │                    │
                              ├──────────────────┤                    │
                              │ item_id (PK)     │                    │
                              │ claim_id (FK)    │                    │
                              │ service_id (FK)  ◄────────────────────┘
                              │ quantity         │
                              │ charge_amount    │
                              │                  │
                              └────────┬─────────┘
                                       │
                                       │
                                       ▼
                              ┌──────────────────┐
                              │    payments      │
                              ├──────────────────┤
                              │ payment_id (PK)  │
                              │ claim_id (FK)    │
                              │ payment_date     │
                              │ payment_amount   │
                              │ payment_method   │
                              │ status           │
                              └──────────────────┘
```

## 6. Audit Process Flow

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│               │     │               │     │               │     │               │
│  Claim        │────►│  Format Claim │────►│  AWS Bedrock  │────►│  Calculate    │
│  Submission   │     │  Data for LLM │     │  AI Analysis  │     │  Fraud Score  │
│               │     │               │     │               │     │               │
└───────────────┘     └───────────────┘     └───────────────┘     └───────┬───────┘
                                                                          │
                                                                          │
                                                                          ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│               │     │               │     │               │     │               │
│  Store Audit  │◄────┤  Update Claim │◄────┤  Generate     │◄────┤  ML Fraud     │
│  Results      │     │  Status       │     │  Audit Report │     │  Detection    │
│               │     │               │     │               │     │               │
└───────────────┘     └───────────────┘     └───────────────┘     └───────────────┘
```

## 7. Deployment Process Flow

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│               │     │               │     │               │     │               │
│  Local Dev    │────►│  Git Commit   │────►│  Create EB    │────►│  Upload to S3 │
│  Environment  │     │  Changes      │     │  App Version  │     │  Bucket       │
│               │     │               │     │               │     │               │
└───────────────┘     └───────────────┘     └───────────────┘     └───────┬───────┘
                                                                          │
                                                                          │
                                                                          ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│               │     │               │     │               │     │               │
│  Domain       │◄────┤  Configure    │◄────┤  Deploy to    │◄────┤  EB           │
│  Setup        │     │  HTTPS & CORS │     │  Elastic      │     │  Environment  │
│               │     │               │     │  Beanstalk    │     │  Setup        │
└───────────────┘     └───────────────┘     └───────────────┘     └───────────────┘
``` 