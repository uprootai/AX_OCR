import type {ReactNode} from 'react';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

const METRICS = [
  {value: '21', label: 'Docker Services'},
  {value: '24', label: 'API Endpoints'},
  {value: '29+', label: 'Node Types'},
  {value: '73', label: 'Detection Classes'},
  {value: '549', label: 'Tests'},
  {value: '10', label: 'GPU Services'},
];

const SECTIONS = [
  {
    title: '1. System Overview',
    description: '21 마이크로서비스 아키텍처, 기술스택, 포트/네트워크 맵',
    link: '/docs/system-overview',
  },
  {
    title: '2. Analysis Pipeline',
    description: 'VLM 분류 → YOLO 검출 → OCR → 공차 분석 파이프라인',
    link: '/docs/analysis-pipeline',
  },
  {
    title: '3. BlueprintFlow',
    description: '29+ 노드 타입, DAG 실행 엔진, 비주얼 워크플로우 빌더',
    link: '/docs/blueprintflow',
  },
  {
    title: '4. Agent Verification',
    description: '3-Level 하이브리드 검증 (Auto/Agent/Human)',
    link: '/docs/agent-verification',
  },
  {
    title: '5. BOM & Quoting',
    description: '73 검출 클래스, BOM 생성, 가격 산출, 견적 PDF',
    link: '/docs/bom-generation',
  },
  {
    title: '6. P&ID Analysis',
    description: '심볼 검출, 라인 검출, 연결성 분석, Design Checker',
    link: '/docs/pid-analysis',
  },
  {
    title: '7. Batch & Delivery',
    description: '대량 배치 처리, 프로젝트 관리, 납품 패키지',
    link: '/docs/batch-delivery',
  },
  {
    title: '8. Quality Assurance',
    description: 'GT 비교, Active Learning, 피드백 파이프라인',
    link: '/docs/quality-assurance',
  },
  {
    title: '9. Frontend',
    description: 'React 19, Zustand, React Flow, 컴포넌트 아키텍처',
    link: '/docs/frontend',
  },
  {
    title: '10. DevOps',
    description: 'Docker Compose, CI/CD, GPU 설정, 모니터링',
    link: '/docs/devops',
  },
];

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header
      style={{
        padding: '4rem 0',
        textAlign: 'center',
        background: 'linear-gradient(135deg, var(--ifm-color-primary-darkest), var(--ifm-color-primary))',
        color: '#fff',
      }}>
      <div className="container">
        <Heading as="h1" style={{fontSize: '2.5rem', color: '#fff'}}>
          {siteConfig.title}
        </Heading>
        <p style={{fontSize: '1.2rem', opacity: 0.9, maxWidth: '600px', margin: '0 auto 1.5rem'}}>
          {siteConfig.tagline}
        </p>
        <code style={{
          display: 'inline-block',
          padding: '8px 16px',
          background: 'rgba(255,255,255,0.15)',
          borderRadius: '6px',
          fontSize: '0.9rem',
          color: '#fff',
        }}>
          Image → VLM → YOLO → OCR → Analysis → BOM → Quote PDF
        </code>
        <div style={{marginTop: '2rem'}}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/system-overview">
            Get Started
          </Link>
        </div>
      </div>
    </header>
  );
}

function MetricsSection() {
  return (
    <section style={{padding: '2rem 0'}}>
      <div className="container">
        <div className="metrics-grid">
          {METRICS.map((m) => (
            <div key={m.label} className="metric-card">
              <div className="metric-value">{m.value}</div>
              <div className="metric-label">{m.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function SectionsGrid() {
  return (
    <section style={{padding: '2rem 0 4rem'}}>
      <div className="container">
        <Heading as="h2" style={{textAlign: 'center', marginBottom: '1.5rem'}}>
          Documentation Sections
        </Heading>
        <div className="section-cards">
          {SECTIONS.map((s) => (
            <Link key={s.title} to={s.link} style={{textDecoration: 'none', color: 'inherit'}}>
              <div className="section-card">
                <h3>{s.title}</h3>
                <p>{s.description}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  return (
    <Layout
      title="Home"
      description="AX POC - 기계 도면 자동 분석 및 제조 견적 생성 시스템 문서">
      <HomepageHeader />
      <main>
        <MetricsSection />
        <SectionsGrid />
      </main>
    </Layout>
  );
}
