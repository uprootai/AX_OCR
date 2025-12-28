import { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { FileText, Folder, FolderOpen, ChevronRight, ChevronDown, Book, Search, X, PanelLeftClose, PanelLeft } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import Mermaid from '../../components/ui/Mermaid';
import ImageZoom from '../../components/ui/ImageZoom';

interface DocFile {
  name: string;
  path: string;
  type: 'file' | 'folder';
  children?: DocFile[];
}

const docStructure: DocFile[] = [
  {
    name: 'Quick Start',
    path: 'quickstart',
    type: 'folder',
    children: [
      { name: 'README', path: '/README.md', type: 'file' },
      { name: 'Installation Guide', path: '/docs/INSTALLATION_GUIDE.md', type: 'file' },
      { name: 'Troubleshooting', path: '/docs/TROUBLESHOOTING.md', type: 'file' },
    ],
  },
  {
    name: 'User Guide',
    path: 'user',
    type: 'folder',
    children: [
      { name: 'User Guide', path: '/docs/user/USER_GUIDE.md', type: 'file' },
      { name: 'API Usage Manual', path: '/docs/user/API_USAGE_MANUAL.md', type: 'file' },
      { name: 'Korean Guide', path: '/docs/user/KOREAN_EXECUTION_GUIDE.md', type: 'file' },
      { name: 'Admin Manual', path: '/docs/ADMIN_MANUAL.md', type: 'file' },
    ],
  },
  {
    name: 'Developer Guide',
    path: 'developer',
    type: 'folder',
    children: [
      { name: 'API Spec System', path: '/docs/developer/API_SPEC_SYSTEM_GUIDE.md', type: 'file' },
      { name: 'Claude Guide (EN)', path: '/docs/developer/CLAUDE.md', type: 'file' },
      { name: 'Claude Guide (KR)', path: '/docs/developer/CLAUDE_KR.md', type: 'file' },
      { name: 'VL API Setup', path: '/docs/developer/VL_API_SETUP_GUIDE.md', type: 'file' },
      { name: 'Dynamic API System', path: '/docs/DYNAMIC_API_SYSTEM_GUIDE.md', type: 'file' },
    ],
  },
  {
    name: 'BlueprintFlow',
    path: 'blueprintflow',
    type: 'folder',
    children: [
      { name: 'Overview', path: '/docs/blueprintflow/README.md', type: 'file' },
      { name: 'TextInput Node', path: '/docs/blueprintflow/08_textinput_node_guide.md', type: 'file' },
      { name: 'VL + TextInput Integration', path: '/docs/blueprintflow/09_vl_textinput_integration.md', type: 'file' },
      { name: 'YOLO Models', path: '/docs/blueprintflow/04_optimization/yolo_models.md', type: 'file' },
      { name: 'Pipeline Options', path: '/docs/blueprintflow/04_optimization/pipeline_options.md', type: 'file' },
      { name: 'Optimization Guide', path: '/docs/blueprintflow/04_optimization/optimization_guide.md', type: 'file' },
      { name: 'Benchmark Insights', path: '/docs/blueprintflow/benchmark-insights.md', type: 'file' },
    ],
  },
  {
    name: 'API Reference',
    path: 'api',
    type: 'folder',
    children: [
      { name: 'API Overview', path: '/docs/api/README.md', type: 'file' },
      // Detection
      { name: 'YOLO', path: '/docs/api/yolo/parameters.md', type: 'file' },
      // OCR
      { name: 'eDOCr2', path: '/docs/api/edocr2/parameters.md', type: 'file' },
      { name: 'PaddleOCR', path: '/docs/api/paddleocr/parameters.md', type: 'file' },
      { name: 'Tesseract', path: '/docs/api/tesseract/parameters.md', type: 'file' },
      { name: 'TrOCR', path: '/docs/api/trocr/parameters.md', type: 'file' },
      { name: 'Surya OCR', path: '/docs/api/surya-ocr/parameters.md', type: 'file' },
      { name: 'DocTR', path: '/docs/api/doctr/parameters.md', type: 'file' },
      { name: 'EasyOCR', path: '/docs/api/easyocr/parameters.md', type: 'file' },
      { name: 'OCR Ensemble', path: '/docs/api/ocr-ensemble/parameters.md', type: 'file' },
      // Segmentation
      { name: 'EDGNet', path: '/docs/api/edgnet/parameters.md', type: 'file' },
      { name: 'Line Detector', path: '/docs/api/line-detector/parameters.md', type: 'file' },
      // Preprocessing
      { name: 'ESRGAN', path: '/docs/api/esrgan/parameters.md', type: 'file' },
      // Analysis
      { name: 'SkinModel', path: '/docs/api/skinmodel/parameters.md', type: 'file' },
      { name: 'PID Analyzer', path: '/docs/api/pid-analyzer/parameters.md', type: 'file' },
      { name: 'Design Checker', path: '/docs/api/design-checker/parameters.md', type: 'file' },
      { name: 'Blueprint AI BOM', path: '/docs/api/blueprint-ai-bom/parameters.md', type: 'file' },
      // Knowledge & AI
      { name: 'Knowledge', path: '/docs/api/knowledge/parameters.md', type: 'file' },
      { name: 'VL', path: '/docs/api/vl/parameters.md', type: 'file' },
    ],
  },
  {
    name: 'Technical',
    path: 'technical',
    type: 'folder',
    children: [
      { name: 'YOLO Quickstart', path: '/docs/technical/yolo/QUICKSTART.md', type: 'file' },
      { name: 'eDOCr Deployment', path: '/docs/technical/ocr/EDOCR_V1_V2_DEPLOYMENT.md', type: 'file' },
    ],
  },
  {
    name: 'Deployment',
    path: 'deployment',
    type: 'folder',
    children: [
      { name: 'Deployment Guide', path: '/docs/DEPLOYMENT_GUIDE.md', type: 'file' },
      { name: 'GPU Configuration', path: '/docs/GPU_CONFIGURATION_EXPLAINED.md', type: 'file' },
      { name: 'YOLO Dockerization', path: '/docs/dockerization/2025-11-23_yolo_dockerization_guide.md', type: 'file' },
      { name: 'PaddleOCR Dockerization', path: '/docs/dockerization/2025-11-23_paddleocr_dockerization_guide.md', type: 'file' },
      { name: 'Model Downloads', path: '/docs/opensource/MODEL_DOWNLOAD_INFO.md', type: 'file' },
    ],
  },
  {
    name: 'Research Papers',
    path: 'papers',
    type: 'folder',
    children: [
      { name: 'Papers Index', path: '/docs/papers/README.md', type: 'file' },
      { name: 'eDOCr - OCR on Drawings', path: '/docs/papers/01_OCR_Engineering_Drawings.md', type: 'file' },
      { name: 'eDOCr2 - VL Integration', path: '/docs/papers/02_eDOCr2_Vision_Language_Integration.md', type: 'file' },
      { name: 'Skin Model - Tolerance', path: '/docs/papers/03_Geometric_Tolerance_Additive_Manufacturing.md', type: 'file' },
      { name: 'EDGNet - Graph Segmentation', path: '/docs/papers/04_Graph_Neural_Network_Engineering_Drawings.md', type: 'file' },
      { name: 'YOLOv11 - Object Detection', path: '/docs/papers/05_YOLOv11_Object_Detection.md', type: 'file' },
      { name: 'PaddleOCR - PP-OCR', path: '/docs/papers/06_PaddleOCR_PP-OCR.md', type: 'file' },
      { name: 'TrOCR - Transformer OCR', path: '/docs/papers/07_TrOCR_Transformer_OCR.md', type: 'file' },
      { name: 'ESRGAN - Super Resolution', path: '/docs/papers/08_ESRGAN_Super_Resolution.md', type: 'file' },
      { name: 'Qwen2-VL - Vision Language', path: '/docs/papers/09_Qwen2-VL_Vision_Language.md', type: 'file' },
      { name: 'GraphRAG - Knowledge Graph', path: '/docs/papers/10_GraphRAG_Knowledge_Graph.md', type: 'file' },
      { name: 'Tesseract - LSTM OCR', path: '/docs/papers/11_Tesseract_LSTM_OCR.md', type: 'file' },
      { name: 'Surya - Multilingual OCR', path: '/docs/papers/12_Surya_OCR_Multilingual.md', type: 'file' },
      { name: 'DocTR - Document OCR', path: '/docs/papers/13_DocTR_Document_OCR.md', type: 'file' },
      { name: 'EasyOCR - Ready-to-use', path: '/docs/papers/14_EasyOCR_Ready_to_Use.md', type: 'file' },
      { name: 'OCR Ensemble - Voting', path: '/docs/papers/15_OCR_Ensemble_Voting.md', type: 'file' },
    ],
  },
];

interface FolderTreeProps {
  items: DocFile[];
  onSelectFile: (path: string) => void;
  selectedFile: string | null;
  searchQuery: string;
}

function FolderTree({ items, onSelectFile, selectedFile, searchQuery }: FolderTreeProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set(['quickstart', 'user', 'api']));

  // Expand all folders when searching
  useEffect(() => {
    if (searchQuery) {
      const allFolders = items.map(item => item.path);
      setExpanded(new Set(allFolders));
    }
  }, [searchQuery, items]);

  const toggleFolder = (path: string) => {
    const newExpanded = new Set(expanded);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpanded(newExpanded);
  };

  const matchesSearch = (name: string): boolean => {
    if (!searchQuery) return true;
    return name.toLowerCase().includes(searchQuery.toLowerCase());
  };

  const hasMatchingChildren = (item: DocFile): boolean => {
    if (matchesSearch(item.name)) return true;
    if (item.children) {
      return item.children.some(child => hasMatchingChildren(child));
    }
    return false;
  };

  const renderItem = (item: DocFile, level: number = 0) => {
    if (!hasMatchingChildren(item)) return null;

    const isExpanded = expanded.has(item.path);
    const isSelected = selectedFile === item.path;
    const Icon = item.type === 'folder'
      ? (isExpanded ? FolderOpen : Folder)
      : FileText;
    const ChevronIcon = isExpanded ? ChevronDown : ChevronRight;

    const folderColors: Record<string, string> = {
      'quickstart': 'text-green-500',
      'user': 'text-blue-500',
      'developer': 'text-purple-500',
      'blueprintflow': 'text-indigo-500',
      'api': 'text-orange-500',
      'technical': 'text-cyan-500',
      'deployment': 'text-red-500',
      'papers': 'text-amber-500',
    };

    const folderColor = item.type === 'folder' ? (folderColors[item.path] || 'text-blue-500') : 'text-gray-500';

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
          className={`w-full flex items-center gap-2 px-3 py-1.5 text-sm rounded-md transition-all ${
            item.type === 'file'
              ? isSelected
                ? 'bg-primary/10 text-primary font-medium border-l-2 border-primary'
                : 'hover:bg-accent text-muted-foreground hover:text-foreground'
              : 'font-semibold hover:bg-accent/50 mt-1'
          }`}
          style={{ paddingLeft: `${level * 16 + 8}px` }}
        >
          {item.type === 'folder' && (
            <ChevronIcon className="w-3.5 h-3.5 flex-shrink-0 text-muted-foreground" />
          )}
          <Icon className={`w-4 h-4 flex-shrink-0 ${folderColor}`} />
          <span className="text-left flex-1 truncate">{item.name}</span>
        </button>
        {item.type === 'folder' && isExpanded && item.children && (
          <div className="border-l border-border/50 ml-4">
            {item.children.map((child) => renderItem(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-0.5">
      {items.map((item) => renderItem(item))}
    </div>
  );
}

export default function Docs() {
  const { t } = useTranslation();
  const [selectedFile, setSelectedFile] = useState<string | null>('/README.md');
  const [markdown, setMarkdown] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Get current file name for breadcrumb
  const currentFileName = useMemo(() => {
    if (!selectedFile) return '';
    const parts = selectedFile.split('/');
    return parts[parts.length - 1];
  }, [selectedFile]);

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
        setError(`${t('docs.notFound')}: ${err instanceof Error ? err.message : 'Unknown error'}`);
        setMarkdown('');
      } finally {
        setLoading(false);
      }
    };

    fetchMarkdown();
  }, [selectedFile, t]);

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
      {/* Sidebar Toggle Button (visible when sidebar is closed) */}
      {!sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(true)}
          className="fixed left-0 top-20 z-10 p-2 bg-card border border-l-0 rounded-r-md shadow-md hover:bg-accent transition-colors"
          title="Open sidebar"
        >
          <PanelLeft className="w-5 h-5 text-muted-foreground" />
        </button>
      )}

      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-72' : 'w-0'} border-r bg-card/50 flex flex-col transition-all duration-300 overflow-hidden`}>
        <div className="p-4 border-b min-w-[288px]">
          <div className="flex items-center gap-2 mb-3">
            <Book className="w-5 h-5 text-primary" />
            <h2 className="font-bold text-lg flex-1">{t('docs.title')}</h2>
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-1.5 hover:bg-accent rounded-md transition-colors"
              title="Close sidebar"
            >
              <PanelLeftClose className="w-4 h-4 text-muted-foreground" />
            </button>
          </div>
          {/* Search Input */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search docs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-8 py-2 text-sm border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-accent rounded"
              >
                <X className="w-3.5 h-3.5 text-muted-foreground" />
              </button>
            )}
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-2 min-w-[288px]">
          <FolderTree
            items={docStructure}
            onSelectFile={setSelectedFile}
            selectedFile={selectedFile}
            searchQuery={searchQuery}
          />
        </div>
        {/* Stats */}
        <div className="p-3 border-t text-xs text-muted-foreground min-w-[288px]">
          8 categories, 60 documents
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Breadcrumb Header */}
        {selectedFile && (
          <div className="px-8 py-3 border-b bg-muted/30 flex items-center gap-2 text-sm">
            <span className="text-muted-foreground">docs</span>
            <ChevronRight className="w-4 h-4 text-muted-foreground" />
            <span className="font-medium text-foreground">{currentFileName}</span>
          </div>
        )}

        <div className="flex-1 overflow-y-auto">
          <div className="max-w-4xl mx-auto p-8">
            {loading && (
              <div className="flex items-center justify-center py-12">
                <div className="animate-pulse text-muted-foreground">{t('docs.loading')}</div>
              </div>
            )}

            {error && (
              <div className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg p-6">
                <h3 className="font-semibold text-red-700 dark:text-red-300 mb-2">{t('common.error')}</h3>
                <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              </div>
            )}

            {!loading && !error && markdown && (
              <article className="prose prose-slate dark:prose-invert max-w-none
                prose-headings:scroll-mt-20
                prose-headings:font-bold
                prose-h1:text-3xl prose-h1:border-b prose-h1:pb-2 prose-h1:mb-6
                prose-h2:text-2xl prose-h2:mt-8 prose-h2:mb-4
                prose-h3:text-xl prose-h3:mt-6
                prose-p:leading-7
                prose-li:my-1
                prose-blockquote:border-l-4 prose-blockquote:border-primary prose-blockquote:bg-muted/50 prose-blockquote:py-1 prose-blockquote:px-4 prose-blockquote:italic
                prose-hr:my-8
                prose-img:rounded-lg prose-img:shadow-md
                prose-pre:bg-slate-900 prose-pre:text-slate-50
              ">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeRaw]}
                components={{
                  // Pre 태그 - Mermaid 다이어그램 및 코드 블록 처리
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
                              <ImageZoom>
                                <Mermaid chart={chartCode} />
                              </ImageZoom>
                            </div>
                          );
                        }
                      }

                      // 언어 라벨 표시
                      if (language) {
                        return (
                          <div className="relative group">
                            <span className="absolute right-3 top-2 text-xs text-slate-400 font-mono opacity-70">
                              {language}
                            </span>
                            <pre className="rounded-lg overflow-x-auto" {...props}>{children}</pre>
                          </div>
                        );
                      }
                    }

                    return <pre className="rounded-lg overflow-x-auto" {...props}>{children}</pre>;
                  },
                  // 코드 블록 스타일링
                  code: ({ node: _node, className, children, ...props }) => {
                    const match = /language-(\w+)/.exec(className || '');
                    const isInline = !match;

                    if (isInline) {
                      return (
                        <code className="bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded text-sm font-mono text-pink-600 dark:text-pink-400" {...props}>
                          {children}
                        </code>
                      );
                    }

                    return (
                      <code className={`${className} text-sm`} {...props}>
                        {children}
                      </code>
                    );
                  },
                  // 링크 스타일링
                  a: ({ node: _node, children, ...props }) => (
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
                  table: ({ node: _node, children, ...props }) => (
                    <div className="overflow-x-auto my-6">
                      <table className="min-w-full border-collapse border border-gray-300 dark:border-gray-700" {...props}>
                        {children}
                      </table>
                    </div>
                  ),
                  th: ({ node: _node, children, ...props }) => (
                    <th className="border border-gray-300 dark:border-gray-700 bg-gray-100 dark:bg-gray-800 px-4 py-2 text-left font-semibold" {...props}>
                      {children}
                    </th>
                  ),
                  td: ({ node: _node, children, ...props }) => (
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
    </div>
  );
}
