import type { components } from "./api";

export type Player = components['schemas']['Player'];
export type ScorecardData = components['schemas']['ScorecardData'];
export type ProcessScorecardResponse = components['schemas']['ProcessScorecardResponse'];
export type ExportRequest = components['schemas']['ExportRequest'];

export type GameMode = 'stroke_play' | 'match_play' | 'scramble' | 'best_ball';

export interface GameModeOption {
  value: GameMode;
  label: string;
  description: string;
}

// For Phase 2: Team support
export interface Team {
  name: string;
  players: Player[];
}

// For future: Scorecard with metadata
export interface ScorecardWithMetadata extends ScorecardData {
  id: string;
  created_at: string;
  game_mode: GameMode;
  notes?: string;
}