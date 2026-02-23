---
sidebar_position: 2
title: State Management
description: Zustand 상태 관리
---

# State Management

Zustand를 사용한 경량 상태 관리입니다.

## Store Architecture

```mermaid
flowchart LR
    subgraph Stores
        WS["workflowStore\n워크플로우 상태"]
        AS["apiConfigStore\nAPI 설정"]
    end

    subgraph Components
        BF["BlueprintFlow"]
        DASH["Dashboard"]
        SET["Settings"]
    end

    BF --> WS & AS
    DASH --> AS
    SET --> AS

    subgraph API["API Layer"]
        LIB["api.ts\nHTTP Client"]
    end

    WS & AS --> LIB
    LIB --> GW["Gateway :8000"]
```

## Stores

### workflowStore

워크플로우 빌더의 노드/엣지 상태를 관리합니다.

```typescript
interface WorkflowState {
  nodes: Node[];
  edges: Edge[];
  selectedNodeId: string | null;
  isExecuting: boolean;
  executionResults: Record<string, NodeResult>;

  // Actions
  addNode: (node: Node) => void;
  removeNode: (id: string) => void;
  updateNodeData: (id: string, data: any) => void;
  connect: (edge: Edge) => void;
  executeWorkflow: () => Promise<void>;
}
```

### apiConfigStore

API 서비스 설정과 상태를 관리합니다.

```typescript
interface ApiConfigState {
  services: ServiceConfig[];
  healthStatus: Record<string, HealthStatus>;

  // Actions
  updateServiceConfig: (id: string, config: Partial<ServiceConfig>) => void;
  checkHealth: (serviceId: string) => Promise<void>;
  checkAllHealth: () => Promise<void>;
}
```

## Patterns

### Selector Pattern

```typescript
// Fine-grained subscription to avoid unnecessary re-renders
const nodes = useWorkflowStore(state => state.nodes);
const isExecuting = useWorkflowStore(state => state.isExecuting);
```

### Async Actions

```typescript
// API calls integrated into store actions
executeWorkflow: async () => {
  set({ isExecuting: true });
  try {
    const results = await api.post('/workflow/execute', getState().toJSON());
    set({ executionResults: results, isExecuting: false });
  } catch (error) {
    set({ isExecuting: false });
  }
}
```
