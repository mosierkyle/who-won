import { Table, TextInput, Box, Tooltip, Group, Button, ActionIcon } from '@mantine/core';
import type { Player } from '../types';
import { IconTrash, IconUserPlus } from '@tabler/icons-react';


interface ScorecardTableProps {
  players: Player[];
  par?: (number | null)[];
  onPlayerUpdate: (playerIndex: number, updatedPlayer: Player) => void;
  onPlayerDelete?: (playerIndex: number) => void;
  onPlayerAdd?: () => void; 
}

// Helper to determine scoring type
const getScoringType = (score: number | null, par: number | null) => {
  if (score === null || par === null) return null;
  const diff = score - par;
  
  if (diff <= -3) return { type: 'albatross', color: '#9775fa', label: 'Albatross or better' };
  if (diff === -2) return { type: 'eagle', color: '#4c6ef5', label: 'Eagle' };
  if (diff === -1) return { type: 'birdie', color: '#ff6b6b', label: 'Birdie' };
  if (diff === 0) return null;
  if (diff === 1) return { type: 'bogey', color: '#fd7e14', label: 'Bogey' };
  if (diff >= 2) return { type: 'double', color: '#495057', label: 'Double Bogey+' };
  
  return null;
};

// Render a score cell with styling
const ScoreCell = ({ 
  score, 
  holePar, 
  onChange 
}: { 
  score: number | null; 
  holePar: number | null; 
  onChange: (value: number | null) => void;
}) => {
  const hasData = score !== null;
  const scoring = getScoringType(score, holePar);
  
  const cell = (
    <Box pos="relative">
      {scoring?.type === 'birdie' && (
        <Box
          style={{
            marginTop: "-7px",
            zIndex: "10",
            position: 'absolute',
            inset: 0,
            borderRadius: '50%',
            border: `1px solid ${scoring.color}`,
            pointerEvents: 'none',
            height: "45px",
            borderColor: "green"
          }}
        />
      )}
      <TextInput
        value={score === null ? '' : score}
        onChange={(e) => {
          onChange(e.target.value === '' ? null : parseInt(e.target.value));
        }}
        size="xs"
        type="number"
        styles={{
          input: {
            textAlign: 'center',
            width: '45px',
            padding: '4px',
            border: hasData ? '1px solid #dee2e6' : '2px solid #ffd43b',
            backgroundColor: hasData ? 'transparent' : '#fff9db',
            fontWeight: 600,
            borderRadius: '4px',
            borderColor: (hasData ? '#dee2e6' : '#ffd43b'),
            borderWidth: (hasData ? '1px' : '2px'),
            color: 'inherit',
          }
        }}
        placeholder="-"
      />
    </Box>
  );

  if (!hasData) {
    return (
      <Tooltip label="Missing score - please fill in" position="top">
        {cell}
      </Tooltip>
    );
  }

  if (scoring) {
    return (
      <Tooltip label={scoring.label} position="top">
        {cell}
      </Tooltip>
    );
  }

  return cell;
};

export function ScorecardTable({ 
  players, 
  par = [], 
  onPlayerUpdate,
  onPlayerDelete,
  onPlayerAdd 
}: ScorecardTableProps) {
  const handleScoreChange = (playerIndex: number, holeIndex: number, newScore: number | null) => {
    const player = players[playerIndex];
    const newScores = [...player.scores];
    newScores[holeIndex] = newScore;
    onPlayerUpdate(playerIndex, { ...player, scores: newScores });
  };

  const handleNameChange = (playerIndex: number, newName: string) => {
    const player = players[playerIndex];
    onPlayerUpdate(playerIndex, { ...player, name: newName });
  };

  return (
    <Box style={{ overflowX: 'auto' }}>
        {onPlayerAdd && (
        <Group mb="md">
          <Button 
            leftSection={<IconUserPlus size={16} />}
            onClick={onPlayerAdd}
            variant="light"
            size="sm"
          >
            Add Player
          </Button>
        </Group>
      )}

      <Table 
        striped 
        highlightOnHover 
        withTableBorder
        style={{ 
          fontSize: '13px',
          minWidth: '1200px',
        }}
      >
        <Table.Thead>
          <Table.Tr>
            <Table.Th style={{ padding: '8px 4px', textAlign: 'center' }}>Player</Table.Th>
            {/* Holes 1-9 */}
            {Array.from({ length: 9 }, (_, i) => (
              <Table.Th key={i} style={{ padding: '8px 4px', textAlign: 'center', fontWeight: 700 }}>
                {i + 1}
              </Table.Th>
            ))}
            <Table.Th style={{ padding: '8px 4px', textAlign: 'center', fontWeight: 700 }}>Out</Table.Th>
            {/* Holes 10-18 */}
            {Array.from({ length: 9 }, (_, i) => (
              <Table.Th key={i + 9} style={{ padding: '8px 4px', textAlign: 'center', fontWeight: 700 }}>
                {i + 10}
              </Table.Th>
            ))}
            <Table.Th style={{ padding: '8px 4px', textAlign: 'center', fontWeight: 700 }}>In</Table.Th>
            <Table.Th style={{ padding: '8px 4px', textAlign: 'center', fontWeight: 700 }}>Total</Table.Th>
            {onPlayerDelete && <Table.Th style={{ padding: '8px 4px', textAlign: 'center' }}></Table.Th>}

          </Table.Tr>
        </Table.Thead>
        
        <Table.Tbody>
          {players.map((player, playerIndex) => (
            <Table.Tr key={playerIndex}>
              {/* Player name */}
              <Table.Td style={{ padding: '4px' }}>
                <TextInput
                  value={player.name}
                  onChange={(e) => handleNameChange(playerIndex, e.target.value)}
                  size="sm"
                  styles={{ input: { fontWeight: 600 } }}
                />
              </Table.Td>

              {/* Front 9 scores */}
              {Array.from({ length: 9 }, (_, holeIndex) => (
                <Table.Td key={holeIndex} style={{ padding: '4px', textAlign: 'center' }}>
                  <ScoreCell
                    score={player.scores[holeIndex]}
                    holePar={par[holeIndex] ?? null}
                    onChange={(newScore) => handleScoreChange(playerIndex, holeIndex, newScore)}
                  />
                </Table.Td>
              ))}

              {/* Out total */}
              <Table.Td style={{ padding: '4px', textAlign: 'center' }}>
                <div style={{ fontWeight: 700, fontSize: '14px', color: '#228be6' }}>
                  {player.front_nine_total ?? '-'}
                </div>
              </Table.Td>

              {/* Back 9 scores */}
              {Array.from({ length: 9 }, (_, i) => {
                const holeIndex = i + 9;
                return (
                  <Table.Td key={holeIndex} style={{ padding: '4px', textAlign: 'center' }}>
                    <ScoreCell
                      score={player.scores[holeIndex]}
                      holePar={par[holeIndex] ?? null}
                      onChange={(newScore) => handleScoreChange(playerIndex, holeIndex, newScore)}
                    />
                  </Table.Td>
                );
              })}

              {/* In total */}
              <Table.Td style={{ padding: '4px', textAlign: 'center' }}>
                <div style={{ fontWeight: 700, fontSize: '14px', color: '#228be6' }}>
                  {player.back_nine_total ?? '-'}
                </div>
              </Table.Td>

              {/* Total */}
              <Table.Td style={{ padding: '4px', textAlign: 'center' }}>
                <div style={{ 
                  fontWeight: 700, 
                  fontSize: '16px',
                  padding: '4px 8px',
                  backgroundColor: '#228be6',
                  color: 'white',
                  borderRadius: '4px',
                }}>
                  {player.total ?? '-'}
                </div>
              </Table.Td>
              {onPlayerDelete && (
                  <Table.Td style={{ padding: '4px', textAlign: 'center' }}>
                    <ActionIcon
                      color="red"
                      variant="subtle"
                      onClick={() => onPlayerDelete(playerIndex)}
                      disabled={players.length === 1}
                    >
                      <IconTrash size={16} />
                    </ActionIcon>
                  </Table.Td>
                )}
            </Table.Tr>
          ))}
        </Table.Tbody>

        {/* Par row at bottom */}
        {par.length > 0 && (
          <Table.Tfoot>
            <Table.Tr style={{ fontWeight: 700 }}>
              <Table.Td style={{ padding: '8px' }}>Par</Table.Td>
              {/* Front 9 */}
              {par.slice(0, 9).map((p, i) => (
                <Table.Td key={i} style={{ padding: '4px', textAlign: 'center' }}>
                  {p ?? '-'}
                </Table.Td>
              ))}
              <Table.Td style={{ textAlign: 'center' }}>
                {par.slice(0, 9).filter(p => p !== null).reduce((sum, p) => sum + (p || 0), 0)}
              </Table.Td>
              {/* Back 9 */}
              {par.slice(9, 18).map((p, i) => (
                <Table.Td key={i + 9} style={{ padding: '4px', textAlign: 'center' }}>
                  {p ?? '-'}
                </Table.Td>
              ))}
              <Table.Td style={{ textAlign: 'center' }}>
                {par.slice(9, 18).filter(p => p !== null).reduce((sum, p) => sum + (p || 0), 0)}
              </Table.Td>
              <Table.Td style={{ textAlign: 'center' }}>
                {par.filter(p => p !== null).reduce((sum, p) => sum + (p || 0), 0)}
              </Table.Td>
              {onPlayerDelete && <Table.Td></Table.Td>}
            </Table.Tr>
          </Table.Tfoot>
        )}
      </Table>
    </Box>
  );
}