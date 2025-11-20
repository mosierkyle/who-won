import { useState } from 'react';
import { MantineProvider, Container, Title, Stack, LoadingOverlay, Alert } from '@mantine/core';
import '@mantine/core/styles.css';
import '@mantine/dropzone/styles.css';
import { IconInfoCircle } from '@tabler/icons-react';

import { FileUpload } from './components/FileUpload';
import { ScorecardTable } from './components/ScorecardTable';
import { WinnerDisplay } from './components/WinnerDisplay';
import { ExportButton } from './components/ExportButton';
import { scorecardApi } from './services/api';
import { ScorecardData, Player } from './types/scorecard';

function App() {
  const [loading, setLoading] = useState(false);
  const [scorecardData, setScorecardData] = useState<ScorecardData | null>(null);
  const [winner, setWinner] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = async (file: File) => {
    try {
      setLoading(true);
      setError(null);

      const response = await scorecardApi.uploadAndProcess(file);
      
      setScorecardData(response.data);
      setWinner(response.winner ?? null);
      
      console.log(`Processed in ${response.processing_time_ms}ms`);
    } catch (err) {
      console.error('Upload failed:', err);
      setError('Failed to process scorecard. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handlePlayerUpdate = (playerIndex: number, updatedPlayer: Player) => {
    if (!scorecardData) return;

    // Recalculate totals
    const validScores = updatedPlayer.scores.filter(s => s !== null) as number[];
    updatedPlayer.total = validScores.length > 0 ? validScores.reduce((a, b) => a + b, 0) : undefined;
    
    const frontNine = updatedPlayer.scores.slice(0, 9).filter(s => s !== null) as number[];
    updatedPlayer.front_nine_total = frontNine.length > 0 ? frontNine.reduce((a, b) => a + b, 0) : undefined;
    
    const backNine = updatedPlayer.scores.slice(9, 18).filter(s => s !== null) as number[];
    updatedPlayer.back_nine_total = backNine.length > 0 ? backNine.reduce((a, b) => a + b, 0) : undefined;

    // Update players array
    const updatedPlayers = [...scorecardData.players];
    updatedPlayers[playerIndex] = updatedPlayer;

    // Recalculate winner
    const playersWithTotals = updatedPlayers.filter(p => p.total !== undefined);
    const newWinner = playersWithTotals.length > 0
      ? playersWithTotals.reduce((prev, curr) => (curr.total! < prev.total! ? curr : prev)).name
      : null;

    setScorecardData({ ...scorecardData, players: updatedPlayers });
    setWinner(newWinner);
  };

  return (
    <MantineProvider>
      <Container size="xl" py="xl">
        <Stack gap="lg">
          <Title order={1}>Golf Scorecard Analyzer</Title>

          {error && (
            <Alert icon={<IconInfoCircle />} title="Error" color="red">
              {error}
            </Alert>
          )}

          <FileUpload onFileSelect={handleFileSelect} loading={loading} />

          <LoadingOverlay visible={loading} />

          {scorecardData && (
            <>
              <WinnerDisplay 
                winner={winner} 
                course={scorecardData.course} 
                date={scorecardData.date} 
              />

              <ScorecardTable
                players={scorecardData.players}
                par={scorecardData.par}
                onPlayerUpdate={handlePlayerUpdate}
              />

              <ExportButton data={scorecardData} />
            </>
          )}
        </Stack>
      </Container>
    </MantineProvider>
  );
}

export default App;