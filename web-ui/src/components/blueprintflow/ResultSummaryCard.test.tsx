import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ResultSummaryCard from './ResultSummaryCard';

// Mock lucide-react
vi.mock('lucide-react', () => ({
  CheckCircle: () => <span data-testid="icon-check-circle" />,
  XCircle: () => <span data-testid="icon-x-circle" />,
  Clock: () => <span data-testid="icon-clock" />,
  AlertTriangle: () => <span data-testid="icon-alert-triangle" />,
}));

const successNode = {
  nodeId: 'node-1',
  nodeType: 'YOLO Detector',
  status: 'success' as const,
  executionTime: 1200,
};

const errorNode = {
  nodeId: 'node-2',
  nodeType: 'OCR Reader',
  status: 'error' as const,
};

const pendingNode = {
  nodeId: 'node-3',
  nodeType: 'BOM Generator',
  status: 'pending' as const,
};

describe('ResultSummaryCard', () => {
  it('renders "Pipeline Summary" heading', () => {
    render(<ResultSummaryCard results={[successNode]} />);

    expect(screen.getByText('Pipeline Summary')).toBeInTheDocument();
  });

  it('shows correct success count', () => {
    render(<ResultSummaryCard results={[successNode, successNode, errorNode]} />);

    expect(screen.getByText(/2 success/)).toBeInTheDocument();
  });

  it('shows correct error count when errors are present', () => {
    render(<ResultSummaryCard results={[successNode, errorNode, errorNode]} />);

    expect(screen.getByText(/2 failed/)).toBeInTheDocument();
  });

  it('does not show error count section when there are no errors', () => {
    render(<ResultSummaryCard results={[successNode]} />);

    expect(screen.queryByText(/failed/)).not.toBeInTheDocument();
  });

  it('shows pending count when pending nodes are present', () => {
    render(<ResultSummaryCard results={[successNode, pendingNode, pendingNode]} />);

    expect(screen.getByText(/2 pending/)).toBeInTheDocument();
  });

  it('does not show pending count when there are no pending nodes', () => {
    render(<ResultSummaryCard results={[successNode]} />);

    expect(screen.queryByText(/pending/)).not.toBeInTheDocument();
  });

  it('shows total execution time formatted in seconds when provided', () => {
    render(<ResultSummaryCard results={[successNode]} totalExecutionTime={4500} />);

    // 4500ms = 4.50s
    expect(screen.getByText('4.50s')).toBeInTheDocument();
  });

  it('does not show execution time badge when totalExecutionTime is not provided', () => {
    render(<ResultSummaryCard results={[successNode]} />);

    // The totalExecutionTime badge (4.50s format) should not appear,
    // but individual node times (1.20s) may still show in the node list
    expect(screen.queryByText('4.50s')).not.toBeInTheDocument();
  });

  it('shows OCR stats section when dimensions are present', () => {
    const nodeWithOCR = {
      nodeId: 'node-1',
      nodeType: 'OCR',
      status: 'success' as const,
      output: {
        dimensions: [{ type: 'linear', text: '25mm' }, { type: 'radial', text: 'R5' }],
      },
    };

    render(<ResultSummaryCard results={[nodeWithOCR]} />);

    expect(screen.getByText('Dims: 2')).toBeInTheDocument();
  });

  it('shows GD&T count in OCR section when gdt items are present', () => {
    const nodeWithGDT = {
      nodeId: 'node-1',
      nodeType: 'OCR',
      status: 'success' as const,
      output: {
        dimensions: [{ type: 'linear', text: '10mm' }],
        gdt: [{ symbol: '⊕', value: '0.1' }, { symbol: '∥', value: '0.05' }],
      },
    };

    render(<ResultSummaryCard results={[nodeWithGDT]} />);

    expect(screen.getByText('GD&T: 2')).toBeInTheDocument();
  });

  it('shows text blocks count in OCR section when total_blocks is provided', () => {
    const nodeWithBlocks = {
      nodeId: 'node-1',
      nodeType: 'OCR',
      status: 'success' as const,
      output: {
        dimensions: [{ type: 'linear', text: '5mm' }],
        text: { total_blocks: 7 },
      },
    };

    render(<ResultSummaryCard results={[nodeWithBlocks]} />);

    expect(screen.getByText('Blocks: 7')).toBeInTheDocument();
  });

  it('lists individual node results with nodeType label', () => {
    render(
      <ResultSummaryCard
        results={[successNode, errorNode, pendingNode]}
      />
    );

    expect(screen.getByText('YOLO Detector')).toBeInTheDocument();
    expect(screen.getByText('OCR Reader')).toBeInTheDocument();
    expect(screen.getByText('BOM Generator')).toBeInTheDocument();
  });

  it('shows individual node execution time when executionTime is provided', () => {
    render(<ResultSummaryCard results={[successNode]} />);

    // successNode.executionTime = 1200ms = 1.20s
    expect(screen.getByText('1.20s')).toBeInTheDocument();
  });

  it('does not show individual node execution time when executionTime is absent', () => {
    const nodeNoTime = {
      nodeId: 'node-1',
      nodeType: 'YOLO',
      status: 'success' as const,
    };

    render(<ResultSummaryCard results={[nodeNoTime]} />);

    // No "Xs" formatted time in the node list
    expect(screen.queryByText(/^\d+\.\d+s$/)).not.toBeInTheDocument();
  });

  it('renders "Node Results" section label', () => {
    render(<ResultSummaryCard results={[successNode]} />);

    expect(screen.getByText('Node Results')).toBeInTheDocument();
  });

  it('handles empty results array without crashing', () => {
    render(<ResultSummaryCard results={[]} />);

    expect(screen.getByText('Pipeline Summary')).toBeInTheDocument();
    expect(screen.getByText(/0 success/)).toBeInTheDocument();
  });
});
