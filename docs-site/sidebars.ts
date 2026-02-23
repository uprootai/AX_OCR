import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    {
      type: 'category',
      label: '1. System Overview',
      link: {type: 'doc', id: 'system-overview/index'},
      items: [
        'system-overview/architecture-map',
        'system-overview/service-catalog',
        'system-overview/tech-stack',
        'system-overview/port-network',
      ],
    },
    {
      type: 'category',
      label: '2. Analysis Pipeline',
      link: {type: 'doc', id: 'analysis-pipeline/index'},
      items: [
        'analysis-pipeline/vlm-classification',
        'analysis-pipeline/yolo-detection',
        'analysis-pipeline/ocr-processing',
        'analysis-pipeline/tolerance-analysis',
        'analysis-pipeline/revision-comparison',
      ],
    },
    {
      type: 'category',
      label: '3. BlueprintFlow',
      link: {type: 'doc', id: 'blueprintflow/index'},
      items: [
        'blueprintflow/node-catalog',
        'blueprintflow/dag-engine',
        'blueprintflow/templates',
        'blueprintflow/custom-api',
      ],
    },
    {
      type: 'category',
      label: '4. Agent Verification',
      link: {type: 'doc', id: 'agent-verification/index'},
      items: [
        'agent-verification/three-level-architecture',
        'agent-verification/api-reference',
        'agent-verification/dashboard',
      ],
    },
    {
      type: 'category',
      label: '5. BOM & Quoting',
      link: {type: 'doc', id: 'bom-generation/index'},
      items: [
        'bom-generation/detection-classes',
        'bom-generation/pricing-engine',
        'bom-generation/export-formats',
        'bom-generation/pdf-report',
      ],
    },
    {
      type: 'category',
      label: '6. P&ID Analysis',
      link: {type: 'doc', id: 'pid-analysis/index'},
      items: [
        'pid-analysis/symbol-detection',
        'pid-analysis/line-detection',
        'pid-analysis/connectivity',
        'pid-analysis/design-checker',
      ],
    },
    {
      type: 'category',
      label: '7. Batch & Delivery',
      link: {type: 'doc', id: 'batch-delivery/index'},
      items: [
        'batch-delivery/batch-processing',
        'batch-delivery/project-management',
        'batch-delivery/export-package',
        'batch-delivery/onboarding-guide',
      ],
    },
    {
      type: 'category',
      label: '8. Quality Assurance',
      link: {type: 'doc', id: 'quality-assurance/index'},
      items: [
        'quality-assurance/gt-comparison',
        'quality-assurance/active-learning',
        'quality-assurance/feedback-pipeline',
        'quality-assurance/ocr-metrics',
      ],
    },
    {
      type: 'category',
      label: '9. Frontend',
      link: {type: 'doc', id: 'frontend/index'},
      items: [
        'frontend/routing',
        'frontend/state-management',
        'frontend/component-library',
        'frontend/bom-frontend',
      ],
    },
    {
      type: 'category',
      label: '10. DevOps',
      link: {type: 'doc', id: 'devops/index'},
      items: [
        'devops/docker-compose',
        'devops/ci-pipeline',
        'devops/cd-pipeline',
        'devops/gpu-config',
      ],
    },
  ],
};

export default sidebars;
