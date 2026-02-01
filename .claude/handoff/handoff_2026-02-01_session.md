# 세션 핸드오프 - 2026-02-01

## 1. 세션 요약
`dimension_service.py`의 멀티 엔진 치수 병합 로직을 기존 IoU 중복 제거 방식에서 OCR Ensemble 패턴의 **가중 투표 방식**으로 개선했습니다. PaddleOCR이 Ø를 0으로 오인하는 문제(예: "0382" vs "Ø382")를 엔진별 가중치 + 치수 유형 특화 보너스로 해결합니다.

## 2. 작업 중인 태스크
- [x] 엔진별 가중치 상수 추가 (`_ENGINE_BASE_WEIGHTS`, `_ENGINE_SPECIALTY_BONUS`)
- [x] 헬퍼 메서드 추가 (`_get_engine_weight`, `_normalize_dim_value`)
- [x] `_merge_multi_engine()` 메서드 구현 (5단계 가중 투표)
- [x] `extract_dimensions()`에서 `_merge_multi_engine()` 호출로 변경
- [x] Python 문법 검증 통과
- [x] 파일 크기 1000줄 미만 유지 (980줄)
- [ ] Docker 재빌드 및 실제 도면으로 E2E 테스트
- [ ] 백엔드 로그에서 "가중 투표 병합" 메시지 확인
- [ ] Ø 기호 정확도 향상 검증

## 3. 수정된 파일
| 파일 | 변경 유형 | 설명 |
|------|----------|------|
| `blueprint-ai-bom/backend/services/dimension_service.py` | Modified | IoU 중복 제거 → 가중 투표 병합으로 개선 (992줄 → 980줄) |

## 4. 미완료 작업
- **Docker 재빌드**: `docker build -f backend/Dockerfile -t blueprint-ai-bom-backend:latest backend/` 실행 필요
- **E2E 검증**: 브라우저에서 치수 분석 실행 후 결과 비교 필요
  - 치수 개수 유사 확인
  - Ø 기호 특수 패턴 정확도 향상 확인
  - 합의 보너스로 신뢰도 상승 확인

## 5. 중요 결정사항
- **OCR Ensemble 패턴 적용**: `models/ocr-ensemble-api/services/ensemble.py`의 `merge_results` 패턴을 차용
- **엔진 가중치**: edocr2 0.40 (도면 특화 최고), paddleocr 0.35, easyocr 0.25, doctr 0.25, trocr/suryaocr 0.20
- **특화 보너스**: edocr2에 직경 +0.15, 공차 +0.15, 반경 +0.10, 나사 +0.10 부여
- **합의 보너스**: +0.05/엔진, 최대 +0.15 (ensemble의 +0.20보다 보수적)
- **기존 `_merge_dimensions()` 유지**: `_call_paddleocr_tiled` 내부 동일 엔진 dedup용으로 계속 사용
- **파일 크기 관리**: 기존 주석/docstring 정리하여 980줄로 유지 (추가 코드 ~100줄에도 불구하고 기존보다 줄어듦)

## 6. 다음 세션에서 할 일
1. Docker 재빌드 후 실제 도면으로 E2E 테스트
2. 백엔드 로그 확인: "가중 투표 병합" 및 "가중 투표:" 디버그 메시지
3. 기존 분석 결과와 비교: 치수 개수, Ø 정확도, confidence 분포
4. 필요 시 가중치 미세 조정

## 7. 참고 컨텍스트
- **변경 파일**: `blueprint-ai-bom/backend/services/dimension_service.py`
- **참조 패턴**: `models/ocr-ensemble-api/services/ensemble.py` (merge_results)
- **스키마**: `blueprint-ai-bom/backend/schemas/dimension.py` (Dimension, DimensionType)
- **호출 경로**: `core_router.py` → `DimensionService.extract_dimensions()` → `_merge_multi_engine()`

### 핵심 개선 효과
```
이전: PaddleOCR "0382" (conf 0.97) 채택 → 오답
이후: eDOCr2 "Ø382" vote=(0.40+0.15)×0.90=0.495 > PaddleOCR "0382" vote=0.35×0.97=0.340
     → "Ø382" 채택 (정답)
```

---
**생성 시간**: 2026-02-01
**브랜치**: main
