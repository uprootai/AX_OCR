import type { WorkflowDefinition } from '../../../lib/api';

export type TemplateCategory = 'all' | 'featured' | 'panasia' | 'techcross' | 'dsebearing' | 'bmt' | 'basic' | 'advanced' | 'pid' | 'ai' | 'benchmark';

export interface TemplateInfo {
  nameKey: string;
  descKey: string;
  useCaseKey: string;
  workflow: WorkflowDefinition;
  estimatedTime: string;
  accuracy: string;
  category: 'basic' | 'advanced' | 'pid' | 'ai' | 'benchmark' | 'panasia' | 'techcross' | 'dsebearing' | 'bmt';
  featured?: boolean;
  hidden?: boolean;
  sampleImage?: string;
  sampleGT?: string;
}
