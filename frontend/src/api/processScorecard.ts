import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface OCRWordResult {
  text: string;
  confidence: number;
  bbox: number[];  // [x, y, width, height]
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

export const processScorecard = async (s3Key: string): Promise<ProcessScorecardResponse> => {
  const response = await api.post<ProcessScorecardResponse>('/process-scorecard', {
    s3_key: s3Key,
  });
  return response.data;
};