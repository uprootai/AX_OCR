import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import PipelineConclusionCard from './PipelineConclusionCard';

// Mock react-i18next — return translation key as the display value
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, fallback?: string) => fallback ?? key,
  }),
}));

// Mock lucide-react
vi.mock('lucide-react', () => ({
  Target: () => <span data-testid="icon-target" />,
  Ruler: () => <span data-testid="icon-ruler" />,
  AlertCircle: () => <span data-testid="icon-alert-circle" />,
  CheckCircle2: () => <span data-testid="icon-check-circle2" />,
  Layers: () => <span data-testid="icon-layers" />,
  Boxes: () => <span data-testid="icon-boxes" />,
  ClipboardList: () => <span data-testid="icon-clipboard-list" />,
}));

const emptyExecutionResult = {
  status: 'completed',
  node_statuses: [],
};

const nodesFixture = [
  { id: 'node-1', type: 'yolo', data: { label: 'YOLO Detector' } },
  { id: 'node-2', type: 'ocr', data: { label: 'OCR Reader' } },
];

describe('PipelineConclusionCard', () => {
  it('returns null when executionResult has no useful data', () => {
    const { container } = render(
      <PipelineConclusionCard
        executionResult={emptyExecutionResult}
        nodes={nodesFixture}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('returns null when node_statuses produce no detections, dimensions, gdt, pid symbols, or bom items', () => {
    const result = {
      status: 'completed',
      node_statuses: [
        {
          node_id: 'node-1',
          status: 'success',
          output: { some_other_field: 'value' },
        },
      ],
    };

    const { container } = render(
      <PipelineConclusionCard executionResult={result} nodes={nodesFixture} />
    );

    expect(container.firstChild).toBeNull();
  });

  it('renders detection count stat card when detections are present', () => {
    const result = {
      status: 'completed',
      node_statuses: [
        {
          node_id: 'node-1',
          status: 'success',
          output: {
            detections: [
              { class_name: 'bolt', confidence: 0.9, bbox: [10, 10, 50, 50] },
              { class_name: 'nut', confidence: 0.85, bbox: [60, 60, 100, 100] },
            ],
          },
        },
      ],
    };

    render(<PipelineConclusionCard executionResult={result} nodes={nodesFixture} />);

    // The detection count should appear as the stat value
    expect(screen.getByText('2')).toBeInTheDocument();
    // Fallback label text from t() mock
    expect(screen.getByText('검출 객체')).toBeInTheDocument();
  });

  it('renders dimension count stat card when dimensions are present', () => {
    const result = {
      status: 'completed',
      node_statuses: [
        {
          node_id: 'node-2',
          status: 'success',
          output: {
            dimensions: [
              { type: 'linear', text: '25mm' },
              { type: 'radial', text: 'R10' },
              { type: 'angular', text: '45°' },
            ],
          },
        },
      ],
    };

    render(<PipelineConclusionCard executionResult={result} nodes={nodesFixture} />);

    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('치수')).toBeInTheDocument();
  });

  it('shows grouped detection badges with class name and count', () => {
    const result = {
      status: 'completed',
      node_statuses: [
        {
          node_id: 'node-1',
          status: 'success',
          output: {
            detections: [
              { class_name: 'bolt', confidence: 0.9 },
              { class_name: 'bolt', confidence: 0.8 },
              { class_name: 'nut', confidence: 0.75 },
            ],
          },
        },
      ],
    };

    render(<PipelineConclusionCard executionResult={result} nodes={nodesFixture} />);

    // Badge for "bolt" group — class name appears as text
    expect(screen.getByText('bolt')).toBeInTheDocument();
    // Badge for "nut" group
    expect(screen.getByText('nut')).toBeInTheDocument();
    // Count badge for bolt (2 occurrences)
    expect(screen.getByText('2')).toBeInTheDocument();
    // Count badge for nut (1 occurrence)
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('shows execution time in the footer when execution_time_ms is provided', () => {
    const result = {
      status: 'completed',
      execution_time_ms: 3500,
      node_statuses: [
        {
          node_id: 'node-1',
          status: 'success',
          output: {
            detections: [{ class_name: 'bolt', confidence: 0.9 }],
          },
        },
      ],
    };

    render(<PipelineConclusionCard executionResult={result} nodes={nodesFixture} />);

    // 3500ms = 3.50s
    expect(screen.getByText(/3\.50s/)).toBeInTheDocument();
  });

  it('does not show execution time section when execution_time_ms is absent', () => {
    const result = {
      status: 'completed',
      node_statuses: [
        {
          node_id: 'node-1',
          status: 'success',
          output: {
            detections: [{ class_name: 'bolt', confidence: 0.9 }],
          },
        },
      ],
    };

    render(<PipelineConclusionCard executionResult={result} nodes={nodesFixture} />);

    expect(screen.queryByText(/총 소요 시간/)).not.toBeInTheDocument();
  });

  it('shows GD&T stat card when gdt items are present', () => {
    const result = {
      status: 'completed',
      node_statuses: [
        {
          node_id: 'node-2',
          status: 'success',
          output: {
            gdt: [
              { symbol: '⊕', value: '0.1', datum: 'A' },
              { symbol: '∥', value: '0.05', datum: 'B' },
            ],
          },
        },
      ],
    };

    render(<PipelineConclusionCard executionResult={result} nodes={nodesFixture} />);

    expect(screen.getByText('GD&T')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('shows P&ID symbols stat card when symbols are present', () => {
    const result = {
      status: 'completed',
      node_statuses: [
        {
          node_id: 'node-1',
          status: 'success',
          output: {
            symbols: [
              { class_name: 'valve', confidence: 0.88 },
              { class_name: 'pump', confidence: 0.92 },
            ],
          },
        },
      ],
    };

    render(<PipelineConclusionCard executionResult={result} nodes={nodesFixture} />);

    expect(screen.getByText('P&ID 심볼')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });
});
