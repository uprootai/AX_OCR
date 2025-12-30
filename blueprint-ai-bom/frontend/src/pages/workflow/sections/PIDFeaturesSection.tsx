/**
 * P&ID Features Section
 * P&ID 분석 기능 UI 섹션
 * - 밸브 검출 (Valve Detection)
 * - 장비 검출 (Equipment Detection)
 * - 설계 체크리스트 검증 (Design Checklist)
 * - 편차 분석 (Deviation Analysis)
 */

import { useState } from 'react';
import { Loader2, Download, CheckCircle, XCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react';
import { InfoTooltip } from '../../../components/Tooltip';
import type { SectionVisibility } from '../types/workflow';

// P&ID Types
interface ValveItem {
  id: string;
  valve_id: string;
  valve_type: string;
  category: string;
  region_name: string;
  confidence: number;
  verification_status: 'pending' | 'approved' | 'rejected' | 'modified';
  notes?: string;
}

interface EquipmentItem {
  id: string;
  tag: string;
  equipment_type: string;
  description: string;
  vendor_supply: boolean;
  confidence: number;
  verification_status: 'pending' | 'approved' | 'rejected' | 'modified';
}

interface ChecklistItem {
  id: string;
  item_no: number;
  category: string;
  description: string;
  auto_status: 'pass' | 'fail' | 'na' | 'pending' | 'manual_required';
  final_status: 'pass' | 'fail' | 'na' | 'pending' | 'manual_required';
  evidence: string;
  confidence: number;
  verification_status: 'pending' | 'approved' | 'rejected' | 'modified';
}

interface DeviationItem {
  id: string;
  category: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  source: string;
  title: string;
  description: string;
  location?: string;
  reference_standard?: string;
  reference_value?: string;
  actual_value?: string;
  action_required?: string;
  action_taken?: string;
  confidence: number;
  verification_status: 'pending' | 'approved' | 'rejected' | 'modified';
  notes?: string;
}

interface PIDFeaturesSectionProps {
  sessionId: string | null;
  visibility: SectionVisibility;

  // Valve Detection
  valves: ValveItem[];
  isDetectingValves: boolean;
  onDetectValves: () => void;
  onVerifyValve: (id: string, status: 'approved' | 'rejected') => void;

  // Equipment Detection
  equipment: EquipmentItem[];
  isDetectingEquipment: boolean;
  onDetectEquipment: () => void;
  onVerifyEquipment: (id: string, status: 'approved' | 'rejected') => void;

  // Design Checklist
  checklistItems: ChecklistItem[];
  isCheckingDesign: boolean;
  onCheckDesign: () => void;
  onVerifyChecklist: (id: string, status: 'approved' | 'rejected') => void;

  // Deviation Analysis
  deviations?: DeviationItem[];
  isAnalyzingDeviations?: boolean;
  onAnalyzeDeviations?: () => void;
  onVerifyDeviation?: (id: string, status: 'approved' | 'rejected') => void;

  // Export
  onExport: (type: 'valve' | 'equipment' | 'checklist' | 'deviation' | 'all') => void;
}

export function PIDFeaturesSection({
  sessionId,
  visibility,
  valves,
  isDetectingValves,
  onDetectValves,
  onVerifyValve,
  equipment,
  isDetectingEquipment,
  onDetectEquipment,
  onVerifyEquipment,
  checklistItems,
  isCheckingDesign,
  onCheckDesign,
  onVerifyChecklist,
  deviations = [],
  isAnalyzingDeviations = false,
  onAnalyzeDeviations,
  onVerifyDeviation,
  onExport,
}: PIDFeaturesSectionProps) {
  const [activeTab, setActiveTab] = useState<'valve' | 'equipment' | 'checklist' | 'deviation'>('valve');

  // 섹션이 하나도 활성화되지 않으면 렌더링하지 않음
  if (!visibility.valveSignalList && !visibility.equipmentList && !visibility.bwmsChecklist && !visibility.deviationList) {
    return null;
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
      case 'pass':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'rejected':
      case 'fail':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600';
    if (confidence >= 0.7) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <XCircle className="w-4 h-4 text-red-600" />;
      case 'high':
        return <AlertTriangle className="w-4 h-4 text-orange-500" />;
      case 'medium':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      case 'low':
        return <AlertCircle className="w-4 h-4 text-blue-400" />;
      default:
        return <Info className="w-4 h-4 text-gray-400" />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    const classes: Record<string, string> = {
      critical: 'bg-red-100 text-red-800',
      high: 'bg-orange-100 text-orange-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-blue-100 text-blue-800',
      info: 'bg-gray-100 text-gray-800',
    };
    return classes[severity] || classes.info;
  };

  return (
    <section className="space-y-4 p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-800">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-orange-800 dark:text-orange-200 flex items-center gap-2">
          <span>P&ID 분석</span>
          <InfoTooltip content="P&ID 도면 분석 기능입니다. 밸브, 장비 검출 및 설계 체크리스트 검증을 수행합니다." />
        </h2>
        <button
          onClick={() => onExport('all')}
          className="flex items-center gap-1 px-3 py-1 text-sm bg-orange-600 text-white rounded hover:bg-orange-700"
        >
          <Download className="w-4 h-4" />
          전체 Excel 내보내기
        </button>
      </div>

      {/* 탭 네비게이션 */}
      <div className="flex gap-2 border-b border-orange-200 dark:border-orange-700">
        {visibility.valveSignalList && (
          <button
            onClick={() => setActiveTab('valve')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'valve'
                ? 'border-orange-500 text-orange-700 dark:text-orange-300'
                : 'border-transparent text-gray-500 hover:text-orange-600'
            }`}
          >
            밸브 ({valves.length})
          </button>
        )}
        {visibility.equipmentList && (
          <button
            onClick={() => setActiveTab('equipment')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'equipment'
                ? 'border-orange-500 text-orange-700 dark:text-orange-300'
                : 'border-transparent text-gray-500 hover:text-orange-600'
            }`}
          >
            장비 ({equipment.length})
          </button>
        )}
        {visibility.bwmsChecklist && (
          <button
            onClick={() => setActiveTab('checklist')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'checklist'
                ? 'border-orange-500 text-orange-700 dark:text-orange-300'
                : 'border-transparent text-gray-500 hover:text-orange-600'
            }`}
          >
            체크리스트 ({checklistItems.length})
          </button>
        )}
        {visibility.deviationList && (
          <button
            onClick={() => setActiveTab('deviation')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'deviation'
                ? 'border-orange-500 text-orange-700 dark:text-orange-300'
                : 'border-transparent text-gray-500 hover:text-orange-600'
            }`}
          >
            편차 ({deviations.length})
          </button>
        )}
      </div>

      {/* Valve Tab */}
      {activeTab === 'valve' && visibility.valveSignalList && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              P&ID 도면에서 밸브 ID를 자동 검출합니다.
            </p>
            <button
              onClick={onDetectValves}
              disabled={!sessionId || isDetectingValves}
              className="flex items-center gap-1 px-3 py-1 text-sm bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50"
            >
              {isDetectingValves && <Loader2 className="w-4 h-4 animate-spin" />}
              {isDetectingValves ? '검출 중...' : '밸브 검출'}
            </button>
          </div>

          {valves.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-orange-100 dark:bg-orange-800/50">
                  <tr>
                    <th className="px-3 py-2 text-left">Valve ID</th>
                    <th className="px-3 py-2 text-left">Type</th>
                    <th className="px-3 py-2 text-left">Category</th>
                    <th className="px-3 py-2 text-left">Confidence</th>
                    <th className="px-3 py-2 text-left">Status</th>
                    <th className="px-3 py-2 text-left">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {valves.map((valve) => (
                    <tr key={valve.id} className="border-b border-orange-100 dark:border-orange-800">
                      <td className="px-3 py-2 font-mono">{valve.valve_id}</td>
                      <td className="px-3 py-2">{valve.valve_type}</td>
                      <td className="px-3 py-2">{valve.category}</td>
                      <td className={`px-3 py-2 ${getConfidenceColor(valve.confidence)}`}>
                        {(valve.confidence * 100).toFixed(1)}%
                      </td>
                      <td className="px-3 py-2">{getStatusIcon(valve.verification_status)}</td>
                      <td className="px-3 py-2">
                        <div className="flex gap-1">
                          <button
                            onClick={() => onVerifyValve(valve.id, 'approved')}
                            className="p-1 text-green-600 hover:bg-green-100 rounded"
                            title="승인"
                          >
                            <CheckCircle className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => onVerifyValve(valve.id, 'rejected')}
                            className="p-1 text-red-600 hover:bg-red-100 rounded"
                            title="거부"
                          >
                            <XCircle className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Equipment Tab */}
      {activeTab === 'equipment' && visibility.equipmentList && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              P&ID 도면에서 장비 태그를 검출합니다.
            </p>
            <button
              onClick={onDetectEquipment}
              disabled={!sessionId || isDetectingEquipment}
              className="flex items-center gap-1 px-3 py-1 text-sm bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50"
            >
              {isDetectingEquipment && <Loader2 className="w-4 h-4 animate-spin" />}
              {isDetectingEquipment ? '검출 중...' : '장비 검출'}
            </button>
          </div>

          {equipment.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-orange-100 dark:bg-orange-800/50">
                  <tr>
                    <th className="px-3 py-2 text-left">Tag</th>
                    <th className="px-3 py-2 text-left">Type</th>
                    <th className="px-3 py-2 text-left">Description</th>
                    <th className="px-3 py-2 text-left">Vendor Supply</th>
                    <th className="px-3 py-2 text-left">Confidence</th>
                    <th className="px-3 py-2 text-left">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {equipment.map((eq) => (
                    <tr key={eq.id} className="border-b border-orange-100 dark:border-orange-800">
                      <td className="px-3 py-2 font-mono">{eq.tag}</td>
                      <td className="px-3 py-2">{eq.equipment_type}</td>
                      <td className="px-3 py-2">{eq.description}</td>
                      <td className="px-3 py-2">{eq.vendor_supply ? '✓' : '-'}</td>
                      <td className={`px-3 py-2 ${getConfidenceColor(eq.confidence)}`}>
                        {(eq.confidence * 100).toFixed(1)}%
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex gap-1">
                          <button
                            onClick={() => onVerifyEquipment(eq.id, 'approved')}
                            className="p-1 text-green-600 hover:bg-green-100 rounded"
                          >
                            <CheckCircle className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => onVerifyEquipment(eq.id, 'rejected')}
                            className="p-1 text-red-600 hover:bg-red-100 rounded"
                          >
                            <XCircle className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Checklist Tab */}
      {activeTab === 'checklist' && visibility.bwmsChecklist && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              설계 체크리스트 항목을 자동 검증합니다.
            </p>
            <button
              onClick={onCheckDesign}
              disabled={!sessionId || isCheckingDesign}
              className="flex items-center gap-1 px-3 py-1 text-sm bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50"
            >
              {isCheckingDesign && <Loader2 className="w-4 h-4 animate-spin" />}
              {isCheckingDesign ? '검증 중...' : '체크리스트 검증'}
            </button>
          </div>

          {checklistItems.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-orange-100 dark:bg-orange-800/50">
                  <tr>
                    <th className="px-3 py-2 text-left">No.</th>
                    <th className="px-3 py-2 text-left">Category</th>
                    <th className="px-3 py-2 text-left">Description</th>
                    <th className="px-3 py-2 text-left">Auto</th>
                    <th className="px-3 py-2 text-left">Final</th>
                    <th className="px-3 py-2 text-left">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {checklistItems.map((item) => (
                    <tr key={item.id} className="border-b border-orange-100 dark:border-orange-800">
                      <td className="px-3 py-2">{item.item_no}</td>
                      <td className="px-3 py-2">{item.category}</td>
                      <td className="px-3 py-2 max-w-xs truncate" title={item.description}>
                        {item.description}
                      </td>
                      <td className="px-3 py-2">{getStatusIcon(item.auto_status)}</td>
                      <td className="px-3 py-2">{getStatusIcon(item.final_status)}</td>
                      <td className="px-3 py-2">
                        <div className="flex gap-1">
                          <button
                            onClick={() => onVerifyChecklist(item.id, 'approved')}
                            className="p-1 text-green-600 hover:bg-green-100 rounded"
                          >
                            <CheckCircle className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => onVerifyChecklist(item.id, 'rejected')}
                            className="p-1 text-red-600 hover:bg-red-100 rounded"
                          >
                            <XCircle className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Deviation Tab */}
      {activeTab === 'deviation' && visibility.deviationList && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              P&ID 도면의 편차를 분석합니다. (표준 위반, 설계 불일치, 리비전 변경사항 등)
            </p>
            <button
              onClick={onAnalyzeDeviations}
              disabled={!sessionId || isAnalyzingDeviations}
              className="flex items-center gap-1 px-3 py-1 text-sm bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50"
            >
              {isAnalyzingDeviations && <Loader2 className="w-4 h-4 animate-spin" />}
              {isAnalyzingDeviations ? '분석 중...' : '편차 분석'}
            </button>
          </div>

          {deviations.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-orange-100 dark:bg-orange-800/50">
                  <tr>
                    <th className="px-3 py-2 text-left">심각도</th>
                    <th className="px-3 py-2 text-left">제목</th>
                    <th className="px-3 py-2 text-left">카테고리</th>
                    <th className="px-3 py-2 text-left">소스</th>
                    <th className="px-3 py-2 text-left">위치</th>
                    <th className="px-3 py-2 text-left">Status</th>
                    <th className="px-3 py-2 text-left">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {deviations.map((deviation) => (
                    <tr key={deviation.id} className="border-b border-orange-100 dark:border-orange-800">
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-1.5">
                          {getSeverityIcon(deviation.severity)}
                          <span className={`text-xs px-1.5 py-0.5 rounded ${getSeverityBadge(deviation.severity)}`}>
                            {deviation.severity}
                          </span>
                        </div>
                      </td>
                      <td className="px-3 py-2 max-w-xs">
                        <div className="font-medium truncate" title={deviation.title}>
                          {deviation.title}
                        </div>
                        {deviation.description && (
                          <div className="text-xs text-gray-500 truncate" title={deviation.description}>
                            {deviation.description}
                          </div>
                        )}
                      </td>
                      <td className="px-3 py-2 text-xs">{deviation.category}</td>
                      <td className="px-3 py-2 text-xs">{deviation.source}</td>
                      <td className="px-3 py-2 text-xs">{deviation.location || '-'}</td>
                      <td className="px-3 py-2">{getStatusIcon(deviation.verification_status)}</td>
                      <td className="px-3 py-2">
                        {onVerifyDeviation && (
                          <div className="flex gap-1">
                            <button
                              onClick={() => onVerifyDeviation(deviation.id, 'approved')}
                              className="p-1 text-green-600 hover:bg-green-100 rounded"
                              title="승인"
                            >
                              <CheckCircle className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => onVerifyDeviation(deviation.id, 'rejected')}
                              className="p-1 text-red-600 hover:bg-red-100 rounded"
                              title="거부"
                            >
                              <XCircle className="w-4 h-4" />
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {deviations.length === 0 && !isAnalyzingDeviations && (
            <div className="text-center py-8 text-gray-500">
              <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">편차 분석 버튼을 클릭하여 분석을 시작하세요.</p>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

// 하위 호환성 별칭
export const BWMSSection = PIDFeaturesSection;
