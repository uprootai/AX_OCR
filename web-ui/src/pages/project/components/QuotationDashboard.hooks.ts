/**
 * QuotationDashboard - 데이터 훅 (상태 + 비즈니스 로직)
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import {
  projectApi,
  type BOMItem,
  type ProjectDetail,
  type ProjectQuotationResponse,
} from '../../../lib/blueprintBomApi';
import type { BatchStatus } from './QuotationDashboard.types';

export interface QuotationDataResult {
  quotation: ProjectQuotationResponse | null;
  isAggregating: boolean;
  batchStatus: BatchStatus | null;
  itemsWithSession: ReturnType<typeof buildItemsWithSession>;
  stats: {
    total: number;
    completed: number;
    quoted: number;
    subtotal: number;
    vat: number;
    grandTotal: number;
    progress: number;
    totalMaterialCost: number;
    totalMachiningCost: number;
  };
  loadQuotation: (refresh?: boolean) => Promise<void>;
  startBatch: (rootDrawingNumber?: string) => Promise<void>;
  cancelBatch: () => Promise<void>;
}

function buildItemsWithSession(
  quotationItems: (BOMItem & { totalQuantity: number })[],
  sessionMap: Map<string, { session_id: string; status: string }>,
  quotationItemMap: Map<string, {
    subtotal: number;
    material_cost: number;
    machining_cost: number;
    weight_kg: number;
    cost_source: string;
    original_dimensions?: Record<string, number>;
    raw_dimensions?: Record<string, number>;
    allowance_applied?: boolean;
  }>
) {
  return quotationItems.map((item) => {
    const costInfo = item.session_id ? quotationItemMap.get(item.session_id) : undefined;
    return {
      ...item,
      quantity: item.totalQuantity ?? item.quantity,
      session: item.session_id ? sessionMap.get(item.session_id) : undefined,
      subtotal: costInfo?.subtotal ?? 0,
      material_cost: costInfo?.material_cost ?? 0,
      machining_cost: costInfo?.machining_cost ?? 0,
      weight_kg: costInfo?.weight_kg ?? 0,
      cost_source: costInfo?.cost_source ?? 'none',
      original_dimensions: costInfo?.original_dimensions,
      raw_dimensions: costInfo?.raw_dimensions,
      allowance_applied: costInfo?.allowance_applied,
    };
  });
}

export function useQuotationData(
  projectId: string,
  project: ProjectDetail,
  bomItems: BOMItem[]
): QuotationDataResult {
  const [quotation, setQuotation] = useState<ProjectQuotationResponse | null>(null);
  const [isAggregating, setIsAggregating] = useState(false);
  const [batchStatus, setBatchStatus] = useState<BatchStatus | null>(null);

  const loadQuotation = useCallback(async (refresh = false) => {
    setIsAggregating(true);
    try {
      const data = await projectApi.getQuotation(projectId, refresh);
      setQuotation(data);
    } catch (err) {
      console.error('Failed to load quotation:', err);
    } finally {
      setIsAggregating(false);
    }
  }, [projectId]);

  const pollBatchStatus = useCallback(() => {
    const interval = setInterval(async () => {
      try {
        const status = await projectApi.getBatchStatus(projectId);
        setBatchStatus(status);
        if (status.status !== 'running') {
          clearInterval(interval);
          if (status.completed > 0) {
            loadQuotation(true);
          }
        }
      } catch {
        clearInterval(interval);
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [projectId, loadQuotation]);

  const startBatch = useCallback(async (rootDrawingNumber?: string) => {
    try {
      await projectApi.startBatchAnalysis(projectId, rootDrawingNumber);
      pollBatchStatus();
    } catch (err) {
      console.error('배치 분석 시작 실패:', err);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  const cancelBatch = useCallback(async () => {
    try {
      await projectApi.cancelBatchAnalysis(projectId);
    } catch {
      // ignore
    }
  }, [projectId]);

  useEffect(() => {
    loadQuotation(false);
    projectApi.getBatchStatus(projectId).then((status) => {
      setBatchStatus(status);
      if (status.status === 'running') {
        pollBatchStatus();
      }
    }).catch(() => {});
  }, [loadQuotation, projectId, pollBatchStatus]);

  const sessionMap = useMemo(() => {
    const sessions = project.sessions ?? [];
    const map = new Map<string, (typeof sessions)[0]>();
    for (const s of sessions) {
      map.set(s.session_id, s);
    }
    return map;
  }, [project.sessions]);

  const quotationItemMap = useMemo(() => {
    const map = new Map<string, {
      subtotal: number;
      material_cost: number;
      machining_cost: number;
      weight_kg: number;
      cost_source: string;
      original_dimensions?: Record<string, number>;
      raw_dimensions?: Record<string, number>;
      allowance_applied?: boolean;
    }>();
    if (quotation) {
      for (const item of quotation.items) {
        map.set(item.session_id, {
          subtotal: item.subtotal,
          material_cost: item.material_cost,
          machining_cost: item.machining_cost,
          weight_kg: item.weight_kg,
          cost_source: item.cost_source,
          original_dimensions: item.original_dimensions,
          raw_dimensions: item.raw_dimensions,
          allowance_applied: item.allowance_applied,
        });
      }
    }
    return map;
  }, [quotation]);

  const quotationItems = useMemo(() => {
    const all = bomItems.filter((i) => i.needs_quotation);
    const grouped = new Map<string, BOMItem & { totalQuantity: number }>();
    for (const item of all) {
      const key = item.drawing_number || item.item_no.toString();
      const existing = grouped.get(key);
      if (existing) {
        existing.totalQuantity += item.quantity;
      } else {
        grouped.set(key, { ...item, totalQuantity: item.quantity });
      }
    }
    return Array.from(grouped.values());
  }, [bomItems]);

  const itemsWithSession = useMemo(
    () => buildItemsWithSession(quotationItems, sessionMap, quotationItemMap),
    [quotationItems, sessionMap, quotationItemMap]
  );

  const stats = useMemo(() => {
    if (quotation) {
      const totalMaterialCost = quotation.items.reduce((s, i) => s + (i.material_cost || 0), 0);
      const totalMachiningCost = quotation.items.reduce((s, i) => s + (i.machining_cost || 0), 0);
      return {
        total: quotation.summary.total_sessions,
        completed: quotation.summary.completed_sessions,
        quoted: quotation.summary.quoted_sessions,
        subtotal: quotation.summary.subtotal,
        vat: quotation.summary.vat,
        grandTotal: quotation.summary.total,
        progress: quotation.summary.progress_percent,
        totalMaterialCost,
        totalMachiningCost,
      };
    }
    const total = quotationItems.length;
    const completed = itemsWithSession.filter(
      (i) => i.session?.status === 'completed'
    ).length;
    return {
      total,
      completed,
      quoted: 0,
      subtotal: 0,
      vat: 0,
      grandTotal: 0,
      progress: total > 0 ? Math.round((completed / total) * 100) : 0,
      totalMaterialCost: 0,
      totalMachiningCost: 0,
    };
  }, [quotation, quotationItems, itemsWithSession]);

  return {
    quotation,
    isAggregating,
    batchStatus,
    itemsWithSession,
    stats,
    loadQuotation,
    startBatch,
    cancelBatch,
  };
}
