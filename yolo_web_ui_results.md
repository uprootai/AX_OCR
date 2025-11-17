# YOLO API 웹 UI 테스트 결과

## 테스트 정보
- **테스트 이미지**: sample3_s60me_shaft.jpg (S60ME-C 중간축 도면)
- **처리 시간**: 0.36초
- **모델**: YOLOv11n (CPU)

## 검출 결과

### 총 검출 객체 수
화면에서 확인된 주요 검출:

1. **parallelism** (평행도): 84.5%
   - Position: [376, 923] | Size: 149 × 32

2. **reference_dim** (참조 치수): 80.4%
   - Position: [1096, 956] | Size: 84 × 39

3. **linear_dim** (선형 치수): 74.1%
   - Position: [1464, 939] | Size: 123 × 35

4. **tolerance_dim** (공차 치수): 74.1%

## Ground Truth와 비교

### Claude의 Ground Truth (api_accuracy_evaluation.json):
```json
{
  "주요 치수": {
    "외경": "Ø476",
    "중간 직경": "Ø370",
    "내경 관련": "Ø324",
    "길이": "163+2/-1.2",
    "깊이": "7-9"
  },
  "GD&T 기호": {
    "평행도": "∥ 0.2",
    "진원도": ["Rev.1", "Rev.2", "Rev.3"],
    "기준면": ["△A", "△B"],
    "표면거칠기": ["Ra 3.2", "Ra 6.3"]
  }
}
```

### YOLO 검출 클래스 매칭

✅ **성공적으로 검출된 항목**:
1. **parallelism** (평행도 ∥ 0.2) - 84.5% 신뢰도 - Ground Truth와 일치!
2. **linear_dim** (선형 치수) - 74.1% - Ground Truth의 길이 치수와 관련
3. **tolerance_dim** (공차 치수) - 74.1% - Ground Truth의 공차 정보와 관련
4. **reference_dim** (참조 치수) - 80.4%

⚠️ **Ground Truth에 있지만 화면에서 확인 안 된 항목**:
- diameter_dim (직경 Ø476, Ø370, Ø324)
- surface_roughness (Ra 3.2, Ra 6.3)
- 진원도 기호
- 기준면 (△A, △B)

## 성능 평가

### 장점:
1. 매우 빠른 처리 속도 (0.36초)
2. GD&T 기호 중 평행도 정확히 검출 (84.5%)
3. 치수 관련 객체들 검출 성공

### 한계:
1. 직경 치수 (Ø) 미검출 또는 화면 밖
2. 표면 거칠기 (Ra) 미검출 또는 화면 밖
3. 전체 검출 결과 확인 위해 스크롤 필요

## 다음 단계
- 전체 검출 목록 확인을 위해 스크롤
- 시각화 이미지 확인
- eDOCr2 API 테스트로 텍스트 인식 정확도 비교
