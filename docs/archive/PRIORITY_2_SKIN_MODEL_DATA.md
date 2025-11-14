# 🟡 우선순위 2-1: Skin Model 학습 데이터

**목적**: Mock 데이터 → 실제 공차 예측 모델로 전환
**소요 시간**: 2-4주
**담당자**: 데이터 사이언티스트 + 도메인 전문가

---

## 📋 현재 문제

### 현재 상태
```python
# skinmodel-api/api_server.py (현재)
predictions = [
    {
        "type": "flatness",
        "value": 0.05,
        "location": {"x": 100, "y": 200},
        "confidence": 0.85
    }
]
# ❌ 하드코딩된 Mock 데이터, 입력 무시
```

### 필요한 것
실제 머신러닝 모델 학습을 위한 **레이블링된 데이터셋**

---

## ✅ 데이터 요구사항

### 최소 데이터셋
- **도면 수**: 1,000개 이상
- **공차 레이블**: 도면당 평균 5개
- **총 레이블**: 5,000개 이상

### 이상적 데이터셋
- **도면 수**: 5,000-10,000개
- **공차 레이블**: 도면당 평균 10개
- **총 레이블**: 50,000개 이상

---

## 📊 데이터 구조

### 입력 데이터
```json
{
  "drawing_id": "DWG-001",
  "image_path": "/data/drawings/dwg001.pdf",
  "contours": [
    {"type": "circle", "center": [100, 200], "radius": 50},
    {"type": "line", "start": [0, 0], "end": [100, 100]}
  ],
  "dimensions": [
    {"type": "diameter", "value": 100, "location": [100, 200]}
  ]
}
```

### 레이블 데이터 (Ground Truth)
```json
{
  "drawing_id": "DWG-001",
  "tolerances": [
    {
      "type": "flatness",
      "value": 0.05,
      "location": {"x": 100, "y": 200},
      "datum": null,
      "applies_to": "surface_1"
    },
    {
      "type": "cylindricity",
      "value": 0.02,
      "location": {"x": 150, "y": 250},
      "datum": "A",
      "applies_to": "hole_2"
    }
  ]
}
```

---

## 🔧 데이터 수집 방법

### 옵션 1: 기존 도면 레이블링 (권장)

#### 1단계: 도면 수집
```bash
# 기존 도면 복사
cp -r /home/uproot/ax/reference/02.\ 수요처\ 및\ 도메인\ 자료/2.\ 도면\(샘플\)/ \
     /home/uproot/ax/poc/skin_model_data/raw_drawings/
```

#### 2단계: 레이블링 도구 설정
```bash
# Label Studio 설치 (권장)
pip install label-studio
label-studio start

# 브라우저 접속: http://localhost:8080
# 프로젝트 생성: "Skin Model Tolerance Labeling"
```

#### 3단계: 레이블링 작업
1. 도면 업로드
2. 공차 위치 표시 (bbox)
3. 공차 타입 선택 (flatness, cylindricity, position 등)
4. 공차 값 입력
5. Datum 지정 (있는 경우)

### 옵션 2: 자동 추출 + 수동 검증

```bash
# eDOCr2로 자동 추출
python TODO/scripts/extract_tolerances_bulk.py

# 결과 검증 및 수정
# → CSV 파일 열어서 수동 검증
```

### 옵션 3: 외주 레이블링 서비스
- **Labelbox**: https://labelbox.com/
- **Scale AI**: https://scale.com/
- **SuperAnnotate**: https://www.superannotate.com/

---

## 📁 데이터 구조

```
skin_model_data/
├── raw_drawings/           # 원본 도면 (PDF/JPG)
│   ├── dwg001.pdf
│   ├── dwg002.pdf
│   └── ...
│
├── labels/                 # 레이블 JSON 파일
│   ├── dwg001.json
│   ├── dwg002.json
│   └── ...
│
├── train/                  # 학습 데이터 (80%)
│   └── train.csv
│
├── val/                    # 검증 데이터 (10%)
│   └── val.csv
│
└── test/                   # 테스트 데이터 (10%)
    └── test.csv
```

---

## 🧪 모델 학습

### 학습 스크립트 (Claude가 준비함)

```bash
# 1. 데이터 전처리
python skinmodel-api/scripts/preprocess_data.py \
  --input skin_model_data/labels \
  --output skin_model_data/processed

# 2. 모델 학습
python skinmodel-api/scripts/train_model.py \
  --train skin_model_data/train/train.csv \
  --val skin_model_data/val/val.csv \
  --epochs 100 \
  --batch-size 32

# 3. 모델 평가
python skinmodel-api/scripts/evaluate_model.py \
  --model models/skin_model_best.pth \
  --test skin_model_data/test/test.csv
```

### 목표 성능
- **위치 정확도**: 87% 이상 (IoU > 0.5)
- **타입 정확도**: 83% 이상
- **값 오차**: ±10% 이내

---

## ✅ 완료 확인

```bash
# 1. 데이터 개수 확인
wc -l skin_model_data/labels/*.json
# 출력: 1000개 이상

# 2. 모델 존재 확인
ls -lh models/skin_model_best.pth

# 3. API 테스트
curl -X POST http://localhost:5003/api/v1/predict \
  -F "file=@test.pdf" \
  -F "contours=..." \
  -F "dimensions=..."

# 4. Mock이 아닌 실제 예측 확인
# predictions[0].confidence != 0.85 (Mock 고정값)
```

---

**작성일**: 2025-11-08
**예상 소요 시간**: 2-4주
**다음 단계**: `PRIORITY_2_SECURITY_POLICY.md`
