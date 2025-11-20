import { useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  createColumnHelper,
} from '@tanstack/react-table';
import { Table, TextInput, Badge } from '@mantine/core';
import type { Player } from '../types/scorecard';

interface ScorecardTableProps {
  players: Player[];
  par?: (number | null)[];
  onPlayerUpdate: (playerIndex: number, updatedPlayer: Player) => void;
}

const columnHelper = createColumnHelper<Player>();

export function ScorecardTable({ players, par, onPlayerUpdate }: ScorecardTableProps) {
  const columns = useMemo(() => {
    // Player name column
    const baseColumns = [
      columnHelper.accessor('name', {
        header: 'Player',
        cell: (info) => (
          <TextInput
            value={info.getValue()}
            onChange={(e) => {
              const player = info.row.original;
              onPlayerUpdate(info.row.index, { ...player, name: e.target.value });
            }}
            size="xs"
          />
        ),
      }),
      columnHelper.accessor('handicap', {
        header: 'HCP',
        cell: (info) => (
          <TextInput
            value={info.getValue() ?? ''}
            onChange={(e) => {
              const player = info.row.original;
              const value = e.target.value === '' ? null : parseInt(e.target.value);
              onPlayerUpdate(info.row.index, { ...player, handicap: value });
            }}
            size="xs"
            type="number"
            style={{ width: '60px' }}
          />
        ),
      }),
    ];

    // Hole columns (1-18)
    const holeColumns = Array.from({ length: 18 }, (_, i) =>
      columnHelper.display({
        id: `hole-${i + 1}`,
        header: () => <div style={{ textAlign: 'center' }}>{i + 1}</div>,
        cell: (info) => {
          const player = info.row.original;
          const score = player.scores[i];
          // CHANGED: Flag cells with null scores
          const hasData = score !== null;
          
          return (
            <TextInput
              value={score ?? ''}
              onChange={(e) => {
                const newScores = [...player.scores];
                newScores[i] = e.target.value === '' ? null : parseInt(e.target.value);
                onPlayerUpdate(info.row.index, { ...player, scores: newScores });
              }}
              size="xs"
              type="number"
              style={{ 
                width: '50px',
                backgroundColor: hasData ? 'transparent' : '#fff3cd'  // Yellow highlight for missing data
              }}
              placeholder="-"
            />
          );
        },
      })
    );

    // Total columns
    const totalColumns = [
      columnHelper.accessor('front_nine_total', {
        header: 'F9',
        cell: (info) => <div style={{ textAlign: 'center', fontWeight: 600 }}>{info.getValue() ?? '-'}</div>,
      }),
      columnHelper.accessor('back_nine_total', {
        header: 'B9',
        cell: (info) => <div style={{ textAlign: 'center', fontWeight: 600 }}>{info.getValue() ?? '-'}</div>,
      }),
      columnHelper.accessor('total', {
        header: 'Total',
        cell: (info) => (
          <Badge color="blue" size="lg">
            {info.getValue() ?? '-'}
          </Badge>
        ),
      }),
    ];

    return [...baseColumns, ...holeColumns, ...totalColumns];
  }, [onPlayerUpdate]);

  const table = useReactTable({
    data: players,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div style={{ overflowX: 'auto' }}>
      <Table striped highlightOnHover withTableBorder>
        <Table.Thead>
          {/* Par row */}
          {par && (
            <Table.Tr>
              <Table.Th>Par</Table.Th>
              <Table.Th></Table.Th>
              {par.map((p, i) => (
                <Table.Th key={i} style={{ textAlign: 'center' }}>
                  {p ?? '-'}
                </Table.Th>
              ))}
              <Table.Th style={{ textAlign: 'center' }}>
                {par.slice(0, 9).filter(p => p !== null).reduce((sum, p) => sum + (p || 0), 0)}
              </Table.Th>
              <Table.Th style={{ textAlign: 'center' }}>
                {par.slice(9, 18).filter(p => p !== null).reduce((sum, p) => sum + (p || 0), 0)}
              </Table.Th>
              <Table.Th style={{ textAlign: 'center' }}>
                {par.filter(p => p !== null).reduce((sum, p) => sum + (p || 0), 0)}
              </Table.Th>
            </Table.Tr>
          )}
          
          {/* Column headers */}
          {table.getHeaderGroups().map((headerGroup) => (
            <Table.Tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <Table.Th key={header.id}>
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
                <Table.Td key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </Table.Td>
              ))}
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </div>
  );
}