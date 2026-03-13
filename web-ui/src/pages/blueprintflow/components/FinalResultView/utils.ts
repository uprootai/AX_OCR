/**
 * FinalResultView — utility functions
 */

import type { APINodeStatus, ExecutionGroup } from '../../types';

// Group nodes by parallel execution
export function groupNodesByExecution(nodeStatuses: APINodeStatus[]): ExecutionGroup[] {
  const groups: ExecutionGroup[] = [];
  const processed = new Set<string>();

  nodeStatuses.forEach((node) => {
    if (processed.has(node.node_id)) return;

    const parallelNodes = [node];
    processed.add(node.node_id);

    if (node.start_time && node.end_time) {
      const nodeStart = new Date(node.start_time).getTime();
      const nodeEnd = new Date(node.end_time).getTime();

      nodeStatuses.forEach((other) => {
        if (processed.has(other.node_id)) return;
        if (!other.start_time || !other.end_time) return;

        const otherStart = new Date(other.start_time).getTime();
        const otherEnd = new Date(other.end_time).getTime();
        const overlaps = nodeStart < otherEnd && nodeEnd > otherStart;

        if (overlaps) {
          parallelNodes.push(other);
          processed.add(other.node_id);
        }
      });
    }

    groups.push({
      type: parallelNodes.length > 1 ? 'parallel' : 'sequential',
      nodes: parallelNodes,
      startTime: node.start_time,
      endTime: node.end_time,
    });
  });

  return groups;
}
