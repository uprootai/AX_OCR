import { useState } from 'react';
import { Image as ImageIcon, AlertCircle } from 'lucide-react';
import { SampleFileCard } from './SampleFileCard';

export interface SampleFile {
  id: string;
  name: string;
  path: string;
  description: string;
  type: 'image' | 'pdf';
  recommended?: boolean;
}

interface SampleFileGridProps {
  samples: SampleFile[];
  onSampleSelect: (file: File) => void;
  disabled?: boolean;
}

export function SampleFileGrid({
  samples,
  onSampleSelect,
  disabled = false
}: SampleFileGridProps) {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<string | null>(null);

  const handleSampleSelect = async (sample: SampleFile) => {
    if (disabled) return;

    try {
      setError(null);
      setLoading(sample.id);

      const response = await fetch(sample.path);

      if (!response.ok) {
        throw new Error(`샘플 파일을 로드할 수 없습니다: ${response.statusText}`);
      }

      const blob = await response.blob();
      const filename = sample.path.split('/').pop() || `${sample.id}.pdf`;

      // Determine MIME type from file extension
      let mimeType = blob.type;
      if (!mimeType || mimeType === 'application/octet-stream') {
        if (filename.endsWith('.jpg') || filename.endsWith('.jpeg')) {
          mimeType = 'image/jpeg';
        } else if (filename.endsWith('.png')) {
          mimeType = 'image/png';
        } else if (filename.endsWith('.pdf')) {
          mimeType = 'application/pdf';
        }
      }

      const file = new File([blob], filename, { type: mimeType });
      onSampleSelect(file);
    } catch (err) {
      const message = err instanceof Error ? err.message : '샘플 파일 로드 중 오류가 발생했습니다.';
      setError(message);
      console.error('Sample file load error:', err);
    } finally {
      setLoading(null);
    }
  };

  if (samples.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <ImageIcon className="h-4 w-4 text-muted-foreground" />
        <h3 className="text-sm font-medium">또는 샘플 파일을 선택하세요</h3>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
        {samples.map((sample) => (
          <SampleFileCard
            key={sample.id}
            name={sample.name}
            description={sample.description}
            type={sample.type}
            recommended={sample.recommended}
            onSelect={() => handleSampleSelect(sample)}
            disabled={disabled || loading === sample.id}
          />
        ))}
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <p>{error}</p>
        </div>
      )}
    </div>
  );
}
