import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Sparkles, Download, GitBranch, Clock, Target } from 'lucide-react';
import { useWorkflowStore } from '../../store/workflowStore';
import type { WorkflowDefinition } from '../../lib/api';

interface TemplateInfo {
  nameKey: string;
  descKey: string;
  workflow: WorkflowDefinition;
  estimatedTime: string;
  accuracy: string;
}

export default function BlueprintFlowTemplates() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { loadWorkflow } = useWorkflowStore();

  const templates: TemplateInfo[] = [
    {
      nameKey: 'accuracyPipeline',
      descKey: 'accuracyPipelineDesc',
      estimatedTime: '10-15s',
      accuracy: '95%',
      workflow: {
        name: 'Accuracy Pipeline',
        description: 'High accuracy pipeline with YOLO detection, edge segmentation, and dual OCR',
        nodes: [
          {
            id: 'yolo_1',
            type: 'yolo',
            label: 'YOLO Detection',
            parameters: { confidence: 0.5, model: 'yolo11n' },
            position: { x: 100, y: 100 },
          },
          {
            id: 'edgnet_1',
            type: 'edgnet',
            label: 'Edge Segmentation',
            parameters: { threshold: 0.5 },
            position: { x: 350, y: 100 },
          },
          {
            id: 'edocr2_1',
            type: 'edocr2',
            label: 'Korean OCR',
            parameters: {},
            position: { x: 600, y: 50 },
          },
          {
            id: 'paddleocr_1',
            type: 'paddleocr',
            label: 'PaddleOCR',
            parameters: { lang: 'en' },
            position: { x: 600, y: 150 },
          },
          {
            id: 'merge_1',
            type: 'merge',
            label: 'Merge Results',
            parameters: {},
            position: { x: 850, y: 100 },
          },
        ],
        edges: [
          { id: 'e1', source: 'yolo_1', target: 'edgnet_1' },
          { id: 'e2', source: 'edgnet_1', target: 'edocr2_1' },
          { id: 'e3', source: 'edgnet_1', target: 'paddleocr_1' },
          { id: 'e4', source: 'edocr2_1', target: 'merge_1' },
          { id: 'e5', source: 'paddleocr_1', target: 'merge_1' },
        ],
      },
    },
    {
      nameKey: 'speedPipeline',
      descKey: 'speedPipelineDesc',
      estimatedTime: '5-8s',
      accuracy: '90%',
      workflow: {
        name: 'Speed Pipeline',
        description: 'Fast pipeline with YOLO and single OCR',
        nodes: [
          {
            id: 'yolo_1',
            type: 'yolo',
            label: 'YOLO Detection',
            parameters: { confidence: 0.5, model: 'yolo11n' },
            position: { x: 100, y: 100 },
          },
          {
            id: 'edocr2_1',
            type: 'edocr2',
            label: 'Korean OCR',
            parameters: {},
            position: { x: 400, y: 100 },
          },
          {
            id: 'skinmodel_1',
            type: 'skinmodel',
            label: 'Tolerance Analysis',
            parameters: {},
            position: { x: 700, y: 100 },
          },
        ],
        edges: [
          { id: 'e1', source: 'yolo_1', target: 'edocr2_1' },
          { id: 'e2', source: 'edocr2_1', target: 'skinmodel_1' },
        ],
      },
    },
    {
      nameKey: 'conditionalOCR',
      descKey: 'conditionalOCRDesc',
      estimatedTime: '10-12s',
      accuracy: '94%',
      workflow: {
        name: 'Conditional OCR Pipeline',
        description: 'Intelligent pipeline with conditional branching based on detection confidence',
        nodes: [
          {
            id: 'yolo_1',
            type: 'yolo',
            label: 'YOLO Detection',
            parameters: { confidence: 0.5, model: 'yolo11n' },
            position: { x: 100, y: 150 },
          },
          {
            id: 'if_1',
            type: 'if',
            label: 'Check Confidence',
            parameters: { condition: 'confidence > 0.8' },
            position: { x: 350, y: 150 },
          },
          {
            id: 'edocr2_1',
            type: 'edocr2',
            label: 'Korean OCR (High Confidence)',
            parameters: {},
            position: { x: 600, y: 80 },
          },
          {
            id: 'paddleocr_1',
            type: 'paddleocr',
            label: 'PaddleOCR (Low Confidence)',
            parameters: { lang: 'en' },
            position: { x: 600, y: 220 },
          },
          {
            id: 'merge_1',
            type: 'merge',
            label: 'Merge Results',
            parameters: {},
            position: { x: 850, y: 150 },
          },
        ],
        edges: [
          { id: 'e1', source: 'yolo_1', target: 'if_1' },
          { id: 'e2', source: 'if_1', target: 'edocr2_1', sourceHandle: 'true' },
          { id: 'e3', source: 'if_1', target: 'paddleocr_1', sourceHandle: 'false' },
          { id: 'e4', source: 'edocr2_1', target: 'merge_1' },
          { id: 'e5', source: 'paddleocr_1', target: 'merge_1' },
        ],
      },
    },
    {
      nameKey: 'loopDetection',
      descKey: 'loopDetectionDesc',
      estimatedTime: '15-20s',
      accuracy: '96%',
      workflow: {
        name: 'Loop Detection Pipeline',
        description: 'Process each YOLO detection individually with loop',
        nodes: [
          {
            id: 'yolo_1',
            type: 'yolo',
            label: 'YOLO Detection',
            parameters: { confidence: 0.5, model: 'yolo11n' },
            position: { x: 100, y: 150 },
          },
          {
            id: 'loop_1',
            type: 'loop',
            label: 'For Each Detection',
            parameters: { iterator: 'detections' },
            position: { x: 350, y: 150 },
          },
          {
            id: 'edocr2_1',
            type: 'edocr2',
            label: 'OCR Each Box',
            parameters: {},
            position: { x: 600, y: 150 },
          },
          {
            id: 'skinmodel_1',
            type: 'skinmodel',
            label: 'Tolerance Analysis',
            parameters: {},
            position: { x: 850, y: 150 },
          },
        ],
        edges: [
          { id: 'e1', source: 'yolo_1', target: 'loop_1' },
          { id: 'e2', source: 'loop_1', target: 'edocr2_1' },
          { id: 'e3', source: 'edocr2_1', target: 'skinmodel_1' },
        ],
      },
    },
  ];

  const handleLoadTemplate = (template: TemplateInfo) => {
    loadWorkflow(template.workflow);
    navigate('/blueprintflow/builder');
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Sparkles className="w-8 h-8 text-cyan-600" />
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
            {t('blueprintflow.workflowTemplates')}
          </h1>
          <Badge className="bg-cyan-600">BETA</Badge>
        </div>
        <p className="text-gray-600 dark:text-gray-400">
          {t('blueprintflow.templatesSubtitle')}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {templates.map((template, index) => (
          <Card key={index} className="hover:shadow-lg transition-shadow group">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-xl font-bold mb-2">
                    {t(`blueprintflow.${template.nameKey}`)}
                  </CardTitle>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {t(`blueprintflow.${template.descKey}`)}
                  </p>
                </div>
                <Badge className="bg-gradient-to-r from-cyan-500 to-blue-500 text-white">
                  Template
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

              <Button
                onClick={() => handleLoadTemplate(template)}
                className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700"
              >
                <Download className="w-4 h-4" />
                {t('blueprintflow.useTemplate')}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

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
    </div>
  );
}
