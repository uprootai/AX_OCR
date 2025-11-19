import { type ReactNode, type HTMLAttributes } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  className?: string;
}

export function Card({ children, className = '', ...props }: CardProps) {
  return (
    <div className={`bg-card border rounded-lg ${className}`} {...props}>
      {children}
    </div>
  );
}

interface CardSubComponentProps {
  children: ReactNode;
  className?: string;
}

export function CardHeader({ children, className = '' }: CardSubComponentProps) {
  return (
    <div className={`px-6 py-4 border-b ${className}`}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className = '' }: CardSubComponentProps) {
  return (
    <h3 className={`text-lg font-semibold ${className}`}>
      {children}
    </h3>
  );
}

export function CardDescription({ children, className = '' }: CardSubComponentProps) {
  return (
    <p className={`text-sm text-muted-foreground ${className}`}>
      {children}
    </p>
  );
}

export function CardContent({ children, className = '' }: CardSubComponentProps) {
  return (
    <div className={`px-6 py-4 ${className}`}>
      {children}
    </div>
  );
}
