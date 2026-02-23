---
sidebar_position: 1
title: DevOps & Infrastructure
description: DevOps 체계 및 인프라 개요
---

# DevOps & Infrastructure

## Overview

```mermaid
flowchart LR
    DEV["Development"] --> CI["CI\nGitHub Actions"]
    CI --> BUILD["Docker Build"]
    BUILD --> STAGE["Staging"]
    STAGE --> PROD["Production"]
```

## Infrastructure Summary

| Component | Technology | Details |
|-----------|-----------|---------|
| **Container Runtime** | Docker Compose | 21+ containers |
| **CI** | GitHub Actions | ESLint + Build + Vitest + Ruff + Pytest |
| **CD** | GitHub Actions | Build → Stage → Prod (manual gate) |
| **GPU Management** | NVIDIA Container Toolkit | Dynamic allocation |
| **Database** | Neo4j | Knowledge graph (port 7687) |
| **Reverse Proxy** | Nginx | Production only |

## Test Coverage

| Suite | Count | Framework |
|-------|-------|-----------|
| Frontend | 185 | Vitest |
| Backend | 364 | Pytest |
| **Total** | **549** | - |

## Sub-pages

| Page | Description |
|------|-------------|
| [Docker Compose](./docker-compose) | 컨테이너 오케스트레이션 |
| [CI Pipeline](./ci-pipeline) | 지속적 통합 |
| [CD Pipeline](./cd-pipeline) | 지속적 배포 |
| [GPU Config](./gpu-config) | GPU 설정 및 할당 |
