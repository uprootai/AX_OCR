# SOTA 논문 상세 구현 가이드

> **작성일**: 2025-12-31
> **목적**: 실현 가능한 SOTA 논문들의 구체적 파라미터 및 적용 방법
> **GPU 기준**: RTX 3080 8GB

---

## 1. YOLOv11 상세 파라미터 (현재 적용됨)

### 1.1 아키텍처 컴포넌트

| 컴포넌트 | 설명 | 구성 |
|----------|------|------|
| **C3k2** | CSP Bottleneck 개선 | 2개 작은 컨볼루션 사용 (C2f 대체) |
| **SPPF** | Spatial Pyramid Pooling Fast | 다중 스케일 특징 추출 |
| **C2PSA** | Parallel Spatial Attention | 채널+공간 정보 통합 |

### 1.2 모델 스케일별 구성

```yaml
# [depth, width, max_channels]
yolo11n: [0.50, 0.25, 1024]  # 2.6M params, 6.6 GFLOPs
yolo11s: [0.50, 0.50, 1024]  # 9.4M params, 21.7 GFLOPs
yolo11m: [0.50, 1.00, 512]   # 20.1M params, 68.5 GFLOPs  ← 권장 (균형)
yolo11l: [1.00, 1.00, 512]   # 25.4M params, 87.6 GFLOPs
yolo11x: [1.00, 1.50, 512]   # 57.0M params, 196.0 GFLOPs
```

### 1.3 도면 심볼 검출 최적 하이퍼파라미터

```python
# 학습 설정 (P&ID 심볼 검출용)
training_config = {
    "imgsz": 1280,           # 소형 심볼 검출을 위해 1280 권장 (기본 640)
    "batch": 16,             # 8GB VRAM 기준 (자동: batch=-1)
    "epochs": 200,           # 충분한 학습
    "patience": 50,          # Early stopping
    "optimizer": "SGD",      # SGD 또는 AdamW
    "lr0": 0.01,             # SGD 초기 학습률
    "lrf": 0.01,             # 최종 학습률 비율
    "momentum": 0.937,
    "weight_decay": 0.0005,
    "warmup_epochs": 3.0,
    "warmup_momentum": 0.8,
    "box": 7.5,              # Box loss 가중치
    "cls": 0.5,              # Classification loss 가중치
    "dfl": 1.5,              # Distribution Focal Loss 가중치
}

# 추론 설정
inference_config = {
    "imgsz": 1280,
    "conf": 0.25,            # 신뢰도 임계값 (0.25-0.5)
    "iou": 0.7,              # NMS IoU 임계값
    "max_det": 300,          # 최대 검출 수
    "device": "cuda:0",
    "half": True,            # FP16 추론 (속도↑)
}
```

### 1.4 현재 시스템 적용 확인

```bash
# 현재 YOLO API 설정 확인
cat gateway-api/api_specs/yolo.yaml
```

**권장 조치**: `imgsz`를 640 → 1280으로 변경 검토 (VRAM 여유 시)

---

## 2. YOLOv12 상세 파라미터 (미출시 - 참조용)

### 2.1 핵심 혁신

| 컴포넌트 | 설명 | 효과 |
|----------|------|------|
| **Area Attention (A²)** | 피처맵을 영역별로 분할하여 어텐션 | O(n²) → 효율적 복잡도 |
| **R-ELAN** | Residual ELAN + Adaptive Scaling | 깊은 네트워크 안정성 |
| **FlashAttention** | 메모리 효율 어텐션 | VRAM 사용량↓ |

### 2.2 MLP 비율 조정

```yaml
# 기존 Transformer
mlp_ratio: 4.0

# YOLOv12 최적화
mlp_ratio: 1.2  # 또는 2.0 (어텐션과 FFN 균형)
```

### 2.3 Position Perceiver

```python
# 7x7 Separable Convolution으로 위치 정보 암묵적 인코딩
position_perceiver = nn.Sequential(
    nn.Conv2d(channels, channels, kernel_size=7,
              padding=3, groups=channels),  # Depthwise
    nn.Conv2d(channels, channels, kernel_size=1)  # Pointwise
)
```

### 2.4 예상 성능 (RTX 3080 8GB)

| 모델 | mAP | 추론 속도 | VRAM |
|------|-----|----------|------|
| YOLOv12-N | 40.6% | 1.64ms (T4) | ~2GB |
| YOLOv12-S | 47.8% | 2.23ms (T4) | ~3GB |
| YOLOv12-M | 52.5% | 3.50ms (T4) | ~5GB |

**상태**: Ultralytics 공식 릴리스 대기

---

## 3. PaddleOCR 3.0 (PP-OCRv5) 상세 설정

### 3.1 모델 구성

```python
from paddleocr import PaddleOCR

# PP-OCRv5 Server 모델 (고정밀)
ocr = PaddleOCR(
    # 모델 선택
    text_detection_model_name="PP-OCRv5_server_det",
    text_recognition_model_name="PP-OCRv5_server_rec",

    # 전처리 옵션
    use_doc_orientation_classify=True,   # 문서 방향 분류
    use_doc_unwarping=True,              # 문서 왜곡 보정
    use_textline_orientation=True,       # 텍스트라인 방향

    # 검출 설정
    text_det_limit_type="max",           # "min" 또는 "max"
    text_det_limit_side_len=1280,        # 960, 1280, 1920

    # 인식 설정
    rec_batch_num=6,                     # 배치 크기

    # 기타
    use_gpu=True,
    gpu_mem=4000,                        # GPU 메모리 제한 (MB)
    enable_mkldnn=False,
    lang="korean",                       # 언어 설정
)
```

### 3.2 Mobile vs Server 모델 비교

| 모델 | 정확도 | 속도 | VRAM | 권장 용도 |
|------|--------|------|------|----------|
| PP-OCRv5_mobile | 중간 | 빠름 | ~1GB | 실시간 처리 |
| PP-OCRv5_server | 높음 | 중간 | ~2GB | 고정밀 필요 시 |

### 3.3 도면 치수 인식 최적 설정

```python
# 엔지니어링 도면 치수 인식용 설정
ocr_config = {
    "text_detection_model_name": "PP-OCRv5_server_det",
    "text_recognition_model_name": "PP-OCRv5_server_rec",
    "text_det_limit_side_len": 1280,     # 큰 도면용
    "det_db_thresh": 0.3,                # DB 임계값
    "det_db_box_thresh": 0.5,            # 박스 신뢰도
    "det_db_unclip_ratio": 1.6,          # 박스 확장 비율
    "rec_char_type": "en",               # 치수는 영문+숫자
    "drop_score": 0.5,                   # 낮은 점수 제거
}
```

### 3.4 현재 시스템 적용 상태

```
현재: PP-OCRv4 → PP-OCRv5 업그레이드 완료 ✅
정확도 향상: +13% (논문 기준)
```

---

## 4. DocLayout-YOLO 구현 가이드

### 4.1 설치

```bash
# 추론만 필요 시
pip install doclayout-yolo

# 전체 개발 환경
git clone https://github.com/opendatalab/DocLayout-YOLO.git
cd DocLayout-YOLO
pip install -r requirements.txt
pip install -e .
```

### 4.2 추론 코드

```python
import cv2
from doclayout_yolo import YOLOv10

# 모델 로드 (Hugging Face에서 다운로드)
from huggingface_hub import hf_hub_download

model_path = hf_hub_download(
    repo_id="juliozhao/DocLayout-YOLO-DocStructBench",
    filename="doclayout_yolo_docstructbench.pt"
)

model = YOLOv10(model_path)

# 추론 설정
det_res = model.predict(
    "drawing.png",
    imgsz=1024,              # 입력 이미지 크기
    conf=0.2,                # 신뢰도 임계값
    device="cuda:0",
    # augment=True,          # TTA (Test Time Augmentation)
)

# 결과 시각화
annotated_frame = det_res[0].plot(
    pil=True,
    line_width=5,
    font_size=20
)
cv2.imwrite("result.jpg", annotated_frame)
```

### 4.3 검출 클래스 (10개)

```python
DOCLAYOUT_CLASSES = [
    "title",           # 제목
    "plain_text",      # 일반 텍스트
    "abandon",         # 버림 영역
    "figure",          # 그림
    "figure_caption",  # 그림 캡션
    "table",           # 표
    "table_caption",   # 표 캡션
    "table_footnote",  # 표 각주
    "isolate_formula", # 수식
    "formula_caption"  # 수식 캡션
]
```

### 4.4 도면 적용 시 고려사항

```python
# 엔지니어링 도면용 커스텀 클래스 매핑
DRAWING_CLASSES = {
    "figure": "drawing_view",      # 도면 뷰
    "table": "bom_table",          # BOM 표
    "title": "title_block",        # 타이틀 블록
    "plain_text": "notes",         # 노트 영역
}

# 도면 특화 설정
drawing_config = {
    "imgsz": 1024,
    "conf": 0.15,      # 낮은 임계값 (다양한 요소 검출)
    "iou": 0.5,        # NMS 임계값
}
```

### 4.5 VRAM 사용량 (RTX 3080 8GB 기준)

| 설정 | VRAM 사용 | 추론 속도 |
|------|----------|----------|
| imgsz=640 | ~1.5GB | ~15ms |
| imgsz=1024 | ~2.5GB | ~25ms |
| imgsz=1280 | ~3.5GB | ~35ms |

**결론**: RTX 3080 8GB에서 충분히 실행 가능 ✅

---

## 5. LLaVA-CoT 프롬프트 상세 가이드

### 5.1 4단계 추론 구조

```
<SUMMARY>질문 요약 및 분석 대상 명시</SUMMARY>
<CAPTION>이미지의 관련 요소 설명</CAPTION>
<REASONING>단계별 논리적 추론</REASONING>
<CONCLUSION>최종 결론</CONCLUSION>
```

### 5.2 현재 VL API 구현 비교

```python
# 현재 구현 (vl_service.py)
COT_SYSTEM_PROMPT = """You are an expert visual reasoning system...

1. **SUMMARY**: Briefly summarize the question...
2. **VISUAL INTERPRETATION**: Describe what you observe...
3. **LOGICAL REASONING**: Based on your visual observations...
4. **CONCLUSION**: State your final answer...
"""

# LLaVA-CoT 원본 태그
LLAVA_COT_TAGS = {
    "summary": "<SUMMARY>...</SUMMARY>",
    "caption": "<CAPTION>...</CAPTION>",
    "reasoning": "<REASONING>...</REASONING>",
    "conclusion": "<CONCLUSION>...</CONCLUSION>"
}
```

### 5.3 도면 분류 최적화 프롬프트

```python
# 현재 구현
COT_CLASSIFICATION_PROMPT = """You are an expert engineering drawing classifier...

Categories:
- MECHANICAL: General mechanical/engineering drawings
- PID: Piping and Instrumentation Diagrams
- ELECTRICAL: Electrical diagrams
- ASSEMBLY: Assembly drawings
- DETAIL: Detail views
- LAYOUT: Layout drawings
- OTHER: None of the above

Follow this 4-stage reasoning process...
"""

# 개선안: 더 구체적인 시각적 단서 추가
IMPROVED_CLASSIFICATION_PROMPT = """You are an expert engineering drawing classifier.

## Visual Cues by Category:

### MECHANICAL
- Orthographic views (front, top, side)
- Dimension lines and measurements
- GD&T symbols (⌀, ⊕, ⊥, //)
- Part numbers, material callouts

### PID (Piping & Instrumentation)
- Flow lines (solid, dashed)
- Instrument symbols (circles with letters: TI, PI, FI)
- Valve symbols (butterfly, gate, ball)
- Equipment tags (P-101, V-201)
- Diamond-shaped indicators

### ELECTRICAL
- Schematic symbols (resistors, capacitors)
- Wire routing with node connections
- Component references (R1, C2)
- Voltage/current annotations

### ASSEMBLY
- Exploded views
- Item balloons with numbers
- Assembly sequence indicators
- Bill of Materials reference

Analyze the drawing systematically using 4 stages:
1. SUMMARY: What type of drawing needs classification?
2. CAPTION: What visual elements are present?
3. REASONING: Which category matches based on observed elements?
4. CONCLUSION: Final classification with confidence.
"""
```

### 5.4 Temperature 설정 가이드

| 용도 | Temperature | 설명 |
|------|-------------|------|
| 분류 | 0.0 | 결정적 출력 (일관성 중요) |
| 분석 | 0.1-0.3 | 약간의 다양성 |
| 설명 | 0.5-0.7 | 더 자연스러운 설명 |

---

## 6. 실현 가능한 최적화 액션 아이템

### 6.1 즉시 적용 가능 (코드 변경만)

| 항목 | 파일 | 변경 내용 | 예상 효과 |
|------|------|----------|----------|
| YOLO imgsz 증가 | yolo.yaml | 640 → 1280 | 소형 심볼 검출↑ |
| YOLO conf 조정 | yolo.yaml | 0.25 → 0.3 | 오검출↓ |
| VL 프롬프트 개선 | vl_service.py | 시각적 단서 추가 | 분류 정확도↑ |

### 6.2 단기 도입 가능 (DocLayout-YOLO)

```bash
# 1. 설치
pip install doclayout-yolo

# 2. 테스트 스크립트 작성
python scripts/test_doclayout.py

# 3. Blueprint AI BOM 통합 검토
```

### 6.3 대기 (미출시)

| 항목 | 상태 | 예상 시기 |
|------|------|----------|
| YOLOv12 | Ultralytics 통합 대기 | 2025 Q1-Q2 |

---

## 7. 현재 시스템 파라미터 점검 체크리스트

```bash
# 1. YOLO API 설정 확인
grep -r "imgsz\|conf\|iou" gateway-api/api_specs/yolo.yaml

# 2. PaddleOCR 설정 확인
grep -r "det_limit\|rec_batch" models/paddleocr-api/

# 3. VL API 프롬프트 확인
grep -r "COT_SYSTEM_PROMPT\|temperature" models/vl-api/

# 4. GPU 메모리 사용량 모니터링
nvidia-smi --query-gpu=memory.used --format=csv -l 1
```

---

## Sources

- [YOLOv11 Architecture](https://arxiv.org/pdf/2410.17725)
- [YOLOv12 Paper](https://arxiv.org/abs/2502.12524)
- [Ultralytics YOLO Docs](https://docs.ultralytics.com/)
- [PaddleOCR 3.0 Technical Report](https://arxiv.org/html/2507.05595v1)
- [PP-OCRv5 Documentation](https://www.paddleocr.ai/v3.0.3/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5.html)
- [DocLayout-YOLO GitHub](https://github.com/opendatalab/DocLayout-YOLO)
- [LLaVA-CoT Paper](https://arxiv.org/abs/2411.10440)

---

*작성자*: Claude Code (Opus 4.5)
*최종 업데이트*: 2025-12-31
