import axios from 'axios';
import type { ExportRequest, ProcessScorecardResponse } from '../types/scorecard';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const scorecardApi = {
  /**
   * Upload and process a scorecard image
   */
  uploadAndProcess: async (file: File): Promise<ProcessScorecardResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<ProcessScorecardResponse>(
      '/upload-and-process',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  },

  /**
   * Export scorecard data to CSV or Excel
   */
  exportScorecard: async (request: ExportRequest): Promise<Blob> => {
    const response = await api.post('/export', request, {
      responseType: 'blob',
    });

    return response.data;
  },
};