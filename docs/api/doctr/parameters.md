# DocTR API Parameters

2단계 파이프라인 OCR API - 텍스트 검출 + 인식

## Overview

| 항목 | 값 |
|------|-----|
| **Port** | 5014 |
| **Endpoint** | POST /api/v1/process |
| **Category** | OCR |

## Parameters

| 파라미터 | 타입 | 기본값 | 옵션 | 설명 |
|---------|------|--------|------|------|
| `det_model` | select | db_resnet50 | db_resnet50/linknet_resnet18 | 텍스트 검출 모델 |
| `reco_model` | select | crnn_vgg16_bn | crnn_vgg16_bn/master | 텍스트 인식 모델 |
| `visualize` | boolean | false | - | OCR 결과 시각화 이미지 생성 |

## Model Options

### Detection Models
| 모델 | 설명 |
|------|------|
| `db_resnet50` | DB (Differentiable Binarization) + ResNet50 백본 |
| `linknet_resnet18` | LinkNet + ResNet18 백본 (경량) |

### Recognition Models
| 모델 | 설명 |
|------|------|
| `crnn_vgg16_bn` | CRNN + VGG16 (기본) |
| `master` | MASTER 아키텍처 (정확도 우선) |

## Resource Requirements

### GPU Mode
- **VRAM**: ~3GB
- **권장**: RTX 3060 이상

### CPU Mode
- **RAM**: ~4GB
