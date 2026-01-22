/**
 * Tests for ConfidenceDistributionChart
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ConfidenceDistributionChart, type Detection } from './ConfidenceDistributionChart';

const mockDetections: Detection[] = [
  { confidence: 0.95, class_name: 'diameter_dim' },
  { confidence: 0.85, class_name: 'linear_dim' },
  { confidence: 0.75, class_name: 'radius_dim' },
  { confidence: 0.65, class_name: 'flatness' },
  { confidence: 0.55, class_name: 'position' },
  { confidence: 0.45, class_name: 'text_block' },
  { confidence: 0.35, class_name: 'surface_roughness' },
  { confidence: 0.25, class_name: 'cylindricity' },
  { confidence: 0.15, class_name: 'parallelism' },
  { confidence: 0.05, class_name: 'perpendicularity' },
];

describe('ConfidenceDistributionChart', () => {
  it('should render with default title', () => {
    render(<ConfidenceDistributionChart detections={mockDetections} />);
    expect(screen.getByText('신뢰도 분포')).toBeInTheDocument();
  });

  it('should render with custom title', () => {
    render(<ConfidenceDistributionChart detections={mockDetections} title="Custom Title" />);
    expect(screen.getByText('Custom Title')).toBeInTheDocument();
  });

  it('should display total detection count', () => {
    render(<ConfidenceDistributionChart detections={mockDetections} />);
    expect(screen.getByText('총 10개 검출')).toBeInTheDocument();
  });

  it('should show empty state when no detections', () => {
    render(<ConfidenceDistributionChart detections={[]} />);
    expect(screen.getByText('검출 데이터가 없습니다')).toBeInTheDocument();
  });

  it('should render statistics when showStatistics is true', () => {
    render(<ConfidenceDistributionChart detections={mockDetections} showStatistics={true} />);
    expect(screen.getByText('평균')).toBeInTheDocument();
    expect(screen.getByText('중앙값')).toBeInTheDocument();
    expect(screen.getByText('표준편차')).toBeInTheDocument();
    expect(screen.getByText('최소')).toBeInTheDocument();
    expect(screen.getByText('최대')).toBeInTheDocument();
  });

  it('should hide statistics when showStatistics is false', () => {
    render(<ConfidenceDistributionChart detections={mockDetections} showStatistics={false} />);
    expect(screen.queryByText('평균')).not.toBeInTheDocument();
  });

  it('should render in compact mode', () => {
    const { container } = render(
      <ConfidenceDistributionChart detections={mockDetections} compact={true} />
    );
    // Compact mode should still render the chart
    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
  });

  it('should handle detections with only confidence values', () => {
    const simpleDetections = [
      { confidence: 0.9 },
      { confidence: 0.5 },
      { confidence: 0.1 },
    ];
    render(<ConfidenceDistributionChart detections={simpleDetections} />);
    expect(screen.getByText('총 3개 검출')).toBeInTheDocument();
  });

  it('should filter out invalid confidence values', () => {
    const mixedDetections = [
      { confidence: 0.9 },
      { confidence: NaN },
      { confidence: 0.5 },
      { confidence: 'invalid' as unknown as number }, // Testing invalid runtime data
    ];
    render(<ConfidenceDistributionChart detections={mixedDetections} />);
    expect(screen.getByText('총 2개 검출')).toBeInTheDocument();
  });

  it('should render color legend in non-compact mode', () => {
    render(<ConfidenceDistributionChart detections={mockDetections} compact={false} />);
    expect(screen.getByText('낮음 (<20%)')).toBeInTheDocument();
    expect(screen.getByText('최상 (>80%)')).toBeInTheDocument();
  });

  it('should hide color legend in compact mode', () => {
    render(<ConfidenceDistributionChart detections={mockDetections} compact={true} />);
    expect(screen.queryByText('낮음 (<20%)')).not.toBeInTheDocument();
  });

  describe('statistics calculation', () => {
    it('should display statistics labels', () => {
      const detections = [{ confidence: 0.2 }, { confidence: 0.4 }, { confidence: 0.6 }];
      render(<ConfidenceDistributionChart detections={detections} showStatistics={true} />);
      // Just verify statistics section is rendered
      expect(screen.getByText('평균')).toBeInTheDocument();
      expect(screen.getByText('중앙값')).toBeInTheDocument();
      expect(screen.getByText('총 3개 검출')).toBeInTheDocument();
    });

    it('should display all statistics boxes', () => {
      const detections = [
        { confidence: 0.1 },
        { confidence: 0.5 },
        { confidence: 0.9 },
      ];
      render(<ConfidenceDistributionChart detections={detections} showStatistics={true} />);
      // Verify all stat boxes are present
      expect(screen.getByText('최소')).toBeInTheDocument();
      expect(screen.getByText('최대')).toBeInTheDocument();
    });
  });

  describe('bucket configuration', () => {
    it('should render responsive container for chart', () => {
      const { container } = render(<ConfidenceDistributionChart detections={mockDetections} />);
      // Verify chart container is rendered
      expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
    });

    it('should render chart with different bucket counts', () => {
      const { rerender, container } = render(
        <ConfidenceDistributionChart detections={mockDetections} buckets={5} />
      );
      expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();

      rerender(<ConfidenceDistributionChart detections={mockDetections} buckets={10} />);
      expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
    });
  });
});
