# Techcross 미팅 - P&ID 고도화 작업

> **작성일**: 2025-12-06
> **최종 업데이트**: 2025-12-14
> **고객사**: Techcross (해양/조선 기자재)

---

## 미완료 작업

### 1. Human-in-the-Loop 검증 UI (중요도: 높음)

**필요 이유**: AI 정확도가 100%가 아니므로 사람이 결과를 검토/수정할 수 있어야 함. 고객 미팅에서 "승인/수정/반려 기능 필수"라고 언급됨.

**현황**:
- DrawingBOMExtractor(`/home/uproot/panasia/DrawingBOMExtractor`)에 Streamlit으로 구현됨
- 하지만 성능/메모리 효율 문제로 React로 재작성 필요
- 상세 전략: `2025-12-14_integration_strategy.md` 참조

**구현 내용**:
```
기능 요구사항:
├── 이미지 뷰어
│   ├── 도면 이미지 위에 바운딩 박스 오버레이 표시
│   ├── 줌/팬 기능 (대형 도면 지원)
│   ├── 박스 색상: 승인(녹색), 반려(빨강), 수정(주황), 수동(보라)
│   └── 박스 위에 클래스명 + 신뢰도 표시
│
├── 바운딩 박스 편집
│   ├── 클릭으로 박스 선택
│   ├── 드래그로 박스 이동
│   ├── 모서리 드래그로 크기 조절
│   ├── 키보드 Delete로 삭제
│   └── 더블클릭으로 새 박스 추가
│
├── 클래스 수정
│   ├── 드롭다운으로 클래스 변경
│   ├── 검색 가능한 클래스 목록
│   └── 최근 사용 클래스 상단 표시
│
├── 승인/반려 워크플로우
│   ├── 개별 항목 승인/반려 버튼
│   ├── 전체 승인/반려 버튼
│   ├── 필터: 미처리/승인/반려/수정됨
│   └── 진행률 표시 (23/50 완료)
│
└── 수정 이력
    ├── 누가, 언제, 무엇을 수정했는지 기록
    ├── 원본 vs 수정본 비교
    └── 감사 추적용 DB 저장
```

**UI 레이아웃**:
```
┌─────────────────────────────────────────────────────────────────┐
│ [< 뒤로] 검증 UI - drawing_001.pdf              [전체승인] [저장] │
├───────────────────────────────────┬─────────────────────────────┤
│                                   │ 검출 목록 (23/50)           │
│                                   ├─────────────────────────────┤
│                                   │ [필터: 전체 ▼]              │
│      ┌─────────┐                  ├─────────────────────────────┤
│      │ CIRCUIT │ 0.95             │ ☑ 1. CIRCUIT_BREAKER  95%  │
│      │ BREAKER │                  │   [승인] [반려] [수정]      │
│      └─────────┘                  ├─────────────────────────────┤
│                                   │ ☐ 2. PLC_CPU         88%   │
│   ┌───────────────┐               │   [승인] [반려] [수정]      │
│   │  TRANSFORMER  │ 0.91          ├─────────────────────────────┤
│   │               │               │ ✗ 3. TERMINAL (반려됨)      │
│   └───────────────┘               │   사유: 오검출              │
│                                   ├─────────────────────────────┤
│      [이미지 영역]                 │ ✎ 4. RELAY → CONTACTOR     │
│      줌: 100% [+] [-] [맞춤]       │   수정됨                    │
│                                   ├─────────────────────────────┤
│                                   │ 🎨 5. (수동 추가)           │
│                                   │   ETHERNET_SWITCH           │
└───────────────────────────────────┴─────────────────────────────┘
```

**기술 스택**:
```typescript
// React 컴포넌트 구조
web-ui/src/pages/verification/
├── VerificationPage.tsx        # 메인 페이지
├── components/
│   ├── ImageViewer.tsx         # Konva 기반 이미지 뷰어
│   ├── BoundingBox.tsx         # 개별 박스 컴포넌트
│   ├── BoxEditor.tsx           # 박스 편집 핸들러
│   ├── DetectionList.tsx       # 우측 검출 목록
│   ├── ClassSelector.tsx       # 클래스 선택 드롭다운
│   ├── ApprovalButtons.tsx     # 승인/반려 버튼
│   └── HistoryPanel.tsx        # 수정 이력 패널
├── hooks/
│   ├── useBoxSelection.ts      # 박스 선택 상태
│   ├── useBoxDrag.ts           # 드래그 로직
│   └── useVerificationStore.ts # Zustand 스토어
└── types/
    └── verification.ts         # 타입 정의
```

**필요 라이브러리**:
```json
{
  "react-konva": "^18.2.10",      // Canvas 렌더링
  "konva": "^9.3.0",              // Canvas 엔진
  "@use-gesture/react": "^10.3.0" // 제스처 처리
}
```

**예상 작업량**: 7일 (React 재작성 포함)

---

### 2. Knowledge Engine 확장 (중요도: 높음)

**필요 이유**: 현재 Knowledge Engine에 도메인 데이터가 없음. "이 밸브가 KR 규정에 맞는가?" 같은 검증 불가.

**추가할 데이터**:

#### 2.1 KR 선급 규정 (한국선급)

```yaml
# gateway-api/data/knowledge/kr_regulations.yaml

regulations:
  piping:
    - id: "KR-PIPE-001"
      title: "배관 재질 규정"
      content: |
        해수 배관: SUS316L 이상
        담수 배관: SUS304 이상
        유압 배관: STKM13A 이상
      applicable_to: ["sea_water_pipe", "fresh_water_pipe", "hydraulic_pipe"]

    - id: "KR-PIPE-002"
      title: "배관 두께 규정"
      content: |
        최소 두께 = (P × D) / (2 × S × E + 0.8 × P) + C
        P: 설계압력, D: 외경, S: 허용응력, E: 용접계수, C: 부식여유
      formula: true

  valves:
    - id: "KR-VALVE-001"
      title: "밸브 사용 조건"
      content: |
        Gate Valve: 완전 개폐용, 유량 조절 불가
        Globe Valve: 유량 조절용, 압력 손실 큼
        Ball Valve: 빠른 개폐, 1/4 회전
        Check Valve: 역류 방지 전용

  safety:
    - id: "KR-SAFETY-001"
      title: "안전밸브 설치 기준"
      content: |
        압력용기 최대허용압력의 110% 이내 작동
        설치 위치: 압력원에서 가장 가까운 곳
        배출 용량: 유입량 이상
```

#### 2.2 ISO 배관 표준

```yaml
# gateway-api/data/knowledge/iso_standards.yaml

standards:
  - id: "ISO-1101"
    title: "기하 공차"
    content: |
      위치도, 진원도, 원통도, 평면도, 직각도 등
      GD&T 심볼 및 적용 방법
    symbols: ["⌖", "○", "⌒", "⊥", "//"]

  - id: "ISO-5208"
    title: "밸브 누설 시험"
    content: |
      Rate A: 누설 없음 (0 방울)
      Rate B: 0.0006 × DN × 시간(초) ml
      Rate C: 0.0018 × DN × 시간(초) ml
    test_pressure: "1.1 × PN"

  - id: "ISO-10497"
    title: "밸브 내화 시험"
    content: |
      화재 시 30분간 기밀 유지
      API 607과 동등
```

#### 2.3 조선소별 심볼 매핑

```yaml
# gateway-api/data/knowledge/shipyard_symbols.yaml

mappings:
  hyundai:
    - symbol: "GV-001"
      standard_name: "Gate Valve"
      category: "valve"
    - symbol: "BV-002"
      standard_name: "Ball Valve"
      category: "valve"
    - symbol: "CV-003"
      standard_name: "Check Valve"
      category: "valve"
    - symbol: "PSV-001"
      standard_name: "Pressure Safety Valve"
      category: "safety"

  samsung:
    - symbol: "V-GT-01"
      standard_name: "Gate Valve"
      category: "valve"
    - symbol: "V-BL-01"
      standard_name: "Ball Valve"
      category: "valve"

  dsme:
    - symbol: "VLV-G-001"
      standard_name: "Gate Valve"
      category: "valve"
```

**Knowledge API 확장**:
```python
# gateway-api/services/knowledge_service.py

class KnowledgeService:
    async def validate_component(self, component: dict) -> ValidationResult:
        """
        입력: {'type': 'valve', 'subtype': 'gate', 'application': 'sea_water'}
        출력: {
            'valid': True,
            'regulations': ['KR-VALVE-001'],
            'warnings': [],
            'suggestions': ['SUS316L 재질 권장']
        }
        """

    async def translate_symbol(self, symbol: str, shipyard: str) -> str:
        """
        입력: symbol='GV-001', shipyard='hyundai'
        출력: 'Gate Valve'
        """

    async def get_standard_info(self, standard_id: str) -> dict:
        """
        입력: 'ISO-5208'
        출력: {'title': '밸브 누설 시험', 'content': '...', ...}
        """
```

**예상 작업량**: 3~4일 (데이터 수집 별도)

---

### 3. 피드백 루프 - 재학습 (중요도: 중간)

**필요 이유**: 검증 UI에서 수정한 내용을 모델 개선에 활용해야 정확도가 점진적으로 향상됨.

**시스템 구조**:
```
┌───────────────────┐
│   검증 UI         │
│   (수정/승인)     │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  Corrections DB   │
│  (수정 이력 저장)  │
└─────────┬─────────┘
          │
          ▼ 100건 누적 시
┌───────────────────┐
│  재학습 트리거     │
│  (Celery Task)    │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  YOLO Fine-tune   │
│  (scripts/retrain)│
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  새 모델 배포      │
│  (Docker 재빌드)   │
└───────────────────┘
```

**DB 스키마**:
```sql
CREATE TABLE corrections (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    original_bbox JSONB NOT NULL,      -- [x1, y1, x2, y2]
    corrected_bbox JSONB,              -- null if deleted
    original_class VARCHAR(50) NOT NULL,
    corrected_class VARCHAR(50),       -- null if class unchanged
    action VARCHAR(20) NOT NULL,       -- 'approved', 'rejected', 'modified', 'added'
    user_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_corrections_action ON corrections(action);
CREATE INDEX idx_corrections_created ON corrections(created_at);
```

**재학습 스크립트**:
```python
# scripts/retrain_from_corrections.py

async def retrain_model():
    # 1. 수정 데이터 수집
    corrections = await db.fetch_all(
        "SELECT * FROM corrections WHERE used_for_training = false"
    )

    if len(corrections) < 100:
        return {"status": "skipped", "reason": "Not enough corrections"}

    # 2. YOLO 학습 데이터 생성
    for correction in corrections:
        if correction['action'] == 'approved':
            # 원본 그대로 학습 데이터로 사용
            create_yolo_label(correction['original_bbox'], correction['original_class'])
        elif correction['action'] == 'modified':
            # 수정된 데이터로 학습
            create_yolo_label(correction['corrected_bbox'], correction['corrected_class'])
        elif correction['action'] == 'added':
            # 수동 추가된 데이터 학습
            create_yolo_label(correction['corrected_bbox'], correction['corrected_class'])
        # rejected는 학습에서 제외

    # 3. Fine-tuning 실행
    result = subprocess.run([
        'python', 'train_yolo.py',
        '--model', 'yolo11n.pt',
        '--data', 'corrections_dataset.yaml',
        '--epochs', '10',
        '--imgsz', '640'
    ])

    # 4. 새 모델 검증
    metrics = evaluate_model('runs/train/exp/weights/best.pt')
    if metrics['mAP50'] > current_model_metrics['mAP50']:
        # 5. 모델 교체
        shutil.copy('runs/train/exp/weights/best.pt', 'models/yolo/best.pt')
        await notify_model_updated(metrics)

    # 6. 사용된 corrections 표시
    await db.execute(
        "UPDATE corrections SET used_for_training = true WHERE id IN (...)"
    )
```

**예상 작업량**: 4~5일

---

### 4. 배관 사이징 계산기 (중요도: 중간)

**필요 이유**: 고객 미팅에서 "펌프 용량 3000m³/h면 배관이 몇 인치여야 하나?" 검증 요구.

**계산 공식**:

#### Darcy-Weisbach (압력 손실)
```
ΔP = f × (L/D) × (ρ × v²/2)

ΔP: 압력 손실 (Pa)
f: 마찰 계수 (Moody diagram)
L: 배관 길이 (m)
D: 배관 내경 (m)
ρ: 유체 밀도 (kg/m³)
v: 유속 (m/s)
```

#### 유량-유속 관계
```
Q = A × v = (π × D²/4) × v

Q: 유량 (m³/s)
A: 단면적 (m²)
D: 배관 내경 (m)
v: 유속 (m/s)
```

#### 권장 유속 범위
| 유체 | 권장 유속 |
|------|----------|
| 물 (흡입) | 1.0~2.0 m/s |
| 물 (토출) | 2.0~3.0 m/s |
| 기름 | 1.0~2.0 m/s |
| 증기 | 20~40 m/s |
| 공기 | 10~20 m/s |

**구현**:
```python
# gateway-api/services/pipe_calculator.py

class PipeCalculator:
    RECOMMENDED_VELOCITY = {
        'water_suction': (1.0, 2.0),
        'water_discharge': (2.0, 3.0),
        'oil': (1.0, 2.0),
        'steam': (20, 40),
        'air': (10, 20)
    }

    def calculate_pipe_size(
        self,
        flow_rate: float,      # m³/h
        fluid_type: str,
        temperature: float,    # °C
        pipe_length: float     # m
    ) -> dict:
        """
        입력: flow_rate=3000, fluid_type='water_discharge', temperature=25, pipe_length=100
        출력: {
            'recommended_diameter': 12,  # inch
            'velocity': 2.45,            # m/s
            'pressure_drop': 0.8,        # bar
            'status': 'OK',
            'warnings': []
        }
        """
        # m³/h → m³/s
        Q = flow_rate / 3600

        # 권장 유속 범위
        v_min, v_max = self.RECOMMENDED_VELOCITY[fluid_type]
        v_target = (v_min + v_max) / 2

        # 필요 단면적: A = Q / v
        A = Q / v_target

        # 필요 직경: D = sqrt(4A/π)
        D = math.sqrt(4 * A / math.pi)

        # 표준 파이프 사이즈로 반올림
        D_inch = self.round_to_standard_size(D * 39.37)  # m → inch

        # 실제 유속 계산
        actual_velocity = Q / (math.pi * (D_inch * 0.0254) ** 2 / 4)

        # 압력 손실 계산 (Darcy-Weisbach)
        pressure_drop = self.darcy_weisbach(
            velocity=actual_velocity,
            diameter=D_inch * 0.0254,
            length=pipe_length,
            fluid_type=fluid_type,
            temperature=temperature
        )

        # 경고 체크
        warnings = []
        if actual_velocity < v_min:
            warnings.append(f"유속이 권장 범위 미만 ({actual_velocity:.2f} < {v_min})")
        if actual_velocity > v_max:
            warnings.append(f"유속이 권장 범위 초과 ({actual_velocity:.2f} > {v_max})")

        return {
            'recommended_diameter': D_inch,
            'velocity': actual_velocity,
            'pressure_drop': pressure_drop,
            'status': 'WARNING' if warnings else 'OK',
            'warnings': warnings
        }

    def validate_design(
        self,
        design_diameter: float,  # inch (도면에서 추출)
        flow_rate: float,
        fluid_type: str
    ) -> dict:
        """도면 설계값과 계산값 비교"""
        calc = self.calculate_pipe_size(flow_rate, fluid_type, 25, 100)

        if design_diameter < calc['recommended_diameter']:
            return {
                'valid': False,
                'message': f"설계 직경({design_diameter}\")이 권장({calc['recommended_diameter']}\")보다 작음",
                'risk': '유속 초과, 압력 손실 증가'
            }
        elif design_diameter > calc['recommended_diameter'] * 1.5:
            return {
                'valid': False,
                'message': f"설계 직경({design_diameter}\")이 과대 설계됨",
                'risk': '유속 저하로 침전물 축적 가능'
            }
        else:
            return {'valid': True, 'message': '적정 설계'}
```

**API 엔드포인트**:
```python
@router.post("/pipe/calculate")
async def calculate_pipe(request: PipeCalcRequest):
    calculator = PipeCalculator()
    return calculator.calculate_pipe_size(
        flow_rate=request.flow_rate,
        fluid_type=request.fluid_type,
        temperature=request.temperature,
        pipe_length=request.pipe_length
    )

@router.post("/pipe/validate")
async def validate_pipe_design(request: PipeValidationRequest):
    calculator = PipeCalculator()
    return calculator.validate_design(
        design_diameter=request.design_diameter,
        flow_rate=request.flow_rate,
        fluid_type=request.fluid_type
    )
```

**예상 작업량**: 3~4일

---

## 우선순위 요약

| 순위 | 작업 | 예상 기간 | 필수 여부 | 비고 |
|------|------|----------|----------|------|
| 1 | Human-in-the-Loop UI | 7일 | **필수** | React 재작성, 통합 전략 참조 |
| 2 | Knowledge Engine 확장 | 3~4일 | 권장 | 데이터 수집 별도 |
| 3 | 피드백 루프 (재학습) | 4~5일 | 선택 | DB 설계 포함 |
| 4 | 배관 사이징 계산기 | 3~4일 | 선택 | P&ID 분석용 |

**총 예상 작업량**: 약 17~20일

---

## 관련 문서

- **통합 전략**: `2025-12-14_integration_strategy.md`
- **기능 확장**: `2025-12-10_pending_tasks.md`
- **프로젝트 구조**: `2025-12-14_project_structure.md`

---

**참고**: Human-in-the-Loop UI는 DrawingBOMExtractor 통합 작업과 함께 진행해야 함
