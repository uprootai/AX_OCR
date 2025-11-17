import { useDropzone } from 'react-dropzone';
import { Upload, FolderOpen } from 'lucide-react';

interface FileDropzoneProps {
  onFileSelect: (file: File) => void;
  accept?: Record<string, string[]>;
  maxSize?: number;
  disabled?: boolean;
}

export function FileDropzone({
  onFileSelect,
  accept = {
    'image/*': ['.png', '.jpg', '.jpeg'],
    'application/pdf': ['.pdf']
  },
  maxSize = 10485760, // 10MB
  disabled = false
}: FileDropzoneProps) {
  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    accept,
    maxSize,
    multiple: false,
    disabled,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        onFileSelect(acceptedFiles[0]);
      }
    }
  });

  return (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
        transition-all duration-200
        ${isDragActive && !isDragReject
          ? 'border-primary bg-primary/10 scale-[1.02]'
          : isDragReject
          ? 'border-destructive bg-destructive/10'
          : 'border-muted-foreground/25 hover:border-primary/50 hover:bg-accent/50'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
      role="button"
      aria-label="파일 업로드 영역"
      tabIndex={disabled ? -1 : 0}
    >
      <input {...getInputProps()} aria-label="파일 선택 input" />

      <Upload
        className={`mx-auto h-12 w-12 mb-4 transition-colors ${
          isDragActive ? 'text-primary' : 'text-muted-foreground'
        }`}
      />

      {isDragActive ? (
        isDragReject ? (
          <div>
            <p className="text-lg font-medium text-destructive mb-2">
              지원하지 않는 파일 형식입니다
            </p>
            <p className="text-sm text-muted-foreground">
              PNG, JPG, PDF 파일만 업로드 가능합니다
            </p>
          </div>
        ) : (
          <p className="text-lg font-medium text-primary">
            파일을 여기에 놓으세요
          </p>
        )
      ) : (
        <div>
          <p className="text-lg font-medium mb-4">
            도면 파일을 드래그하여 업로드
          </p>
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="flex-1 h-px bg-border"></div>
            <span className="text-xs text-muted-foreground">또는</span>
            <div className="flex-1 h-px bg-border"></div>
          </div>
          <button
            type="button"
            className="inline-flex items-center justify-center gap-2 px-6 py-3
                     bg-background border-2 border-input rounded-lg
                     hover:bg-accent hover:text-accent-foreground
                     transition-colors font-medium"
            onClick={(e: React.MouseEvent<HTMLButtonElement>) => {
              e.stopPropagation();
            }}
          >
            <FolderOpen className="h-5 w-5" />
            파일 선택
          </button>
          <p className="text-xs text-muted-foreground mt-3">
            PNG, JPG, PDF 지원 (최대 10MB)
          </p>
        </div>
      )}
    </div>
  );
}
