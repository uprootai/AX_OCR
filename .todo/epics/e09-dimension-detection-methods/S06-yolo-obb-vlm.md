# S06: YOLOv11-OBB + VLM 하이브리드 — 치수 영역 검출 + 의미 해석

> YOLOv11-OBB로 회전된 치수 주석 영역을 검출하고, VLM(Qwen2-VL / GPT-4o)으로 의미를 해석하여 OD/ID/W를 분류한다.

## 왜 이 방법인가

기존 방법은 OCR → 숫자 추출 → 규칙 기반 분류. 하지만:
- 치수 주석은 회전, 기울임, 다양한 포맷으로 존재
- "Ø1036"이 OD인지 홀 직경인지는 **위치적 맥락**으로 판단해야 함
- VLM은 이미지 컨텍스트를 직접 이해 → 규칙 하드코딩 불필요

2025년 최신 논문:
> "From drawings to decisions: hybrid vision-language framework" (ScienceDirect)
> YOLOv11-OBB가 치수 영역 검출, Donut/Florence-2가 텍스트 인식. 1,367개 도면 9개 클래스.

## 핵심 참고 자료

- [From drawings to decisions: hybrid VLM framework (ScienceDirect 2025)](https://www.sciencedirect.com/science/article/abs/pii/S0736584525002406)
- [Intelligent GD&T symbol detection: YOLOv11 (Springer 2025)](https://link.springer.com/article/10.1007/s10845-025-02669-3)
- [YOLOv11 Ultralytics](https://docs.ultralytics.com/) — OBB 모드 지원
- [Fine-Tuning VLM for Drawing Extraction (arXiv 2411.03707)](https://arxiv.org/abs/2411.03707)

## 구현 계획

### Step 1: 치수 영역 라벨링 (4h)

```
클래스 정의:
  - diameter_dim: 직경 치수 (Ø 포함)
  - linear_dim: 선형 치수 (수평/수직)
  - radius_dim: 반지름 치수 (R 포함)
  - angle_dim: 각도 치수
  - gdt_frame: GD&T 프레임

87개 도면 중 30개 선별 → OBB 라벨링 (CVAT 회전 bbox)
도면당 평균 10~15 치수 → 약 400 어노테이션
```

### Step 2: YOLOv11-OBB 학습 (3h)

```
- ultralytics YOLOv11n-obb pretrained → fine-tune
- 입력: 1024×1024 (도면은 고해상도이므로 타일링 고려)
- 70/15/15 분할
- epochs=200, batch=8
```

### Step 3: VLM 의미 해석 (3h)

```python
def classify_dimension_vlm(cropped_region, detected_class, drawing_context):
    """
    1. YOLOv11-OBB가 검출한 치수 영역을 크롭
    2. 도면 전체 맥락(원 위치, 단면도 위치)과 함께 VLM에 전달
    3. VLM 프롬프트:
       "이 치수 주석이 가리키는 대상은?
        (a) 외경(OD) (b) 내경(ID) (c) 폭(W) (d) 기타"
    4. VLM 응답 파싱
    """
    # Qwen2-VL-7B (로컬) 또는 GPT-4o (API) 선택
```

### Step 4: 통합 파이프라인 (2h)

```
도면 입력
  → YOLOv11-OBB: 치수 영역 검출 + 클래스
  → 각 검출에서 OCR 값 추출 (기존 PaddleOCR)
  → diameter_dim 클래스 치수 중:
    - VLM이 OD로 판단 → OD
    - VLM이 ID로 판단 → ID
  → linear_dim 클래스 치수 중 W 판단
  → 결과 반환
```

### Step 5: 배치 테스트 (1h)

## 예상 소요: 13시간

## 리스크

- **라벨링 비용**: OBB 라벨링은 일반 bbox보다 시간이 2배
- **VLM 비용/지연**: GPT-4o API 호출 = $/도면, 로컬 Qwen2-VL은 GPU 필요
- **이중 모델 파이프라인 복잡도**: YOLO + VLM + OCR 3개 모델 체인
- **소규모 데이터**: 30개 도면 400 라벨은 OBB 학습에 부족할 수 있음

## 성공 기준

- 치수 영역 검출 mAP > 0.8 (OBB IoU=0.5)
- VLM OD/ID/W 분류 정확도 > 85%
- 전체 파이프라인 처리 시간 < 30초/도면 (VLM 포함)
