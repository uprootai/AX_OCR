import { useState, useEffect } from 'react';
import { FileText, Folder, FolderOpen, ChevronRight, ChevronDown, Book } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import Mermaid from '../../components/ui/Mermaid';

interface DocFile {
  name: string;
  path: string;
  type: 'file' | 'folder';
  children?: DocFile[];
}

const docStructure: DocFile[] = [
  {
    name: '📘 필수 문서',
    path: 'root',
    type: 'folder',
    children: [
      { name: 'README.md', path: '/README.md', type: 'file' },
      { name: 'INSTALLATION_GUIDE.md ⭐', path: '/INSTALLATION_GUIDE.md', type: 'file' },
      { name: 'TROUBLESHOOTING.md ⭐', path: '/TROUBLESHOOTING.md', type: 'file' },
    ],
  },
  {
    name: '👤 사용자 가이드',
    path: 'user',
    type: 'folder',
    children: [
      { name: '사용자 가이드', path: '/docs/user/USER_GUIDE.md', type: 'file' },
      { name: 'API 사용 매뉴얼', path: '/docs/user/API_USAGE_MANUAL.md', type: 'file' },
      { name: '한글 실행 가이드', path: '/docs/user/KOREAN_EXECUTION_GUIDE.md', type: 'file' },
      { name: '트러블슈팅 가이드', path: '/docs/user/TROUBLESHOOTING_GUIDE.md', type: 'file' },
    ],
  },
  {
    name: '👨‍💻 개발자 가이드',
    path: 'developer',
    type: 'folder',
    children: [
      { name: 'Claude 가이드 (EN)', path: '/docs/developer/CLAUDE.md', type: 'file' },
      { name: 'Claude 가이드 (KR)', path: '/docs/developer/CLAUDE_KR.md', type: 'file' },
      { name: '기여 가이드', path: '/docs/developer/CONTRIBUTING.md', type: 'file' },
      { name: 'Git 워크플로우', path: '/docs/developer/GIT_WORKFLOW.md', type: 'file' },
    ],
  },
  {
    name: '⚙️ 기술 구현',
    path: 'technical',
    type: 'folder',
    children: [
      { name: 'YOLO 구현 가이드', path: '/docs/technical/yolo/IMPLEMENTATION_GUIDE.md', type: 'file' },
      { name: 'YOLO 빠른 시작', path: '/docs/technical/yolo/QUICKSTART.md', type: 'file' },
      { name: 'eDOCr v1/v2 배포', path: '/docs/technical/ocr/EDOCR_V1_V2_DEPLOYMENT.md', type: 'file' },
      { name: 'OCR 개선 전략', path: '/docs/technical/ocr/OCR_IMPROVEMENT_STRATEGY.md', type: 'file' },
      { name: 'VL API 구현 가이드', path: '/docs/technical/VL_API_IMPLEMENTATION_GUIDE.md', type: 'file' },
      { name: '합성 데이터 전략', path: '/docs/technical/SYNTHETIC_DATA_STRATEGY.md', type: 'file' },
    ],
  },
  {
    name: '🏗️ 아키텍처 & 분석',
    path: 'architecture',
    type: 'folder',
    children: [
      { name: '시스템 아키텍처 ⭐', path: '/docs/architecture/system-architecture.md', type: 'file' },
      { name: '의사결정 매트릭스', path: '/docs/architecture/DECISION_MATRIX.md', type: 'file' },
      { name: '배포 상태', path: '/docs/architecture/DEPLOYMENT_STATUS.md', type: 'file' },
      { name: '구현 상태', path: '/docs/architecture/IMPLEMENTATION_STATUS.md', type: 'file' },
      { name: '프로덕션 준비도', path: '/docs/architecture/PRODUCTION_READINESS_ANALYSIS.md', type: 'file' },
      { name: '프로젝트 구조 분석', path: '/docs/architecture/PROJECT_STRUCTURE_ANALYSIS.md', type: 'file' },
    ],
  },
  {
    name: '📊 최종 보고서',
    path: 'reports',
    type: 'folder',
    children: [
      { name: '최종 프로젝트 보고서', path: '/docs/reports/FINAL_COMPREHENSIVE_REPORT.md', type: 'file' },
      { name: '종합 평가 보고서', path: '/docs/reports/COMPREHENSIVE_EVALUATION_REPORT.md', type: 'file' },
    ],
  },
  {
    name: '🏆 100점 달성 문서',
    path: 'achievement',
    type: 'folder',
    children: [
      { name: '100점 달성 보고서 ⭐', path: '/docs/PERFECT_SCORE_ACHIEVEMENT.md', type: 'file' },
      { name: '최종 점수 리포트', path: '/docs/FINAL_SCORE_REPORT.md', type: 'file' },
      { name: '시스템 이슈 분석', path: '/docs/SYSTEM_ISSUES_REPORT.md', type: 'file' },
      { name: '적용된 수정사항', path: '/docs/FIXES_APPLIED.md', type: 'file' },
      { name: '감점 분석', path: '/docs/DEDUCTION_ANALYSIS.md', type: 'file' },
      { name: 'GPU 설정 설명', path: '/docs/GPU_CONFIGURATION_EXPLAINED.md', type: 'file' },
    ],
  },
];

function FolderTree({ items, onSelectFile }: { items: DocFile[]; onSelectFile: (path: string) => void }) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set(['root', 'user']));

  const toggleFolder = (path: string) => {
    const newExpanded = new Set(expanded);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpanded(newExpanded);
  };

  const renderItem = (item: DocFile, level: number = 0) => {
    const isExpanded = expanded.has(item.path);
    const Icon = item.type === 'folder'
      ? (isExpanded ? FolderOpen : Folder)
      : FileText;
    const ChevronIcon = isExpanded ? ChevronDown : ChevronRight;

    return (
      <div key={item.path}>
        <button
          onClick={() => {
            if (item.type === 'folder') {
              toggleFolder(item.path);
            } else {
              onSelectFile(item.path);
            }
          }}
          className={`w-full flex items-center gap-2 px-3 py-2 text-sm rounded-md transition-colors ${
            item.type === 'file'
              ? 'hover:bg-accent text-muted-foreground hover:text-foreground'
              : 'font-semibold hover:bg-accent/50'
          }`}
          style={{ paddingLeft: `${level * 12 + 12}px` }}
        >
          {item.type === 'folder' && (
            <ChevronIcon className="w-4 h-4 flex-shrink-0" />
          )}
          <Icon className={`w-4 h-4 flex-shrink-0 ${item.type === 'folder' ? 'text-blue-500' : 'text-gray-500'}`} />
          <span className="text-left flex-1">{item.name}</span>
        </button>
        {item.type === 'folder' && isExpanded && item.children && (
          <div>
            {item.children.map((child) => renderItem(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-1">
      {items.map((item) => renderItem(item))}
    </div>
  );
}

export default function Docs() {
  const [selectedFile, setSelectedFile] = useState<string | null>('/README.md');
  const [markdown, setMarkdown] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedFile) return;

    const fetchMarkdown = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(selectedFile);
        if (!response.ok) {
          throw new Error(`Failed to fetch: ${response.statusText}`);
        }
        const text = await response.text();
        setMarkdown(text);
      } catch (err) {
        console.error('Error fetching markdown:', err);
        setError(`문서를 불러올 수 없습니다: ${err instanceof Error ? err.message : '알 수 없는 오류'}`);
        setMarkdown('');
      } finally {
        setLoading(false);
      }
    };

    fetchMarkdown();
  }, [selectedFile]);

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
      {/* Sidebar */}
      <div className="w-80 border-r bg-card overflow-y-auto">
        <div className="p-4 border-b bg-accent/30">
          <div className="flex items-center gap-2">
            <Book className="w-5 h-5 text-blue-500" />
            <h2 className="font-bold text-lg">문서</h2>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            총 31개 문서 파일
          </p>
        </div>
        <div className="p-2">
          <FolderTree items={docStructure} onSelectFile={setSelectedFile} />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto p-8">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="text-muted-foreground">문서를 불러오는 중...</div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg p-6">
              <h3 className="font-semibold text-red-700 dark:text-red-300 mb-2">오류</h3>
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}

          {!loading && !error && markdown && (
            <article className="prose prose-slate dark:prose-invert max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeRaw]}
                components={{
                  // Pre 태그 - Mermaid 다이어그램 처리
                  pre: ({ node, children, ...props }) => {
                    // Check if this pre contains a mermaid code block
                    const codeElement = node?.children?.[0];
                    if (codeElement && codeElement.type === 'element' && codeElement.tagName === 'code') {
                      const className = codeElement.properties?.className as string[] | undefined;
                      const match = className?.[0]?.match(/language-(\w+)/);
                      const language = match?.[1];

                      if (language === 'mermaid') {
                        const codeContent = codeElement.children?.[0];
                        const chartCode = codeContent && 'value' in codeContent
                          ? String(codeContent.value).trim()
                          : '';

                        if (chartCode) {
                          return (
                            <div className="my-6">
                              <Mermaid chart={chartCode} />
                            </div>
                          );
                        }
                      }
                    }

                    return <pre {...props}>{children}</pre>;
                  },
                  // 코드 블록 스타일링
                  code: ({ node, className, children, ...props }) => {
                    const match = /language-(\w+)/.exec(className || '');
                    const isInline = !match;

                    if (isInline) {
                      return (
                        <code className="bg-accent px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                          {children}
                        </code>
                      );
                    }

                    return (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  },
                  // 링크 스타일링
                  a: ({ node, children, ...props }) => (
                    <a
                      className="text-blue-600 dark:text-blue-400 hover:underline"
                      target="_blank"
                      rel="noopener noreferrer"
                      {...props}
                    >
                      {children}
                    </a>
                  ),
                  // 테이블 스타일링
                  table: ({ node, children, ...props }) => (
                    <div className="overflow-x-auto my-6">
                      <table className="min-w-full border-collapse border border-gray-300 dark:border-gray-700" {...props}>
                        {children}
                      </table>
                    </div>
                  ),
                  th: ({ node, children, ...props }) => (
                    <th className="border border-gray-300 dark:border-gray-700 bg-gray-100 dark:bg-gray-800 px-4 py-2 text-left font-semibold" {...props}>
                      {children}
                    </th>
                  ),
                  td: ({ node, children, ...props }) => (
                    <td className="border border-gray-300 dark:border-gray-700 px-4 py-2" {...props}>
                      {children}
                    </td>
                  ),
                }}
              >
                {markdown}
              </ReactMarkdown>
            </article>
          )}

          {!loading && !error && !markdown && (
            <div className="text-center py-12 text-muted-foreground">
              <FileText className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p>왼쪽 사이드바에서 문서를 선택하세요</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
