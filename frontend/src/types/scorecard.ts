export interface Player {
  name: string;
  scores: (number | null)[];
  handicap?: number | null;
  total?: number;
  front_nine_total?: number;
  back_nine_total?: number;
}

export interface ScorecardData {
  course?: string | null;
  date?: string | null;
  par?: (number | null)[];
  players: Player[];
}

export interface ProcessScorecardResponse {
  scorecard_id: string;
  data: ScorecardData;
  winner?: string;
  processing_time_ms: number
}

export interface ExportRequest {
    data: any
    format: 'csv' | 'excel'
}