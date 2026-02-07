import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Sparkles, Download, GitBranch, Clock, Target, Star, Zap, Brain, Layers, Lightbulb, FlaskConical, Ship, Cog, Factory, Rocket } from 'lucide-react';
import { useWorkflowStore } from '../../store/workflowStore';
import { DeployTemplateModal } from './components/DeployTemplateModal';
import { templates } from './templates';
import type { TemplateInfo, TemplateCategory } from './templates';

export default function BlueprintFlowTemplates() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { loadWorkflow } = useWorkflowStore();
  const [activeTab, setActiveTab] = useState<TemplateCategory>('all');
  const [deployModalOpen, setDeployModalOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateInfo | null>(null);

  const handleLoadTemplate = async (template: TemplateInfo) => {
    loadWorkflow(template.workflow);

    // 샘플 이미지 번들 로드
    if (template.sampleImage) {
      try {
        const res = await fetch(template.sampleImage);
        const blob = await res.blob();
        const filename = template.sampleImage.split('/').pop() || 'sample.jpg';
        const file = new File([blob], filename, { type: 'image/jpeg' });
        const reader = new FileReader();
        reader.onload = (e) => {
          useWorkflowStore.getState().setUploadedImage(e.target?.result as string, filename);
        };
        reader.readAsDataURL(file);
      } catch { /* ignore sample load failure */ }
    }

    // 샘플 GT 번들 로드
    if (template.sampleGT) {
      try {
        const res = await fetch(template.sampleGT);
        const text = await res.text();
        const gtName = template.sampleGT.split('/').pop() || 'labels.txt';
        const dataUrl = 'data:text/plain;base64,' + btoa(text);
        useWorkflowStore.getState().setUploadedGTFile({ name: gtName, content: dataUrl });
      } catch { /* ignore GT load failure */ }
    }

    navigate('/blueprintflow/builder');
  };

  const handleDeployTemplate = (template: TemplateInfo) => {
    setSelectedTemplate(template);
    setDeployModalOpen(true);
  };

  const categoryInfo: Record<TemplateCategory, { icon: typeof Star; color: string; label: string; shortLabel: string }> = {
    all: { icon: Sparkles, color: 'from-gray-500 to-gray-600', label: t('blueprintflow.allTemplates', '전체'), shortLabel: t('blueprintflow.all', '전체') },
    featured: { icon: Star, color: 'from-amber-500 to-orange-500', label: t('blueprintflow.featuredTemplates'), shortLabel: '⭐ Featured' },
    panasia: { icon: Factory, color: 'from-emerald-500 to-green-600', label: t('blueprintflow.panasiaTemplates'), shortLabel: '🏭 PANASIA' },
    techcross: { icon: Ship, color: 'from-sky-500 to-blue-600', label: t('blueprintflow.techcrossTemplates'), shortLabel: '🚢 TECHCROSS' },
    dsebearing: { icon: Cog, color: 'from-amber-500 to-orange-600', label: t('blueprintflow.dsebearingTemplates'), shortLabel: '⚙️ DSE Bearing' },
    basic: { icon: Zap, color: 'from-green-500 to-emerald-500', label: t('blueprintflow.basicTemplates'), shortLabel: '⚡ Basic' },
    advanced: { icon: Layers, color: 'from-blue-500 to-indigo-500', label: t('blueprintflow.advancedTemplates'), shortLabel: '🔧 Advanced' },
    pid: { icon: GitBranch, color: 'from-purple-500 to-pink-500', label: t('blueprintflow.pidTemplates'), shortLabel: '🔀 P&ID' },
    ai: { icon: Brain, color: 'from-cyan-500 to-teal-500', label: t('blueprintflow.aiTemplates'), shortLabel: '🧠 AI' },
    benchmark: { icon: FlaskConical, color: 'from-rose-500 to-red-500', label: t('blueprintflow.benchmarkTemplates'), shortLabel: '🧪 Benchmark' },
  };

  // Get templates for active tab (hidden 템플릿 제외)
  const visibleTemplates = templates.filter(t => !t.hidden);

  const getFilteredTemplates = (): TemplateInfo[] => {
    if (activeTab === 'all') return visibleTemplates;
    if (activeTab === 'featured') return visibleTemplates.filter(t => t.featured);
    return visibleTemplates.filter(t => t.category === activeTab);
  };

  const filteredTemplates = getFilteredTemplates();

  // Count templates per category
  const getCategoryCount = (category: TemplateCategory): number => {
    if (category === 'all') return visibleTemplates.length;
    if (category === 'featured') return visibleTemplates.filter(t => t.featured).length;
    return visibleTemplates.filter(t => t.category === category).length;
  };

  const tabCategories: TemplateCategory[] = ['all', 'featured', 'panasia', 'techcross', 'dsebearing', 'basic', 'advanced', 'pid', 'ai', 'benchmark'];


  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <Sparkles className="w-8 h-8 text-cyan-600" />
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
            {t('blueprintflow.workflowTemplates')}
          </h1>
          <Badge className="bg-cyan-600">BETA</Badge>
          <Badge variant="outline" className="ml-2">{templates.length} templates</Badge>
        </div>
        <p className="text-gray-600 dark:text-gray-400">
          {t('blueprintflow.templatesSubtitle')}
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="mb-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex flex-wrap gap-1 -mb-px overflow-x-auto pb-px">
          {tabCategories.map((category) => {
            const { icon: Icon, shortLabel } = categoryInfo[category];
            const count = getCategoryCount(category);
            const isActive = activeTab === category;

            return (
              <button
                key={category}
                onClick={() => setActiveTab(category)}
                className={`
                  flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all whitespace-nowrap
                  ${isActive
                    ? `border-cyan-500 text-cyan-600 dark:text-cyan-400 bg-cyan-50 dark:bg-cyan-900/20`
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
                  }
                `}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-500' : ''}`} />
                <span>{shortLabel}</span>
                <Badge
                  variant={isActive ? 'default' : 'outline'}
                  className={`ml-1 text-xs px-1.5 py-0 ${isActive ? 'bg-cyan-500' : ''}`}
                >
                  {count}
                </Badge>
              </button>
            );
          })}
        </div>
      </div>

      {/* Active Tab Header */}
      {activeTab !== 'all' && (
        <div className="flex items-center gap-3 mb-6">
          <div className={`p-2 rounded-lg bg-gradient-to-r ${categoryInfo[activeTab].color}`}>
            {(() => {
              const Icon = categoryInfo[activeTab].icon;
              return <Icon className="w-5 h-5 text-white" />;
            })()}
          </div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            {categoryInfo[activeTab].label}
          </h2>
          <Badge variant="outline">{filteredTemplates.length}</Badge>
        </div>
      )}

      {/* Template Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {filteredTemplates.map((template, index) => {
          const { color } = categoryInfo[template.category as TemplateCategory] || categoryInfo.basic;

          return (
            <Card
              key={`${template.nameKey}-${index}`}
              className={`hover:shadow-lg transition-shadow group ${template.featured ? 'ring-2 ring-amber-400 dark:ring-amber-500' : ''}`}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <CardTitle className="text-xl font-bold">
                        {t(`blueprintflow.${template.nameKey}`)}
                      </CardTitle>
                      {template.featured && (
                        <Star className="w-5 h-5 text-amber-500 fill-amber-500" />
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {t(`blueprintflow.${template.descKey}`)}
                    </p>
                  </div>
                  <Badge className={`bg-gradient-to-r ${color} text-white`}>
                    {template.category.toUpperCase()}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 mb-6">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                      <GitBranch className="w-4 h-4" />
                      <span>{t('blueprintflow.nodes')}:</span>
                    </div>
                    <span className="font-semibold">{template.workflow.nodes.length} nodes</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                      <Clock className="w-4 h-4" />
                      <span>{t('blueprintflow.estimatedTime')}:</span>
                    </div>
                    <span className="font-semibold">{template.estimatedTime}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                      <Target className="w-4 h-4" />
                      <span>{t('blueprintflow.accuracy')}:</span>
                    </div>
                    <span className="font-semibold text-green-600 dark:text-green-400">
                      {template.accuracy}
                    </span>
                  </div>
                </div>

                {/* Use Case Recommendation */}
                <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3 mb-4">
                  <div className="flex items-start gap-2">
                    <Lightbulb className="w-4 h-4 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="text-xs font-semibold text-amber-800 dark:text-amber-300 mb-1">
                        {t('blueprintflow.whenToUse')}
                      </div>
                      <p className="text-xs text-amber-700 dark:text-amber-400">
                        {t(`blueprintflow.${template.useCaseKey}`)}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 mb-4">
                  <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                    Pipeline Flow:
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {template.workflow.nodes.map((node, idx) => (
                      <div key={node.id} className="flex items-center">
                        <Badge variant="outline" className="text-xs">
                          {node.label}
                        </Badge>
                        {idx < template.workflow.nodes.length - 1 && (
                          <span className="mx-1 text-gray-400">→</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={() => handleLoadTemplate(template)}
                    className="flex-1 flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700"
                  >
                    <Download className="w-4 h-4" />
                    {t('blueprintflow.useTemplate')}
                  </Button>
                  <Button
                    onClick={() => handleDeployTemplate(template)}
                    variant="outline"
                    className="flex items-center gap-1 border-purple-300 hover:bg-purple-50 hover:border-purple-500 dark:border-purple-600 dark:hover:bg-purple-900/20"
                    title="고객용 세션으로 배포"
                  >
                    <Rocket className="w-4 h-4 text-purple-500" />
                    <span className="hidden sm:inline text-purple-600 dark:text-purple-400">Deploy</span>
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Empty State */}
      {filteredTemplates.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">
            {t('blueprintflow.noTemplatesInCategory', '이 카테고리에 템플릿이 없습니다.')}
          </p>
        </div>
      )}

      {/* How Templates Work */}
      <Card className="mt-8 border-cyan-200 dark:border-cyan-800">
        <CardHeader className="bg-cyan-50 dark:bg-cyan-900/20">
          <CardTitle className="text-cyan-900 dark:text-cyan-100">
            {t('blueprintflow.howTemplatesWork')}
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            {t('blueprintflow.templatesExplanation')}
          </p>
          <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg text-xs font-mono overflow-x-auto">
            <pre>{`{
  "workflow": {
    "name": "${t('blueprintflow.accuracyPipeline')}",
    "nodes": [
      { "id": "yolo_1", "type": "yolo", "params": {...} },
      { "id": "edocr2_1", "type": "edocr2", "params": {...} }
    ],
    "edges": [
      { "source": "yolo_1", "target": "edocr2_1" }
    ]
  }
}`}</pre>
          </div>
        </CardContent>
      </Card>

      {/* Deploy Template Modal */}
      {selectedTemplate && (
        <DeployTemplateModal
          isOpen={deployModalOpen}
          onClose={() => {
            setDeployModalOpen(false);
            setSelectedTemplate(null);
          }}
          template={selectedTemplate}
        />
      )}
    </div>
  );
}
