# Blueprint AI BOM Ground Truth 시스템 개선

> 생성일: 2026-01-05
> 관련 파일: blueprint-ai-bom/backend/api_server.py

## 개요

Blueprint AI BOM의 Ground Truth API가 개선되었습니다:
- 업로드된 GT 파일 지원 (기존: 레퍼런스 GT만)
- GT_UPLOAD_DIR 추가
- 파일 우선순위: 업로드 > 레퍼런스

---

## 1. 변경 내용

### 1.1 새 디렉토리 추가

```python
# Reference GT (read-only, from test_drawings)
GT_LABELS_DIR = BASE_DIR / "test_drawings" / "labels"
GT_CLASSES_FILE = BASE_DIR / "test_drawings" / "classes.txt"

# Uploaded GT (writable, for user uploads)
GT_UPLOAD_DIR = BASE_DIR / "uploads" / "gt_labels"
```

### 1.2 새 함수들

```python
def find_gt_label_file(base_name: str) -> Path | None:
    """GT 라벨 파일 찾기 (업로드된 파일 우선, 없으면 레퍼런스 파일)"""
    # 업로드된 GT 먼저 확인
    uploaded_file = GT_UPLOAD_DIR / f"{base_name}.txt"
    if uploaded_file.exists():
        return uploaded_file
    # 레퍼런스 GT 확인
    reference_file = GT_LABELS_DIR / f"{base_name}.txt"
    if reference_file.exists():
        return reference_file
    return None


def load_gt_classes_for_file(label_file: Path) -> list[str]:
    """라벨 파일에 해당하는 클래스 목록 로드"""
    # 업로드된 GT인 경우 uploads의 classes.txt 사용
    if label_file.parent == GT_UPLOAD_DIR:
        classes_file = GT_UPLOAD_DIR / "classes.txt"
        if classes_file.exists():
            with open(classes_file, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
    # 레퍼런스 GT classes
    return load_gt_classes()
```

### 1.3 엔드포인트 수정

**GET /api/ground-truth/{filename}:**
```diff
- label_file = GT_LABELS_DIR / f"{base_name}.txt"
+ label_file = find_gt_label_file(base_name)

- if not label_file.exists():
+ if not label_file:

- classes = load_gt_classes()
+ classes = load_gt_classes_for_file(label_file)
```

**GET /api/ground-truth:**
```diff
+ # 업로드된 GT 먼저 (우선순위 높음)
+ if GT_UPLOAD_DIR.exists():
+     for f in GT_UPLOAD_DIR.iterdir():
+         ...
+         label_files.append({
+             ...
+             "source": "uploaded"  # 소스 표시
+         })
+
+ # 레퍼런스 GT (업로드에 없는 것만)
+ ...
+     label_files.append({
+         ...
+         "source": "reference"
+     })
```

---

## 2. 관련 작업 필요

### 2.1 GT 업로드 엔드포인트

**현재:** GT 파일 조회만 가능
**필요:** GT 파일 업로드 엔드포인트

```python
@app.post("/api/ground-truth/upload")
async def upload_ground_truth(
    file: UploadFile = File(...),
    filename: str = Form(...),
):
    """사용자 정의 GT 라벨 업로드"""
    # GT_UPLOAD_DIR에 저장
    ...
```

**TODO:**
- [x] POST /api/ground-truth/upload 엔드포인트 구현 (기존 존재)
- [x] classes.txt 업로드 지원
- [ ] 기존 파일 덮어쓰기 경고

### 2.2 GT 삭제 엔드포인트

```python
@app.delete("/api/ground-truth/{filename}")
async def delete_ground_truth(filename: str):
    """업로드된 GT 삭제 (레퍼런스는 삭제 불가)"""
    ...
```

**TODO:**
- [x] DELETE 엔드포인트 구현 ✅
- [x] 레퍼런스 파일 보호 ✅

### 2.3 GT_UPLOAD_DIR 디렉토리 생성

**startup에서 디렉토리 생성:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 업로드 디렉토리 생성
    GT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ...
```

**TODO:**
- [ ] lifespan에서 GT_UPLOAD_DIR 생성 확인

---

## 3. 프론트엔드 연동

### 3.1 GTComparisonSection 수정

**현재:** 레퍼런스 GT만 표시
**필요:** 업로드된 GT도 표시, 소스 구분

```typescript
// GT 목록에 source 표시
interface GTLabel {
  filename: string;
  source: 'uploaded' | 'reference';
}
```

**TODO:**
- [x] GT 목록에 source 배지 추가 ✅
- [x] 업로드된 GT 삭제 버튼 추가 ✅

### 3.2 GT 업로드 UI

**필요:**
- [x] 파일 드롭존 또는 업로드 버튼 ✅ (기존 구현됨)
- [ ] classes.txt 함께 업로드 옵션
- [ ] 업로드 진행률 표시

---

## 4. 테스트

### 4.1 기존 테스트 영향

**확인 필요:**
- [ ] `tests/test_techcross_workflow.py` - GT 관련 테스트가 있다면 업데이트

### 4.2 신규 테스트

```python
class TestGroundTruthUpload:
    async def test_upload_gt_label(self):
        """GT 라벨 업로드 테스트"""
        ...

    async def test_uploaded_gt_priority(self):
        """업로드된 GT가 레퍼런스보다 우선하는지"""
        ...

    async def test_delete_uploaded_gt(self):
        """업로드된 GT 삭제 테스트"""
        ...

    async def test_cannot_delete_reference_gt(self):
        """레퍼런스 GT 삭제 불가 테스트"""
        ...
```

---

## 5. Dockerfile/docker-compose

### 5.1 볼륨 마운트

**docker-compose.yml:**
```yaml
blueprint-ai-bom-backend:
  volumes:
    - ./blueprint-ai-bom/backend/uploads:/app/uploads  # GT 업로드용
```

**TODO:**
- [x] uploads 디렉토리가 볼륨 마운트되어 있는지 확인 ✅ (2026-01-17)
- [x] 컨테이너 재시작해도 GT 유지되는지 확인 ✅ (2026-01-17)

**검증 결과:**
- 볼륨: `./blueprint-ai-bom/uploads:/app/uploads` ✅
- 쓰기 권한: 컨테이너에서 파일 생성 가능 ✅
- 데이터 영속성: 호스트에 파일 유지됨 ✅

---

## 6. 다른 API에 적용할 패턴

### 6.1 Design Checker에도 유사 패턴 적용 가능

**사용자 정의 규칙 업로드:**
- 현재: config/ 디렉토리의 YAML만 사용
- 개선: uploads/ 디렉토리에 사용자 규칙 저장

```python
RULES_UPLOAD_DIR = BASE_DIR / "uploads" / "rules"

def find_rule_file(rule_id: str) -> Path | None:
    """규칙 파일 찾기 (업로드 우선)"""
    ...
```

**TODO:**
- [ ] Design Checker에 사용자 규칙 업로드 기능 검토

---

## 7. 우선순위

| 순위 | 작업 | 영향도 | 상태 |
|------|------|--------|------|
| P0 | GT_UPLOAD_DIR 디렉토리 생성 확인 | 기능 | ✅ 완료 |
| P1 | GT 업로드 엔드포인트 구현 | 기능 완성 | ✅ 완료 (기존 존재) |
| P1 | 프론트엔드 source 구분 표시 | UX | ✅ 완료 (2026-01-16) |
| P2 | GT 삭제 엔드포인트 구현 | 관리 | ✅ 완료 (2026-01-16) |
| P2 | 볼륨 마운트 확인 | 데이터 보존 | ✅ 완료 (2026-01-17) |
| P3 | 테스트 추가 | 안정성 | 대기 |

---

## 8. 완료 내역 (2026-01-16)

### 8.1 백엔드 변경

**DELETE /api/ground-truth/{filename} 구현:**
```python
@app.delete("/api/ground-truth/{filename}")
async def delete_ground_truth(filename: str):
    """업로드된 GT 라벨 삭제 (레퍼런스 파일은 삭제 불가)"""
    base_name = Path(filename).stem
    uploaded_file = GT_UPLOAD_DIR / f"{base_name}.txt"

    if not uploaded_file.exists():
        reference_file = GT_LABELS_DIR / f"{base_name}.txt"
        if reference_file.exists():
            raise HTTPException(status_code=403, detail="레퍼런스 GT 파일은 삭제할 수 없습니다.")
        raise HTTPException(status_code=404, detail=f"GT 파일을 찾을 수 없습니다")

    uploaded_file.unlink()
    return {"success": True, "filename": base_name, "message": f"GT 파일 삭제됨"}
```

### 8.2 프론트엔드 변경

**groundTruth.ts:**
- `list()` 반환 타입에 `source: 'uploaded' | 'reference'` 추가
- `delete(filename)` 함수 추가

**GTComparisonSection.tsx:**
- GT 파일 목록 UI 추가 (접기/펼치기 토글)
- Source 배지 표시 (업로드/레퍼런스 구분)
- 업로드된 파일에 삭제 버튼 추가
- 목록에서 GT 파일 직접 선택 기능
