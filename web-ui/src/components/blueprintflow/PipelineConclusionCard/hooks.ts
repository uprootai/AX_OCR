import { useMemo } from 'react';
import type { ExecutionResult, ConclusionData } from './types';

type NodesArray = Array<{ id: string; type?: string; data?: { label?: string } }>;

export function useConclusion(
  executionResult: ExecutionResult,
  nodes: NodesArray,
): ConclusionData {
  return useMemo(() => {
    const result: ConclusionData = {
      detectedObjects: [],
      dimensions: [],
      gdtSymbols: [],
      textBlocks: [],
      pidSymbols: [],
      pidConnections: 0,
      pidViolations: [],
      bomItems: [],
      totalDetections: 0,
      totalDimensions: 0,
      totalGDT: 0,
      totalTexts: 0,
    };

    if (!executionResult.node_statuses) return result;

    executionResult.node_statuses.forEach((nodeStatus) => {
      const node = nodes.find((n) => n.id === nodeStatus.node_id);
      const nodeType = node?.type || nodeStatus.node_type || 'unknown';
      const nodeName = node?.data?.label || nodeType;
      const output = nodeStatus.output ?? executionResult.final_output?.[nodeStatus.node_id];

      if (!output) return;

      // Extract YOLO detections
      const detections = output.detections ?? output.predictions ?? output.objects;
      if (Array.isArray(detections)) {
        detections.forEach((det) => {
          const name = det.class_name ?? det.class ?? det.label ?? 'unknown';
          const confidence = det.confidence ?? 0;
          result.detectedObjects.push({ name, confidence, source: nodeName });
          result.totalDetections++;
        });
      }

      // Extract OCR dimensions
      if (Array.isArray(output.dimensions)) {
        output.dimensions.forEach((dim) => {
          const type = dim.type ?? 'linear';
          const value = dim.text ?? dim.value ?? dim.raw_text ?? '';
          if (value) {
            result.dimensions.push({ type, value, source: nodeName });
            result.totalDimensions++;
          }
        });
      }

      // Extract GD&T
      if (Array.isArray(output.gdt)) {
        output.gdt.forEach((g) => {
          result.gdtSymbols.push({
            symbol: g.symbol ?? '',
            value: g.value ?? g.tolerance ?? '',
            datum: g.datum ?? '',
          });
          result.totalGDT++;
        });
      }

      // Extract OCR texts
      if (Array.isArray(output.ocr_results)) {
        output.ocr_results.forEach((r) => {
          if (r.text) {
            result.textBlocks.push(r.text);
            result.totalTexts++;
          }
        });
      }
      if (Array.isArray(output.texts)) {
        output.texts.forEach((text) => {
          result.textBlocks.push(text);
          result.totalTexts++;
        });
      }
      if (typeof output.text === 'string' && output.text) {
        result.textBlocks.push(output.text);
        result.totalTexts++;
      }

      // Extract P&ID symbols
      if (Array.isArray(output.symbols)) {
        output.symbols.forEach((sym) => {
          result.pidSymbols.push({
            name: sym.class_name ?? sym.symbol_type ?? 'unknown',
            confidence: sym.confidence ?? 0,
          });
        });
      }

      // Extract P&ID connections
      if (Array.isArray(output.connections)) {
        result.pidConnections += output.connections.length;
      }

      // Extract P&ID violations
      if (Array.isArray(output.violations)) {
        output.violations.forEach((v) => {
          result.pidViolations.push({
            rule: v.rule ?? 'unknown',
            message: v.message ?? '',
          });
        });
      }

      // Extract BOM
      if (Array.isArray(output.bom)) {
        output.bom.forEach((b) => {
          result.bomItems.push({
            item: b.item ?? 'unknown',
            quantity: b.quantity ?? 1,
          });
        });
      }
    });

    return result;
  }, [executionResult, nodes]);
}

export function useGroupedResults(conclusion: ConclusionData) {
  const groupedDetections = useMemo(() => {
    const groups: Record<string, { count: number; avgConfidence: number }> = {};
    conclusion.detectedObjects.forEach((obj) => {
      if (!groups[obj.name]) {
        groups[obj.name] = { count: 0, avgConfidence: 0 };
      }
      groups[obj.name].count++;
      groups[obj.name].avgConfidence += obj.confidence;
    });
    Object.keys(groups).forEach((key) => {
      groups[key].avgConfidence /= groups[key].count;
    });
    return groups;
  }, [conclusion.detectedObjects]);

  const groupedDimensions = useMemo(() => {
    const groups: Record<string, string[]> = {};
    conclusion.dimensions.forEach((dim) => {
      if (!groups[dim.type]) {
        groups[dim.type] = [];
      }
      groups[dim.type].push(dim.value);
    });
    return groups;
  }, [conclusion.dimensions]);

  return { groupedDetections, groupedDimensions };
}
