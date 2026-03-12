import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import DetectionResultCard from './DetectionResultCard';

// Mock lucide-react
vi.mock('lucide-react', () => ({
  CheckCircle2: () => <span data-testid="icon-check-circle2" />,
  XCircle: () => <span data-testid="icon-x-circle" />,
  AlertTriangle: () => <span data-testid="icon-alert-triangle" />,
  Eye: () => <span data-testid="icon-eye" />,
  EyeOff: () => <span data-testid="icon-eye-off" />,
  Loader2: () => <span data-testid="icon-loader2" />,
}));

// Mock detection types module
vi.mock('../../types/detection', () => ({
  DETECTION_COLORS: {
    TP: { stroke: 'green', fill: 'rgba(0,255,0,0.1)', label: 'green' },
    FP: { stroke: 'red', fill: 'rgba(255,0,0,0.1)', label: 'red' },
    FN: { stroke: 'yellow', fill: 'rgba(255,255,0,0.1)', label: 'yellow', dash: [5, 5] },
  },
  parseYOLOFormat: vi.fn(() => []),
  compareWithGT: vi.fn(() => ({
    tp_matches: [],
    fp_detections: [],
    fn_labels: [],
    gt_count: 0,
    metrics: { precision: 1, recall: 1, f1_score: 1, tp: 0, fp: 0, fn: 0 },
  })),
  normalizeBBox: vi.fn((bbox) => bbox),
}));

// Mock canvas API — jsdom does not implement getContext
const mockGetContext = vi.fn(() => ({
  drawImage: vi.fn(),
  fillRect: vi.fn(),
  strokeRect: vi.fn(),
  fillText: vi.fn(),
  measureText: vi.fn(() => ({ width: 50 })),
  setLineDash: vi.fn(),
  clearRect: vi.fn(),
}));

beforeEach(() => {
  vi.clearAllMocks();

  // Stub HTMLCanvasElement.getContext
  HTMLCanvasElement.prototype.getContext = mockGetContext as unknown as typeof HTMLCanvasElement.prototype.getContext;

  // Stub global Image so src assignment triggers onload synchronously
  const OrigImage = globalThis.Image;
  vi.stubGlobal(
    'Image',
    class MockImage {
      onload: (() => void) | null = null;
      onerror: (() => void) | null = null;
      width = 640;
      height = 480;
      set src(_val: string) {
        // Trigger onload on next microtask to simulate async image load
        Promise.resolve().then(() => this.onload?.());
      }
    }
  );

  // Stub global fetch — GT files should not be found
  vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: false })));

  return () => {
    vi.unstubAllGlobals();
    globalThis.Image = OrigImage;
  };
});

const makeNodeStatus = (overrides = {}) => ({
  nodeId: 'node-1',
  status: 'completed' as const,
  progress: 1,
  ...overrides,
});

describe('DetectionResultCard', () => {
  it('returns null when there is no output and no detections', () => {
    const nodeStatus = makeNodeStatus({ output: undefined });

    const { container } = render(
      <DetectionResultCard
        nodeStatus={nodeStatus}
        uploadedImage={null}
        uploadedFileName={null}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('renders detection summary with count and confidence when detections are present', () => {
    const nodeStatus = makeNodeStatus({
      output: {
        detections: [
          { class_name: 'bolt', confidence: 0.9, bbox: { x1: 0, y1: 0, x2: 50, y2: 50 } },
          { class_name: 'nut', confidence: 0.8, bbox: { x1: 60, y1: 60, x2: 110, y2: 110 } },
        ],
      },
    });

    render(
      <DetectionResultCard
        nodeStatus={nodeStatus}
        uploadedImage={null}
        uploadedFileName={null}
      />
    );

    // Detection count — "2개"
    expect(screen.getByText('2개')).toBeInTheDocument();
    // Average confidence — (0.9 + 0.8) / 2 = 0.85 → 85.0%
    expect(screen.getByText('85.0%')).toBeInTheDocument();
  });

  it('shows elapsed time in seconds when elapsedSeconds is provided', () => {
    const nodeStatus = makeNodeStatus({
      elapsedSeconds: 2.734,
      output: {
        detections: [
          { class_name: 'bolt', confidence: 0.9, bbox: { x1: 0, y1: 0, x2: 50, y2: 50 } },
        ],
      },
    });

    render(
      <DetectionResultCard
        nodeStatus={nodeStatus}
        uploadedImage={null}
        uploadedFileName={null}
      />
    );

    expect(screen.getByText('2.7s')).toBeInTheDocument();
  });

  it('does not show elapsed time when elapsedSeconds is not provided', () => {
    const nodeStatus = makeNodeStatus({
      output: {
        detections: [
          { class_name: 'bolt', confidence: 0.9, bbox: { x1: 0, y1: 0, x2: 50, y2: 50 } },
        ],
      },
    });

    render(
      <DetectionResultCard
        nodeStatus={nodeStatus}
        uploadedImage={null}
        uploadedFileName={null}
      />
    );

    // Should have no "s" time indicator separate from confidence percentages
    expect(screen.queryByText(/^\d+\.\ds$/)).not.toBeInTheDocument();
  });

  it('shows JSON data details section when output is present', () => {
    const nodeStatus = makeNodeStatus({
      output: {
        detections: [
          { class_name: 'bolt', confidence: 0.9, bbox: { x1: 0, y1: 0, x2: 50, y2: 50 } },
        ],
      },
    });

    render(
      <DetectionResultCard
        nodeStatus={nodeStatus}
        uploadedImage={null}
        uploadedFileName={null}
      />
    );

    expect(screen.getByText('JSON 데이터 보기')).toBeInTheDocument();
  });

  it('does not show JSON data details section when output is absent', () => {
    // output is undefined so the component returns null — verify nothing is rendered
    const nodeStatus = makeNodeStatus({ output: undefined });

    const { container } = render(
      <DetectionResultCard
        nodeStatus={nodeStatus}
        uploadedImage={null}
        uploadedFileName={null}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('renders the AI detection result header label', () => {
    const nodeStatus = makeNodeStatus({
      output: {
        detections: [
          { class_name: 'bolt', confidence: 0.95, bbox: { x1: 0, y1: 0, x2: 50, y2: 50 } },
        ],
      },
    });

    render(
      <DetectionResultCard
        nodeStatus={nodeStatus}
        uploadedImage={null}
        uploadedFileName={null}
      />
    );

    expect(screen.getByText('AI 검출 결과')).toBeInTheDocument();
  });

  it('renders single detection with 100% confidence correctly', () => {
    const nodeStatus = makeNodeStatus({
      output: {
        detections: [
          { class_name: 'flange', confidence: 1.0, bbox: { x1: 0, y1: 0, x2: 80, y2: 80 } },
        ],
      },
    });

    render(
      <DetectionResultCard
        nodeStatus={nodeStatus}
        uploadedImage={null}
        uploadedFileName={null}
      />
    );

    expect(screen.getByText('1개')).toBeInTheDocument();
    expect(screen.getByText('100.0%')).toBeInTheDocument();
  });
});
