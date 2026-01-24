/**
 * LoadTemplateModal Component
 * 템플릿 목록에서 선택하여 워크플로우에 로드하는 모달
 */

import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { FolderOpen, X, Loader2, AlertCircle, Trash2, Copy, RefreshCw } from 'lucide-react';
import { Button } from '../../../components/ui/Button';
import { templateApi, type TemplateResponse, type TemplateDetail } from '../../../lib/api';

interface LoadTemplateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoad: (template: TemplateDetail) => void;
}

export function LoadTemplateModal({
  isOpen,
  onClose,
  onLoad,
}: LoadTemplateModalProps) {
  const { t } = useTranslation();

  // Data state
  const [templates, setTemplates] = useState<TemplateResponse[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateDetail | null>(null);

  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterModelType, setFilterModelType] = useState<string>('');

  // Load template list on open
  useEffect(() => {
    if (isOpen) {
      loadTemplates();
    }
  }, [isOpen]);

  // Load template detail when selected
  useEffect(() => {
    if (selectedId) {
      loadTemplateDetail(selectedId);
    } else {
      setSelectedTemplate(null);
    }
  }, [selectedId]);

  const loadTemplates = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await templateApi.list(filterModelType || undefined);
      setTemplates(response.templates);
    } catch (err) {
      console.error('Failed to load templates:', err);
      setError(err instanceof Error ? err.message : 'Failed to load templates');
    } finally {
      setIsLoading(false);
    }
  };

  const loadTemplateDetail = async (templateId: string) => {
    setIsLoadingDetail(true);
    try {
      const detail = await templateApi.get(templateId);
      setSelectedTemplate(detail);
    } catch (err) {
      console.error('Failed to load template detail:', err);
      setError(err instanceof Error ? err.message : 'Failed to load template detail');
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const handleLoad = () => {
    if (selectedTemplate) {
      onLoad(selectedTemplate);
      onClose();
    }
  };

  const handleDelete = async (templateId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this template?')) return;

    try {
      await templateApi.delete(templateId);
      setTemplates((prev) => prev.filter((t) => t.template_id !== templateId));
      if (selectedId === templateId) {
        setSelectedId(null);
        setSelectedTemplate(null);
      }
    } catch (err) {
      console.error('Failed to delete template:', err);
      alert('Failed to delete template');
    }
  };

  const handleDuplicate = async (templateId: string, name: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const newName = prompt('Enter name for duplicated template:', `${name} (Copy)`);
    if (!newName) return;

    try {
      const duplicated = await templateApi.duplicate(templateId, newName);
      setTemplates((prev) => [duplicated, ...prev]);
    } catch (err) {
      console.error('Failed to duplicate template:', err);
      alert('Failed to duplicate template');
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[85vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-purple-50 dark:bg-purple-900/30 px-6 py-4 border-b border-purple-200 dark:border-purple-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FolderOpen className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            <h3 className="text-lg font-semibold text-purple-900 dark:text-purple-100">
              {t('blueprintflow.loadTemplate', 'Load Template')}
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
        <div className="flex-1 overflow-hidden flex">
          {/* Template List */}
          <div className="w-1/2 border-r border-gray-200 dark:border-gray-700 flex flex-col">
            {/* Filter */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex gap-2">
              <select
                value={filterModelType}
                onChange={(e) => setFilterModelType(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
              >
                <option value="">All Model Types</option>
                <option value="bom_detector">BOM Detector</option>
                <option value="pid_symbol">P&ID Symbol</option>
                <option value="pid_class_aware">P&ID Class-Aware</option>
                <option value="engineering">Engineering</option>
              </select>
              <Button
                variant="outline"
                size="sm"
                onClick={loadTemplates}
                disabled={isLoading}
                className="px-3"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              </Button>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto p-2">
              {isLoading ? (
                <div className="flex items-center justify-center h-32">
                  <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                </div>
              ) : error ? (
                <div className="flex items-center gap-2 p-4 text-red-600 dark:text-red-400">
                  <AlertCircle className="w-5 h-5" />
                  <span>{error}</span>
                </div>
              ) : templates.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  No templates found
                </div>
              ) : (
                <div className="space-y-2">
                  {templates.map((template) => (
                    <div
                      key={template.template_id}
                      onClick={() => setSelectedId(template.template_id)}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedId === template.template_id
                          ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/30'
                          : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-gray-900 dark:text-white truncate">
                            {template.name}
                          </h4>
                          <div className="flex flex-wrap gap-1 mt-1">
                            <span className="px-1.5 py-0.5 text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
                              {template.model_type}
                            </span>
                            <span className="px-1.5 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded">
                              {template.node_count} nodes
                            </span>
                          </div>
                        </div>
                        <div className="flex gap-1 ml-2">
                          <button
                            onClick={(e) => handleDuplicate(template.template_id, template.name, e)}
                            className="p-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                            title="Duplicate"
                          >
                            <Copy className="w-4 h-4" />
                          </button>
                          <button
                            onClick={(e) => handleDelete(template.template_id, e)}
                            className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {formatDate(template.updated_at)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Template Preview */}
          <div className="w-1/2 flex flex-col">
            {isLoadingDetail ? (
              <div className="flex-1 flex items-center justify-center">
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              </div>
            ) : selectedTemplate ? (
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {selectedTemplate.name}
                  </h4>
                  {selectedTemplate.description && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {selectedTemplate.description}
                    </p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
                    <div className="text-xs text-gray-500 dark:text-gray-400">Model Type</div>
                    <div className="font-medium text-gray-900 dark:text-white">
                      {selectedTemplate.model_type}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
                    <div className="text-xs text-gray-500 dark:text-gray-400">Drawing Type</div>
                    <div className="font-medium text-gray-900 dark:text-white">
                      {selectedTemplate.drawing_type}
                    </div>
                  </div>
                </div>

                {selectedTemplate.features.length > 0 && (
                  <div>
                    <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Features
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {selectedTemplate.features.map((feature) => (
                        <span
                          key={feature}
                          className="px-2 py-0.5 text-xs bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded"
                        >
                          {feature}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Node Types ({selectedTemplate.node_count})
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {selectedTemplate.node_types.map((type) => (
                      <span
                        key={type}
                        className="px-2 py-0.5 text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded"
                      >
                        {type}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">Edges: </span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {selectedTemplate.edge_count}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">Usage: </span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {selectedTemplate.usage_count} times
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-500 dark:text-gray-400">
                Select a template to preview
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
          <Button variant="outline" onClick={onClose}>
            {t('common.cancel', 'Cancel')}
          </Button>
          <Button
            onClick={handleLoad}
            disabled={!selectedTemplate}
            className="bg-purple-600 hover:bg-purple-700 flex items-center gap-2"
          >
            <FolderOpen className="w-4 h-4" />
            {t('blueprintflow.loadTemplate', 'Load Template')}
          </Button>
        </div>
      </div>
    </div>
  );
}
