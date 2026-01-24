/**
 * SaveTemplateModal Component
 * 워크플로우를 템플릿으로 저장하는 모달
 */

import React, { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Save, X, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from '../../../components/ui/Button';
import { templateApi, type TemplateCreate, type TemplateNode, type TemplateEdge } from '../../../lib/api';
import type { Node, Edge } from 'reactflow';

// YOLO 모델 타입
const MODEL_TYPES = [
  { value: 'bom_detector', label: 'BOM Detector (기계 도면)' },
  { value: 'pid_symbol', label: 'P&ID Symbol (심볼 검출)' },
  { value: 'pid_class_aware', label: 'P&ID Class-Aware (클래스 분류)' },
  { value: 'engineering', label: 'Engineering (엔지니어링 도면)' },
] as const;

// 지원 기능 목록
const FEATURE_OPTIONS = [
  { value: 'symbol_detection', label: 'Symbol Detection' },
  { value: 'dimension_ocr', label: 'Dimension OCR' },
  { value: 'table_extraction', label: 'Table Extraction' },
  { value: 'gdt_parsing', label: 'GD&T Parsing' },
  { value: 'gt_comparison', label: 'GT Comparison' },
  { value: 'bom_generation', label: 'BOM Generation' },
  { value: 'pdf_export', label: 'PDF Export' },
  { value: 'excel_export', label: 'Excel Export' },
] as const;

// 도면 타입
const DRAWING_TYPES = [
  { value: 'auto', label: 'Auto (자동 분류)' },
  { value: 'mechanical', label: 'Mechanical (기계 도면)' },
  { value: 'pid', label: 'P&ID (배관계장도)' },
  { value: 'electrical', label: 'Electrical (전기 도면)' },
  { value: 'architectural', label: 'Architectural (건축 도면)' },
] as const;

interface SaveTemplateModalProps {
  isOpen: boolean;
  onClose: () => void;
  workflowName: string;
  nodes: Node[];
  edges: Edge[];
  onSuccess?: (templateId: string) => void;
}

export function SaveTemplateModal({
  isOpen,
  onClose,
  workflowName,
  nodes,
  edges,
  onSuccess,
}: SaveTemplateModalProps) {
  const { t } = useTranslation();

  // Form state
  const [name, setName] = useState(workflowName || 'New Template');
  const [description, setDescription] = useState('');
  const [modelType, setModelType] = useState<string>('bom_detector');
  const [drawingType, setDrawingType] = useState<string>('auto');
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Extract node types from workflow
  const nodeTypes = useMemo(() => {
    const types = new Set<string>();
    nodes.forEach((node) => {
      if (node.type) types.add(node.type);
    });
    return Array.from(types);
  }, [nodes]);

  // Toggle feature selection
  const toggleFeature = (feature: string) => {
    setSelectedFeatures((prev) =>
      prev.includes(feature)
        ? prev.filter((f) => f !== feature)
        : [...prev, feature]
    );
  };

  // Handle form submit
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      // Transform nodes to template format
      const templateNodes: TemplateNode[] = nodes.map((node) => ({
        id: node.id,
        type: node.type || 'unknown',
        label: node.data?.label,
        position: node.position,
        parameters: node.data?.parameters || {},
      }));

      // Transform edges to template format
      const templateEdges: TemplateEdge[] = edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        sourceHandle: edge.sourceHandle || undefined,
        targetHandle: edge.targetHandle || undefined,
      }));

      // Build template create request
      const templateData: TemplateCreate = {
        name,
        description: description || undefined,
        model_type: modelType,
        features: selectedFeatures,
        drawing_type: drawingType,
        detection_params: {},
        nodes: templateNodes,
        edges: templateEdges,
      };

      const result = await templateApi.create(templateData);

      setSuccess(true);
      setTimeout(() => {
        onSuccess?.(result.template_id);
        onClose();
      }, 1500);
    } catch (err) {
      console.error('Failed to save template:', err);
      setError(err instanceof Error ? err.message : 'Failed to save template');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-blue-50 dark:bg-blue-900/30 px-6 py-4 border-b border-blue-200 dark:border-blue-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Save className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100">
              {t('blueprintflow.saveAsTemplate', 'Save as Template')}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-4">
          {/* Success Message */}
          {success && (
            <div className="bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-lg p-4 flex items-center gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
              <span className="text-green-800 dark:text-green-200">
                {t('blueprintflow.templateSaved', 'Template saved successfully!')}
              </span>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
              <span className="text-red-800 dark:text-red-200">{error}</span>
            </div>
          )}

          {/* Template Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('blueprintflow.templateName', 'Template Name')} *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter template name"
              required
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('blueprintflow.description', 'Description')}
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Optional description for this template"
            />
          </div>

          {/* Model Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('blueprintflow.modelType', 'YOLO Model Type')} *
            </label>
            <select
              value={modelType}
              onChange={(e) => setModelType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {MODEL_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* Drawing Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('blueprintflow.drawingType', 'Drawing Type')}
            </label>
            <select
              value={drawingType}
              onChange={(e) => setDrawingType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {DRAWING_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* Features */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t('blueprintflow.features', 'Features')}
            </label>
            <div className="grid grid-cols-2 gap-2">
              {FEATURE_OPTIONS.map((feature) => (
                <label
                  key={feature.value}
                  className="flex items-center gap-2 p-2 border border-gray-200 dark:border-gray-600 rounded-md cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  <input
                    type="checkbox"
                    checked={selectedFeatures.includes(feature.value)}
                    onChange={() => toggleFeature(feature.value)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">{feature.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Workflow Summary */}
          <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t('blueprintflow.workflowSummary', 'Workflow Summary')}
            </h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="text-gray-600 dark:text-gray-400">
                Nodes: <span className="font-medium text-gray-900 dark:text-white">{nodes.length}</span>
              </div>
              <div className="text-gray-600 dark:text-gray-400">
                Edges: <span className="font-medium text-gray-900 dark:text-white">{edges.length}</span>
              </div>
            </div>
            {nodeTypes.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {nodeTypes.map((type) => (
                  <span
                    key={type}
                    className="px-2 py-0.5 text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded"
                  >
                    {type}
                  </span>
                ))}
              </div>
            )}
          </div>
        </form>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={isSubmitting}
          >
            {t('common.cancel', 'Cancel')}
          </Button>
          <Button
            type="submit"
            onClick={handleSubmit}
            disabled={isSubmitting || success || !name.trim()}
            className="bg-blue-600 hover:bg-blue-700 flex items-center gap-2"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                {t('blueprintflow.saving', 'Saving...')}
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                {t('blueprintflow.saveTemplate', 'Save Template')}
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
