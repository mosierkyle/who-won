import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ProcessScorecardRequest {
  s3_key: string;
}

export interface ProcessScorecardResponse {
  message: string;
  s3_key: string;
  size_bytes: number;
  bucket: string;
}

export const processScorecard = async (s3Key: string): Promise<ProcessScorecardResponse> => {
  const response = await api.post<ProcessScorecardResponse>('/process_scorecard', {
    s3_key: s3Key,
  });
  return response.data;
};