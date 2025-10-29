import { useState, useCallback, type DragEvent, type ChangeEvent } from 'react';
import { Upload, File, X, AlertCircle, Image } from 'lucide-react';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';

interface FileUploaderProps {
  onFileSelect: (file: File | null) => void;
  accept?: string;
  maxSize?: number; // in MB
  currentFile?: File | null;
}

interface SampleFile {
  name: string;
  path: string;
  description: string;
}

const SAMPLE_FILES: SampleFile[] = [
  {
    name: 'Intermediate Shaft (Image) ⭐',
    path: '/samples/sample2_interm_shaft.jpg',
    description: '선박 중간축 도면 - 모든 분석 지원 (권장)',
  },
  {
    name: 'S60ME-C Shaft (Korean)',
    path: '/samples/sample3_s60me_shaft.jpg',
    description: 'S60ME-C 중간축 도면 - 한글 포함',
  },
  {
    name: 'Intermediate Shaft (PDF)',
    path: '/samples/sample1_interm_shaft.pdf',
    description: '선박 중간축 도면 - OCR/공차 분석만',
  },
  {
    name: 'Handrail Carrier (PDF)',
    path: '/samples/sample4_handrail_carrier.pdf',
    description: '핸드레일 캐리어 - OCR/공차 분석만',
  },
  {
    name: 'Cover Locking (PDF)',
    path: '/samples/sample5_cover_locking.pdf',
    description: '커버 잠금 장치 - OCR/공차 분석만',
  },
];

export default function FileUploader({
  onFileSelect,
  accept = 'image/*,.pdf',
  maxSize = 10,
  currentFile = null,
}: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

  const validateFile = (file: File): string | null => {
    // Check file size
    const sizeMB = file.size / (1024 * 1024);
    if (sizeMB > maxSize) {
      return `파일 크기가 너무 큽니다. 최대 ${maxSize}MB까지 업로드 가능합니다.`;
    }

    // Check file type
    const acceptedTypes = accept.split(',').map(t => t.trim());
    const isAccepted = acceptedTypes.some(type => {
      if (type === 'image/*') {
        return file.type.startsWith('image/');
      }
      if (type.startsWith('.')) {
        return file.name.toLowerCase().endsWith(type.toLowerCase());
      }
      return file.type === type;
    });

    if (!isAccepted) {
      return '지원하지 않는 파일 형식입니다.';
    }

    return null;
  };

  const handleFile = useCallback(
    (file: File) => {
      setError(null);

      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        return;
      }

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

      onFileSelect(file);
    },
    [onFileSelect, maxSize, accept]
  );

  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFileInput = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleRemove = () => {
    setPreview(null);
    setError(null);
    onFileSelect(null);
  };

  const handleSampleSelect = async (samplePath: string) => {
    if (!samplePath) return;

    try {
      setError(null);
      const response = await fetch(samplePath);

      if (!response.ok) {
        throw new Error('샘플 파일을 로드할 수 없습니다.');
      }

      const blob = await response.blob();
      const filename = samplePath.split('/').pop() || 'sample.pdf';

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

      const file = new (window as any).File([blob], filename, { type: mimeType }) as File;

      handleFile(file);
    } catch (err) {
      setError(err instanceof Error ? err.message : '샘플 파일 로드 중 오류가 발생했습니다.');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="space-y-4">
      {!currentFile ? (
        <>
          <div
            onDragEnter={handleDragEnter}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`relative border-2 border-dashed rounded-lg transition-colors ${
              isDragging
                ? 'border-primary bg-primary/5'
                : 'border-border hover:border-primary/50'
            }`}
          >
            <input
              type="file"
              id="file-upload"
              className="hidden"
              accept={accept}
              onChange={handleFileInput}
            />
            <label
              htmlFor="file-upload"
              className="flex flex-col items-center justify-center p-12 cursor-pointer"
            >
              <Upload
                className={`h-12 w-12 mb-4 ${
                  isDragging ? 'text-primary' : 'text-muted-foreground'
                }`}
              />
              <p className="text-lg font-medium mb-2">
                {isDragging ? '파일을 놓으세요' : '파일을 선택하거나 드래그하세요'}
              </p>
              <p className="text-sm text-muted-foreground">
                지원 형식: 이미지, PDF (최대 {maxSize}MB)
              </p>
            </label>
          </div>

          {/* Sample File Selector */}
          <div className="relative">
            <div className="flex items-center gap-2 mb-2">
              <Image className="h-4 w-4 text-muted-foreground" />
              <p className="text-sm font-medium">또는 샘플 파일을 선택하세요</p>
            </div>
            <select
              onChange={(e) => handleSampleSelect(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              defaultValue=""
            >
              <option value="" disabled>
                샘플 파일 선택...
              </option>
              {SAMPLE_FILES.map((sample, index) => (
                <option key={index} value={sample.path}>
                  {sample.name} - {sample.description}
                </option>
              ))}
            </select>
          </div>
        </>
      ) : (
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              {preview ? (
                <img
                  src={preview}
                  alt="Preview"
                  className="w-24 h-24 object-cover rounded border"
                />
              ) : (
                <div className="w-24 h-24 bg-accent rounded border flex items-center justify-center">
                  <File className="h-8 w-8 text-muted-foreground" />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{currentFile.name}</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      {formatFileSize(currentFile.size)} · {currentFile.type || '알 수 없음'}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleRemove}
                    className="flex-shrink-0"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {error && (
        <div className="flex items-center gap-2 p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}
    </div>
  );
}
