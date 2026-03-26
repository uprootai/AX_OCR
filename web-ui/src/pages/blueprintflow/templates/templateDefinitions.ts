// Barrel re-export — splits 872-line file into domain modules.
// Each module is <400 lines. Existing imports (`import { templates } from './templateDefinitions'`) are unaffected.

import { featuredTemplates } from './templates.featured';
import { techcrossTemplates } from './templates.techcross';
import { dseBearingTemplates } from './templates.dsebearing';
import { panasiaTemplates } from './templates.panasia';
import { basicAdvancedTemplates } from './templates.basic-advanced';
import { benchmarkTemplates } from './templates.benchmark';
import { aiTemplates } from './templates.ai';
import { bmtTemplates } from './templates.bmt';
import type { TemplateInfo } from './types';

export const templates: TemplateInfo[] = [
  ...featuredTemplates,
  ...techcrossTemplates,
  ...dseBearingTemplates,
  ...bmtTemplates,
  ...panasiaTemplates,
  ...basicAdvancedTemplates,
  ...benchmarkTemplates,
  ...aiTemplates,
];
