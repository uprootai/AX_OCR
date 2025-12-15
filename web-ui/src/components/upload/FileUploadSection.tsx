import { FileDropzone } from './FileDropzone';
import { FilePreview } from './FilePreview';
import { SampleFileGrid, type SampleFile } from './SampleFileGrid';

interface FileUploadSectionProps {
  onFileSelect: (file: File | null) => void;
  currentFile?: File | null;
  accept?: Record<string, string[]>;
  maxSize?: number; // in bytes
  disabled?: boolean;
  showSamples?: boolean;
  samples?: SampleFile[];
}

// Default sample files
const DEFAULT_SAMPLES: SampleFile[] = [
  {
    id: 'sample-1',
    name: 'Intermediate Shaft (Image)',
    path: '/samples/sample2_interm_shaft.jpg',
    description: '선박 중간축 도면 - 모든 분석 지원',
    type: 'image',
    recommended: true
  },
  {
    id: 'sample-2',
    name: 'S60ME-C Shaft (Korean)',
    path: '/samples/sample3_s60me_shaft.jpg',
    description: 'S60ME-C 중간축 도면 - 한글 포함',
    type: 'image'
  },
  {
    id: 'sample-6',
    name: 'P&ID Diagram',
    path: '/samples/sample6_pid_diagram.png',
    description: 'P&ID 배관계장도 - 심볼/라인 검출',
    type: 'image'
  },
  {
    id: 'sample-7',
    name: 'MCP Panel Body (BOM)',
    path: '/samples/sample7_mcp_panel_body.jpg',
    description: '전기 제어판 도면 - BOM 부품 검출',
    type: 'image'
  },
  {
    id: 'sample-8',
    name: 'Control Panel Blueprint 1',
    path: '/samples/sample8_blueprint_31.jpg',
    description: '제어판 도면 - BOM 부품 검출',
    type: 'image'
  },
  {
    id: 'sample-9',
    name: 'Control Panel Blueprint 2',
    path: '/samples/sample9_blueprint_35.jpg',
    description: '제어판 도면 - BOM 부품 검출',
    type: 'image'
  },
  {
    id: 'sample-3',
    name: 'Intermediate Shaft (PDF)',
    path: '/samples/sample1_interm_shaft.pdf',
    description: '선박 중간축 도면 - OCR/공차 분석만',
    type: 'pdf'
  },
  {
    id: 'sample-4',
    name: 'Handrail Carrier (PDF)',
    path: '/samples/sample4_handrail_carrier.pdf',
    description: '핸드레일 캐리어 - OCR/공차 분석만',
    type: 'pdf'
  },
  {
    id: 'sample-5',
    name: 'Cover Locking (PDF)',
    path: '/samples/sample5_cover_locking.pdf',
    description: '커버 잠금 장치 - OCR/공차 분석만',
    type: 'pdf'
  }
];

export function FileUploadSection({
  onFileSelect,
  currentFile = null,
  accept = {
    'image/*': ['.png', '.jpg', '.jpeg'],
    'application/pdf': ['.pdf']
  },
  maxSize = 10485760, // 10MB
  disabled = false,
  showSamples = true,
  samples = DEFAULT_SAMPLES
}: FileUploadSectionProps) {
  const handleFileRemove = () => {
    onFileSelect(null);
  };

  return (
    <div className="space-y-4">
      {!currentFile ? (
        <>
          <FileDropzone
            onFileSelect={onFileSelect}
            accept={accept}
            maxSize={maxSize}
            disabled={disabled}
          />

          {showSamples && samples.length > 0 && (
            <SampleFileGrid
              samples={samples}
              onSampleSelect={onFileSelect}
              disabled={disabled}
            />
          )}
        </>
      ) : (
        <FilePreview
          file={currentFile}
          onRemove={handleFileRemove}
        />
      )}
    </div>
  );
}
