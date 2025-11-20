import { Card, Text, Badge, Group } from '@mantine/core';
import { IconTrophy } from '@tabler/icons-react';

interface WinnerDisplayProps {
  winner?: string | null;
  course?: string | null;
  date?: string | null;
}

export function WinnerDisplay({ winner, course, date }: WinnerDisplayProps) {
  if (!winner) {
    return null;
  }

  return (
    <Card shadow="sm" padding="lg" radius="md" withBorder>
      <Group justify="space-between" mb="xs">
        <Group>
          <IconTrophy size={32} color="gold" />
          <div>
            <Text size="lg" fw={700}>
              Winner
            </Text>
            <Text size="xl" c="blue" fw={900}>
              {winner}
            </Text>
          </div>
        </Group>
        
        <div style={{ textAlign: 'right' }}>
          {course && (
            <Text size="sm" c="dimmed">
              {course}
            </Text>
          )}
          {date && (
            <Text size="xs" c="dimmed">
              {date}
            </Text>
          )}
        </div>
      </Group>
      
      <Badge color="green" variant="light" size="sm">
        Stroke Play - Lowest Score Wins
      </Badge>
    </Card>
  );
}