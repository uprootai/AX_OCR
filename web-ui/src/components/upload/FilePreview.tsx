import { useState, useEffect } from 'react';
import { File as FileIcon, X, Image as ImageIcon } from 'lucide-react';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';

interface FilePreviewProps {
  file: File;
  onRemove: () => void;
}

export function FilePreview({ file, onRemove }: FilePreviewProps) {
  const [preview, setPreview] = useState<string | null>(null);

  useEffect(() => {
    // Create preview for images
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    } else {
      setPreview(null);
    }

    return () => {
      setPreview(null);
    };
  }, [file]);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start gap-4">
          {preview ? (
            <img
              src={preview}
              alt="미리보기"
              className="w-24 h-24 object-cover rounded border"
            />
          ) : (
            <div className="w-24 h-24 bg-accent rounded border flex items-center justify-center">
              {file.type === 'application/pdf' ? (
                <FileIcon className="h-8 w-8 text-muted-foreground" />
              ) : (
                <ImageIcon className="h-8 w-8 text-muted-foreground" />
              )}
            </div>
          )}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{file.name}</p>
                <p className="text-sm text-muted-foreground mt-1">
                  {formatFileSize(file.size)} · {file.type || '알 수 없음'}
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={onRemove}
                className="flex-shrink-0"
                aria-label="파일 제거"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
