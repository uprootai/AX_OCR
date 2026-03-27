# S01: OCR 엔진별 벤치마크 (전체 이미지)

> GAR 3페이지 이미지를 각 OCR 엔진에 넣어 TAG 추출률을 비교

| 항목 | 값 |
|------|---|
| 상태 | ✅ Done |
| 입력 | `/tmp/gar-page3.png` (1684x2382px, 래스터) |
| 정답 (GT) | Part List에서 확인된 TAG 20개 (V01~V15, PT01~PT07, TT01, FT01, B01~B03, PI02, ORI 등) |

---

## 실험 순서 (메모리 제약 — 하나씩)

| # | 엔진 | 포트 | Docker 서비스 | GPU | 우선순위 |
|---|------|------|-------------|-----|---------|
| 1 | **PaddleOCR** | 5006 | `paddleocr-api` | CPU | 🟢 먼저 (가벼움) |
| 2 | **Tesseract** | 5008 | `tesseract-api` | CPU | 🟢 먼저 (가벼움) |
| 3 | **EasyOCR** | 5015 | `easyocr-api` | CPU/GPU | 🟡 중간 |
| 4 | **eDOCr2 v2** | 5002 | `edocr2-v2-api` | GPU | 🟡 도면 특화 |
| 5 | **Surya OCR** | 5013 | `surya-ocr-api` | GPU | 🟡 레이아웃 분석 |
| 6 | **DocTR** | 5014 | `doctr-api` | GPU | 🟡 2-stage |
| 7 | **TrOCR** | 5009 | `trocr-api` | GPU | 🔴 마지막 |
| 8 | **로컬 Python** | - | - | - | 🟢 Docker 없이 |

---

## 실험 절차 (각 엔진)

```bash
# 1. 엔진 기동
docker compose up <service> -d
# 2. 헬스체크
curl -s http://localhost:<port>/health
# 3. OCR 실행
curl -F "file=@/tmp/gar-page3.png" http://localhost:<port>/api/v1/ocr
# 4. 결과 저장
# 5. TAG 필터링 (알파벳 시작 패턴)
# 6. GT 대조 (20개 TAG 중 몇 개 검출?)
# 7. 엔진 중지
docker compose stop <service>
```

---

## 평가 지표

| 지표 | 설명 |
|------|------|
| TAG Recall | GT 20개 중 몇 개 검출? |
| TAG Precision | 검출된 것 중 실제 TAG는 몇 개? (치수/노이즈 제외) |
| False Positive | TAG가 아닌데 TAG로 검출된 것 |
| 처리 시간 | 이미지 1장 처리 소요 시간 |

---

## 결과 (2026-03-25)

| Engine | Time | Items | TAGs | Matched | Recall |
|--------|------|-------|------|---------|--------|
| **PaddleOCR** 🏆 | 5.4s | 158 | 26 | **12/28** | **42.9%** |
| Tesseract | 5.8s | 553 | 18 | 6/28 | 21.4% |
| EasyOCR | 6.3s | 260 | 3 | 0/28 | 0.0% |
| DocTR | 6.1s | 391 | 2 | 0/28 | 0.0% |
| eDOCr2 | 3.5s | 84 | 0 | 0/28 | 0.0% |
| Surya | 0.35s | 0 | 0 | 0/28 | 0.0% (모듈 에러) |
| TrOCR | 4.2s | 1 | 0 | 0/28 | 0.0% |

### PaddleOCR 검출 TAG (12개)
B02, FT01, ORI, PI02, PT03, PT05, PT07, TT01, V01, V09, V11, V11-1

### PaddleOCR 미검출 TAG (16개)
B01, B03, PI01, PT01, PT04, PT06, V02, V03, V04, V05, V06, V07, V08, V11-2, V14, V15

### 분석
- **PaddleOCR**가 압도적 1위 (42.9%). 도면 내 작은 텍스트도 비교적 잘 인식
- **Tesseract**가 2위 (21.4%)이지만 노이즈가 많음 (553개 중 대부분 무의미)
- **EasyOCR**: 한국어 모드 기본 → 영어 TAG 인식 저조
- **eDOCr2**: 치수 전문 OCR라 TAG 인식에 부적합
- **Surya/TrOCR/DocTR**: 이 이미지에서는 거의 동작 안 함
- **42.9%는 전체 이미지 1장 기준** → 뷰별 분리(S02)로 향상 가능성 있음
- 로컬 PaddleOCR은 paddle 미설치로 테스트 불가 (Docker API로 대체)

## 완료 조건

- [x] 최소 4개 엔진 벤치마크 완료 (7개 완료)
- [ ] ~~TAG Recall 70% 이상인 엔진 1개 이상 확인~~ → 최대 42.9%, 뷰 분리(S02)로 개선 필요
- [x] 결과를 비교 표로 정리
- [x] ~~로컬 Python vs Docker~~ paddle 미설치, Docker API로 통일
