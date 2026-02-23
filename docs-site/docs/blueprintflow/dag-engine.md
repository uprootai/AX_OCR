---
sidebar_position: 2
title: DAG Engine
description: Topological sort execution engine with parallel branch processing and executor registry
---

# DAG Engine

The DAG (Directed Acyclic Graph) Engine is the execution runtime for BlueprintFlow workflows. It takes a workflow graph, determines execution order via topological sort, runs independent branches in parallel, and routes each node to its registered executor.

## Execution Flow

```mermaid
sequenceDiagram
    participant UI as BlueprintFlow UI
    participant Store as Workflow Store
    participant Engine as DAG Engine
    participant Topo as Topological Sort
    participant Registry as Executor Registry
    participant API as ML Service API

    UI->>Store: Run workflow
    Store->>Engine: Submit graph (nodes + edges)
    Engine->>Topo: Sort nodes
    Topo-->>Engine: Ordered execution plan
    loop For each execution level
        Engine->>Engine: Identify parallel nodes
        par Parallel execution
            Engine->>Registry: Resolve executor (node type)
            Registry-->>Engine: Executor instance
            Engine->>API: Execute (parameters + input data)
            API-->>Engine: Result
        end
        Engine->>Engine: Pass results to downstream nodes
    end
    Engine-->>Store: Workflow complete
    Store-->>UI: Update results
```

## Topological Sort

The engine uses Kahn's algorithm for topological sorting:

1. Compute in-degree for every node in the graph.
2. Enqueue all nodes with in-degree 0 (source nodes).
3. Process nodes level by level, decrementing in-degrees of downstream nodes.
4. Nodes at the same level have no dependencies on each other and can run in parallel.

```mermaid
flowchart TD
    subgraph Level_0["Level 0 (parallel)"]
        A["ImageInput A"]
        B["ImageInput B"]
    end

    subgraph Level_1["Level 1 (parallel)"]
        C["YOLO (from A)"]
        D["YOLO (from B)"]
    end

    subgraph Level_2["Level 2 (parallel)"]
        E["eDOCr2 (from C)"]
        F["eDOCr2 (from D)"]
    end

    subgraph Level_3["Level 3"]
        G["Merge Results"]
    end

    A --> C --> E --> G
    B --> D --> F --> G
```

## Parallel Execution

Nodes within the same topological level are dispatched concurrently:

- Each node execution is an independent async task.
- The engine waits for all tasks in a level to complete before advancing to the next level.
- Failed nodes mark their downstream subgraph as skipped (unless an error handler is connected).

## Executor Registry

The Executor Registry maps node types to their execution handlers. Each executor knows how to:

1. Prepare the request payload from node parameters and upstream outputs.
2. Call the appropriate service endpoint.
3. Parse and normalize the response for downstream consumption.

```mermaid
flowchart LR
    Node["Node Type\n(e.g., yolo)"]
    Registry["Executor\nRegistry"]
    Executor["YOLO\nExecutor"]
    API["YOLO API\n:5005"]

    Node --> Registry --> Executor --> API

    style Registry fill:#fff3e0,stroke:#e65100
```

### Registry Location

| File | Purpose |
|------|---------|
| `gateway-api/blueprintflow/executors/executor_registry.py` | Central registry mapping node types to executors |
| `gateway-api/blueprintflow/executors/*.py` | Individual executor implementations |

### Registration Pattern

Executors are registered at startup:

```python
# executor_registry.py
registry = {
    "yolo": YOLOExecutor(),
    "edocr2": EDOCr2Executor(),
    "vl": VLExecutor(),
    "skinmodel": SkinModelExecutor(),
    # ... 29+ executors
}
```

Each executor implements a common interface:

```python
class BaseExecutor:
    async def execute(self, params: dict, inputs: dict) -> dict:
        """Execute the node with given parameters and upstream inputs."""
        ...
```

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Node timeout | Mark node as failed, skip downstream subgraph |
| API unreachable | Retry once, then fail with connection error |
| Invalid parameters | Fail immediately with validation error |
| Partial success | Report per-node status in workflow result |

## Data Flow

Data flows through the graph via edges. Each edge carries the output of the source node to the input of the target node:

- **Single output**: The entire result object is passed downstream.
- **Selective output**: Nodes can specify which output fields to forward using port mappings.
- **Merge node**: Combines multiple upstream outputs into a single object for downstream nodes.

## Notes

- The DAG Engine validates the graph for cycles before execution. Cyclic graphs are rejected with an error.
- Execution progress is reported in real-time through WebSocket updates to the UI.
- The Gateway API (port 8000) hosts the DAG Engine and manages all service-to-service communication.
