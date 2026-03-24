# S07: Florence-2 Fine-tuning — GD&T 통합 추출 모델

> Florence-2 VLM을 engineering drawing 도메인에 fine-tune하여 OCR + 분류를 단일 모델로 통합한다.

## 왜 이 방법인가

현재 파이프라인: 원 검출 → OCR → 후처리 → 분류 (4단계, 각 단계에서 오류 가능)
Florence-2: 이미지 → 프롬프트 → 구조화된 출력 (end-to-end)

```
프롬프트: "이 베어링 도면에서 OD, ID, W 치수를 찾아라"
출력: {"od": "Ø1036", "id": "Ø580", "w": "200", "od_bbox": [...], ...}
```

2024 arXiv 논문(2411.03707)에서 Florence-2를 GD&T 추출에 fine-tune하여 유망한 결과를 보고.

## 핵심 참고 자료

- [Fine-Tuning VLM for Engineering Drawing Information Extraction (arXiv 2411.03707)](https://arxiv.org/abs/2411.03707)
- [Florence-2: Advancing a Unified Representation (arXiv 2311.06242)](https://arxiv.org/abs/2311.06242)
- [microsoft/Florence-2-large (HuggingFace)](https://huggingface.co/microsoft/Florence-2-large)
- [eDOCr2 + VLM 통합 논문 (MDPI 2025)](https://www.mdpi.com/2075-1702/13/3/254)

## 구현 계획

### Step 1: 학습 데이터 준비 (5h)

```
포맷: {image, prompt, response} 쌍

프롬프트 유형 A — 구조화된 추출:
  prompt: "<OD_ID_W>"
  response: "OD: Ø1036 <loc_300_200_400_220> ID: Ø580 <loc_...> W: 200 <loc_...>"

프롬프트 유형 B — 자유 질의:
  prompt: "What is the outer diameter of this bearing?"
  response: "Ø1036"

87개 도면에서 GT가 있는 것 + 수동 라벨링
  → 약 100~200 학습 샘플 (augmentation으로 확장)
```

### Step 2: Florence-2 Fine-tuning (4h)

```python
from transformers import AutoProcessor, AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained("microsoft/Florence-2-large")
processor = AutoProcessor.from_pretrained("microsoft/Florence-2-large")

# LoRA fine-tuning (메모리 효율)
# lr=1e-5, epochs=30, batch=4
# GPU: RTX 3090 (24GB) 또는 A100
```

### Step 3: 추론 파이프라인 (2h)

```python
def extract_od_id_w_florence(image_path):
    """
    1. 이미지 로드 + 전처리
    2. Florence-2 추론: prompt="<OD_ID_W>"
    3. 응답 파싱: OD/ID/W 값 + bbox 추출
    4. 후처리: 숫자 정규화, Ø/R 접두사 처리
    """
```

### Step 4: 기존 방법과 앙상블 (2h)

```
- Florence-2 결과를 독립 방법 `Q`로 등록
- K방법 결과와 투표(voting) 앙상블
- 불일치 시 confidence 기반 선택
```

### Step 5: 배치 테스트 (1h)

## 예상 소요: 14시간

## S06과의 차이

| 항목 | S06 (YOLO-OBB + VLM) | S07 (Florence-2) |
|------|----------------------|-------------------|
| 검출 | YOLO-OBB (영역) | Florence-2 (end-to-end) |
| OCR | PaddleOCR 별도 | Florence-2 내장 |
| 분류 | VLM 별도 호출 | Florence-2 내장 |
| 모델 수 | 3개 (YOLO+OCR+VLM) | 1개 |
| 데이터 | OBB 라벨링 필요 | 텍스트 쌍 라벨링 |
| 추론 속도 | 느림 (3모델) | 중간 (1모델) |

## 리스크

- **GPU 메모리**: Florence-2-large는 ~0.7B 파라미터, LoRA로도 16GB+ 필요
- **소규모 데이터**: 100~200 샘플로 fine-tune은 과적합 위험
- **공간 정확도**: VLM은 텍스트 인식에 강하지만 정밀 좌표 예측은 약할 수 있음
- **배포 복잡도**: PyTorch + transformers를 Docker에 추가

## 성공 기준

- OD/ID/W 동시 정확도 > 75% (end-to-end)
- 기존 K방법과 앙상블 시 정확도 > 85%
- 추론 시간 < 10초/도면
