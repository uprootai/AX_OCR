import React from 'react';

interface StatusBadgeProps {
  status: 'healthy' | 'warning' | 'error' | 'unknown';
  label?: string;
}

const STATUS_COLORS: Record<string, { bg: string; color: string; text: string }> = {
  healthy: { bg: '#e8f5e9', color: '#1b5e20', text: 'Healthy' },
  warning: { bg: '#fff3e0', color: '#e65100', text: 'Warning' },
  error: { bg: '#ffebee', color: '#b71c1c', text: 'Error' },
  unknown: { bg: '#f5f5f5', color: '#616161', text: 'Unknown' },
};

export default function StatusBadge({ status, label }: StatusBadgeProps) {
  const cfg = STATUS_COLORS[status] || STATUS_COLORS.unknown;
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 8px',
      borderRadius: '4px',
      fontSize: '0.75rem',
      fontWeight: 600,
      background: cfg.bg,
      color: cfg.color,
    }}>
      {label || cfg.text}
    </span>
  );
}
