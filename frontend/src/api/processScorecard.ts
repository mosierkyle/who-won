import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Existing interfaces
export interface OCRWordResult {
  text: string;
  confidence: number;
  bbox: number[];
}

export interface PlayerData {
  row: number;
  name: string;
  all_values: (string | null)[];
}

export interface ScorecardExtractionData {
  total_players: number;
  players: PlayerData[];
  grid_size: string;
  debug_images?: string[];
}

export interface TableDetectionData {
  num_rows: number;
  num_cols: number;
  total_cells: number;
}

export interface ProcessingStepResponse {
  step_name: string;
  status: string;
  image_base64?: string;
  s3_path?: string;
  data?: any;
  processing_time_ms: number;
  error?: string;
}

export interface ProcessScorecardResponse {
  scorecard_id: string;
  filename: string;
  status: string;
  completed_steps: number;
  total_steps: number;
  steps: ProcessingStepResponse[];
  s3_paths: {
    raw: string;
    processed_folder: string;
    completed: string[];
  };
  total_processing_time_ms: number;
}

// NEW: Claude API interfaces
export interface ClaudePlayer {
  name: string;
  scores: (number | null)[];
  total: number;
}

export interface ProcessScorecardClaudeResponse {
  scorecard_id: string;
  filename: string;
  method: string;
  players: ClaudePlayer[];
  winner?: string;
  course?: string;
  date?: string;
  processing_time_ms: number;
}

// Existing OCR endpoint
export const processScorecard = async (s3Key: string): Promise<ProcessScorecardResponse> => {
  const response = await api.post<ProcessScorecardResponse>('/process-scorecard', {
    s3_key: s3Key,
  });
  return response.data;
};

// NEW: Claude API endpoint
export const processScorecardClaude = async (s3Key: string): Promise<ProcessScorecardClaudeResponse> => {
  const response = await api.post<ProcessScorecardClaudeResponse>('/process-scorecard-claude', {
    s3_key: s3Key,
  });
  return response.data;
};