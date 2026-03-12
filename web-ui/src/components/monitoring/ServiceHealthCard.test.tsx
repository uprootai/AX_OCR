import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ServiceHealthCard from './ServiceHealthCard';
import type { ServiceHealth } from '../../types/api';

// Mock date-fns
vi.mock('date-fns', () => ({
  formatDistanceToNow: vi.fn(() => '2 minutes ago'),
}));

// Mock lucide-react
vi.mock('lucide-react', () => ({
  Activity: () => <span data-testid="icon-activity" />,
  AlertCircle: () => <span data-testid="icon-alert-circle" />,
  CheckCircle: () => <span data-testid="icon-check-circle" />,
  Clock: () => <span data-testid="icon-clock" />,
  ExternalLink: () => <span data-testid="icon-external-link" />,
}));

const baseService: ServiceHealth = {
  name: 'Detection API',
  status: 'healthy',
  latency: 42,
  lastCheck: new Date('2024-01-01T12:00:00Z'),
};

describe('ServiceHealthCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders service name and latency', () => {
    render(<ServiceHealthCard service={baseService} />);

    expect(screen.getByText('Detection API')).toBeInTheDocument();
    expect(screen.getByText('42ms')).toBeInTheDocument();
  });

  it('shows Healthy badge for healthy status', () => {
    render(<ServiceHealthCard service={{ ...baseService, status: 'healthy' }} />);

    expect(screen.getByText('Healthy')).toBeInTheDocument();
  });

  it('shows Degraded badge for degraded status', () => {
    render(<ServiceHealthCard service={{ ...baseService, status: 'degraded' }} />);

    expect(screen.getByText('Degraded')).toBeInTheDocument();
  });

  it('shows Error badge for error status', () => {
    render(<ServiceHealthCard service={{ ...baseService, status: 'error' }} />);

    expect(screen.getByText('Error')).toBeInTheDocument();
  });

  it('shows error count when errorCount is greater than zero', () => {
    render(<ServiceHealthCard service={{ ...baseService, errorCount: 3 }} />);

    expect(screen.getByText('Errors: 3')).toBeInTheDocument();
  });

  it('does not show error count when errorCount is zero', () => {
    render(<ServiceHealthCard service={{ ...baseService, errorCount: 0 }} />);

    expect(screen.queryByText(/Errors:/)).not.toBeInTheDocument();
  });

  it('does not show error count when errorCount is undefined', () => {
    render(<ServiceHealthCard service={baseService} />);

    expect(screen.queryByText(/Errors:/)).not.toBeInTheDocument();
  });

  it('shows external link icon and documentation text when swaggerUrl is provided', () => {
    render(
      <ServiceHealthCard
        service={{ ...baseService, swaggerUrl: 'http://localhost:5005/docs' }}
      />
    );

    expect(screen.getByTestId('icon-external-link')).toBeInTheDocument();
    expect(screen.getByText('Click to view API documentation')).toBeInTheDocument();
  });

  it('does not show documentation text when swaggerUrl is not provided', () => {
    render(<ServiceHealthCard service={baseService} />);

    expect(screen.queryByText('Click to view API documentation')).not.toBeInTheDocument();
    expect(screen.queryByTestId('icon-external-link')).not.toBeInTheDocument();
  });

  it('shows Test button when onTest prop is provided', () => {
    const onTest = vi.fn();
    render(<ServiceHealthCard service={baseService} onTest={onTest} />);

    expect(screen.getByRole('button', { name: 'Test' })).toBeInTheDocument();
  });

  it('hides Test button when onTest prop is not provided', () => {
    render(<ServiceHealthCard service={baseService} />);

    expect(screen.queryByRole('button', { name: 'Test' })).not.toBeInTheDocument();
  });

  it('calls onTest when Test button is clicked', () => {
    const onTest = vi.fn();
    render(<ServiceHealthCard service={baseService} onTest={onTest} />);

    fireEvent.click(screen.getByRole('button', { name: 'Test' }));

    expect(onTest).toHaveBeenCalledTimes(1);
  });

  it('shows last check time using formatDistanceToNow', () => {
    render(<ServiceHealthCard service={baseService} />);

    expect(screen.getByText(/Last check:.*2 minutes ago/)).toBeInTheDocument();
  });
});
