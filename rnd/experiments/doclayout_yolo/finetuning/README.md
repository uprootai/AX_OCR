# DocLayout-YOLO Fine-tuning

> **목적**: 도면 전용 레이아웃 분석 모델 학습
> **생성일**: 2025-12-31
> **상태**: 🔬 데이터 수집 중

---

## 디렉토리 구조

```
finetuning/
├── README.md                    # 이 파일
├── configs/
│   ├── data.yaml               # 데이터셋 설정 (8개 클래스)
│   └── train_config.yaml       # 학습 하이퍼파라미터
├── scripts/
│   ├── train.py                # 2단계 학습 스크립트
│   └── prepare_data.py         # 데이터 수집/분할 스크립트
├── data/
│   ├── unlabeled/              # 라벨링 전 이미지 (29개)
│   ├── train/
│   │   ├── images/
│   │   └── labels/
│   ├── val/
│   │   ├── images/
│   │   └── labels/
│   └── sample_label.txt        # YOLO 라벨 형식 예시
├── models/                      # 학습된 모델 저장
└── runs/                        # 학습 로그
```

---

## 현재 상태

### 수집된 이미지: 29개

| 카테고리 | 수량 | 소스 |
|----------|------|------|
| Mechanical (기계 도면) | 7개 | web-ui/public/samples, samples/ |
| P&ID | 19개 | apply-company/techloss/test_output |
| Panel (패널 도면) | 3개 | blueprint-ai-bom/test_drawings |

### 목표: 500+ 이미지

| 소스 | 목표 | 현재 | Gap |
|------|------|------|-----|
| 프로젝트 내부 | 50개 | 29개 | 21개 |
| 공개 데이터셋 | 300개 | 0개 | 300개 |
| 추가 수집 | 150개 | 0개 | 150개 |
| **총계** | **500개** | **29개** | **471개** |

---

## 클래스 정의 (8개)

| ID | 클래스 | 설명 | 위치 |
|----|--------|------|------|
| 0 | `title_block` | 표제란 | 우하단 |
| 1 | `main_view` | 주 도면 뷰 | 중앙 |
| 2 | `detail_view` | 상세도 | 다양 |
| 3 | `section_view` | 단면도 | 다양 |
| 4 | `bom_table` | BOM 테이블 | 우측/상단 |
| 5 | `notes` | 주기/노트 | 좌하단 |
| 6 | `legend` | 범례 | 다양 |
| 7 | `revision_block` | 리비전 블록 | 우상단 |

---

## 사용법

### 1. 데이터 수집

```bash
cd /home/uproot/ax/poc/rnd/experiments/doclayout_yolo/finetuning

# 프로젝트 내 이미지 수집
python3 scripts/prepare_data.py --collect

# 상태 확인
python3 scripts/prepare_data.py --status
```

### 2. 라벨링

**추천 도구**: [Roboflow](https://roboflow.com/) (자동 라벨링 + YOLO 포맷)

```bash
# 라벨링 대상 폴더
data/unlabeled/

# 라벨 형식: YOLO TXT
# class_id x_center y_center width height (0-1 정규화)

# 예시 (sample_label.txt 참조):
0 0.85 0.9 0.25 0.15    # title_block
1 0.4 0.5 0.7 0.8       # main_view
```

### 3. Train/Val 분할

```bash
# 라벨링 완료 후 분할 (80:20)
python3 scripts/prepare_data.py --split --ratio 0.8
```

### 4. 학습

```bash
# Stage 1: Head만 학습 (빠른 클래스 매핑)
python3 scripts/train.py --stage 1

# Stage 2: 전체 Fine-tuning
python3 scripts/train.py --stage 2

# Stage 1 이어서 Stage 2
python3 scripts/train.py --stage 2 --resume runs/doclayout/drawing_finetuning_v1_stage1/weights/best.pt
```

---

## 공개 데이터셋

### 추천 데이터셋

| 데이터셋 | 이미지 수 | 유형 | 링크 |
|----------|----------|------|------|
| **Roboflow Engineering Drawing** | 다양 | 기계 도면 | [링크](https://universe.roboflow.com/vanigaa/engineering-drawing-datasets/dataset/1) |
| **YOLO Layout Analysis** | 119개 | PDF 레이아웃 | [링크](https://universe.roboflow.com/yololayoutanalysis/yolo-layout-analysis) |
| **DocLayNet** | 80K+ | 문서 레이아웃 | [Hugging Face](https://huggingface.co/datasets/ds4sd/DocLayNet) |
| **PubLayNet** | 360K+ | 문서 레이아웃 | [GitHub](https://github.com/ibm-aur-nlp/PubLayNet) |

### 다운로드 방법

```python
# Roboflow (API Key 필요)
from roboflow import Roboflow
rf = Roboflow(api_key="YOUR_API_KEY")
project = rf.workspace("vanigaa").project("engineering-drawing-datasets")
dataset = project.version(1).download("yolov8")

# Hugging Face (DocLayNet)
from datasets import load_dataset
dataset = load_dataset("ds4sd/DocLayNet")
```

---

## 학습 설정

### GPU 요구사항

| 설정 | RTX 3080 8GB |
|------|-------------|
| batch_size | 4 |
| imgsz | 1024 |
| VRAM 사용량 | ~6GB |
| 학습 시간 (100 epochs) | ~4-8시간 |

### 하이퍼파라미터

| 파라미터 | Stage 1 | Stage 2 |
|----------|---------|---------|
| epochs | 30 | 70 |
| lr0 | 0.001 | 0.0001 |
| freeze | 10 (Head만) | 0 (전체) |
| augment | ✅ | ✅ |
| mosaic | 0.3 | 0.3 |

---

## 예상 결과

| 지표 | 현재 (DocStructBench) | 목표 (Fine-tuned) |
|------|----------------------|------------------|
| 신뢰도 (기계 도면) | 0.19~0.36 | **0.70+** |
| 신뢰도 (P&ID) | 0.94 (단일) | **0.80+ (다중)** |
| mAP50 | - | **0.75+** |
| VLM 폴백 필요 | ~40% | **~10%** |

---

## 참조

- [DocLayout-YOLO 논문](https://arxiv.org/abs/2410.12628)
- [Ultralytics YOLO 문서](https://docs.ultralytics.com/)
- [아이디어 문서](../../../idea-thinking/sub/001_doclayout_yolo_finetuning.md)
- [통합 완료 문서](../../../idea-thinking/main/001_doclayout_yolo_integration.md)

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2025-12-31 | Fine-tuning 환경 구축, 29개 이미지 수집 |

---

*관리자*: Claude Code (Opus 4.5)
