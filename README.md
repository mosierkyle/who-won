# Golf Scorecard Analyzer

Upload Scorecard, find out who won!

### Backend
- FastAPI
- Python 3.9+
- Anthropic Claude API (Haiku model)
- AWS S3
- Pydantic

### Frontend
- React + TypeScript
- Vite
- Mantine UI components
- TanStack Table
- Axios for API calls

## Setup Instructions

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your credentials:
   ```
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   S3_BUCKET_NAME=your_bucket_name
   S3_REGION=us-east-1
   ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

5. **Run the backend**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

   API will be available at: `http://localhost:8000`
   API docs at: `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Run the development server**
   ```bash
   npm run dev
   ```

   App will be available at: `http://localhost:5173`

## Usage

1. Open `http://localhost:5173` in your browser
2. Drag and drop a golf scorecard image (or click to select)
3. Wait for processing (~2-3 seconds)
4. View extracted data in the editable table
5. Edit any scores, names, or handicaps as needed
6. See the winner displayed at the top
7. Export to CSV for record-keeping