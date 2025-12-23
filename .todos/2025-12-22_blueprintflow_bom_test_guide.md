# BlueprintFlow에서 Blueprint AI BOM 테스트 가이드

> 작성일: 2025-12-22
> 목적: BlueprintFlow 빌더에서 Blueprint AI BOM 워크플로우 구성 및 테스트

## 접속 URL

| 서비스 | URL | 설명 |
|--------|-----|------|
| BlueprintFlow Builder | http://localhost:5173/blueprintflow/builder | 워크플로우 빌더 |
| Blueprint AI BOM UI | http://localhost:3000 | Human-in-the-Loop 검증 UI |
| Blueprint AI BOM API | http://localhost:5020 | 백엔드 API |

---

## Step 1: BlueprintFlow 빌더 접속

1. 브라우저에서 열기:
   ```
   http://localhost:5173/blueprintflow/builder
   ```

2. 좌측 노드 팔레트에서 카테고리 확인:
   - **Input**: ImageInput
   - **Detection**: YOLO
   - **Analysis**: Blueprint AI BOM

---

## Step 2: 워크플로우 구성

### 기본 파이프라인 구조
```
┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐
│ ImageInput  │────▶│    YOLO     │────▶│  Blueprint AI BOM   │
│             │     │ (Detection) │     │ (Human-in-the-Loop) │
└─────────────┘     └─────────────┘     └─────────────────────┘
```

### 노드 추가 순서

1. **ImageInput 노드** 추가
   - 좌측 팔레트에서 "Input" → "ImageInput" 드래그
   - 테스트 이미지 경로 설정 또는 업로드

2. **YOLO 노드** 추가
   - "Detection" → "YOLO" 드래그
   - 권장 설정:
     - confidence: 0.4
     - model_type: bom_detector
   - ImageInput → YOLO 연결

3. **Blueprint AI BOM 노드** 추가
   - "Analysis" → "Blueprint AI BOM" 드래그
   - YOLO → Blueprint AI BOM 연결
   - **interactiveMode**: Human-in-the-Loop UI 자동 연동

---

## Step 3: 워크플로우 실행

1. 상단의 **"실행"** 버튼 클릭
2. 파이프라인 순차 실행:
   - ImageInput: 이미지 로드
   - YOLO: 심볼 검출
   - Blueprint AI BOM: 세션 생성 → UI에서 검증

---

## Step 4: Blueprint AI BOM UI에서 검증

### 4.1 접속
워크플로우 실행 후 자동으로 열리거나 직접 접속:
```
http://localhost:3000
```

### 4.2 치수-객체 관계 섹션 찾기
1. 좌측에서 세션 선택
2. 페이지 스크롤하여 **"🔗 치수-객체 관계"** 섹션 이동

### 4.3 수동 연결 테스트
1. 관계 항목 클릭하여 확장 (예: "100mm → 없음")
2. **"수동 연결"** 버튼 클릭
3. 드롭다운에서 심볼 선택 (예: "PT")
4. 결과 확인:
   - 연결 상태: 100mm → PT
   - 신뢰도: 100%
   - 방법: 수동

### 4.4 삭제 테스트
1. 관계 항목 확장
2. **"삭제"** 버튼 (빨간색) 클릭
3. 확인 대화 상자에서 "확인"
4. 목록에서 제거 확인

### 4.5 관계 재추출
- 상단 **"관계 재추출"** 버튼으로 전체 재추출 가능

---

## Step 5: BOM 생성 및 내보내기

1. 심볼 검증 완료 후 **"검증 완료"** 버튼 클릭
2. BOM 자동 생성
3. 내보내기 형식 선택:
   - Excel (.xlsx)
   - PDF
   - JSON
   - CSV

---

## 테스트 시나리오

### 시나리오 1: 기본 워크플로우
1. ImageInput → YOLO → Blueprint AI BOM 구성
2. 워크플로우 실행
3. BOM UI에서 검증 수행
4. BOM 내보내기

### 시나리오 2: 관계 기능 테스트
1. 세션 생성 (워크플로우 실행 또는 직접 업로드)
2. 치수 OCR 실행 (치수가 없으면 수동 추가)
3. 관계 추출 실행
4. 수동 연결 테스트
5. 삭제 테스트
6. 재추출 테스트

---

## 문제 해결

### 노드가 보이지 않는 경우
```bash
# API 스펙 확인
curl http://localhost:8000/api/v1/specs/blueprint-ai-bom

# Gateway 재시작
cd /home/uproot/ax/poc/gateway-api
docker-compose restart gateway-api
```

### BOM UI가 열리지 않는 경우
```bash
# 컨테이너 상태 확인
docker ps | grep blueprint-ai-bom

# 로그 확인
docker logs blueprint-ai-bom-frontend
docker logs blueprint-ai-bom-backend
```

### 관계가 추출되지 않는 경우
1. 치수가 있는지 확인 (치수 OCR 실행 또는 수동 추가)
2. 검출 결과가 있는지 확인 (YOLO 실행)
3. API 직접 호출로 테스트:
   ```bash
   curl -X POST http://localhost:5020/relations/extract/{session_id}
   ```

---

## 관련 문서

- `.todos/2025-12-22_blueprint_ai_bom_relation_feature.md` - 관계 기능 구현 상세
- `.todos/2025-12-19_blueprint_ai_bom_implementation_guide.md` - 전체 구현 가이드
- `gateway-api/api_specs/blueprint-ai-bom.yaml` - API 스펙
