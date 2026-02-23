---
sidebar_position: 1
title: BlueprintFlow
description: Visual workflow builder for composing custom analysis pipelines with 29+ node types
---

# BlueprintFlow

BlueprintFlow is a visual workflow builder that allows engineers to compose custom analysis pipelines by connecting processing nodes on a canvas. Built with React Flow, it provides a drag-and-drop interface for assembling detection, OCR, analysis, and export stages into a directed acyclic graph (DAG).

## Key Features

- **29+ Node Types** across 9 categories
- **DAG Execution Engine** with topological sort and parallel branch execution
- **Pre-built Templates** for common analysis workflows
- **Real-time Execution** with progress tracking per node
- **Custom API Integration** via scaffold tooling

## Node Categories

```mermaid
mindmap
  root((BlueprintFlow))
    Input
      ImageInput
      TextInput
    Detection
      YOLO
      Table Detector
    OCR
      eDOCr2
      PaddleOCR
      Tesseract
      TrOCR
      OCR Ensemble
      Surya OCR
      DocTR
      EasyOCR
    Segmentation
      EDGNet
      Line Detector
    Preprocessing
      ESRGAN
    Analysis
      SkinModel
      PID Analyzer
      Design Checker
      GT Comparison
      PDF Export
    Knowledge
      Knowledge Graph
    AI
      Vision-Language
    Control
      IF
      Loop
      Merge
```

## Architecture

```mermaid
flowchart TB
    UI["BlueprintFlow Canvas\n(React Flow)"]
    Store["Workflow Store\n(Zustand)"]
    Exec["DAG Engine\n(Gateway API)"]
    Reg["Executor Registry"]
    APIs["ML Services\n(21 containers)"]

    UI --> Store
    Store --> Exec
    Exec --> Reg
    Reg --> APIs

    style UI fill:#e3f2fd,stroke:#1565c0
    style Exec fill:#fff3e0,stroke:#e65100
```

## Sub-pages

| Page | Description |
|------|-------------|
| [Node Catalog](./node-catalog.md) | Complete reference of all 29+ node types with parameters |
| [DAG Engine](./dag-engine.md) | Execution engine internals: topological sort, parallelism, executor registry |
| [Templates](./templates.md) | Pre-built workflow templates for common analysis scenarios |
| [Custom API](./custom-api.md) | Guide to adding custom API nodes and executors |

## Quick Start

1. Navigate to **BlueprintFlow Builder** at `http://localhost:5173/blueprintflow/builder`.
2. Drag nodes from the sidebar onto the canvas.
3. Connect outputs to inputs to define the data flow.
4. Configure node parameters in the properties panel.
5. Click **Run** to execute the workflow.

## Frontend Location

| File | Purpose |
|------|---------|
| `web-ui/src/pages/blueprintflow/BlueprintFlowBuilder.tsx` | Main builder page |
| `web-ui/src/config/nodeDefinitions.ts` | Node type definitions (29+ nodes, 70+ parameters) |
| `web-ui/src/config/apiRegistry.ts` | API endpoint registry |
| `web-ui/src/store/workflowStore.ts` | Workflow state management |
