import React from 'react';

interface MetricCardProps {
  value: string | number;
  label: string;
  icon?: string;
}

export default function MetricCard({ value, label, icon }: MetricCardProps) {
  return (
    <div className="metric-card">
      {icon && <div style={{ fontSize: '1.5rem', marginBottom: '4px' }}>{icon}</div>}
      <div className="metric-value">{value}</div>
      <div className="metric-label">{label}</div>
    </div>
  );
}
