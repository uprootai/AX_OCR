// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

import react from '@astrojs/react';

// https://astro.build/config
export default defineConfig({
    base: '/',
    integrations: [starlight({
        title: 'AX POC Documentation',
        defaultLocale: 'ko',
        disable404Route: false,
        customCss: ['./src/styles/custom.css'],
        components: {
            SocialIcons: './src/components/NavLinks.astro',
            Head: './src/components/Head.astro',
        },
        sidebar: [
            {
                label: '1. 시스템 개요',
                items: [
                    { label: '개요', slug: 'system-overview' },
                    { label: '아키텍처 맵', slug: 'system-overview/architecture-map' },
                    { label: '서비스 카탈로그', slug: 'system-overview/service-catalog' },
                    { label: '기술 스택', slug: 'system-overview/tech-stack' },
                    { label: '포트 & 네트워크', slug: 'system-overview/port-network' },
                    { label: '아키텍처 결정', slug: 'system-overview/architecture-decisions' },
                ],
            },
            {
                label: '2. 분석 파이프라인',
                items: [
                    { label: '개요', slug: 'analysis-pipeline' },
                    { label: 'VLM 분류', slug: 'analysis-pipeline/vlm-classification' },
                    { label: 'YOLO 검출', slug: 'analysis-pipeline/yolo-detection' },
                    { label: 'OCR 처리', slug: 'analysis-pipeline/ocr-processing' },
                    { label: '공차 분석', slug: 'analysis-pipeline/tolerance-analysis' },
                    { label: '리비전 비교', slug: 'analysis-pipeline/revision-comparison' },
                ],
            },
            {
                label: '3. BlueprintFlow',
                items: [
                    { label: '개요', slug: 'blueprintflow' },
                    { label: '노드 카탈로그', slug: 'blueprintflow/node-catalog' },
                    { label: 'DAG 엔진', slug: 'blueprintflow/dag-engine' },
                    { label: '템플릿', slug: 'blueprintflow/templates' },
                    { label: '커스텀 API', slug: 'blueprintflow/custom-api' },
                    { label: '최적화', slug: 'blueprintflow/optimization' },
                ],
            },
            {
                label: '4. 검증 시스템',
                items: [
                    { label: '개요', slug: 'agent-verification' },
                    { label: '3단계 아키텍처', slug: 'agent-verification/three-level-architecture' },
                    { label: 'API 레퍼런스', slug: 'agent-verification/api-reference' },
                    { label: '대시보드', slug: 'agent-verification/dashboard' },
                ],
            },
            {
                label: '5. BOM & 견적',
                items: [
                    { label: '개요', slug: 'bom-generation' },
                    { label: '검출 클래스', slug: 'bom-generation/detection-classes' },
                    { label: '견적 엔진', slug: 'bom-generation/pricing-engine' },
                    { label: '내보내기 형식', slug: 'bom-generation/export-formats' },
                    { label: 'PDF 리포트', slug: 'bom-generation/pdf-report' },
                ],
            },
            {
                label: '6. P&ID 분석',
                items: [
                    { label: '개요', slug: 'pid-analysis' },
                    { label: '심볼 검출', slug: 'pid-analysis/symbol-detection' },
                    { label: '라인 검출', slug: 'pid-analysis/line-detection' },
                    { label: '연결성 분석', slug: 'pid-analysis/connectivity' },
                    { label: '설계 검사기', slug: 'pid-analysis/design-checker' },
                ],
            },
            {
                label: '7. 배치 & 납품',
                items: [
                    { label: '개요', slug: 'batch-delivery' },
                    { label: '배치 처리', slug: 'batch-delivery/batch-processing' },
                    { label: '프로젝트 관리', slug: 'batch-delivery/project-management' },
                    { label: '납품 패키지', slug: 'batch-delivery/export-package' },
                    { label: '온보딩 가이드', slug: 'batch-delivery/onboarding-guide' },
                ],
            },
            {
                label: '8. 품질 보증',
                items: [
                    { label: '개요', slug: 'quality-assurance' },
                    { label: 'GT 비교', slug: 'quality-assurance/gt-comparison' },
                    { label: '능동 학습', slug: 'quality-assurance/active-learning' },
                    { label: '피드백 파이프라인', slug: 'quality-assurance/feedback-pipeline' },
                    { label: 'OCR 메트릭', slug: 'quality-assurance/ocr-metrics' },
                    { label: '평가 리포트', slug: 'quality-assurance/evaluation-reports' },
                    { label: 'Dimension Lab 배치평가', slug: 'quality-assurance/dimension-lab-eval' },
                ],
            },
            {
                label: '9. 프론트엔드',
                items: [
                    { label: '개요', slug: 'frontend' },
                    { label: '라우팅', slug: 'frontend/routing' },
                    { label: '라우트 맵', slug: 'frontend/route-map' },
                    {
                        label: '페이지 상세',
                        collapsed: true,
                        items: [
                            { label: '페이지 개요', slug: 'frontend/pages' },
                            { label: '대시보드', slug: 'frontend/pages/dashboard' },
                            { label: '프로젝트', slug: 'frontend/pages/project' },
                            { label: 'BlueprintFlow', slug: 'frontend/pages/blueprintflow' },
                            { label: '세션', slug: 'frontend/pages/session' },
                            { label: '관리자', slug: 'frontend/pages/admin' },
                        ],
                    },
                    { label: '상태 관리', slug: 'frontend/state-management' },
                    { label: '컴포넌트 라이브러리', slug: 'frontend/component-library' },
                    { label: 'BOM 프론트엔드', slug: 'frontend/bom-frontend' },
                ],
            },
            {
                label: '10. DevOps',
                items: [
                    { label: '개요', slug: 'devops' },
                    { label: 'Docker Compose', slug: 'devops/docker-compose' },
                    { label: 'CI 파이프라인', slug: 'devops/ci-pipeline' },
                    { label: 'CD 파이프라인', slug: 'devops/cd-pipeline' },
                    { label: 'GPU 설정', slug: 'devops/gpu-config' },
                ],
            },
            {
                label: '11. R&D 연구',
                autogenerate: { directory: 'research' },
            },
            {
                label: '12. API 레퍼런스',
                autogenerate: { directory: 'api-reference' },
            },
            {
                label: '13. 개발자 가이드',
                items: [
                    { label: '개요', slug: 'developer' },
                    { label: '기여 가이드', slug: 'developer/contributing' },
                    { label: 'Git 워크플로우', slug: 'developer/git-workflow' },
                    { label: 'API 스펙 시스템', slug: 'developer/api-spec-system' },
                    { label: '동적 API 시스템', slug: 'developer/dynamic-api-system' },
                    { label: 'LLM 활용성', slug: 'developer/llm-usability' },
                    { label: 'API 교체', slug: 'developer/api-replacement' },
                ],
            },
            {
                label: '14. 배포',
                items: [
                    { label: '개요', slug: 'deployment' },
                    { label: '설치', slug: 'deployment/installation' },
                    { label: '온프레미스 인프라', slug: 'deployment/on-premise-infra' },
                    { label: '온프레미스 운영', slug: 'deployment/on-premise-operation' },
                    { label: '관리자 매뉴얼', slug: 'deployment/admin-manual' },
                    { label: 'Docker화', slug: 'deployment/dockerization' },
                ],
            },
            {
                label: '15. 고객 사례',
                items: [
                    { label: '개요', slug: 'customer-cases' },
                    {
                        label: '동서기연 — 터빈 베어링',
                        collapsed: true,
                        items: [
                            { label: '프로젝트 개요', slug: 'customer-cases/dsebearing' },
                            { label: '미팅 & 커뮤니케이션', slug: 'customer-cases/dsebearing/meeting-history' },
                            { label: '전달 자료 & 도면 분석', slug: 'customer-cases/dsebearing/data-overview' },
                            { label: '1차 테스트 결과', slug: 'customer-cases/dsebearing/results' },
                            { label: '다음 단계 & 미결 사항', slug: 'customer-cases/dsebearing/next-steps' },
                            { label: '2차 미팅 (03-17)', slug: 'customer-cases/dsebearing/2nd-meeting' },
                            { label: '전수 분석 실험', slug: 'customer-cases/dsebearing/batch-test-report' },
                            {
                                label: '기하학 파이프라인',
                                collapsed: true,
                                items: [
                                    { label: '개요 (K/L/M/N)', slug: 'customer-cases/dsebearing/pipeline' },
                                    { label: 'Thrust — 성공', slug: 'customer-cases/dsebearing/pipeline/thrust' },
                                    { label: 'T5 — 실패', slug: 'customer-cases/dsebearing/pipeline/t5' },
                                    { label: 'TD0062042 — 랜덤', slug: 'customer-cases/dsebearing/pipeline/random' },
                                ],
                            },
                            {
                                label: '앙상블 최적화 (v2→v5)',
                                collapsed: true,
                                items: [
                                    { label: '개요', slug: 'customer-cases/dsebearing/ensemble' },
                                    { label: '투표 실패 분석', slug: 'customer-cases/dsebearing/ensemble/voting-problem' },
                                    { label: '코드 수정 상세', slug: 'customer-cases/dsebearing/ensemble/code-fixes' },
                                    { label: '87도면 배치 비교', slug: 'customer-cases/dsebearing/ensemble/batch-results' },
                                    { label: 'GT 검증 + 한계', slug: 'customer-cases/dsebearing/ensemble/gt-validation' },
                                ],
                            },
                        ],
                    },
                    { label: '파나시아 — MCP Panel', slug: 'customer-cases/panasia' },
                ],
            },
        ],
    }), react()],
});
