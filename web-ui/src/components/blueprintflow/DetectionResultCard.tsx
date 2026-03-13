/**
 * DetectionResultCard - barrel re-export
 * Implementation split into: DetectionResultCard/
 *   - index.tsx      (main component)
 *   - types.ts       (interfaces)
 *   - MetricCard.tsx (sub-component)
 *   - FilterCheckbox.tsx (sub-component)
 *   - useDetectionData.ts (state + canvas hook)
 */

export { default, MetricCard, FilterCheckbox, useDetectionData } from './DetectionResultCard/index';
export type { DetectionResultCardProps, MetricCardProps, FilterCheckboxProps } from './DetectionResultCard/index';
