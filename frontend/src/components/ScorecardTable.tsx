import { useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  createColumnHelper,
} from '@tanstack/react-table';
import { Table, TextInput, Box, Tooltip } from '@mantine/core';
import type { Player } from '../types';

interface ScorecardTableProps {
  players: Player[];
  par?: (number | null)[];
  onPlayerUpdate: (playerIndex: number, updatedPlayer: Player) => void;
}

const columnHelper = createColumnHelper<Player>();

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

export function ScorecardTable({ players, par, onPlayerUpdate }: ScorecardTableProps) {
  const columns = useMemo(() => {
    const baseColumns = [
      columnHelper.accessor('name', {
        header: 'Player',
        size: 150,
        cell: (info) => (
          <TextInput
            value={info.getValue()}
            onChange={(e) => {
              const player = info.row.original;
              onPlayerUpdate(info.row.index, { ...player, name: e.target.value });
            }}
            size="sm"
            styles={{ input: { fontWeight: 600 } }}
          />
        ),
      }),
    ];

    // Holes 1-9
    const frontNineColumns = Array.from({ length: 9 }, (_, i) =>
      columnHelper.display({
        id: `hole-${i + 1}`,
        header: () => <div style={{ textAlign: 'center', fontWeight: 700 }}>{i + 1}</div>,
        size: 45,
        cell: (info) => {
          const player = info.row.original;
          const score = player.scores[i];
          const holePar = par?.[i] ?? null;
          const hasData = score !== null;
          const scoring = getScoringType(score, holePar); 
          
          const cell = (
            <Box pos="relative" >
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
                value={score ?? ''}
                onChange={(e) => {
                  const newScores = [...player.scores];
                  newScores[i] = e.target.value === '' ? null : parseInt(e.target.value);
                  onPlayerUpdate(info.row.index, { ...player, scores: newScores });
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
        },
      })
    );

    const outColumn = columnHelper.accessor('front_nine_total', {
      header: 'Out',
      size: 50,
      cell: (info) => (
        <div style={{ textAlign: 'center', fontWeight: 700, fontSize: '14px', color: '#228be6' }}>
          {info.getValue() ?? '-'}
        </div>
      ),
    });

    // Holes 10-18
    const backNineColumns = Array.from({ length: 9 }, (_, i) =>
      columnHelper.display({
        id: `hole-${i + 10}`,
        header: () => <div style={{ textAlign: 'center', fontWeight: 700 }}>{i + 10}</div>,
        size: 45,
        cell: (info) => {
          const player = info.row.original;
          const holeIndex = i + 9;
          const score = player.scores[holeIndex];
          const holePar = par?.[holeIndex] ?? null;
          const hasData = score !== null;
          const scoring = getScoringType(score, holePar);
          
          const cell = (
            <Box pos="relative" >
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
                value={score ?? ''}
                onChange={(e) => {
                  const newScores = [...player.scores];
                  newScores[holeIndex] = e.target.value === '' ? null : parseInt(e.target.value);
                  onPlayerUpdate(info.row.index, { ...player, scores: newScores });
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
        },
      })
    );

    const inColumn = columnHelper.accessor('back_nine_total', {
      header: 'In',
      size: 50,
      cell: (info) => (
        <div style={{ textAlign: 'center', fontWeight: 700, fontSize: '14px', color: '#228be6' }}>
          {info.getValue() ?? '-'}
        </div>
      ),
    });

    const totalColumn = columnHelper.accessor('total', {
      header: 'Total',
      size: 60,
      cell: (info) => (
        <div style={{ 
          textAlign: 'center', 
          fontWeight: 700, 
          fontSize: '16px',
          padding: '4px 8px',
          backgroundColor: '#228be6',
          color: 'white',
          borderRadius: '4px',
        }}>
          {info.getValue() ?? '-'}
        </div>
      ),
    });

    return [...baseColumns, ...frontNineColumns, outColumn, ...backNineColumns, inColumn, totalColumn];
  }, [onPlayerUpdate, par]);

  const table = useReactTable({
    data: players,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <Box style={{ overflowX: 'auto' }}>
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
          {table.getHeaderGroups().map((headerGroup) => (
            <Table.Tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <Table.Th 
                  key={header.id}
                  style={{ 
                    padding: '8px 4px',
                    textAlign: 'center',
                  }}
                >
                  {flexRender(header.column.columnDef.header, header.getContext())}
                </Table.Th>
              ))}
            </Table.Tr>
          ))}
        </Table.Thead>
        
        <Table.Tbody>
          {table.getRowModel().rows.map((row) => (
            <Table.Tr key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <Table.Td 
                  key={cell.id}
                  style={{ 
                    padding: '4px',
                    textAlign: 'center',
                  }}
                >
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </Table.Td>
              ))}
            </Table.Tr>
          ))}
        </Table.Tbody>

        {/* Par row at bottom */}
        {par && (
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
            </Table.Tr>
          </Table.Tfoot>
        )}
      </Table>
    </Box>
  );
}