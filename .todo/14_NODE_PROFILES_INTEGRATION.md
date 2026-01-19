# NodeDefinitions 프로파일 통합 작업

> **생성일**: 2026-01-19
> **우선순위**: P2 (중요도 중간)
> **관련**: config/ 디렉토리 일관성 작업

---

## 현황

### 프로파일 시스템 추가됨

`web-ui/src/config/nodes/types.ts`에 새 타입 추가:

```typescript
export interface ProfileDefinition {
  name: string;
  label: string;
  description: string;
  params: Record<string, string | number | boolean>;
}

export interface ProfilesConfig {
  default: string;
  available: ProfileDefinition[];
}

export interface NodeDefinition {
  // ... 기존 필드
  profiles?: ProfilesConfig;  // 새로 추가됨
}
```

### 백엔드 패턴 (models/*/config/defaults.py)

```python
DEFAULTS: Dict[str, Dict[str, Any]] = {
    "general": { ... },
    "engineering": { ... },
    "debug": { ... },
}
```

---

## 동기화 필요 항목

### 프론트엔드 ↔ 백엔드 프로파일 매핑

| API | 백엔드 프로파일 | 프론트엔드 노드 | 동기화 상태 |
|-----|-----------------|-----------------|-------------|
| DocTR | general, document, structured, engineering, scanned, debug | doctr | ❌ 미완료 |
| EasyOCR | general, document, engineering | easyocr | ❌ 미완료 |
| EDGNet | general, detailed, engineering | edgnet | ❌ 미완료 |
| eDOCr2 | general, engineering, dimension | edocr2 | ❌ 미완료 |
| PaddleOCR | general, document, engineering | paddleocr | ❌ 미완료 |
| SuryaOCR | general, multilingual, engineering | suryaocr | ❌ 미완료 |
| Tesseract | general, document, engineering | tesseract | ❌ 미완료 |
| TrOCR | general, handwriting, engineering | trocr | ❌ 미완료 |
| YOLO | pid_class_aware, pid_symbol_only, gd_tolerance | yolo | ⚠️ 부분 |
| Line Detector | general, detailed, minimal | linedetector | ❌ 미완료 |

---

## 작업 계획

### Phase 1: 프로파일 데이터 수집

각 API의 `config/defaults.py`에서 프로파일 정보 추출:

```bash
# 예시: DocTR 프로파일 조회
cat models/doctr-api/config/defaults.py | grep -A 10 "DEFAULTS"
```

### Phase 2: NodeDefinitions 업데이트

`web-ui/src/config/nodes/`의 각 노드 정의에 profiles 추가:

```typescript
// 예시: DocTR 노드 정의
export const doctrNode: NodeDefinition = {
  type: 'doctr',
  // ... 기존 필드
  profiles: {
    default: 'general',
    available: [
      {
        name: 'general',
        label: '일반 OCR',
        description: '범용 텍스트 인식 (기본값)',
        params: {
          straighten_pages: false,
          export_as_xml: false,
          visualize: false,
        }
      },
      {
        name: 'engineering',
        label: '도면 OCR',
        description: '도면 텍스트/치수 인식',
        params: {
          straighten_pages: false,
          export_as_xml: false,
          visualize: false,
        }
      },
      // ...
    ]
  }
};
```

### Phase 3: UI 컴포넌트 업데이트

BlueprintFlow 노드 패널에서 프로파일 선택 UI 추가:

- 프로파일 드롭다운 선택
- 프로파일 선택 시 파라미터 자동 설정
- 커스텀 파라미터 오버라이드 허용

---

## 파일 목록

### 업데이트 필요 파일

| 파일 | 변경 내용 |
|------|-----------|
| `web-ui/src/config/nodes/ocrNodes.ts` | OCR 노드 프로파일 추가 |
| `web-ui/src/config/nodes/detectionNodes.ts` | YOLO 프로파일 추가 |
| `web-ui/src/config/nodes/segmentationNodes.ts` | EDGNet, LineDetector 프로파일 |
| `web-ui/src/components/blueprintflow/NodeDetailPanel.tsx` | 프로파일 선택 UI |

### 참조 파일

| 파일 | 용도 |
|------|------|
| `models/doctr-api/config/defaults.py` | 프로파일 정의 예시 |
| `models/design-checker-api/config/` | 프로파일 시스템 참조 |

---

## 완료 체크리스트

- [ ] DocTR 노드 프로파일 추가
- [ ] EasyOCR 노드 프로파일 추가
- [ ] EDGNet 노드 프로파일 추가
- [ ] eDOCr2 노드 프로파일 추가
- [ ] PaddleOCR 노드 프로파일 추가
- [ ] SuryaOCR 노드 프로파일 추가
- [ ] Tesseract 노드 프로파일 추가
- [ ] TrOCR 노드 프로파일 추가
- [ ] Line Detector 노드 프로파일 추가
- [ ] YOLO 노드 프로파일 완성
- [ ] NodeDetailPanel 프로파일 선택 UI
- [ ] 테스트 작성

---

*마지막 업데이트: 2026-01-19*
