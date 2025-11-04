# who-won

OCR-powered golf scorecard analyzer with multiple game mode support to help determine who won your match.

## Tech Stack
- **Frontend**: React + TypeScript + Vite + MUI
- **Backend**: FastAPI + Python
- **OCR**: Tesseract (local) → AWS Textract (future)
- **Storage**: Local files (MVP) → S3 + PostgreSQL (future)

## Project Structure
- `/frontend` - React application
- `/backend` - FastAPI application

## Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```