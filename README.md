# Medical Billing System - Python Backend

This is the Python FastAPI backend for the Medical Billing System, providing APIs for patient management, provider management, service codes, appointments, claims, payments, and AI-powered claim auditing.

## Setup and Installation

### Prerequisites
- Python 3.8 or higher
- PostgreSQL database

### Setup Instructions

1. Clone the repository
2. Navigate to the backend directory
3. Create a virtual environment:
   ```
   python -m venv venv
   ```
4. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
5. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
6. Create a `.env` file based on `env.example` with your configuration
7. Run the server:
   ```
   python main.py
   ```
   
Alternatively, use the provided shell script (Unix/macOS only):
```
chmod +x run.sh
./run.sh
```

## API Endpoints

The backend provides the following API endpoints:

- `/api/patients` - Patient management
- `/api/providers` - Provider management
- `/api/services` - Medical service codes
- `/api/appointments` - Appointments
- `/api/claims` - Claims management
- `/api/payments` - Payment processing
- `/api/ollama-test` - Ollama LLM integration for claim auditing

## AI Features

This backend integrates with Ollama for AI-powered claim auditing. The following features are available:

- Claim auditing using LLM models
- Fraud detection based on claim patterns

## Database Configuration

The application connects to a PostgreSQL database. Configure your database connection in the `.env` file:

```
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_DATABASE=medical_billing
```

## Development

For development, the server runs with hot-reload enabled:
```
uvicorn main:app --reload --port 5002
```

## OpenAPI Documentation

When the server is running, access the auto-generated API documentation at:
- Swagger UI: http://localhost:5002/docs
- ReDoc: http://localhost:5002/redoc 