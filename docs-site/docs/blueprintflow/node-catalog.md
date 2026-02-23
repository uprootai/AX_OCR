---
sidebar_position: 1
title: 노드 카탈로그
description: 카테고리별로 정리된 29개 이상의 BlueprintFlow 노드 타입 전체 레퍼런스
---

# 노드 카탈로그

BlueprintFlow는 9개 카테고리에 걸쳐 29개 이상의 노드 타입을 제공합니다. 각 노드는 마이크로서비스 API 엔드포인트를 래핑하며, 속성 패널을 통해 설정 가능한 파라미터를 노출합니다.

## 입력 노드 (Input Nodes)

워크플로우에 데이터를 입력하는 진입점입니다.

| 노드 | 설명 | 주요 파라미터 |
|------|------|--------------|
| **ImageInput** | 도면 이미지 업로드 또는 참조 | `source`, `format` |
| **TextInput** | 텍스트 입력 (부품 번호, 쿼리 등) | `text`, `mode` |

## 검출 노드 (Detection Nodes)

이미지에서 객체 및 심볼을 검출합니다.

| 노드 | 포트 | 설명 | 주요 파라미터 |
|------|------|------|--------------|
| **YOLO** | 5005 | YOLOv11 심볼 검출 (73개 클래스) | `model_type`, `confidence`, `iou`, `imgsz`, `use_sahi`, `slice_height`, `slice_width`, `overlap_ratio`, `visualize`, `task` |
| **Table Detector** | 5022 | 테이블 구조 검출 및 추출 | `mode`, `ocr_engine`, `borderless`, `confidence_threshold`, `min_confidence`, `output_format` |

## OCR 노드

텍스트 및 치수 추출 엔진입니다.

| 노드 | 포트 | 설명 | 주요 파라미터 |
|------|------|------|--------------|
| **eDOCr2** | 5002 | 한국어 기계 도면 OCR | `language`, `extract_dimensions`, `extract_gdt`, `extract_text`, `extract_tables`, `cluster_threshold`, `visualize`, `enable_crop_upscale`, `crop_preset`, `upscale_scale`, `upscale_denoise` |
| **PaddleOCR** | 5006 | 다국어 OCR (80개 이상 언어) | `language`, `det_model`, `rec_model` |
| **Tesseract** | 5008 | 범용 문서 OCR | `language`, `psm`, `oem` |
| **TrOCR** | 5009 | 필기체 텍스트 인식 | `model_size` |
| **OCR Ensemble** | 5011 | 4엔진 가중 투표 방식 | `engines`, `weights` |
| **Surya OCR** | 5013 | 레이아웃 인식 OCR (90개 이상 언어) | `language`, `detect_layout` |
| **DocTR** | 5014 | 2단계 검출 + 인식 파이프라인 | `det_arch`, `reco_arch` |
| **EasyOCR** | 5015 | 간편한 OCR (80개 이상 언어) | `language`, `detail` |

## 세그멘테이션 노드 (Segmentation Nodes)

이미지 세그멘테이션 및 라인 검출을 수행합니다.

| 노드 | 포트 | 설명 | 주요 파라미터 |
|------|------|------|--------------|
| **EDGNet** | 5012 | 윤곽 추출을 위한 엣지 세그멘테이션 | `threshold`, `mode` |
| **Line Detector** | 5016 | P&ID 라인 및 연결 검출 | `min_length`, `merge_distance` |

## 전처리 노드 (Preprocessing Nodes)

분석 전 이미지 향상 처리를 수행합니다.

| 노드 | 포트 | 설명 | 주요 파라미터 |
|------|------|------|--------------|
| **ESRGAN** | 5010 | 4배 이미지 초해상도 업스케일링 | `scale`, `denoise_strength` |

## 분석 노드 (Analysis Nodes)

도메인별 분석 및 리포트를 생성합니다.

| 노드 | 포트 | 설명 | 주요 파라미터 |
|------|------|------|--------------|
| **SkinModel** | 5003 | GD&T 공차 분석 | `material_type`, `manufacturing_process`, `correlation_length`, `task` |
| **PID Analyzer** | 5018 | P&ID 연결 및 흐름 분석 | `analysis_mode` |
| **Design Checker** | 5019 | P&ID 설계 규칙 검증 | `ruleset` |
| **GT Comparison** | -- | 정답 데이터(Ground Truth) / 리비전 비교 | `threshold`, `mode` |
| **PDF Export** | -- | 결과로부터 PDF 리포트 생성 | `template`, `include_images` |
| **PID Features** | -- | P&ID 특징 추출 | `feature_types` |
| **Verification Queue** | -- | 휴먼 인 더 루프(Human-in-the-Loop) 검토 대기열 | `priority`, `auto_approve_threshold` |
| **Dimension Updater** | -- | OCR 결과를 이용한 치수 값 업데이트 | `merge_strategy` |

## BOM 노드

자재 명세서(Bill of Materials) 생성 및 관리를 수행합니다.

| 노드 | 포트 | 설명 | 주요 파라미터 |
|------|------|------|--------------|
| **Blueprint AI BOM** | 5020 | 휴먼 인 더 루프 BOM 생성 | `features` (배열: `verification`, `gt_comparison`, `bom_generation`, `dimension_extraction`) |

## 지식 노드 (Knowledge Nodes)

지식 그래프 및 검색 기능을 제공합니다.

| 노드 | 포트 | 설명 | 주요 파라미터 |
|------|------|------|--------------|
| **Knowledge** | 5007 | 엔지니어링 지식을 위한 Neo4j GraphRAG | `query_type`, `depth` |

## AI 노드

비전-언어 모델(Vision-Language Model) 통합 기능을 제공합니다.

| 노드 | 포트 | 설명 | 주요 파라미터 |
|------|------|------|--------------|
| **VL** | 5004 | Qwen2-VL 비전-언어 모델 | `task`, `prompt` |

## 제어 노드 (Control Nodes)

워크플로우 제어 흐름 및 분기를 관리합니다.

| 노드 | 설명 | 주요 파라미터 |
|------|------|--------------|
| **IF** | 결과 값에 따른 조건부 분기 | `condition`, `field`, `value` |
| **Loop** | 배열 순회 또는 N회 반복 | `mode`, `count`, `field` |
| **Merge** | 여러 브랜치의 결과를 병합 | `strategy` |

## 노드 카테고리 타입

모든 노드에는 코드 내에서 다음 카테고리 중 하나가 할당됩니다:

```typescript
type NodeCategory =
  | 'input'
  | 'detection'
  | 'ocr'
  | 'segmentation'
  | 'preprocessing'
  | 'analysis'
  | 'knowledge'
  | 'ai'
  | 'control';
```

참고: `'api'` 타입은 사용하지 않습니다.

## 참고 사항

- 파라미터 이름은 `gateway-api/api_specs/*.yaml`에 정의된 것과 반드시 일치해야 합니다. API 스펙에 없는 파라미터는 사용하지 마십시오.
- GPU 가속 노드(YOLO, eDOCr2, VL 등)는 대시보드를 통해 GPU 할당을 설정할 수 있습니다.
- `visualize` 파라미터를 사용할 수 있는 경우, JSON 결과와 함께 주석이 표시된 이미지를 반환합니다.
