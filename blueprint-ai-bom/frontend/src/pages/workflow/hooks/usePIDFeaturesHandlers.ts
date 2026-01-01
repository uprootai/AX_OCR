/**
 * P&ID 분석 기능 Hook
 * P&ID 분석 기능 상태 및 핸들러
 * - 밸브 검출
 * - 장비 검출
 * - 설계 체크리스트 검증
 * - 편차 분석
 * - Excel 내보내기
 */

import { useState, useCallback } from 'react';
import { pidFeaturesApi } from '../../../lib/api';
import type {
  ValveItem,
  EquipmentItem,
  ChecklistItem,
  DeviationItem,
  DeviationAnalysisRequest,
} from '../../../lib/api';
import logger from '../../../lib/logger';

// UI용 타입 정의 (api.ts 타입과 호환)
export interface UIValveItem {
  id: string;
  valve_id: string;
  valve_type: string;
  category: string;
  region_name: string;
  confidence: number;
  verification_status: 'pending' | 'approved' | 'rejected' | 'modified';
  notes?: string;
}

export interface UIEquipmentItem {
  id: string;
  tag: string;
  equipment_type: string;
  description: string;
  vendor_supply: boolean;
  confidence: number;
  verification_status: 'pending' | 'approved' | 'rejected' | 'modified';
}

export interface UIChecklistItem {
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

export interface UIDeviationItem {
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

interface UsePIDFeaturesHandlersResult {
  // Valve Detection
  valves: UIValveItem[];
  isDetectingValves: boolean;
  handleDetectValves: (sessionId: string, profile?: string) => Promise<void>;
  handleVerifyValve: (sessionId: string, id: string, status: 'approved' | 'rejected') => Promise<void>;

  // Equipment Detection
  equipment: UIEquipmentItem[];
  isDetectingEquipment: boolean;
  handleDetectEquipment: (sessionId: string, profile?: string) => Promise<void>;
  handleVerifyEquipment: (sessionId: string, id: string, status: 'approved' | 'rejected') => Promise<void>;

  // Design Checklist
  checklistItems: UIChecklistItem[];
  isCheckingDesign: boolean;
  handleCheckDesign: (sessionId: string, ruleProfile?: string) => Promise<void>;
  handleVerifyChecklist: (sessionId: string, id: string, status: 'approved' | 'rejected') => Promise<void>;

  // Deviation Analysis
  deviations: UIDeviationItem[];
  isAnalyzingDeviations: boolean;
  handleAnalyzeDeviations: (sessionId: string, request?: DeviationAnalysisRequest) => Promise<void>;
  handleVerifyDeviation: (sessionId: string, id: string, status: 'approved' | 'rejected') => Promise<void>;

  // Export
  handleExport: (sessionId: string, exportType: 'valve' | 'equipment' | 'checklist' | 'deviation' | 'all') => Promise<void>;
  handleExportPDF: (sessionId: string, exportType: 'valve' | 'equipment' | 'checklist' | 'deviation' | 'all') => Promise<void>;
}

export function usePIDFeaturesHandlers(): UsePIDFeaturesHandlersResult {
  // Valve state
  const [valves, setValves] = useState<UIValveItem[]>([]);
  const [isDetectingValves, setIsDetectingValves] = useState(false);

  // Equipment state
  const [equipment, setEquipment] = useState<UIEquipmentItem[]>([]);
  const [isDetectingEquipment, setIsDetectingEquipment] = useState(false);

  // Checklist state
  const [checklistItems, setChecklistItems] = useState<UIChecklistItem[]>([]);
  const [isCheckingDesign, setIsCheckingDesign] = useState(false);

  // Deviation state
  const [deviations, setDeviations] = useState<UIDeviationItem[]>([]);
  const [isAnalyzingDeviations, setIsAnalyzingDeviations] = useState(false);

  // Convert API types to UI types
  const toUIValve = (item: ValveItem): UIValveItem => ({
    id: item.id,
    valve_id: item.valve_id,
    valve_type: item.valve_type,
    category: item.category,
    region_name: item.region_name,
    confidence: item.confidence,
    verification_status: item.verification_status,
    notes: item.notes || undefined,
  });

  const toUIEquipment = (item: EquipmentItem): UIEquipmentItem => ({
    id: item.id,
    tag: item.tag,
    equipment_type: item.equipment_type,
    description: item.description,
    vendor_supply: item.vendor_supply,
    confidence: item.confidence,
    verification_status: item.verification_status,
  });

  const toUIChecklist = (item: ChecklistItem): UIChecklistItem => ({
    id: item.id,
    item_no: item.item_no,
    category: item.category,
    description: item.description,
    auto_status: item.auto_status,
    final_status: item.final_status,
    evidence: item.evidence,
    confidence: item.confidence,
    verification_status: item.verification_status,
  });

  const toUIDeviation = (item: DeviationItem): UIDeviationItem => ({
    id: item.id,
    category: item.category,
    severity: item.severity,
    source: item.source,
    title: item.title,
    description: item.description,
    location: item.location,
    reference_standard: item.reference_standard,
    reference_value: item.reference_value,
    actual_value: item.actual_value,
    action_required: item.action_required,
    action_taken: item.action_taken,
    confidence: item.confidence,
    verification_status: item.verification_status,
    notes: item.notes,
  });

  // Valve handlers
  const handleDetectValves = useCallback(async (sessionId: string, profile = 'default') => {
    if (!sessionId) return;
    setIsDetectingValves(true);
    try {
      const result = await pidFeaturesApi.detectValves(sessionId, 'valve_detection_default', profile);
      setValves(result.valves.map(toUIValve));
      logger.log(`🎛️ 밸브 검출 완료: ${result.total_count}개`);
    } catch (err) {
      logger.error('Valve detection failed:', err);
    } finally {
      setIsDetectingValves(false);
    }
  }, []);

  const handleVerifyValve = useCallback(async (
    sessionId: string,
    id: string,
    status: 'approved' | 'rejected'
  ) => {
    if (!sessionId) return;
    try {
      await pidFeaturesApi.verify(sessionId, id, 'valve', status === 'approved' ? 'approve' : 'reject');
      setValves(prev =>
        prev.map(v => v.id === id ? { ...v, verification_status: status } : v)
      );
      logger.log(`✓ Valve ${id} ${status}`);
    } catch (err) {
      logger.error('Valve verification failed:', err);
    }
  }, []);

  // Equipment handlers
  const handleDetectEquipment = useCallback(async (sessionId: string, profile = 'default') => {
    if (!sessionId) return;
    setIsDetectingEquipment(true);
    try {
      const result = await pidFeaturesApi.detectEquipment(sessionId, profile);
      setEquipment(result.equipment.map(toUIEquipment));
      logger.log(`⚙️ 장비 검출 완료: ${result.total_count}개`);
    } catch (err) {
      logger.error('Equipment detection failed:', err);
    } finally {
      setIsDetectingEquipment(false);
    }
  }, []);

  const handleVerifyEquipment = useCallback(async (
    sessionId: string,
    id: string,
    status: 'approved' | 'rejected'
  ) => {
    if (!sessionId) return;
    try {
      await pidFeaturesApi.verify(sessionId, id, 'equipment', status === 'approved' ? 'approve' : 'reject');
      setEquipment(prev =>
        prev.map(e => e.id === id ? { ...e, verification_status: status } : e)
      );
      logger.log(`✓ Equipment ${id} ${status}`);
    } catch (err) {
      logger.error('Equipment verification failed:', err);
    }
  }, []);

  // Design Checklist handlers
  const handleCheckDesign = useCallback(async (sessionId: string, ruleProfile = 'default') => {
    if (!sessionId) return;
    setIsCheckingDesign(true);
    try {
      const result = await pidFeaturesApi.checkDesignChecklist(sessionId, ruleProfile);
      setChecklistItems(result.items.map(toUIChecklist));
      logger.log(`✅ 설계 체크리스트 검증 완료: ${result.total_count}개 항목, 준수율 ${result.compliance_rate}%`);
    } catch (err) {
      logger.error('Design checklist check failed:', err);
    } finally {
      setIsCheckingDesign(false);
    }
  }, []);

  const handleVerifyChecklist = useCallback(async (
    sessionId: string,
    id: string,
    status: 'approved' | 'rejected'
  ) => {
    if (!sessionId) return;
    try {
      await pidFeaturesApi.verify(sessionId, id, 'checklist_item', status === 'approved' ? 'approve' : 'reject');
      setChecklistItems(prev =>
        prev.map(c => c.id === id ? { ...c, verification_status: status } : c)
      );
      logger.log(`✓ Checklist ${id} ${status}`);
    } catch (err) {
      logger.error('Checklist verification failed:', err);
    }
  }, []);

  // Deviation Analysis handlers
  const handleAnalyzeDeviations = useCallback(async (
    sessionId: string,
    request?: DeviationAnalysisRequest
  ) => {
    if (!sessionId) return;
    setIsAnalyzingDeviations(true);
    try {
      const result = await pidFeaturesApi.analyzeDeviations(sessionId, request);
      setDeviations(result.deviations.map(toUIDeviation));
      logger.log(`📋 편차 분석 완료: ${result.total_count}개 항목`);
    } catch (err) {
      logger.error('Deviation analysis failed:', err);
    } finally {
      setIsAnalyzingDeviations(false);
    }
  }, []);

  const handleVerifyDeviation = useCallback(async (
    sessionId: string,
    id: string,
    status: 'approved' | 'rejected'
  ) => {
    if (!sessionId) return;
    try {
      await pidFeaturesApi.verifyDeviation(sessionId, id, status === 'approved' ? 'approve' : 'reject');
      setDeviations(prev =>
        prev.map(d => d.id === id ? { ...d, verification_status: status } : d)
      );
      logger.log(`✓ Deviation ${id} ${status}`);
    } catch (err) {
      logger.error('Deviation verification failed:', err);
    }
  }, []);

  // Export handler (Excel)
  const handleExport = useCallback(async (
    sessionId: string,
    exportType: 'valve' | 'equipment' | 'checklist' | 'deviation' | 'all'
  ) => {
    if (!sessionId) return;
    try {
      const blob = await pidFeaturesApi.export(sessionId, exportType);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `PID_Analysis_${exportType}_${new Date().toISOString().slice(0, 10)}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      logger.log(`📥 P&ID ${exportType} Excel 다운로드 완료`);
    } catch (err) {
      logger.error('Export failed:', err);
    }
  }, []);

  // Export handler (PDF)
  const handleExportPDF = useCallback(async (
    sessionId: string,
    exportType: 'valve' | 'equipment' | 'checklist' | 'deviation' | 'all'
  ) => {
    if (!sessionId) return;
    try {
      const blob = await pidFeaturesApi.exportPDF(sessionId, exportType);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `PID_Report_${exportType}_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      logger.log(`📥 P&ID ${exportType} PDF 다운로드 완료`);
    } catch (err) {
      logger.error('PDF Export failed:', err);
    }
  }, []);

  return {
    // Valve Detection
    valves,
    isDetectingValves,
    handleDetectValves,
    handleVerifyValve,

    // Equipment Detection
    equipment,
    isDetectingEquipment,
    handleDetectEquipment,
    handleVerifyEquipment,

    // Design Checklist
    checklistItems,
    isCheckingDesign,
    handleCheckDesign,
    handleVerifyChecklist,

    // Deviation Analysis
    deviations,
    isAnalyzingDeviations,
    handleAnalyzeDeviations,
    handleVerifyDeviation,

    // Export
    handleExport,
    handleExportPDF,
  };
}

// 하위 호환성 별칭
export const useBWMSHandlers = usePIDFeaturesHandlers;
