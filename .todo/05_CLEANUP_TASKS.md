# 정리 작업 목록

> 현재 변경사항에서 발견된 정리 필요 항목

---

## 1. 삭제된 파일 정리

### Gateway에서 제거된 파일 (물리적 삭제 필요)
```bash
# 이미 코드에서 제거됨, 파일도 삭제 확인 필요
rm gateway-api/services/pid_overlay_service.py
rm gateway-api/routers/pid_overlay_router.py
rm gateway-api/services/__pycache__/pid_overlay_service.cpython-*.pyc
rm gateway-api/routers/__pycache__/pid_overlay_router.cpython-*.pyc
```

**상태**: ✅ 완료됨 (git status에서 확인)

---

## 2. 파라미터 정리

### eDOCr2 version 파라미터 제거
**파일**: `web-ui/src/config/nodes/ocrNodes.ts`
**변경**: version 파라미터 (v1/v2/ensemble) 제거됨

**확인 필요**:
- [ ] edocr2-api에서도 v1/v2 분기 제거 여부
- [ ] gateway-api/services/ocr_service.py에서 버전 로직 정리
- [ ] API 스펙에서 version 파라미터 제거

```bash
# 확인 명령
grep -r "version.*v1\|version.*v2" gateway-api/
grep -r "version.*v1\|version.*v2" models/edocr2-v2-api/
```

---

## 3. Web-UI 레거시 컴포넌트 정리

### PID Overlay 컴포넌트 검토
**위치**:
- `web-ui/src/components/pid/PIDOverlayViewer.tsx`
- `web-ui/src/pages/pid-overlay/PIDOverlayPage.tsx`

**검토 필요**:
- [ ] Gateway API 대신 PID Composer API 호출로 변경
- [ ] 또는 삭제 후 BlueprintFlow에서만 사용

---

## 4. 모델 레지스트리 동기화

### YOLO 모델 클래스 변경
**파일**: `models/yolo-api/models/model_registry.yaml`
**변경**: pid_symbol 60종 → 32종으로 변경

**확인 필요**:
- [ ] 실제 .pt 모델 파일과 일치 여부
- [ ] Blueprint AI BOM의 CLASS_NAMES와 동기화
- [ ] nodeDefinitions.ts의 model_type 옵션과 일치

```yaml
# 변경된 클래스 목록 확인
pid_symbol:
  classes: 32  # 기존 60
  class_names:
    - Arrowhead
    - Arrowhead + Triangle
    # ... 32개
```

---

## 5. Docker 설정 정리

### 불필요한 환경 변수 정리
**파일**: `docker-compose.yml`, `gateway-api/docker-compose.yml`

```bash
# 사용되지 않는 환경 변수 확인
grep -E "^      - [A-Z_]+=" docker-compose.yml | \
  while read var; do
    name=$(echo "$var" | cut -d'=' -f1 | tr -d ' -')
    grep -q "$name" models/*/api_server.py || echo "Unused: $var"
  done
```

---

## 6. 생성된 임시 파일 정리

### Excel 리포트 파일
**위치**: 프로젝트 루트
```
TECHCROSS_BWMS_Analysis_Report.xlsx
TECHCROSS_BWMS_Analysis_Report_v2.xlsx
```

**처리**:
- [ ] .gitignore에 `*.xlsx` 추가 또는
- [ ] results/ 디렉토리로 이동

---

## 7. 설정 파일 일관성

### Design Checker 설정 구조
**현재**:
```
models/design-checker-api/config/
├── _active.yaml
└── common/           # 신규 생성됨
```

**확인 필요**:
- [ ] common/ 디렉토리 구조 검토
- [ ] _active.yaml 포맷 확인
- [ ] 다른 API에도 동일 패턴 적용 여부

---

## 8. 테스트 파일 정리

### 신규 생성된 테스트
**위치**: `models/pid-composer-api/tests/`

**확인 필요**:
- [ ] pytest.ini 설정 확인
- [ ] CI/CD 파이프라인에 포함 여부
- [ ] 다른 API와 테스트 구조 일관성

---

## 9. 린트 에러 정리 (기존)

### 현재 린트 상태
```
✖ 24 problems (3 errors, 21 warnings)
```

**에러 파일**:
1. `e2e/hooks/global.setup.ts` - empty object pattern
2. `e2e/ui/workflow.spec.ts` - unused variables
3. `src/components/dashboard/ContainerManager.tsx` - unused _err

**작업 항목**:
- [ ] 3개 에러 수정
- [ ] 21개 경고 검토 (unused variables → prefix with _)

---

## 10. 문서 업데이트

### CLAUDE.md 추가 업데이트 필요
- [ ] API 서비스 테이블 정렬 확인
- [ ] 포트 번호 중복 없는지 확인
- [ ] 버전 히스토리에 PID Composer 추가 기록

### API 스펙 문서
- [ ] gateway-api/api_specs/CONVENTIONS.md 업데이트
- [ ] 새 API 추가 섹션에 체크리스트 링크

---

## 우선순위 정리

| 작업 | 우선순위 | 예상 시간 |
|------|----------|-----------|
| PID 컴포넌트 API 호출 수정 | P0 | 1시간 |
| eDOCr2 version 파라미터 정리 | P1 | 0.5시간 |
| 린트 에러 수정 | P1 | 0.5시간 |
| 모델 레지스트리 동기화 확인 | P1 | 1시간 |
| Excel 파일 정리 | P2 | 0.1시간 |
| 문서 업데이트 | P2 | 0.5시간 |
