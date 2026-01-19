# PP-StructureV3: BOM 테이블 OCR 개선

> **상태**: 🔬 검증 (리소스 제약 발견)
> **생성일**: 2026-01-17
> **우선순위**: P2 → P3 (리소스 이슈로 하향)
> **예상 공수**: 3-5일 (+ 별도 인프라 구축 필요)

---

## 배경

### 현재 BOM 테이블 인식 방식

Blueprint AI BOM에서 BOM 테이블 인식은 현재 다음과 같이 처리됨:

```
현재 파이프라인:
이미지 → DocLayout-YOLO (영역 검출) → OCR (텍스트 추출) → 휴리스틱 파싱
```

**문제점**:
1. 테이블 구조 인식 부재 (셀 경계, 행/열 구분 없음)
2. 휴리스틱 기반 파싱의 한계 (다양한 테이블 형식 대응 어려움)
3. 병합 셀, 복잡한 헤더 처리 어려움

### PP-StructureV3란?

PaddleOCR 3.0의 **문서 구조 분석 파이프라인**:
- 2025.05.20 정식 릴리스 (PaddleOCR v3.0)
- 레이아웃 분석 + 테이블 인식 + 공식 인식 + 차트 파싱
- Markdown/JSON 구조화 출력 지원
- 상용 솔루션 대비 벤치마크 우수

**핵심 모델**: SLANeXt (유선/무선 테이블 전용)
- SLANeXt_wired mAP: 69.65%
- 기존 SLANet 대비 "모든 테이블 유형에서 성능 크게 향상"

---

## 핵심 아이디어

### 테이블 전용 파이프라인 추가

```
개선된 파이프라인:
이미지 → DocLayout-YOLO (영역 검출)
              ↓
         ┌────────────────┐
         │  BOM 테이블?   │
         └────────────────┘
              ↓ Yes              ↓ No
    PP-StructureV3          기존 OCR
    (테이블 구조 인식)       (텍스트 추출)
              ↓
    구조화된 BOM 데이터
    (HTML/Markdown)
```

### 기대 출력 예시

**입력**: BOM 테이블 이미지
**출력** (Markdown):

```markdown
| 품번 | 품명 | 규격 | 수량 | 재질 | 비고 |
|------|------|------|------|------|------|
| 1 | SHAFT | Ø50x200 | 1 | SUS304 | - |
| 2 | BEARING | 6205 | 2 | - | NSK |
| 3 | HOUSING | - | 1 | AL6061 | 가공 |
```

---

## 예상 효과

### 정량적

| 지표 | 현재 | 개선 후 | 향상 |
|------|------|---------|------|
| 테이블 구조 인식률 | ~60% | **90%+** | +30%p |
| 복잡 테이블 처리 | 제한적 | **양호** | 신규 기능 |
| 후처리 코드량 | 많음 | **적음** | -50% |
| BOM 파싱 정확도 | 중 | **상** | +20%p |

### 정성적

- **구조화된 출력**: 행/열/셀 단위 데이터 접근
- **다양한 형식 대응**: 병합 셀, 복잡 헤더 지원
- **표준 포맷**: HTML/Markdown 출력으로 후처리 간소화
- **확장성**: 차트, 공식 인식 기능 활용 가능

---

## 구현 방안

### Phase 1: 환경 구축 및 테스트 (1일)

#### 1.1 PP-StructureV3 설치

```bash
# PaddleOCR 3.0+ 필요
pip install paddleocr>=3.0.0

# 테스트 실행
paddleocr pp_structurev3 -i ./samples/bom_table.png
```

#### 1.2 기본 테스트

```python
from paddleocr import PPStructureV3

pipeline = PPStructureV3()

# BOM 테이블 이미지 테스트
result = pipeline.predict("./samples/bom_table.png")

# Markdown 출력
for item in result:
    if item.get("type") == "table":
        print(item.get("res", {}).get("markdown"))
```

### Phase 2: 서비스 모듈 개발 (2일)

#### 2.1 테이블 인식 서비스

```python
# blueprint-ai-bom/backend/services/table_recognizer.py (신규)

from paddleocr import PPStructureV3
from typing import List, Dict, Any

class TableRecognizer:
    """PP-StructureV3 기반 테이블 인식"""

    def __init__(self):
        self.pipeline = PPStructureV3(
            table_model_name="SLANeXt_wired",  # 유선 테이블 최적화
            show_log=False,
        )

    def recognize(self, image_path: str) -> List[Dict[str, Any]]:
        """테이블 인식 및 구조화"""
        result = self.pipeline.predict(image_path)

        tables = []
        for item in result:
            if item.get("type") == "table":
                tables.append({
                    "bbox": item.get("bbox"),
                    "html": item.get("res", {}).get("html"),
                    "markdown": item.get("res", {}).get("markdown"),
                    "cells": self._parse_cells(item),
                })

        return tables

    def _parse_cells(self, table_item) -> List[Dict]:
        """셀 단위 파싱"""
        # HTML 파싱하여 셀 데이터 추출
        pass
```

#### 2.2 BOM 파서 연동

```python
# services/bom_extractor.py 수정

from services.table_recognizer import TableRecognizer

class BOMExtractor:
    def __init__(self):
        self.table_recognizer = TableRecognizer()
        self.layout_analyzer = get_layout_analyzer()

    def extract_bom(self, image_path: str) -> Dict:
        # 1. 레이아웃 분석
        regions = self.layout_analyzer.detect(image_path)

        # 2. BOM 테이블 영역 추출
        bom_regions = [r for r in regions if r.region_type == "BOM_TABLE"]

        # 3. PP-StructureV3로 테이블 인식
        bom_data = []
        for region in bom_regions:
            cropped = crop_region(image_path, region.bbox)
            tables = self.table_recognizer.recognize(cropped)
            bom_data.extend(tables)

        return {"bom_tables": bom_data}
```

### Phase 3: 통합 및 테스트 (1-2일)

- [ ] 기존 BOM 추출 로직과 통합
- [ ] 다양한 BOM 형식 테스트 (TECHCROSS, 일반)
- [ ] 성능 벤치마크 (속도, 정확도)
- [ ] 에러 케이스 처리

---

## 리스크 & 대안

### 리스크

| 리스크 | 영향 | 확률 | 대응 | 검증 결과 |
|--------|------|------|------|-----------|
| 도면 BOM 형식 불일치 | 중 | 중 | Fine-tuning 검토 | 미검증 |
| GPU 메모리 추가 사용 | **높** | **높** | ~~기존 PaddleOCR와 공유~~ **별도 컨테이너 필요** | ⚠️ 실제 발생 |
| 처리 속도 저하 | 낮 | 중 | 테이블 영역만 선택적 적용 | 미검증 |
| 한글 테이블 인식 | 중 | 중 | 한국어 모델 사용 | 미검증 |

### 대안

1. **Plan B: 기존 방식 개선**
   - 휴리스틱 파싱 강화
   - 장점: 추가 모델 불필요
   - 단점: 한계 명확

2. **Plan C: TableTransformer 사용**
   - Microsoft TableTransformer
   - 장점: 학술적 검증
   - 단점: PaddleOCR보다 무거움

3. **Plan D: VLM 테이블 추출**
   - GPT-4o / Claude Vision 활용
   - 장점: 높은 정확도
   - 단점: API 비용, 속도

---

## 검증 계획

### 테스트 데이터셋

| 유형 | 수량 | 소스 |
|------|------|------|
| TECHCROSS BOM | 20장 | 기존 샘플 |
| 일반 기계도면 BOM | 20장 | 공개 데이터 |
| 복잡 병합 테이블 | 10장 | 수동 수집 |

### 평가 지표

1. **테이블 검출률**: 테이블 영역 정확 검출 비율
2. **구조 인식률**: 행/열 구조 정확 인식 비율
3. **셀 텍스트 정확도**: 개별 셀 텍스트 일치율
4. **처리 속도**: 테이블당 평균 처리 시간

---

## 검증 결과 (2026-01-17)

### 테스트 환경

| 항목 | 값 |
|------|-----|
| PaddleOCR 버전 | 3.3.1 |
| 컨테이너 | paddleocr-api (Docker) |
| GPU | RTX 3080 (8GB VRAM) |
| RAM | 15.51 GiB (컨테이너 제한) |

### 테스트 결과

| 단계 | 상태 | 비고 |
|------|------|------|
| Import | ✅ 성공 | `from paddleocr import PPStructureV3` |
| 추가 의존성 설치 | ✅ 성공 | `pip install "paddlex[ocr]"` 필요 |
| 모델 로딩 | ✅ 성공 | 12개+ 서브 모델 다운로드 |
| 이미지 추론 | ❌ OOM | 메모리 부족으로 프로세스 종료 |

### 로드된 서브 모델 (12개+)

```
PP-LCNet_x1_0_doc_ori        # 문서 방향 분류
UVDoc                        # 문서 보정
PP-DocBlockLayout            # 블록 레이아웃
PP-DocLayout_plus-L          # 레이아웃 분석
PP-LCNet_x1_0_textline_ori   # 텍스트라인 방향
PP-OCRv5_server_det          # 텍스트 검출
PP-OCRv5_server_rec          # 텍스트 인식
PP-LCNet_x1_0_table_cls      # 테이블 분류
SLANeXt_wired                # 유선 테이블 구조
SLANet_plus                  # 무선 테이블 구조
RT-DETR-L_wired_table_cell   # 유선 셀 검출
RT-DETR-L_wireless_table_cell # 무선 셀 검출
PP-FormulaNet_plus-L         # 수식 인식
PP-Chart2Table               # 차트 → 테이블 변환
```

### 메모리 이슈 분석

PP-StructureV3는 **12개 이상의 서브 모델**을 동시에 로드하여 메모리 사용량이 매우 높음:
- 예상 GPU VRAM: 6-8GB
- 예상 시스템 RAM: 8GB+
- 현재 컨테이너에서 기존 PaddleOCR 서비스와 충돌

### 결론 및 권장사항

1. **별도 컨테이너 필요**: 기존 PaddleOCR 컨테이너와 분리 운영
2. **GPU 메모리 확보**: 최소 8GB VRAM 권장 (단독 사용)
3. **선택적 모델 로딩**: 테이블 인식만 필요시 서브셋 로딩 검토
4. **대안 검토**: 리소스 제약 시 Plan C (TableTransformer) 또는 Plan D (VLM) 고려

---

## 다음 단계

### 즉시 실행 가능

- [x] PP-StructureV3 로컬 테스트 환경 구축 (완료)
- [x] 기존 BOM 샘플 이미지로 기본 테스트 (메모리 부족으로 실패)
- [x] 테스트 결과 기록 및 평가 (완료)

### 검증 완료 후

- [ ] `table_recognizer.py` 서비스 모듈 개발
- [ ] BOM 추출 파이프라인 통합
- [ ] main/ 으로 승격 및 본격 구현

---

## 참조

- [PP-StructureV3 공식 문서](http://www.paddleocr.ai/main/en/version3.x/pipeline_usage/PP-StructureV3.html)
- [PaddleOCR GitHub](https://github.com/PaddlePaddle/PaddleOCR)
- [PaddleOCR 3.0 Technical Report](https://arxiv.org/html/2507.05595v1)
- DocLayout-YOLO 통합: `idea-thinking/main/001_doclayout_yolo_integration.md`
- 현재 PaddleOCR 구현: `models/paddleocr-api/`

---

*작성자*: Claude Code (Opus 4.5)
*최종 업데이트*: 2026-01-17
