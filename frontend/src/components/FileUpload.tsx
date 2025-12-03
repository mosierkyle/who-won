import { Dropzone, IMAGE_MIME_TYPE } from '@mantine/dropzone';
import { Text, Group, rem } from '@mantine/core';
import { IconUpload, IconX, IconPhoto } from '@tabler/icons-react';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  loading: boolean;
}

export function FileUpload({ onFileSelect, loading }: FileUploadProps) {
  return (
    <Dropzone
      onDrop={(files) => onFileSelect(files[0])}
      onReject={(files) => console.log('rejected files', files)}
      maxSize={50 * 1024 ** 2}
      accept={IMAGE_MIME_TYPE}
      loading={loading}
      multiple={false}
    >
      <Group justify="center" gap="xl" mih={220} style={{ pointerEvents: 'none' }}>
        <Dropzone.Accept>
          <IconUpload
            style={{ width: rem(52), height: rem(52), color: 'var(--mantine-color-blue-6)' }}
            stroke={1.5}
          />
        </Dropzone.Accept>
        <Dropzone.Reject>
          <IconX
            style={{ width: rem(52), height: rem(52), color: 'var(--mantine-color-red-6)' }}
            stroke={1.5}
          />
        </Dropzone.Reject>
        <Dropzone.Idle>
          <IconPhoto
            style={{ width: rem(52), height: rem(52), color: 'var(--mantine-color-dimmed)' }}
            stroke={1.5}
          />
        </Dropzone.Idle>

        <div>
          <Text size="xl" inline>
            Drag scorecard image here or click to select
          </Text>
          <Text size="sm" c="dimmed" inline mt={7}>
            Upload a golf scorecard image (max 5MB)
          </Text>
        </div>
      </Group>
    </Dropzone>
  );
}