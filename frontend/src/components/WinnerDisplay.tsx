import { Card, Text, Badge, Group, TextInput } from '@mantine/core'; // CHANGE: Added TextInput
import { IconTrophy } from '@tabler/icons-react';

interface WinnerDisplayProps {
  winner?: string | null;
  course?: string | null;
  date?: string | null;
  onCourseChange?: (course: string) => void;
  onDateChange?: (date: string) => void;
}

export function WinnerDisplay({ winner, course, date, onCourseChange, onDateChange }: WinnerDisplayProps) {
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
        
        {/* CHANGE: Made course and date editable */}
        <div style={{ textAlign: 'right' }}>
          {onCourseChange ? (
            <TextInput
              value={course || ''}
              onChange={(e) => onCourseChange(e.target.value)}
              placeholder="Course name"
              size="sm"
              styles={{ input: { textAlign: 'right' } }}
            />
          ) : course ? (
            <Text size="sm" c="dimmed">
              {course}
            </Text>
          ) : null}
          
          {onDateChange ? (
            <TextInput
              value={date || ''}
              onChange={(e) => onDateChange(e.target.value)}
              placeholder="Date"
              size="xs"
              styles={{ input: { textAlign: 'right' } }}
              mt={4}
            />
          ) : date ? (
            <Text size="xs" c="dimmed">
              {date}
            </Text>
          ) : null}
        </div>
      </Group>
      
      <Badge color="green" variant="light" size="sm">
        Stroke Play - Lowest Score Wins
      </Badge>
    </Card>
  );
}