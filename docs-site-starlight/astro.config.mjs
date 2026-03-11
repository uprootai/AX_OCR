// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

import react from '@astrojs/react';

// https://astro.build/config
export default defineConfig({
    base: '/docs/',
    integrations: [starlight({
        title: 'AX POC Documentation',
        defaultLocale: 'ko',
        disable404Route: false,
        customCss: ['./src/styles/custom.css'],
        components: {
            SocialIcons: './src/components/NavLinks.astro',
        },
        sidebar: [
            {
                label: '1. System Overview',
                items: [
                    { label: 'Overview', slug: 'system-overview' },
                    { label: 'Architecture Map', slug: 'system-overview/architecture-map' },
                    { label: 'Service Catalog', slug: 'system-overview/service-catalog' },
                    { label: 'Tech Stack', slug: 'system-overview/tech-stack' },
                    { label: 'Port & Network', slug: 'system-overview/port-network' },
                    { label: 'Architecture Decisions', slug: 'system-overview/architecture-decisions' },
                ],
            },
            {
                label: '2. Analysis Pipeline',
                items: [
                    { label: 'Overview', slug: 'analysis-pipeline' },
                    { label: 'VLM Classification', slug: 'analysis-pipeline/vlm-classification' },
                    { label: 'YOLO Detection', slug: 'analysis-pipeline/yolo-detection' },
                    { label: 'OCR Processing', slug: 'analysis-pipeline/ocr-processing' },
                    { label: 'Tolerance Analysis', slug: 'analysis-pipeline/tolerance-analysis' },
                    { label: 'Revision Comparison', slug: 'analysis-pipeline/revision-comparison' },
                ],
            },
            {
                label: '3. BlueprintFlow',
                items: [
                    { label: 'Overview', slug: 'blueprintflow' },
                    { label: 'Node Catalog', slug: 'blueprintflow/node-catalog' },
                    { label: 'DAG Engine', slug: 'blueprintflow/dag-engine' },
                    { label: 'Templates', slug: 'blueprintflow/templates' },
                    { label: 'Custom API', slug: 'blueprintflow/custom-api' },
                    { label: 'Optimization', slug: 'blueprintflow/optimization' },
                ],
            },
            {
                label: '4. Agent Verification',
                items: [
                    { label: 'Overview', slug: 'agent-verification' },
                    { label: 'Three-Level Architecture', slug: 'agent-verification/three-level-architecture' },
                    { label: 'API Reference', slug: 'agent-verification/api-reference' },
                    { label: 'Dashboard', slug: 'agent-verification/dashboard' },
                ],
            },
            {
                label: '5. BOM & Quoting',
                items: [
                    { label: 'Overview', slug: 'bom-generation' },
                    { label: 'Detection Classes', slug: 'bom-generation/detection-classes' },
                    { label: 'Pricing Engine', slug: 'bom-generation/pricing-engine' },
                    { label: 'Export Formats', slug: 'bom-generation/export-formats' },
                    { label: 'PDF Report', slug: 'bom-generation/pdf-report' },
                ],
            },
            {
                label: '6. P&ID Analysis',
                items: [
                    { label: 'Overview', slug: 'pid-analysis' },
                    { label: 'Symbol Detection', slug: 'pid-analysis/symbol-detection' },
                    { label: 'Line Detection', slug: 'pid-analysis/line-detection' },
                    { label: 'Connectivity', slug: 'pid-analysis/connectivity' },
                    { label: 'Design Checker', slug: 'pid-analysis/design-checker' },
                ],
            },
            {
                label: '7. Batch & Delivery',
                items: [
                    { label: 'Overview', slug: 'batch-delivery' },
                    { label: 'Batch Processing', slug: 'batch-delivery/batch-processing' },
                    { label: 'Project Management', slug: 'batch-delivery/project-management' },
                    { label: 'Export Package', slug: 'batch-delivery/export-package' },
                    { label: 'Onboarding Guide', slug: 'batch-delivery/onboarding-guide' },
                ],
            },
            {
                label: '8. Quality Assurance',
                items: [
                    { label: 'Overview', slug: 'quality-assurance' },
                    { label: 'GT Comparison', slug: 'quality-assurance/gt-comparison' },
                    { label: 'Active Learning', slug: 'quality-assurance/active-learning' },
                    { label: 'Feedback Pipeline', slug: 'quality-assurance/feedback-pipeline' },
                    { label: 'OCR Metrics', slug: 'quality-assurance/ocr-metrics' },
                    { label: 'Evaluation Reports', slug: 'quality-assurance/evaluation-reports' },
                ],
            },
            {
                label: '9. Frontend',
                items: [
                    { label: 'Overview', slug: 'frontend' },
                    { label: 'Routing', slug: 'frontend/routing' },
                    { label: 'Route Map', slug: 'frontend/route-map' },
                    {
                        label: '페이지 상세',
                        collapsed: true,
                        items: [
                            { label: 'Pages Overview', slug: 'frontend/pages' },
                            { label: 'Dashboard', slug: 'frontend/pages/dashboard' },
                            { label: 'Project', slug: 'frontend/pages/project' },
                            { label: 'BlueprintFlow', slug: 'frontend/pages/blueprintflow' },
                            { label: 'Session', slug: 'frontend/pages/session' },
                            { label: 'Admin', slug: 'frontend/pages/admin' },
                        ],
                    },
                    { label: 'State Management', slug: 'frontend/state-management' },
                    { label: 'Component Library', slug: 'frontend/component-library' },
                    { label: 'BOM Frontend', slug: 'frontend/bom-frontend' },
                ],
            },
            {
                label: '10. DevOps',
                items: [
                    { label: 'Overview', slug: 'devops' },
                    { label: 'Docker Compose', slug: 'devops/docker-compose' },
                    { label: 'CI Pipeline', slug: 'devops/ci-pipeline' },
                    { label: 'CD Pipeline', slug: 'devops/cd-pipeline' },
                    { label: 'GPU Config', slug: 'devops/gpu-config' },
                ],
            },
            {
                label: '11. R&D Research',
                autogenerate: { directory: 'research' },
            },
            {
                label: '12. API Reference',
                autogenerate: { directory: 'api-reference' },
            },
            {
                label: '13. Developer Guide',
                items: [
                    { label: 'Overview', slug: 'developer' },
                    { label: 'Contributing', slug: 'developer/contributing' },
                    { label: 'Git Workflow', slug: 'developer/git-workflow' },
                    { label: 'API Spec System', slug: 'developer/api-spec-system' },
                    { label: 'Dynamic API System', slug: 'developer/dynamic-api-system' },
                    { label: 'LLM Usability', slug: 'developer/llm-usability' },
                    { label: 'API Replacement', slug: 'developer/api-replacement' },
                ],
            },
            {
                label: '14. Deployment',
                items: [
                    { label: 'Overview', slug: 'deployment' },
                    { label: 'Installation', slug: 'deployment/installation' },
                    { label: 'On-Premise Infra', slug: 'deployment/on-premise-infra' },
                    { label: 'On-Premise Operation', slug: 'deployment/on-premise-operation' },
                    { label: 'Admin Manual', slug: 'deployment/admin-manual' },
                    { label: 'Dockerization', slug: 'deployment/dockerization' },
                ],
            },
            {
                label: '15. Customer Cases',
                items: [
                    { label: 'Overview', slug: 'customer-cases' },
                    {
                        label: '동서기연 — 터빈 베어링',
                        collapsed: true,
                        items: [
                            { label: 'DSE Bearing Overview', slug: 'customer-cases/dsebearing' },
                            { label: 'Data Overview', slug: 'customer-cases/dsebearing/data-overview' },
                            { label: 'Meeting History', slug: 'customer-cases/dsebearing/meeting-history' },
                            { label: 'Results', slug: 'customer-cases/dsebearing/results' },
                            { label: 'Next Steps', slug: 'customer-cases/dsebearing/next-steps' },
                        ],
                    },
                    { label: 'Panasia', slug: 'customer-cases/panasia' },
                ],
            },
        ],
    }), react()],
});
