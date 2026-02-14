/**
 * useWorkflowEffects - Workflow 페이지 사이드 이펙트 훅
 * 모든 useEffect와 데이터 로딩 로직을 중앙화하여 관리
 */

import { useEffect, useCallback } from 'react';
import axios from 'axios';
import { detectionApi, systemApi, groundTruthApi, blueprintFlowApi } from '../../../lib/api';
import logger from '../../../lib/logger';
import { API_BASE_URL } from '../../../lib/constants';
import type { Detection } from '../../../types';
import type { WorkflowState, ClassExample } from './useWorkflowState';

// ==================== Type Definitions ====================

interface UseWorkflowEffectsParams {
  state: WorkflowState;
  currentSession: {
    session_id: string;
    filename: string;
    drawing_type?: string;
    project_id?: string;
  } | null;
  detections: Detection[];
  imageSize: { width: number; height: number } | null;
  loadSessions: (limit?: number, projectId?: string) => void;
  loadSession: (sessionId: string) => void;
  urlSessionId: string | null;
}

// ==================== Hook Definition ====================

export function useWorkflowEffects({
  state,
  currentSession,
  detections,
  imageSize,
  loadSessions,
  loadSession,
  urlSessionId,
}: UseWorkflowEffectsParams) {
  const {
    setConfig,
    darkMode,
    setAvailableClasses,
    setClassExamples,
    setGpuStatus,
    setVerificationFinalized,
    setDimensions,
    setDimensionStats,
    setRelations,
    setRelationStats,
    setFcfList,
    setGdtDatums,
    setGdtSummary,
    gtCompareResult,
    setGtCompareResult,
    isLoadingGT,
    setIsLoadingGT,
  } = state;

  // Load YOLO defaults from BlueprintFlow API
  useEffect(() => {
    const fetchYOLODefaults = async () => {
      const defaults = await blueprintFlowApi.getYOLODefaults();
      setConfig(prev => ({
        ...prev,
        confidence: defaults.confidence,
        iou_threshold: defaults.iou,
      }));
      logger.log('BlueprintFlow YOLO defaults loaded:', defaults);
    };
    fetchYOLODefaults();
  }, [setConfig]);

  // Dark mode effect
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('darkMode', String(darkMode));
  }, [darkMode]);

  // Load initial data
  useEffect(() => {
    const loadClasses = async () => {
      try {
        const { classes } = await detectionApi.getClasses();
        setAvailableClasses(classes);
      } catch (err) {
        logger.error('Failed to load classes:', err);
      }
    };

    const loadClassExamples = async () => {
      try {
        const { data } = await axios.get<{ examples: ClassExample[] }>(
          `${API_BASE_URL}/api/config/class-examples`
        );
        setClassExamples(data.examples || []);
      } catch (err) {
        logger.error('Failed to load class examples:', err);
      }
    };

    const loadSystemStatus = async () => {
      try {
        const gpu = await systemApi.getGPUStatus();
        setGpuStatus(gpu);
      } catch (err) {
        logger.error('Failed to load system status:', err);
      }
    };

    loadSessions();
    loadClasses();
    loadClassExamples();
    loadSystemStatus();

    const interval = setInterval(loadSystemStatus, 30000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load session from URL parameter
  useEffect(() => {
    if (urlSessionId && (!currentSession || currentSession.session_id !== urlSessionId)) {
      loadSession(urlSessionId);
    }
  }, [urlSessionId, currentSession, loadSession]);

  // Reset verificationFinalized when session changes
  useEffect(() => {
    setVerificationFinalized(false);
  }, [currentSession?.session_id, setVerificationFinalized]);

  // Reload sessions filtered by project when current session's project changes
  useEffect(() => {
    if (currentSession?.session_id && currentSession.project_id) {
      loadSessions(50, currentSession.project_id);
    }
  }, [currentSession?.session_id, currentSession?.project_id, loadSessions]);

  // Auto-load dimensions when session changes
  useEffect(() => {
    const fetchDimensions = async () => {
      if (currentSession?.session_id) {
        try {
          const { data } = await axios.get(`${API_BASE_URL}/analysis/dimensions/${currentSession.session_id}`);
          setDimensions(data.dimensions || []);
          setDimensionStats(data.stats || null);
        } catch (err) {
          logger.error('Failed to auto-load dimensions:', err);
        }
      }
    };
    fetchDimensions();
  }, [currentSession?.session_id, setDimensions, setDimensionStats]);

  // Auto-load relations when session changes
  useEffect(() => {
    const fetchRelations = async () => {
      if (currentSession?.session_id) {
        try {
          const { data } = await axios.get(`${API_BASE_URL}/relations/${currentSession.session_id}`);
          setRelations(data.relations || []);
          const statsRes = await axios.get(`${API_BASE_URL}/relations/${currentSession.session_id}/statistics`);
          setRelationStats(statsRes.data || null);
        } catch {
          setRelations([]);
          setRelationStats(null);
        }
      }
    };
    fetchRelations();
  }, [currentSession?.session_id, setRelations, setRelationStats]);

  // Auto-load GD&T when session changes
  useEffect(() => {
    const fetchGDT = async () => {
      if (currentSession?.session_id) {
        try {
          const { data } = await axios.get(`${API_BASE_URL}/analysis/gdt/${currentSession.session_id}`);
          setFcfList(data.fcf_list || []);
          setGdtDatums(data.datums || []);
          const summaryRes = await axios.get(`${API_BASE_URL}/analysis/gdt/${currentSession.session_id}/summary`);
          setGdtSummary(summaryRes.data || null);
        } catch {
          setFcfList([]);
          setGdtDatums([]);
          setGdtSummary(null);
        }
      }
    };
    fetchGDT();
  }, [currentSession?.session_id, setFcfList, setGdtDatums, setGdtSummary]);

  // Auto-load GT when detections are available
  useEffect(() => {
    const autoLoadGT = async () => {
      if (!currentSession || !imageSize || detections.length === 0) return;
      if (gtCompareResult) return;
      if (isLoadingGT) return;

      setIsLoadingGT(true);
      try {
        const detectionsForCompare = detections.map(d => ({
          class_name: d.class_name,
          bbox: d.bbox,
        }));
        const result = await groundTruthApi.compare(
          currentSession.filename,
          detectionsForCompare,
          imageSize.width,
          imageSize.height,
          0.3,
          { classAgnostic: true }
        );
        if (result.has_ground_truth) {
          setGtCompareResult(result);
        }
      } catch {
        // GT not available
      } finally {
        setIsLoadingGT(false);
      }
    };
    autoLoadGT();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentSession?.session_id, imageSize, detections.length]);

  // Reload GT comparison (callable from outside, e.g. after sidebar GT upload)
  const reloadGTComparison = useCallback(async () => {
    if (!currentSession || !imageSize || detections.length === 0) return;
    setIsLoadingGT(true);
    try {
      const detectionsForCompare = detections.map(d => ({
        class_name: d.class_name,
        bbox: d.bbox,
      }));
      const result = await groundTruthApi.compare(
        currentSession.filename,
        detectionsForCompare,
        imageSize.width,
        imageSize.height,
        0.3,
        { classAgnostic: true }
      );
      if (result.has_ground_truth) {
        setGtCompareResult(result);
      } else {
        setGtCompareResult(null);
      }
    } catch {
      setGtCompareResult(null);
    } finally {
      setIsLoadingGT(false);
    }
  }, [currentSession, imageSize, detections, setGtCompareResult, setIsLoadingGT]);

  // Reload system status
  const reloadSystemStatus = useCallback(async () => {
    try {
      const gpu = await systemApi.getGPUStatus();
      setGpuStatus(gpu);
    } catch (err) {
      logger.error('Failed to reload system status:', err);
    }
  }, [setGpuStatus]);

  return {
    reloadSystemStatus,
    reloadGTComparison,
  };
}
