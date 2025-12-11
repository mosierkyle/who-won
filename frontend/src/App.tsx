import { useState, useCallback, useRef } from 'react'; // CHANGE: Added useRef
import { MantineProvider, Container, Title, Stack, LoadingOverlay, Alert, Button, Group, Select, ActionIcon, useMantineColorScheme } from '@mantine/core';
import '@mantine/core/styles.css';
import '@mantine/dropzone/styles.css';
import { IconInfoCircle, IconMoon, IconSun } from '@tabler/icons-react';

import { FileUpload } from './components/FileUpload';
import { ScorecardTable } from './components/ScorecardTable';
import { WinnerDisplay } from './components/WinnerDisplay';
import { ExportButton } from './components/ExportButton';
import { scorecardApi } from './services/api';
import type { ScorecardData, Player, GameMode } from './types';

function AppContent() {
  const [loading, setLoading] = useState(false);
  const [scorecardData, setScorecardData] = useState<ScorecardData | null>(null);
  const [winner, setWinner] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [gameMode, setGameMode] = useState<GameMode>('stroke_play');
  const { colorScheme, toggleColorScheme } = useMantineColorScheme();
  const recalcTimerRef = useRef<number | null>(null); // CHANGE: Added ref for debounce

  const handleFileSelect = async (file: File) => {
    try {
      setLoading(true);
      setError(null);

      console.log('Uploading file:', {
        name: file.name,
        size: file.size,
        type: file.type
      });

      const response = await scorecardApi.uploadAndProcess(file);
      
      console.log('Success! Response:', response);
      
      setScorecardData(response.data);
      setWinner(response.winner ?? null);
      
      console.log(`Processed in ${response.processing_time_ms}ms`);
    } catch (err: any) {
      console.error('Upload failed - Full error:', err);
      console.error('Error response:', err.response?.data);
      console.error('Error status:', err.response?.status);
      
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to process scorecard';
      setError(`Upload failed: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const handlePlayerUpdate = useCallback((playerIndex: number, updatedPlayer: Player) => {
  setScorecardData(prev => {
    if (!prev) return prev;
    const updatedPlayers = [...prev.players];
    updatedPlayers[playerIndex] = updatedPlayer;
    return { ...prev, players: updatedPlayers };
  });

  if (recalcTimerRef.current) {
    clearTimeout(recalcTimerRef.current);
  }

  recalcTimerRef.current = window.setTimeout(() => {
    setScorecardData(prev => {
      if (!prev) return prev;

      const player = prev.players[playerIndex];
      const validScores = player.scores.filter(s => s !== null) as number[];
      const total = validScores.length > 0 ? validScores.reduce((a, b) => a + b, 0) : undefined;
      
      const frontNine = player.scores.slice(0, 9).filter(s => s !== null) as number[];
      const front_nine_total = frontNine.length > 0 ? frontNine.reduce((a, b) => a + b, 0) : undefined;
      
      const backNine = player.scores.slice(9, 18).filter(s => s !== null) as number[];
      const back_nine_total = backNine.length > 0 ? backNine.reduce((a, b) => a + b, 0) : undefined;

      const updatedPlayers = [...prev.players];
      updatedPlayers[playerIndex] = { ...player, total, front_nine_total, back_nine_total };

      let newWinner: string | null = null;
      const playersWithTotals = updatedPlayers.filter(p => p.total !== undefined);
      
      if (playersWithTotals.length > 0 && gameMode === 'stroke_play') {
        newWinner = playersWithTotals.reduce((prev, curr) => (curr.total! < prev.total! ? curr : prev)).name;
      }

      setWinner(newWinner);
      return { ...prev, players: updatedPlayers };
    });
  }, 300);
}, [gameMode]);


const handlePlayerDelete = useCallback((playerIndex: number) => {
  setScorecardData(prev => {
    if (!prev || prev.players.length === 1) return prev;
    const updatedPlayers = prev.players.filter((_, idx) => idx !== playerIndex);
    return { ...prev, players: updatedPlayers };
  });
}, []);

const handlePlayerAdd = useCallback(() => {
  setScorecardData(prev => {
    if (!prev) return prev;
    const newPlayer: Player = {
      name: `Player ${prev.players.length + 1}`,
      scores: Array(18).fill(null),
      total: undefined,
      front_nine_total: undefined,
      back_nine_total: undefined,
    };
    return { ...prev, players: [...prev.players, newPlayer] };
  });
}, []);

const handleCourseChange = useCallback((course: string) => {
  setScorecardData(prev => prev ? { ...prev, course } : prev);
}, []);

const handleDateChange = useCallback((date: string) => {
  setScorecardData(prev => prev ? { ...prev, date } : prev);
}, []);


  return (
    <Container size="xl" py="xl">
      <Stack gap="lg">
        <Group justify="space-between">
          <Title order={1}>Golf Scorecard Analyzer</Title>
          <ActionIcon
            variant="default"
            onClick={() => toggleColorScheme()}
            size="lg"
            aria-label="Toggle color scheme"
          >
            {colorScheme === 'dark' ? <IconSun size={20} /> : <IconMoon size={20} />}
          </ActionIcon>
        </Group>

        {error && (
          <Alert icon={<IconInfoCircle />} title="Error" color="red">
            {error}
          </Alert>
        )}

        {scorecardData ? (
          <>
            <Group>
              <Select
                label="Game Mode"
                value={gameMode}
                onChange={(value) => setGameMode(value as GameMode)}
                data={[
                  { value: 'stroke_play', label: 'Stroke Play' },
                  { value: 'match_play', label: 'Match Play (Coming Soon)', disabled: true },
                  { value: 'best_ball', label: 'Best Ball (Coming Soon)', disabled: true },
                  { value: 'scramble', label: 'Scramble (Coming Soon)', disabled: true },
                ]}
                style={{ width: 250 }}
              />
            </Group>

            <WinnerDisplay 
              winner={winner} 
              course={scorecardData.course} 
              date={scorecardData.date} 
              onCourseChange={handleCourseChange}
              onDateChange={handleDateChange}
            />

            <ScorecardTable
              players={scorecardData.players}
              par={scorecardData.par || []}
              onPlayerUpdate={handlePlayerUpdate}
              onPlayerDelete={handlePlayerDelete}
              onPlayerAdd={handlePlayerAdd}
            />

            <ExportButton data={scorecardData} />

            <Button
              variant="light"
              onClick={() => {
                setScorecardData(null);
                setWinner(null);
                setError(null);
              }}
              fullWidth
            >
              Analyze Another Scorecard
            </Button>
          </>
        ) : (
          <>
            <FileUpload onFileSelect={handleFileSelect} loading={loading} />
          </>
        )}
      </Stack>
    </Container>
  );
}

function App() {
  return (
    <MantineProvider defaultColorScheme="light">
      <AppContent />
    </MantineProvider>
  );
}

export default App;