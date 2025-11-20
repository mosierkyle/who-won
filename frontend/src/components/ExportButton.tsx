import { Button, Group } from '@mantine/core';
import { IconDownload } from '@tabler/icons-react';
import { scorecardApi } from '../services/api';
import { useState } from 'react';
import type { ScorecardData } from '../types';

interface ExportButtonProps {
  data: ScorecardData;
}

export function ExportButton({ data }: ExportButtonProps) {
  const [loading, setLoading] = useState(false);

  const handleExport = async (format: 'csv' | 'excel') => {
    try {
      setLoading(true);
      const blob = await scorecardApi.exportScorecard({ data, format });

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `scorecard.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Group>
      <Button
        leftSection={<IconDownload size={16} />}
        onClick={() => handleExport('csv')}
        loading={loading}
        variant="light"
      >
        Export CSV
      </Button>
      
      {/* Excel export - Phase 1.5 */}
      <Button
        leftSection={<IconDownload size={16} />}
        onClick={() => handleExport('excel')}
        loading={loading}
        variant="light"
        disabled
      >
        Export Excel (Coming Soon)
      </Button>
    </Group>
  );
}