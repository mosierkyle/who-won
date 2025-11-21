import { useMemo, useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  createColumnHelper,
} from '@tanstack/react-table';
import { Table, TextInput, Badge, Box, Tooltip } from '@mantine/core';
import type { Player } from '../types';

interface ScorecardTableProps {
  players: Player[];
  par?: (number | null)[];
  onPlayerUpdate: (playerIndex: number, updatedPlayer: Player) => void;
}

const columnHelper = createColumnHelper<Player>();

// const getScoringBadge = (score: number | null, par: number | null) => {
//   if (score === null || par === null) return null;
  
//   const diff = score - par;
  
//   if (diff <= -3) return { label: '▲', color: 'grape', title: 'Albatross or better' }; // Triangle
//   if (diff === -2) return { label: '◆◆', color: 'blue', title: 'Eagle' }; // Double circle
//   if (diff === -1) return { label: '◯', color: 'red', title: 'Birdie' }; // Circle
//   if (diff === 0) return null; // Par - no badge
//   if (diff === 1) return { label: '□', color: 'orange', title: 'Bogey' }; // Square
//   if (diff >= 2) return { label: '□□', color: 'dark', title: 'Double Bogey+' }; // Double square
  
//   return null;
// };

export function ScorecardTable({ players, par, onPlayerUpdate }: ScorecardTableProps) {
  const [showScoring, setShowScoring] = useState(true);

  const columns = useMemo(() => {
    const baseColumns = [
      columnHelper.accessor('name', {
        header: 'Player',
        size: 180,
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

    const holeColumns = Array.from({ length: 18 }, (_, i) =>
      columnHelper.display({
        id: `hole-${i + 1}`,
        header: () => (
          <div style={{ textAlign: 'center', fontWeight: 700, fontSize: '12px' }}>
            {i + 1}
          </div>
        ),
        size: 45,
        cell: (info) => {
          const player = info.row.original;
          const score = player.scores[i];
          const holePar = par?.[i] ?? null;
          const hasData = score !== null;
        //   const badge = showScoring ? getScoringBadge(score, holePar) : null;
          
          const cell = (
            <Box pos="relative">
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
                  }
                }}
                placeholder="-"
              />
              {/* {badge && (
                <div style={{
                  position: 'absolute',
                  top: '-2px',
                  right: '2px',
                  fontSize: '10px',
                  color: badge.color,
                }}>
                  {badge.label}
                </div>
              )} */}
            </Box>
          );

          if (!hasData) {
            return (
              <Tooltip label="Missing score - please fill in" position="top">
                {cell}
              </Tooltip>
            );
          }

        //   if (badge && showScoring) {
        //     return (
        //       <Tooltip label={badge.title} position="top">
        //         {cell}
        //       </Tooltip>
        //     );
        //   }

          return cell;
        },
      })
    );

    const totalColumns = [
      columnHelper.accessor('front_nine_total', {
        header: 'Out',
        size: 50,
        cell: (info) => {
          const total = info.getValue();
          return (
            <div style={{ textAlign: 'center', fontWeight: 700, color: '#228be6' }}>
              {total ?? '-'}
            </div>
          );
        },
      }),
      columnHelper.accessor('back_nine_total', {
        header: 'In',
        size: 50,
        cell: (info) => {
          const total = info.getValue();
          return (
            <div style={{ textAlign: 'center', fontWeight: 700, color: '#228be6' }}>
              {total ?? '-'}
            </div>
          );
        },
      }),
      columnHelper.accessor('total', {
        header: 'Total',
        size: 60,
        cell: (info) => (
          <Badge color="blue" size="lg" style={{ minWidth: '50px' }}>
            {info.getValue() ?? '-'}
          </Badge>
        ),
      }),
    ];

    return [...baseColumns, ...holeColumns, ...totalColumns];
  }, [onPlayerUpdate, par, showScoring]);

  const table = useReactTable({
    data: players,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <Box>
      <Table 
        striped 
        highlightOnHover 
        withTableBorder
        style={{ 
          fontSize: '13px',
          tableLayout: 'fixed',
        }}
      >
        <Table.Thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <Table.Tr key={headerGroup.id} style={{ backgroundColor: '#f8f9fa' }}>
              {headerGroup.headers.map((header) => (
                <Table.Th 
                  key={header.id}
                  style={{ 
                    width: header.getSize(),
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
          {/* Player rows */}
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

        {par && (
          <Table.Tfoot>
            <Table.Tr style={{ backgroundColor: '#e9ecef', fontWeight: 700 }}>
              <Table.Td style={{ padding: '8px', textAlign: 'left' }}>Par</Table.Td>
              {par.map((p, i) => (
                <Table.Td key={i} style={{ padding: '4px', textAlign: 'center' }}>
                  {p ?? '-'}
                </Table.Td>
              ))}
              <Table.Td style={{ textAlign: 'center' }}>
                {par.slice(0, 9).filter(p => p !== null).reduce((sum, p) => sum + (p || 0), 0)}
              </Table.Td>
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