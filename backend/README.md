# Backend Service

This is the backend service for the TeleDL project.

## Prerequisites

- Python 3.9 or higher
- `pip` package manager
- PostgreSQL database

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure the database:
   - Ensure PostgreSQL is running.
   - Create a database named `teledb` with the user `teleuser` and password `telepassword`.

3. Run the backend service:
   ```bash
   python main.py
   ```

## Docker Setup

1. Build the Docker image:
   ```bash
   docker build -t tele-backend .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 tele-backend
   ```

## API Endpoints

Refer to the `api/` directory for available endpoints and their documentation.
