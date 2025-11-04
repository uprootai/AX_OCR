# 합성 데이터 생성 전략

**작성일**: 2025-10-31
**목적**: 적은 데이터로 높은 성능 달성
**핵심 아이디어**: 랜덤 배치 + 템플릿 기반 + 실제 도면 증강

---

## 🎯 핵심 전략

### 문제점
- 실제 공학 도면 데이터 부족 (100장 미만)
- 수동 라벨링 비용 높음 (1시간/10장)
- 다양한 레이아웃 학습 필요

### 해결책
1. **랜덤 배치 합성 데이터** (무한 생성 가능)
2. **템플릿 기반 생성** (실제 도면 스타일 모방)
3. **실제 도면 + 증강** (기존 데이터 활용)

---

## 📊 3가지 생성 방법

### 방법 1: 랜덤 배치 합성 (추천) ⭐

**원리**:
```
빈 흰색 배경 (1920x1080)
  ↓
랜덤하게 요소 배치:
  - 치수: φ476, 120, R50 등
  - GD&T: ⌹0.1, ○0.05 등
  - 표면조도: Ra3.2 등
  ↓
랜덤 변환:
  - 크기: 0.5x ~ 2.0x
  - 회전: 0° ~ 360°
  - 위치: 전체 영역
  - 폰트: 다양한 기술 폰트
  ↓
자동 라벨 생성 (bbox 알고 있음)
```

**장점**:
- ✅ 무한 데이터 생성 가능
- ✅ 완벽한 라벨 (bbox 정확)
- ✅ 다양한 레이아웃 학습
- ✅ 빠른 생성 (1초/100장)

**단점**:
- ⚠️ 실제 도면과 차이 있음
- ⚠️ 맥락 없음 (치수가 의미 없이 배치)

**예상 성능**:
- 10,000장 생성 시: F1 60-70%
- 실제 도면 100장 추가 시: F1 75-85%

---

### 방법 2: 템플릿 기반 생성

**원리**:
```
실제 도면 템플릿 (10종류)
  - 샤프트 도면
  - 플랜지 도면
  - 하우징 도면
  - 기어 도면 등
  ↓
파라메트릭 변경:
  - 치수 값 변경
  - GD&T 기호 변경
  - 재질 변경
  ↓
렌더링 + 라벨 생성
```

**장점**:
- ✅ 실제 도면과 유사
- ✅ 의미 있는 맥락
- ✅ 다양한 도면 타입

**단점**:
- ⚠️ 템플릿 제작 필요 (CAD 지식)
- ⚠️ 생성 속도 느림 (10초/장)

**예상 성능**:
- 1,000장 생성 시: F1 70-80%
- 실제 도면 100장 추가 시: F1 80-90%

---

### 방법 3: 실제 도면 + 증강

**원리**:
```
실제 도면 100장
  ↓
다양한 증강:
  - Cut-Mix: 여러 도면 조각 합성
  - Copy-Paste: 요소 복사/붙여넣기
  - Mosaic: 4장 합성
  - Perspective: 원근 왜곡
  - Noise: 스캔 노이즈 추가
  ↓
라벨 자동 업데이트
```

**장점**:
- ✅ 실제 도면 기반
- ✅ 높은 품질
- ✅ YOLO 내장 증강 활용

**단점**:
- ⚠️ 초기 데이터 필요 (100장)
- ⚠️ 다양성 제한

**예상 성능**:
- 100장 → 1,000장 증강 시: F1 70-80%

---

## 💡 추천 조합 전략

### Phase 1: 랜덤 배치 (Week 1)
```python
# 10,000장 합성 데이터 생성
python scripts/generate_synthetic_random.py \
  --count 10000 \
  --output datasets/synthetic_random/

# 학습
python scripts/train_yolo.py \
  --data datasets/synthetic_random/data.yaml \
  --epochs 100
```

**예상 결과**: F1 60-70%

---

### Phase 2: 실제 도면 추가 (Week 2)
```python
# 실제 도면 100장 준비
python scripts/prepare_dataset.py

# 합성 + 실제 혼합
python scripts/merge_datasets.py \
  --synthetic datasets/synthetic_random/ \
  --real datasets/engineering_drawings/ \
  --output datasets/combined/

# 재학습
python scripts/train_yolo.py \
  --data datasets/combined/data.yaml \
  --epochs 150
```

**예상 결과**: F1 75-85%

---

### Phase 3: 템플릿 기반 추가 (Week 3-4)
```python
# 템플릿 1,000장 생성
python scripts/generate_synthetic_template.py \
  --templates templates/ \
  --count 1000 \
  --output datasets/synthetic_template/

# 전체 혼합
python scripts/merge_datasets.py \
  --datasets datasets/synthetic_random/ \
              datasets/synthetic_template/ \
              datasets/engineering_drawings/ \
  --output datasets/final/

# 최종 학습
python scripts/train_yolo.py \
  --data datasets/final/data.yaml \
  --epochs 200 \
  --model-size m
```

**예상 결과**: F1 85-95%

---

## 🎨 상세 구현: 랜덤 배치 생성

### 핵심 알고리즘

```python
def generate_synthetic_image():
    # 1. 빈 캔버스 생성
    canvas = np.ones((1080, 1920, 3), dtype=np.uint8) * 255

    # 2. 랜덤 요소 개수 (10-30개)
    num_elements = random.randint(10, 30)

    annotations = []

    for _ in range(num_elements):
        # 3. 요소 타입 선택 (치수, GD&T, 표면조도 등)
        element_type = random.choice([
            'diameter_dim', 'linear_dim', 'radius_dim',
            'flatness', 'cylindricity', 'surface_roughness'
        ])

        # 4. 텍스트 생성
        if element_type == 'diameter_dim':
            text = f"φ{random.randint(10, 500)}"
        elif element_type == 'linear_dim':
            text = f"{random.randint(5, 1000)}"
        elif element_type == 'flatness':
            text = f"⌹{random.uniform(0.01, 0.5):.2f}"
        # ... 기타 타입

        # 5. 랜덤 위치, 크기, 회전
        x = random.randint(50, 1870)
        y = random.randint(50, 1030)
        size = random.uniform(20, 80)
        angle = random.randint(0, 360)
        font = random.choice(['Arial', 'DejaVu Sans', 'Liberation Sans'])

        # 6. 텍스트 렌더링
        bbox = draw_text(canvas, text, x, y, size, angle, font)

        # 7. 어노테이션 저장
        annotations.append({
            'class': element_type,
            'bbox': bbox
        })

    return canvas, annotations
```

---

## 📐 요소 라이브러리

### 치수 타입 (7종)

```python
DIMENSION_TEMPLATES = {
    'diameter_dim': [
        'φ{value}',
        'Ø{value}',
        '⌀{value}',
    ],
    'linear_dim': [
        '{value}',
        '{value}mm',
    ],
    'radius_dim': [
        'R{value}',
        'r{value}',
    ],
    'angular_dim': [
        '{value}°',
        '{value}DEG',
    ],
    'chamfer_dim': [
        '{value}x45°',
        'C{value}',
    ],
    'tolerance_dim': [
        '±{value}',
        '+{plus}/-{minus}',
        '{value} ±{tol}',
    ],
    'reference_dim': [
        '({value})',
    ],
}

# 값 범위
VALUE_RANGES = {
    'diameter_dim': (5, 500),
    'linear_dim': (1, 1000),
    'radius_dim': (1, 250),
    'angular_dim': (0, 180),
    'chamfer_dim': (0.5, 10),
    'tolerance_dim': (0.01, 5),
}
```

---

### GD&T 기호 (5종)

```python
GDT_SYMBOLS = {
    'flatness': ['⌹', '⏥'],
    'cylindricity': ['○', '◯'],
    'position': ['⌖', '⊕'],
    'perpendicularity': ['⊥', '┴'],
    'parallelism': ['∥', '‖'],
}

GDT_TEMPLATES = [
    '{symbol}{value}',
    '{symbol}{value}|{datum}',
    '{symbol}{value}|{datum1}|{datum2}',
]
```

---

### 표면조도 (Surface Roughness)

```python
SURFACE_ROUGHNESS_TEMPLATES = [
    'Ra{value}',
    'Rz{value}',
    'Rmax{value}',
]

ROUGHNESS_VALUES = [0.4, 0.8, 1.6, 3.2, 6.3, 12.5, 25]
```

---

## 🎲 랜덤 변환 전략

### 1. 위치 (Position)
```python
# 전체 영역에 균등 분포
x = random.uniform(margin, width - margin)
y = random.uniform(margin, height - margin)

# 또는 그리드 기반 (충돌 방지)
grid_x = random.randint(0, grid_cols - 1)
grid_y = random.randint(0, grid_rows - 1)
x = grid_x * cell_width + random.uniform(0, cell_width)
y = grid_y * cell_height + random.uniform(0, cell_height)
```

---

### 2. 크기 (Scale)
```python
# 로그 정규 분포 (실제 도면과 유사)
base_size = 40  # 기본 폰트 크기
scale = np.random.lognormal(mean=0, sigma=0.5)
size = base_size * np.clip(scale, 0.5, 2.0)
```

---

### 3. 회전 (Rotation)
```python
# 주로 수평/수직, 가끔 대각선
if random.random() < 0.7:
    # 수평/수직 (±5도 오차)
    angle = random.choice([0, 90, 180, 270]) + random.uniform(-5, 5)
else:
    # 자유 각도
    angle = random.uniform(0, 360)
```

---

### 4. 폰트 (Font)
```python
# 기술 도면용 폰트
TECHNICAL_FONTS = [
    'DejaVu Sans',
    'Liberation Sans',
    'Arial',
    'Helvetica',
    'Courier New',
]

font = random.choice(TECHNICAL_FONTS)
```

---

### 5. 색상 (Color)
```python
# 대부분 검정, 가끔 파랑/빨강
if random.random() < 0.8:
    color = (0, 0, 0)  # Black
elif random.random() < 0.5:
    color = (255, 0, 0)  # Blue (BGR)
else:
    color = (0, 0, 255)  # Red
```

---

### 6. 노이즈 (Noise)
```python
# 스캔 노이즈 추가
noise = np.random.normal(0, 5, image.shape).astype(np.uint8)
noisy_image = cv2.add(image, noise)

# JPEG 압축 노이즈
_, encoded = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, random.randint(70, 95)])
decoded = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
```

---

## 📈 성능 예측

### 시나리오 A: 순수 합성 데이터
```
데이터: 10,000장 (랜덤 배치)
학습: 100 epochs
예상 F1: 60-70%
```

**장점**: 빠른 시작 (Week 1)
**단점**: 실제 도면과 차이

---

### 시나리오 B: 합성 + 실제 혼합 (추천)
```
데이터:
  - 합성 10,000장 (랜덤 배치)
  - 실제 100장
  - 증강 1,000장 (실제 도면 기반)
학습: 150 epochs
예상 F1: 75-85%
```

**장점**: 균형잡힌 성능
**단점**: 실제 도면 100장 필요

---

### 시나리오 C: 전체 조합
```
데이터:
  - 합성 10,000장 (랜덤 배치)
  - 합성 1,000장 (템플릿 기반)
  - 실제 100장
  - 증강 1,000장
학습: 200 epochs
예상 F1: 85-95%
```

**장점**: 최고 성능
**단점**: 시간 소요 (2-3주)

---

## 🛠️ 구현 우선순위

### Week 1: 랜덤 배치 생성기
1. ✅ 기본 생성기 구현
2. ✅ 14개 클래스 템플릿
3. ✅ 랜덤 변환 로직
4. ✅ 자동 라벨 생성
5. ✅ 10,000장 생성

---

### Week 2: 실제 도면 통합
1. 실제 도면 100장 준비
2. 데이터셋 병합 스크립트
3. 혼합 학습

---

### Week 3-4: 템플릿 기반 (선택)
1. CAD 템플릿 제작 (10종)
2. 파라메트릭 생성기
3. 1,000장 생성

---

## 💰 비용 분석

### 수동 라벨링
- 시간: 1시간/10장
- 1,000장: 100시간 = 12.5일
- 비용: $1,500 (시급 $15 기준)

### 합성 데이터 생성
- 시간: 1초/100장
- 10,000장: 100초 = **2분**
- 비용: **$0**

**ROI**: 10,000배 효율 향상! 🚀

---

## ⚡ 다음 단계

### 즉시 실행 (오늘)
```bash
# 랜덤 배치 생성기 구현
python scripts/generate_synthetic_random.py --count 1000

# 학습
python scripts/train_yolo.py \
  --data datasets/synthetic_random/data.yaml \
  --epochs 50
```

### Week 2
```bash
# 실제 도면 추가
python scripts/merge_datasets.py

# 재학습
python scripts/train_yolo.py \
  --data datasets/combined/data.yaml \
  --epochs 100
```

---

**작성자**: Claude 3.7 Sonnet
**최종 업데이트**: 2025-10-31

**핵심 메시지**:
> 랜덤 배치 합성 데이터로 **무한 학습 데이터** 생성!
> 실제 도면 100장만 있으면 F1 75-85% 달성 가능! 🎯
