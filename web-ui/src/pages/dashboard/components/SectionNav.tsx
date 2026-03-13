import { Server, Container, FolderOpen, Rocket, BarChart3, FileText, Wrench } from 'lucide-react';

interface SectionNavProps {
  hasCustomAPIs: boolean;
}

export function SectionNav({ hasCustomAPIs }: SectionNavProps) {
  const items = [
    { id: 'section-api', icon: Server, label: 'API 상태', tooltip: 'YOLO, eDOCr2, PaddleOCR 등 21개 AI 서비스의 실시간 헬스체크 상태를 확인합니다. GPU VRAM 사용량, 온도, 카테고리별(Detection, OCR, Segmentation 등) 가동률과 응답 시간을 모니터링할 수 있습니다.' },
    { id: 'section-containers', icon: Container, label: '컨테이너', tooltip: 'Docker로 실행 중인 모든 API 컨테이너의 상태(Running/Stopped)를 확인하고, 개별 서비스를 시작하거나 중지할 수 있습니다. 포트 번호와 컨테이너 이름도 표시됩니다.' },
    { id: 'section-projects', icon: FolderOpen, label: '프로젝트 현황', tooltip: 'BOM 견적 프로젝트와 P&ID 검출 프로젝트의 전체 현황을 확인합니다. 프로젝트별 세션 수, 완료/대기 상태, 진행률을 한눈에 볼 수 있고, 각 세션을 클릭하면 BlueprintFlow 워크플로우로 이동합니다.' },
    { id: 'section-quick-actions', icon: Rocket, label: '빠른 실행', tooltip: '자주 사용하는 기능으로 바로 이동합니다. BlueprintFlow 빌더에서 워크플로우를 구성하거나, 분석 템플릿을 선택하여 OCR·세그멘테이션·공차 예측을 한 번에 실행하거나, 실시간 모니터링 페이지로 이동할 수 있습니다.' },
    { id: 'section-stats', icon: BarChart3, label: '통계', tooltip: '시스템 운영 지표를 요약합니다. 오늘 처리한 분석 건수, 전체 API 호출 성공률(%), 평균 응답 시간(초), 누적 에러 수를 카드 형태로 보여줍니다.' },
    ...(hasCustomAPIs ? [{ id: 'section-custom-apis', icon: Wrench, label: 'Custom APIs', tooltip: '사용자가 직접 등록한 Custom API 목록입니다. 각 API를 활성화/비활성화하거나, Built-in API로 내보내기하거나, 삭제할 수 있습니다. Gateway에서 자동 검색된 API도 여기에 표시됩니다.' }] : []),
    { id: 'section-getting-started', icon: FileText, label: 'Getting Started', tooltip: '시스템 사용법을 3단계로 안내합니다. ① API 상태 확인 → ② BlueprintFlow에서 노드 기반 워크플로우 구성 → ③ 템플릿을 활용한 통합 분석 실행. 처음 사용하시는 분은 이 가이드를 따라해 보세요.' },
  ];

  return (
    <nav className="flex flex-wrap gap-2 p-3 bg-muted/40 rounded-lg border">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <button
            key={item.id}
            title={item.tooltip}
            onClick={() => document.getElementById(item.id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md bg-background border hover:bg-accent hover:text-accent-foreground transition-colors"
          >
            <Icon className="w-3.5 h-3.5" />
            {item.label}
          </button>
        );
      })}
    </nav>
  );
}
