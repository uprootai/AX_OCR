# 진행 중인 작업

> **마지막 업데이트**: 2026-02-02
> **기준 커밋**: 6386618 (feat: eDOCr2 버그 수정, Table Detector 멀티크롭, dimension_service 멀티 엔진, Excel Export 제거)

---

## 미커밋 변경 요약 (6386618 대비)

> eDOCr2 크롭 업스케일 + BOM 치수 임포트 버그 수정 + DimensionOverlay 스케일링 수정

### 변경 카테고리

| 영역 | 수정 | 신규 | 핵심 변경 |
|------|------|------|----------|
| **Gateway API** | 3개 | 1개 | eDOCr2 크롭 업스케일, dimension_updater_executor 신규 |
| **BOM Backend** | 1개 | 0 | dimension_router.py bbox/location 매핑 수정 |
| **BOM Frontend** | 1개 | 0 | DimensionOverlay.tsx viewBox 스케일링 수정 |
| **Web-UI** | 4개 | 0 | eDOCr2 파라미터, DSE 1-1 템플릿, nodeDefinitions 테스트 수정 |
| **Docker** | 2개 | 0 | table-detector-api Dockerfile/requirements 수정 |
| **문서** | 2개 | 0 | CLAUDE.md + ACTIVE.md 갱신 |

---

## 핵심 변경 상세

### 1. eDOCr2 크롭 업스케일 (ESRGAN 2x)

**목표**: 전체 이미지(3306×2339) 대신 4분할 크롭 → ESRGAN 2x 업스케일 → OCR 수행하여 치수 인식 정확도 향상

**결과**: 정확도 28% → 82% (오탐 36→22, 정탐률 대폭 향상)

#### 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `gateway-api/blueprintflow/executors/image_utils.py` | `crop_image_region()`, `upscale_via_esrgan()` 유틸 추가 (439→498줄) |
| `gateway-api/blueprintflow/executors/edocr2_executor.py` | 크롭+업스케일+좌표변환+중복제거+오탐필터 (131→438줄) |
| `gateway-api/api_specs/edocr2.yaml` | 파라미터 4개 + 프로필 1개 추가 |
| `web-ui/src/config/nodes/ocrNodes.ts` | eDOCr2 노드 파라미터 4개 + 프로필 1개 추가 |
| `web-ui/src/pages/blueprintflow/BlueprintFlowTemplates.tsx` | DSE 1-1 템플릿에 crop upscale 활성화 |

#### 핵심 설계

- **DIMENSION_CROP_PRESETS**: 4분할 (Q1~Q4), 15-20% 오버랩
- **asyncio.gather**: 4개 크롭 동시 처리 (ESRGAN + eDOCr2)
- **좌표 변환**: `원본 = 오프셋 + (업스케일 좌표 / scale)`, nested list + flat 둘 다 지원
- **중복 제거**: 텍스트 일치 + IoU > 0.3 OR 중심점 거리 < 100px
- **오탐 필터**: 길이, 숫자 존재, 특수문자 비율, 숫자 비율 4개 규칙
- **graceful fallback**: ESRGAN 실패 시 원본 크롭으로 OCR (기능 중단 없음)

#### 새 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `enable_crop_upscale` | boolean | false | 크롭+업스케일 활성화 |
| `crop_preset` | select | quadrants | 크롭 프리셋 |
| `upscale_scale` | select | "2" | ESRGAN 배율 (2 권장, 4는 OOM 위험) |
| `upscale_denoise` | number | 0.3 | 노이즈 제거 강도 |

### 2. dimension_updater_executor (신규)

**파일**: `gateway-api/blueprintflow/executors/dimension_updater_executor.py` (신규)

### 3. BOM dimension_router.py 버그 수정 3건

**파일**: `blueprint-ai-bom/backend/routers/analysis/dimension_router.py`

| 버그 | 수정 |
|------|------|
| `dim_data.get("bbox", {})` → eDOCr2는 `"location"` 사용 | `dim_data.get("bbox") or dim_data.get("location", {})` |
| nested list `[[x1,y1],[x2,y2],...]` 미지원 | min/max 변환 추가 |
| confidence 기본값 0.5 고정 | `dim_data.get("confidence", dim_data.get("score", 0.5))` |

### 4. DimensionOverlay.tsx viewBox 스케일링 수정

**파일**: `blueprint-ai-bom/frontend/src/components/DimensionOverlay.tsx`

**문제**: SVG viewBox(3306×2339)가 ~668px 컨테이너에 렌더링되어 strokeWidth/fontSize가 서브픽셀(0.3px, 1.8px)로 축소 → bbox 보이지 않음

**수정**:
- `scale` 상태로 viewBox↔렌더링 비율 계산
- `px()` 헬퍼로 화면 픽셀을 SVG 단위 변환
- strokeWidth `px(2)`, fontSize `px(11)` → 항상 화면에 2px/11px 렌더링
- 텍스트에 흰색 외곽선(`stroke="white"`, `paintOrder="stroke"`) 추가
- `onLoad` + `resize` 이벤트로 스케일 재계산

### 5. nodeDefinitions 테스트 수정

**파일**: `web-ui/src/config/nodeDefinitions.test.ts`

- 총 노드 수 34 → 35 (dimension_updater 추가)
- analysis 카테고리 13 → 14

---

## 프로젝트 상태

| 항목 | 결과 |
|------|------|
| **web-ui 빌드** | ✅ 정상 |
| **web-ui 테스트** | ✅ 67/67 통과 |
| **Python 문법** | ✅ 정상 |
| **DSE 1-1 크롭 업스케일** | ✅ 22개 치수 검출, 정확도 ~82% |
| **BOM 치수 임포트** | ✅ bbox 좌표 정확 (nested list → dict 변환) |
| **DimensionOverlay** | ✅ bbox + 텍스트 라벨 도면 위 표시 |
| **bbox 클릭 → 카드 선택** | ✅ 작동 |
| **크롭 썸네일 HITL 카드** | ✅ 정상 표시 |

---

*마지막 업데이트: 2026-02-02*
