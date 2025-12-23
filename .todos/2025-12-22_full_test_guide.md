# Blueprint AI BOM 전체 테스트 가이드

> 작성일: 2025-12-22
> 대상: 마지막 커밋 (0d78e4a) 이후 변경 사항

---

## 주요 변경 사항 요약

| 기능 | 위치 | 상태 |
|------|------|------|
| Phase 2: 치수-객체 관계 추출 | BOM Backend/Frontend | 신규 |
| 수동 관계 연결 | RelationList.tsx | 신규 |
| 관계 삭제 | RelationList.tsx, WorkflowPage.tsx | 신규 |
| 세션 일괄 삭제 | Dashboard.tsx, session_router.py | 신규 |
| 관계 오버레이 시각화 | RelationOverlay.tsx | 신규 |

---

## 사전 준비

### 1. 서비스 상태 확인

```bash
# 필수 서비스 확인
docker ps | grep -E "yolo-api|blueprint-ai-bom"
```

필요한 컨테이너:
- `yolo-api` (포트 5005)
- `blueprint-ai-bom-backend` (포트 5020)
- `blueprint-ai-bom-frontend` (포트 3000)
- `gateway-api` (포트 8000)

### 2. 서비스 시작 (필요시)

```bash
cd /home/uproot/ax/poc
docker-compose up -d yolo-api blueprint-ai-bom-backend blueprint-ai-bom-frontend gateway-api
```

---

## 테스트 시나리오

### 시나리오 1: BlueprintFlow에서 BOM 워크플로우 실행

#### Step 1.1: 빌더 접속
1. 브라우저에서 열기: **http://localhost:5173/blueprintflow/builder**
2. 좌측 노드 팔레트 확인

#### Step 1.2: 워크플로우 구성
```
┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐
│ ImageInput  │────▶│    YOLO     │────▶│  Blueprint AI BOM   │
└─────────────┘     └─────────────┘     └─────────────────────┘
```

1. **ImageInput 노드** 추가
   - 좌측 팔레트 → "Input" → "ImageInput" 드래그
   - 테스트 이미지 선택

2. **YOLO 노드** 추가
   - "Detection" → "YOLO" 드래그
   - 설정:
     - confidence: 0.4
     - model_type: bom_detector
   - ImageInput → YOLO 연결

3. **Blueprint AI BOM 노드** 추가
   - "Analysis" → "Blueprint AI BOM" 드래그
   - YOLO → Blueprint AI BOM 연결

#### Step 1.3: 워크플로우 실행
1. 상단 **"실행"** 버튼 클릭
2. 각 노드 순차 실행 확인
3. BOM 노드 완료 시 UI 열림 확인

---

### 시나리오 2: BOM UI에서 관계 기능 테스트

#### Step 2.1: BOM UI 접속
- URL: **http://localhost:3000**
- 또는 워크플로우 실행 후 자동 열림

#### Step 2.2: 세션 선택
1. 좌측 세션 목록에서 세션 선택
2. 이미지와 검출 결과 확인

#### Step 2.3: 치수-객체 관계 섹션
1. 페이지 스크롤하여 **"🔗 치수-객체 관계"** 섹션 이동
2. 관계 통계 확인:
   - 총 관계 수
   - 방법별 통계 (치수선, 연장선, 근접성, 수동)
   - 신뢰도별 통계 (높음/중간/낮음)

#### Step 2.4: 수동 연결 테스트
1. 관계 항목 클릭하여 확장 (예: "100mm → 없음")
2. **"수동 연결"** 버튼 클릭
3. 드롭다운에서 심볼 선택 (예: "PT")
4. 결과 확인:
   - 연결 상태: 100mm → PT
   - 신뢰도: 100%
   - 방법: 수동 (보라색)

#### Step 2.5: 관계 삭제 테스트
1. 관계 항목 확장
2. **"삭제"** 버튼 (빨간색) 클릭
3. 확인 대화 상자에서 "확인"
4. 목록에서 제거 확인
5. 통계 자동 업데이트 확인

#### Step 2.6: 관계 오버레이 확인
1. 이미지 위에 관계 시각화 확인
2. 색상 범례:
   - 녹색: 치수선 기반
   - 파란색: 연장선 기반
   - 노란색 점선: 근접성 기반
   - 보라색: 수동 연결

---

### 시나리오 3: Dashboard에서 세션 관리

#### Step 3.1: Dashboard 접속
- URL: **http://localhost:5173/dashboard**

#### Step 3.2: BOM 세션 관리 섹션 확인
1. "BOM 세션 관리" 카드 찾기
2. 세션 개수 표시 확인 (예: "(15개)")

#### Step 3.3: 개별 세션 삭제
1. 세션 항목의 휴지통 아이콘 클릭
2. 확인 후 삭제

#### Step 3.4: 전체 세션 삭제 테스트
1. **"전체 삭제"** 버튼 클릭 (빨간색 테두리)
2. 확인 대화 상자: "N개의 세션을 모두 삭제하시겠습니까?"
3. "확인" 클릭
4. 완료 알림: "✅ N개의 세션이 삭제되었습니다."
5. 세션 목록 비워짐 확인

---

### 시나리오 4: BOM 생성 및 내보내기

#### Step 4.1: 심볼 검증
1. BOM UI에서 검출된 심볼 검증
2. 승인/수정/거부 처리

#### Step 4.2: 검증 완료
1. **"검증 완료"** 버튼 클릭
2. BOM 자동 생성

#### Step 4.3: 내보내기
1. 내보내기 형식 선택:
   - Excel (.xlsx)
   - PDF
   - JSON
   - CSV
2. 다운로드 확인

---

## API 직접 테스트 (선택사항)

### 관계 API

```bash
# 관계 목록 조회
curl http://localhost:5020/relations/{session_id}

# 관계 통계 조회
curl http://localhost:5020/relations/{session_id}/statistics

# 관계 자동 추출
curl -X POST http://localhost:5020/relations/extract/{session_id}

# 수동 연결
curl -X POST http://localhost:5020/relations/{session_id}/link/{dimension_id}/{target_id}

# 관계 삭제
curl -X DELETE http://localhost:5020/relations/{session_id}/{relation_id}
```

### 세션 API

```bash
# 세션 목록 조회
curl http://localhost:5020/sessions

# 세션 전체 삭제
curl -X DELETE http://localhost:5020/sessions
```

---

## 체크리스트

| # | 테스트 항목 | 결과 |
|---|------------|------|
| 1 | BlueprintFlow 빌더 접속 | [ ] |
| 2 | ImageInput → YOLO → BOM 워크플로우 구성 | [ ] |
| 3 | 워크플로우 실행 | [ ] |
| 4 | BOM UI 열림 | [ ] |
| 5 | 치수-객체 관계 섹션 표시 | [ ] |
| 6 | 수동 연결 기능 | [ ] |
| 7 | 관계 삭제 기능 | [ ] |
| 8 | 관계 오버레이 시각화 | [ ] |
| 9 | Dashboard 세션 목록 | [ ] |
| 10 | 세션 전체 삭제 | [ ] |
| 11 | BOM 생성 및 내보내기 | [ ] |

---

## 문제 해결

### BOM UI가 열리지 않는 경우
```bash
docker logs blueprint-ai-bom-frontend
docker logs blueprint-ai-bom-backend
```

### 관계가 추출되지 않는 경우
1. 치수가 있는지 확인 (치수 OCR 실행)
2. 검출 결과가 있는지 확인 (YOLO 실행)

### 전체 삭제 버튼이 보이지 않는 경우
- 세션이 0개인 경우 버튼이 숨겨집니다
- 새로고침 버튼으로 세션 목록 갱신

---

## 접속 URL 요약

| 서비스 | URL |
|--------|-----|
| BlueprintFlow Builder | http://localhost:5173/blueprintflow/builder |
| Dashboard | http://localhost:5173/dashboard |
| BOM UI | http://localhost:3000 |
| BOM API Docs | http://localhost:5020/docs |
