import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { X, FileText } from 'lucide-react';
import { Button } from '../ui/Button';

interface FilePreviewProps {
  file: File;
  onRemove?: () => void;
}

export function FilePreview({ file, onRemove }: FilePreviewProps) {
  const [preview, setPreview] = useState<string>('');
  const isImage = file.type.startsWith('image/');

  useEffect(() => {
    if (isImage) {
      const reader = new FileReader();
      reader.onloadend = () => setPreview(reader.result as string);
      reader.readAsDataURL(file);
    }

    return () => {
      if (preview) {
        URL.revokeObjectURL(preview);
      }
    };
  }, [file, isImage]);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-base">업로드된 파일</CardTitle>
        {onRemove && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onRemove}
            aria-label="파일 제거"
            className="h-8 w-8 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </CardHeader>
      <CardContent>
        {/* Preview */}
        <div className="relative aspect-video bg-muted rounded-lg overflow-hidden mb-4">
          {isImage ? (
            <img
              src={preview}
              alt={`${file.name} 미리보기`}
              className="object-contain w-full h-full"
            />
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <FileText className="h-16 w-16 mx-auto text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">PDF 파일</p>
              </div>
            </div>
          )}
        </div>

        {/* File Info */}
        <div className="space-y-2 text-sm">
          <div className="flex items-start justify-between gap-2">
            <span className="text-muted-foreground flex-shrink-0">파일명</span>
            <span className="font-medium text-right break-all">{file.name}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">크기</span>
            <span className="font-medium">{formatFileSize(file.size)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">타입</span>
            <span className="font-medium">
              {file.type || '알 수 없음'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">수정일</span>
            <span className="font-medium">
              {new Date(file.lastModified).toLocaleDateString('ko-KR')}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
