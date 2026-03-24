# S05: CircleNet — Anchor-Free 딥러닝 원 검출

> CenterNet 기반 anchor-free 모델을 engineering drawing 도메인에 적용하여 (cx, cy, r)을 직접 예측한다.

## 왜 이 방법인가

기존 원 검출(Contour, Hough, RANSAC)은 모두 에지 기반 → 노이즈에 민감.
CircleNet은 학습 기반으로 "원처럼 보이는 패턴"을 직접 인식:
- bbox 대신 (center_x, center_y, radius) 출력 → 회전 불변
- 부분 가림(occlusion)에도 학습으로 대응
- 의료 이미지에서 box 대비 >10% 성능 향상 보고

## 핵심 참고 자료

- [CircleNet GitHub](https://github.com/hrlblab/CircleNet) — PyTorch, CenterNet 기반
- [Circle Representation for Medical Object Detection (arXiv 2110.12093)](https://arxiv.org/abs/2110.12093)
- [Circle detection: a deep learning approach (ResearchGate)](https://www.researchgate.net/publication/344801439)

## 구현 계획

### Step 1: 학습 데이터 준비 (4h)

```
- 87개 DSE 도면에서 원 위치 라벨링 (cx, cy, r)
- 도면당 평균 3~5개 원 → 약 300~400 원 어노테이션
- LabelMe 또는 CVAT으로 원 어노테이션
- COCO 형식으로 변환 (CircleNet 입력 포맷)
- 70/15/15 train/val/test 분할
```

### Step 2: CircleNet 학습 (3h)

```
- hrlblab/CircleNet 클론 + 의존성 설치
- 백본: DLA-34 (기본) 또는 ResNet-50
- 전이학습: COCO pretrained → engineering drawing fine-tune
- 학습 파라미터: lr=1e-4, batch=8, epochs=100
- GPU: 단일 RTX 3090 (또는 T4)
```

### Step 3: 추론 파이프라인 통합 (2h)

```python
def detect_circles_circlenet(img_gray):
    """
    1. 이미지 전처리 (512×512 리사이즈, 정규화)
    2. CircleNet 모델 추론
    3. NMS로 중복 원 제거
    4. 원본 좌표로 역변환
    5. confidence > 0.5 필터링
    """
    return [(cx, cy, r, conf), ...]
```

### Step 4: 기존 앙상블 통합 (1h)

```
- detect_circles_circlenet을 5차 패스로 추가
- 또는 DL 결과를 primary, 기존을 fallback으로 구성
- ensemble_circles로 통합
```

### Step 5: 배치 테스트 (1h)

- DL 단독 vs 기존 vs 앙상블 비교
- 원 검출 precision/recall 측정

## 예상 소요: 11시간

## 리스크

- **데이터 부족**: 87개 도면 × 3~5원 = 300~400개. 학습에 부족할 수 있음 → augmentation 필수
- **도메인 갭**: 의료 이미지와 engineering drawing은 시각적으로 매우 다름
- **GPU 필요**: 학습에 GPU 환경 필요 (현재 WSL2에 GPU 접근 가능한지 확인 필요)
- **배포 복잡도**: PyTorch 모델을 Docker 컨테이너에 추가 배포해야 함

## 성공 기준

- 원 검출 mAP > 0.7 (IoU=0.5 기준, 원의 IoU는 면적 겹침으로 계산)
- T5 도면에서 외원 중심 편차 < 50px (기존 194px)
- 추론 시간 < 2초/도면
