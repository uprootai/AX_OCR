/**
 * BuilderToolbar — top toolbar for the workflow builder canvas.
 * Contains: workflow name input, image upload, GT/pricing file attachments,
 * template buttons, save, execute, clear, debug toggle.
 */

import React from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '../../../components/ui/Button';
import {
  Play, Save, Trash2, Upload, X, Bug, Loader2, StopCircle,
  FolderOpen, FileDown, FileText, DollarSign, Download, Briefcase,
} from 'lucide-react';
import { BLUEPRINT_SAMPLES } from '../constants';
import { ExecutionModeToggle } from './ExecutionModeToggle';
import { ExecutionStatusPanel } from '../components';
import type { Project } from '../../../lib/blueprintBomApi';
import type { ReactFlowNode } from './types';
import type { NodeStatus } from '../../../store/workflowStore';

export interface BuilderToolbarProps {
  // Workflow state
  workflowName: string;
  nodes: ReactFlowNode[];
  edges: { id: string; source: string; target: string; sourceHandle?: string | null; targetHandle?: string | null }[];
  isExecuting: boolean;
  executionResult: Record<string, unknown> | null;
  executionError: string | null;
  nodeStatuses: Record<string, NodeStatus>;
  executionId: string | null;
  executionMode: 'sequential' | 'parallel' | 'eager';
  isCheckingContainers: boolean;

  // Image upload
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  uploadedImage: string | null;
  uploadedFileName: string | null;
  handleImageUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleRemoveImage: () => void;
  triggerFileInput: () => void;
  loadSampleImage: (path: string) => void;

  // GT file
  gtFileInputRef: React.RefObject<HTMLInputElement | null>;
  uploadedGTFile: { name: string; content: string } | null;
  handleGTFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  setUploadedGTFile: (file: null) => void;

  // Pricing file
  pricingFileInputRef: React.RefObject<HTMLInputElement | null>;
  uploadedPricingFile: { name: string; content: string } | null;
  handlePricingFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  setUploadedPricingFile: (file: null) => void;

  // Projects
  projects: Project[];
  selectedProjectId: string | null;
  setSelectedProjectId: (id: string | null) => void;

  // Callbacks
  onSave: () => void;
  onExecute: () => void;
  onCancelExecution: () => void;
  onClearWorkflow: () => void;
  onDownloadJSON: () => void;
  onDownloadFile: (dataUrl: string, filename: string) => void;
  onOpenSaveTemplateModal: () => void;
  onOpenLoadTemplateModal: () => void;
  onToggleDebugPanel: () => void;
  onSetWorkflowName: (name: string) => void;
  setExecutionMode: (mode: 'sequential' | 'parallel' | 'eager') => void;
  isDebugPanelOpen: boolean;
}

export function BuilderToolbar({
  workflowName,
  nodes,
  edges: _edges,
  isExecuting,
  executionResult,
  executionError,
  nodeStatuses,
  executionId,
  executionMode,
  isCheckingContainers,
  fileInputRef,
  uploadedImage,
  uploadedFileName,
  handleImageUpload,
  handleRemoveImage,
  triggerFileInput,
  loadSampleImage,
  gtFileInputRef,
  uploadedGTFile,
  handleGTFileChange,
  setUploadedGTFile,
  pricingFileInputRef,
  uploadedPricingFile,
  handlePricingFileChange,
  setUploadedPricingFile,
  projects,
  selectedProjectId,
  setSelectedProjectId,
  onSave,
  onExecute,
  onCancelExecution,
  onClearWorkflow,
  onDownloadJSON,
  onDownloadFile,
  onOpenSaveTemplateModal,
  onOpenLoadTemplateModal,
  onToggleDebugPanel,
  onSetWorkflowName,
  setExecutionMode,
  isDebugPanelOpen,
}: BuilderToolbarProps) {
  const { t } = useTranslation();

  return (
    <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center gap-4">
        {/* Workflow Name */}
        <input
          type="text"
          value={workflowName}
          onChange={(e) => onSetWorkflowName(e.target.value)}
          className="px-3 py-2 border rounded-md text-lg font-semibold flex-1 max-w-md text-gray-900 dark:text-white bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
          placeholder={t('blueprintflow.workflowName')}
        />

        {/* Image Upload */}
        <div className="flex items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            className="hidden"
          />
          <Button
            onClick={triggerFileInput}
            variant="outline"
            className="flex items-center gap-2"
            title="Upload input image"
          >
            <Upload className="w-4 h-4" />
            {uploadedFileName || 'Upload Image'}
          </Button>

          {/* Sample Selection */}
          {!uploadedImage && (
            <div className="relative group">
              <Button variant="outline" className="flex items-center gap-2" title="Select sample image">
                <span>또는 샘플 선택</span>
                <span className="text-xs">▼</span>
              </Button>
              <div className="absolute top-full left-0 mt-1 hidden group-hover:block z-50 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg p-2 min-w-[320px] max-h-[400px] overflow-y-auto">
                <div className="text-xs text-gray-500 dark:text-gray-400 px-3 py-1 mb-1 border-b border-gray-200 dark:border-gray-700">
                  샘플 이미지 ({BLUEPRINT_SAMPLES.length}개)
                </div>
                {BLUEPRINT_SAMPLES.map((sample) => (
                  <button
                    key={sample.id}
                    onClick={() => loadSampleImage(sample.path)}
                    className="w-full text-left px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded flex flex-col gap-1"
                  >
                    <div className="font-medium text-sm flex items-center gap-2">
                      {sample.name}
                      {sample.recommended && (
                        <span className="text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 px-1.5 py-0.5 rounded">
                          추천
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      {sample.description}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {uploadedImage && (
            <>
              <button
                onClick={() => onDownloadFile(uploadedImage, uploadedFileName || 'image.png')}
                className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                title="이미지 다운로드"
              >
                <Download className="w-3.5 h-3.5" />
              </button>
              <Button
                onClick={handleRemoveImage}
                variant="outline"
                size="sm"
                className="p-2"
                title="Remove image"
              >
                <X className="w-4 h-4" />
              </Button>
            </>
          )}

          {/* GT 파일 첨부 (이미지 업로드 후) */}
          {uploadedImage && (
            <>
              <input
                ref={gtFileInputRef}
                type="file"
                accept=".txt,.json,.xml"
                className="hidden"
                onChange={handleGTFileChange}
              />
              {uploadedGTFile ? (
                <div className="flex items-center gap-1 text-xs text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-900/30 px-2 py-1 rounded border border-amber-200 dark:border-amber-700">
                  <FileText className="w-3.5 h-3.5" />
                  <span className="truncate max-w-[120px]">GT: {uploadedGTFile.name}</span>
                  <button
                    onClick={() => onDownloadFile(uploadedGTFile.content, uploadedGTFile.name)}
                    className="ml-1 hover:text-amber-500 transition-colors"
                    title="GT 파일 다운로드"
                  >
                    <Download className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => setUploadedGTFile(null)}
                    className="ml-1 hover:text-red-500 transition-colors"
                    title="GT 파일 제거"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => gtFileInputRef.current?.click()}
                  className="flex items-center gap-1 text-xs"
                  title="GT 라벨 파일 첨부 (.txt .json .xml)"
                >
                  <FileText className="w-3.5 h-3.5" />
                  GT 첨부
                </Button>
              )}
            </>
          )}

          {/* 단가 파일 첨부 (이미지 업로드 후) */}
          {uploadedImage && (
            <>
              <input
                ref={pricingFileInputRef}
                type="file"
                accept=".json"
                className="hidden"
                onChange={handlePricingFileChange}
              />
              {uploadedPricingFile ? (
                <div className="flex items-center gap-1 text-xs text-green-700 dark:text-green-300 bg-green-50 dark:bg-green-900/30 px-2 py-1 rounded border border-green-200 dark:border-green-700">
                  <DollarSign className="w-3.5 h-3.5" />
                  <span className="truncate max-w-[120px]">{uploadedPricingFile.name}</span>
                  <button
                    onClick={() => onDownloadFile(uploadedPricingFile.content, uploadedPricingFile.name)}
                    className="ml-1 hover:text-green-500 transition-colors"
                    title="단가 파일 다운로드"
                  >
                    <Download className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => setUploadedPricingFile(null)}
                    className="ml-1 hover:text-red-500 transition-colors"
                    title="단가 파일 제거"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => pricingFileInputRef.current?.click()}
                  className="flex items-center gap-1 text-xs"
                  title="단가 JSON 파일 첨부 (.json)"
                >
                  <DollarSign className="w-3.5 h-3.5" />
                  단가 첨부
                </Button>
              )}
            </>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 ml-auto">
          {/* Template Buttons */}
          <Button
            onClick={onOpenLoadTemplateModal}
            variant="outline"
            className="flex items-center gap-2"
            title={t('blueprintflow.loadTemplateTooltip', 'Load template')}
          >
            <FolderOpen className="w-4 h-4" />
            {t('blueprintflow.loadTemplate', 'Load Template')}
          </Button>

          <Button
            onClick={onOpenSaveTemplateModal}
            variant="outline"
            className="flex items-center gap-2"
            disabled={nodes.length === 0}
            title={t('blueprintflow.saveAsTemplateTooltip', 'Save current workflow as reusable template')}
          >
            <FileDown className="w-4 h-4" />
            {t('blueprintflow.saveAsTemplate', 'Save as Template')}
          </Button>

          <div className="w-px h-8 bg-gray-300 dark:bg-gray-600 mx-1" />

          <Button
            onClick={onSave}
            variant="outline"
            className="flex items-center gap-2"
            title={t('blueprintflow.saveTooltip')}
          >
            <Save className="w-4 h-4" />
            {t('blueprintflow.save')}
          </Button>

          {/* Project Selector */}
          {projects.length > 0 && (
            <div className="flex items-center gap-1">
              <Briefcase className="w-4 h-4 text-gray-500 dark:text-gray-400" />
              <select
                value={selectedProjectId || ''}
                onChange={(e) => setSelectedProjectId(e.target.value || null)}
                className="px-2 py-1.5 text-xs bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-200 max-w-[200px]"
              >
                <option value="">프로젝트 미지정</option>
                {projects.map(p => (
                  <option key={p.project_id} value={p.project_id}>
                    {p.name} ({p.customer})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Execution Mode Toggle */}
          <ExecutionModeToggle
            executionMode={executionMode}
            setExecutionMode={setExecutionMode}
          />

          {/* Execute Button */}
          <Button
            onClick={onExecute}
            disabled={isExecuting || isCheckingContainers || !uploadedImage}
            className={`flex items-center gap-2 ${
              isExecuting || isCheckingContainers
                ? 'bg-gray-500 hover:bg-gray-500 cursor-not-allowed opacity-70'
                : 'bg-green-600 hover:bg-green-700'
            } disabled:bg-gray-400 disabled:cursor-not-allowed`}
            title={
              isCheckingContainers
                ? t('blueprintflow.checkingContainers', '컨테이너 확인 중...')
                : isExecuting
                  ? t('blueprintflow.executingTooltip', '실행 중입니다...')
                  : (uploadedImage ? t('blueprintflow.executeTooltip') : 'Upload an image first')
            }
          >
            {isExecuting || isCheckingContainers ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            {isCheckingContainers
              ? t('blueprintflow.checkingContainers', '확인 중...')
              : isExecuting
                ? t('blueprintflow.executing')
                : t('blueprintflow.execute')}
          </Button>

          {isExecuting && (
            <Button
              onClick={onCancelExecution}
              className="flex items-center gap-2 bg-red-600 hover:bg-red-700"
              title={t('blueprintflow.cancel', 'Cancel execution')}
            >
              <StopCircle className="w-4 h-4" />
              {t('blueprintflow.cancel', 'Cancel')}
            </Button>
          )}

          <Button
            onClick={onClearWorkflow}
            variant="outline"
            className="flex items-center gap-2"
            title={t('blueprintflow.clearTooltip')}
          >
            <Trash2 className="w-4 h-4" />
            {t('blueprintflow.clear')}
          </Button>

          <Button
            onClick={onToggleDebugPanel}
            variant={isDebugPanelOpen ? 'default' : 'outline'}
            className="flex items-center gap-2"
            title="Toggle Debug Panel"
          >
            <Bug className="w-4 h-4" />
            Debug
          </Button>
        </div>
      </div>

      {/* Execution Status Panel */}
      <ExecutionStatusPanel
        isExecuting={isExecuting}
        executionResult={executionResult}
        executionError={executionError}
        nodeStatuses={nodeStatuses}
        executionId={executionId}
        nodes={nodes}
        uploadedImage={uploadedImage}
        onRerun={onExecute}
        onDownloadJSON={onDownloadJSON}
      />
    </div>
  );
}
