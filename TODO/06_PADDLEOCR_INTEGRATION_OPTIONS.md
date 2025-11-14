# PaddleOCR 통합 옵션

> 작성일: 2025-11-13
> 현재 상태: ✅ 구현 완료, ❌ 미사용
> 우선순위: 🟡 Priority 2

---

## 📊 현재 상태

### PaddleOCR API 현황

**파일**: `paddle-ocr-api/api_server.py`

**구현 상태**: ✅ 완전히 작동
**통합 상태**: ❌ Gateway에서 호출 안 함
**포트**: 5006
**라이브러리**: paddleocr >= 2.7.0

**기능**:
```python
@app.post("/api/v1/ocr")
async def perform_ocr(
    file: UploadFile,
    det_db_thresh: float = 0.3,
    det_db_box_thresh: float = 0.5,
    min_confidence: float = 0.5,
    use_angle_cls: bool = True
):
    """
    PaddleOCR 텍스트 검출 + 인식
    - 텍스트 영역 검출
    - 각도 보정 (선택적)
    - 텍스트 인식
    """
    ocr = PaddleOCR(
        use_angle_cls=use_angle_cls,
        lang="en",
        use_gpu=torch.cuda.is_available()
    )

    result = ocr.ocr(image_path)

    return {
        "text_blocks": [
            {
                "text": text,
                "bbox": bbox,
                "confidence": conf
            }
            for line in result
            for bbox, (text, conf) in line
            if conf >= min_confidence
        ],
        "total_blocks": len(filtered_blocks),
        "processing_time": elapsed
    }
```

---

## 🔍 PaddleOCR vs 다른 OCR

### 성능 비교표

| 특징 | PaddleOCR | Tesseract | eDOCr2 | EasyOCR |
|------|-----------|-----------|--------|---------|
| **정확도 (일반 텍스트)** | 95%+ | 85-90% | ? | 90-95% |
| **정확도 (도면 텍스트)** | 90-95% | 80-85% | **90-95%** | 85-90% |
| **치수 인식** | 중간 | 중간 | **높음** | 중간 |
| **GD&T 기호 인식** | ❌ | ❌ | ✅ | ❌ |
| **속도 (GPU)** | 빠름 (50-200ms) | 중간 | 빠름 | 느림 (1-3s) |
| **속도 (CPU)** | 중간 (500ms-1s) | 빠름 | 중간 | 느림 (5-10s) |
| **딥러닝** | ✅ CRNN | ❌ 전통 | ✅ | ✅ |
| **각도 보정** | ✅ | 제한적 | ✅ | ✅ |
| **다국어 지원** | 80+ 언어 | 100+ 언어 | 제한적 | 80+ 언어 |
| **라이선스** | Apache 2.0 | Apache 2.0 | ? | Apache 2.0 |

**결론**:
- eDOCr2가 도면 특화 OCR이어야 함 (GD&T 기호, 치수 문맥 이해)
- PaddleOCR은 범용 OCR (일반 텍스트는 우수)
- **하지만 eDOCr2가 Mock 상태이므로 PaddleOCR이 대안 가능**

---

## 🎯 통합 옵션

### Option 1: 삭제 (가장 간단)

#### 1.1 근거

- eDOCr2 수리 완료 후 불필요
- Gateway에서 사용 안 함
- 유지보수 비용 발생
- Docker 이미지 크기 증가 (2GB+)

#### 1.2 구현

```bash
# 1. Docker Compose에서 제거
# docker-compose.yml
services:
  # paddle-ocr-api:  # ← 주석 처리
  #   build: ./paddle-ocr-api
  #   ...

# 2. 서비스 중지 및 제거
docker-compose stop paddle-ocr-api
docker-compose rm paddle-ocr-api

# 3. 이미지 삭제 (선택적)
docker rmi paddle-ocr-api:latest

# 4. 디렉토리 보관 (재사용 가능)
mv paddle-ocr-api paddle-ocr-api.backup
```

#### 1.3 장단점

**장점**:
- ✅ 리소스 절약 (메모리, 디스크)
- ✅ 배포 간소화
- ✅ 유지보수 부담 감소

**단점**:
- ⚠️ 재사용 시 재구현 필요
- ⚠️ eDOCr2 실패 시 대안 없음

**추천 시나리오**:
- eDOCr2 수리 완료 후
- 리소스 제약이 있는 환경
- 온프레미스 배포 (최소 구성)

---

### Option 2: eDOCr2 Fallback으로 사용 (추천)

#### 2.1 개요

eDOCr2 실패 시 PaddleOCR로 자동 전환

#### 2.2 구현

**Gateway API 수정**:

```python
async def extract_text_with_fallback(image_path: str):
    """
    eDOCr2 → PaddleOCR Fallback 체인
    """

    # 1차 시도: eDOCr2 (도면 특화)
    try:
        response = requests.post(
            f"{EDOCR2_API_URL}/api/v1/ocr",
            files={"file": open(image_path, "rb")},
            timeout=30
        )
        response.raise_for_status()
        result = response.json()

        # Mock 데이터 체크
        if result.get("dimensions") or result.get("gdt"):
            print("✅ Using eDOCr2 results")
            return result, "edocr2"
        else:
            print("⚠️ eDOCr2 returned empty, trying PaddleOCR...")
            raise ValueError("eDOCr2 returned empty results")

    except Exception as e:
        print(f"⚠️ eDOCr2 failed: {e}, falling back to PaddleOCR")

    # 2차 시도: PaddleOCR (범용 텍스트)
    try:
        response = requests.post(
            f"{PADDLE_OCR_API_URL}/api/v1/ocr",
            files={"file": open(image_path, "rb")},
            data={
                "det_db_thresh": 0.3,
                "min_confidence": 0.6,
                "use_angle_cls": True
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json()

        # PaddleOCR 결과를 eDOCr2 포맷으로 변환
        converted_result = convert_paddle_to_edocr_format(result)

        print("✅ Using PaddleOCR results (fallback)")
        return converted_result, "paddleocr"

    except Exception as e:
        print(f"❌ Both eDOCr2 and PaddleOCR failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="All OCR services failed"
        )

def convert_paddle_to_edocr_format(paddle_result: Dict) -> Dict:
    """
    PaddleOCR 결과를 eDOCr2 포맷으로 변환
    """
    text_blocks = paddle_result.get("text_blocks", [])

    # 치수 패턴 매칭 (간단한 휴리스틱)
    dimension_pattern = re.compile(r'\d+\.?\d*\s*[xX×]\s*\d+\.?\d*|\d+\.?\d*\s*mm|\d+\.?\d*\s*°|Ø\s*\d+\.?\d*')

    dimensions = []
    general_text = []

    for block in text_blocks:
        text = block["text"]
        if dimension_pattern.search(text):
            dimensions.append({
                "value": text,
                "bbox": block["bbox"],
                "confidence": block["confidence"]
            })
        else:
            general_text.append(block)

    return {
        "dimensions": dimensions,  # 불완전하지만 빈 배열보다 나음
        "gdt": [],  # PaddleOCR은 GD&T 기호 인식 안 됨
        "text_blocks": general_text,
        "tables": [],
        "processing_time": paddle_result["processing_time"],
        "source": "paddleocr"  # 출처 명시
    }
```

#### 2.3 장단점

**장점**:
- ✅ eDOCr2 실패 시 자동 복구
- ✅ 일반 텍스트는 잘 인식
- ✅ 시스템 가용성 향상
- ✅ 기존 구현 재사용

**단점**:
- ⚠️ GD&T 기호 인식 안 됨
- ⚠️ 치수 맥락 이해 제한적
- ⚠️ 변환 로직 복잡도 증가

**추천 시나리오**:
- eDOCr2 수리 중 (임시 대안)
- 고가용성 요구 환경
- 다양한 도면 포맷 처리

---

### Option 3: 앙상블에 추가 (고급)

#### 3.1 개요

eDOCr2 + PaddleOCR 결과를 병합하여 정확도 향상

#### 3.2 구현

```python
async def ensemble_ocr(image_path: str):
    """
    eDOCr2 + PaddleOCR 앙상블
    """

    # 병렬 실행
    edocr2_task = asyncio.create_task(call_edocr2(image_path))
    paddle_task = asyncio.create_task(call_paddleocr(image_path))

    try:
        edocr2_result, paddle_result = await asyncio.gather(
            edocr2_task,
            paddle_task,
            return_exceptions=True
        )
    except Exception as e:
        print(f"⚠️ Ensemble OCR failed: {e}")
        raise

    # 결과 병합
    merged_result = merge_ocr_results(edocr2_result, paddle_result)

    return merged_result

def merge_ocr_results(edocr2: Dict, paddle: Dict) -> Dict:
    """
    두 OCR 결과를 병합

    전략:
    1. 치수/GD&T: eDOCr2 우선 (도면 특화)
    2. 일반 텍스트: PaddleOCR 우선 (범용 텍스트)
    3. 중복 제거: NMS (Non-Maximum Suppression)
    """

    # 1. 치수/GD&T는 eDOCr2 사용
    dimensions = edocr2.get("dimensions", [])
    gdt = edocr2.get("gdt", [])

    # 2. 텍스트 블록 병합
    edocr2_text = edocr2.get("text_blocks", [])
    paddle_text = paddle.get("text_blocks", [])

    # 3. NMS로 중복 제거
    all_text_blocks = edocr2_text + paddle_text
    deduplicated_text = non_max_suppression_text(all_text_blocks, iou_threshold=0.5)

    # 4. 신뢰도 기반 선택
    final_text_blocks = []
    for block in deduplicated_text:
        # eDOCr2와 PaddleOCR 모두 검출한 경우 신뢰도 비교
        if block["source"] == "both":
            if block["edocr2_conf"] > block["paddle_conf"]:
                final_text_blocks.append({**block, "text": block["edocr2_text"]})
            else:
                final_text_blocks.append({**block, "text": block["paddle_text"]})
        else:
            final_text_blocks.append(block)

    return {
        "dimensions": dimensions,  # eDOCr2
        "gdt": gdt,  # eDOCr2
        "text_blocks": final_text_blocks,  # Merged
        "tables": edocr2.get("tables", []),  # eDOCr2
        "processing_time": max(edocr2["processing_time"], paddle["processing_time"]),
        "sources": ["edocr2", "paddleocr"]
    }

def non_max_suppression_text(text_blocks: List[Dict], iou_threshold: float = 0.5) -> List[Dict]:
    """
    텍스트 블록에 NMS 적용하여 중복 제거
    """
    if not text_blocks:
        return []

    # IoU 계산
    def compute_iou(box1, box2):
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])

        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0

    # 신뢰도 순으로 정렬
    sorted_blocks = sorted(text_blocks, key=lambda x: x.get("confidence", 0), reverse=True)

    keep = []
    for block in sorted_blocks:
        should_keep = True
        for kept_block in keep:
            iou = compute_iou(block["bbox"], kept_block["bbox"])
            if iou > iou_threshold:
                should_keep = False
                # 중복 발견 - 둘 다 보관 (앙상블용)
                kept_block["source"] = "both"
                kept_block["edocr2_text"] = kept_block.get("text", "")
                kept_block["paddle_text"] = block.get("text", "")
                kept_block["edocr2_conf"] = kept_block.get("confidence", 0)
                kept_block["paddle_conf"] = block.get("confidence", 0)
                break

        if should_keep:
            keep.append(block)

    return keep
```

#### 3.3 장단점

**장점**:
- ✅ 정확도 향상 (+5-10%)
- ✅ 누락 감소 (Recall 증가)
- ✅ 신뢰도 검증
- ✅ 로버스트성 증가

**단점**:
- ⚠️ 복잡도 증가
- ⚠️ 처리 시간 증가 (병렬 실행 필요)
- ⚠️ 병합 로직 개발 필요
- ⚠️ 디버깅 어려움

**추천 시나리오**:
- 최고 정확도 요구 환경
- 실시간성 덜 중요
- eDOCr2 수리 후 추가 개선

---

### Option 4: 텍스트 영역만 담당 (역할 분리)

#### 4.1 개요

- **eDOCr2**: 치수, GD&T 기호 (도면 특화)
- **PaddleOCR**: 타이틀 블록, 주석, 노트 (일반 텍스트)

#### 4.2 구현

```python
async def process_drawing_with_role_separation(image_path: str):
    """
    역할 분리 전략
    """

    # 1. YOLO로 영역 분할
    yolo_result = await call_yolo(image_path)
    detections = yolo_result["detections"]

    # 2. 영역별 OCR 할당
    dimension_regions = [d for d in detections if d["class_name"] in [
        "diameter_dim", "linear_dim", "radius_dim", "angular_dim",
        "chamfer_dim", "tolerance_dim", "reference_dim"
    ]]

    gdt_regions = [d for d in detections if d["class_name"] in [
        "flatness", "cylindricity", "position", "perpendicularity", "parallelism"
    ]]

    text_regions = [d for d in detections if d["class_name"] == "unclassified_text"]

    # 3. eDOCr2로 치수/GD&T 처리
    edocr2_tasks = []
    for region in dimension_regions + gdt_regions:
        cropped_image = crop_image(image_path, region["bbox"])
        edocr2_tasks.append(call_edocr2(cropped_image))

    # 4. PaddleOCR로 텍스트 영역 처리
    paddle_tasks = []
    for region in text_regions:
        cropped_image = crop_image(image_path, region["bbox"])
        paddle_tasks.append(call_paddleocr(cropped_image))

    # 5. 병렬 실행
    edocr2_results, paddle_results = await asyncio.gather(
        asyncio.gather(*edocr2_tasks),
        asyncio.gather(*paddle_tasks)
    )

    # 6. 결과 통합
    return {
        "dimensions": [r["dimensions"] for r in edocr2_results if "dimensions" in r],
        "gdt": [r["gdt"] for r in edocr2_results if "gdt" in r],
        "text_blocks": [r["text_blocks"] for r in paddle_results],
        "processing_time": max(...)
    }
```

#### 4.3 장단점

**장점**:
- ✅ 각 OCR의 장점 활용
- ✅ 명확한 역할 분리
- ✅ 병렬 처리 가능
- ✅ 정확도 향상

**단점**:
- ⚠️ 구현 복잡도 높음
- ⚠️ YOLO 의존성 증가
- ⚠️ 이미지 크롭 오버헤드

**추천 시나리오**:
- 고성능 요구 환경
- GPU 리소스 충분
- 복잡한 도면 처리

---

## 📊 옵션 비교

| 옵션 | 구현 난이도 | 정확도 | 속도 | 리소스 | 추천도 |
|------|------------|--------|------|--------|--------|
| **삭제** | ⭐ (쉬움) | N/A | N/A | 절약 | ⭐⭐⭐ (eDOCr2 수리 후) |
| **Fallback** | ⭐⭐ (중간) | 80% | 빠름 | 유지 | ⭐⭐⭐⭐⭐ (현재) |
| **앙상블** | ⭐⭐⭐⭐ (어려움) | 90%+ | 느림 | 유지 | ⭐⭐⭐⭐ (장기) |
| **역할 분리** | ⭐⭐⭐⭐⭐ (매우 어려움) | 90%+ | 중간 | 유지 | ⭐⭐⭐ (고급) |

---

## 🎯 최종 권장 사항

### 단계별 접근

#### Phase 1: 현재 (eDOCr2 수리 전)
**Option 2: Fallback 구현**
- eDOCr2 실패 시 PaddleOCR 자동 전환
- 시스템 가용성 확보
- 구현 시간: 4-6시간

#### Phase 2: eDOCr2 수리 완료 후
**Option A: 유지 (Fallback)**
- 고가용성 유지
- 추가 비용: 메모리 2GB, 디스크 5GB

**Option B: 삭제**
- 리소스 절약
- 최소 구성 배포

#### Phase 3: 장기 개선 (선택적)
**Option 3: 앙상블**
- 정확도 최대화
- 실시간성 덜 중요한 환경
- 구현 시간: 2-3일

---

## 📝 구현 체크리스트

### Phase 1: Fallback 구현 (추천)

- [ ] Gateway API 수정
  - [ ] `extract_text_with_fallback()` 함수 추가
  - [ ] `convert_paddle_to_edocr_format()` 함수 추가
  - [ ] 에러 핸들링 강화

- [ ] 테스트
  - [ ] eDOCr2 정상 작동 시 테스트
  - [ ] eDOCr2 실패 시 Fallback 테스트
  - [ ] 변환 로직 검증

- [ ] 문서화
  - [ ] API 문서 업데이트 (Swagger)
  - [ ] Fallback 동작 설명
  - [ ] 성능 영향 기록

**예상 소요**: 4-6시간

### Phase 2: 삭제 (eDOCr2 수리 후)

- [ ] 의존성 검증
  - [ ] Gateway 사용 여부 확인
  - [ ] 다른 서비스 연결 확인

- [ ] 제거
  - [ ] docker-compose.yml 수정
  - [ ] 서비스 중지 및 삭제
  - [ ] 백업 (재사용 가능하게)

- [ ] 검증
  - [ ] 전체 파이프라인 테스트
  - [ ] 리소스 사용량 확인

**예상 소요**: 1-2시간

---

**관련 문서**:
- `01_CURRENT_STATUS_OVERVIEW.md`: 전체 시스템 현황
- `02_EDOCR2_INTEGRATION_PLAN.md`: eDOCr2 수리 계획
- `07_ALTERNATIVE_MODELS_RESEARCH.md`: OCR 대안 조사
