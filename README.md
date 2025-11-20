# Golf Scorecard Analyzer - Phase 1 MVP

A web application for uploading golf scorecards, extracting data using AI, and analyzing results.

## Features (Phase 1)
- 📤 Drag-and-drop scorecard image upload
- 🤖 AI-powered data extraction using Claude Haiku
- ✏️ Editable scorecard table with live updates
- 🏆 Automatic winner calculation (Stroke Play)
- 📊 Front 9 / Back 9 / Total score tracking
- 📥 CSV export functionality
- ⚠️ Visual indicators for missing data

## Tech Stack

### Backend
- FastAPI
- Python 3.9+
- Anthropic Claude API (Haiku model)
- AWS S3 for image storage
- Pydantic for data validation

### Frontend
- React 18 + TypeScript
- Vite
- Mantine UI components
- TanStack Table for editable tables
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
3. Wait for AI processing (~2-3 seconds)
4. View extracted data in the editable table
5. Edit any scores, names, or handicaps as needed
6. See the winner displayed at the top
7. Export to CSV for record-keeping

## API Endpoints

### `POST /api/upload-and-process`
Upload and process a scorecard image

**Request:** `multipart/form-data` with `file` field

**Response:**
```json
{
  "scorecard_id": "uuid",
  "data": {
    "course": "Course Name",
    "date": "2024-01-01",
    "par": [4,4,3,5,...],
    "players": [
      {
        "name": "Player Name",
        "scores": [4,5,3,...],
        "handicap": 10,
        "total": 85,
        "front_nine_total": 42,
        "back_nine_total": 43
      }
    ]
  },
  "winner": "Player Name",
  "processing_time_ms": 2500
}
```

### `POST /api/export`
Export scorecard data

**Request:**
```json
{
  "data": { /* scorecard data */ },
  "format": "csv"
}
```

**Response:** File download (CSV)

## Cost Optimization

- Using **Claude Haiku** instead of Sonnet: **~$0.003** per scorecard (5x cheaper)
- Max tokens capped at 1500 for structured data extraction
- Average processing time: 2-3 seconds

## Roadmap

### Phase 1.5 (Coming Soon)
- [ ] Excel export
- [ ] Better error handling
- [ ] Loading states and progress indicators

### Phase 2
- [ ] Handicap adjustments
- [ ] Match Play mode
- [ ] Best Ball mode with team support
- [ ] Team assignment UI

### Phase 3
- [ ] Tournament support (multiple scorecards)
- [ ] Integration with golf apps (18Birdies, GHIN)
- [ ] Mobile app version
- [ ] Historical data storage

## Notes

- Yellow highlighting indicates cells with missing data that Claude couldn't extract
- All scores are editable in real-time
- Winner recalculates automatically when scores change
- CSV export includes par row, all scores, and totals

## License

MIT