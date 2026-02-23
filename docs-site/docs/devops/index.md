---
sidebar_position: 1
title: DevOps 및 인프라
description: DevOps 체계 및 인프라 개요
---

# DevOps 및 인프라

## 개요

```mermaid
flowchart LR
    DEV["개발"] --> CI["CI\nGitHub Actions"]
    CI --> BUILD["Docker 빌드"]
    BUILD --> STAGE["스테이징"]
    STAGE --> PROD["프로덕션"]
```

## 인프라 요약

| 구성 요소 | 기술 | 상세 |
|-----------|------|------|
| **컨테이너 런타임** | Docker Compose | 21개 이상 컨테이너 |
| **CI (지속적 통합)** | GitHub Actions | ESLint + Build + Vitest + Ruff + Pytest |
| **CD (지속적 배포)** | GitHub Actions | 빌드 → 스테이징 → 프로덕션 (수동 승인) |
| **GPU 관리** | NVIDIA Container Toolkit | 동적 할당 |
| **데이터베이스** | Neo4j | 지식 그래프 (포트 7687) |
| **리버스 프록시** | Nginx | 프로덕션 전용 |

## 테스트 커버리지

| 테스트 스위트 | 수량 | 프레임워크 |
|--------------|------|-----------|
| 프론트엔드 | 185 | Vitest |
| 백엔드 | 364 | Pytest |
| **합계** | **549** | - |

## 하위 페이지

| 페이지 | 설명 |
|--------|------|
| [Docker Compose](./docker-compose) | 컨테이너 오케스트레이션 |
| [CI 파이프라인](./ci-pipeline) | 지속적 통합 |
| [CD 파이프라인](./cd-pipeline) | 지속적 배포 |
| [GPU 설정](./gpu-config) | GPU 설정 및 할당 |
