---
name: api-creation-guide
description: 새 API/새 서비스/엔드포인트 추가 시 스캐폴딩 가이드. create_api.py, Docker, gateway 등록 체크리스트. Triggers — scaffold, new API, new service, 라우터 추가
user-invocable: true
allowed-tools: [Read, Grep, Glob, Bash, Edit, Write]
skill-type: workflow
---

# 새 API 추가 가이드

이 스킬은 새 API 서비스를 추가할 때 필요한 전체 가이드입니다.

---

## 1. 스캐폴딩 스크립트 사용 (권장)

```bash
# 스크립트 실행 - 자동으로 모든 파일 생성
python scripts/create_api.py my-detector --port 5015 --category detection

# 생성되는 파일:
# - models/my-detector-api/api_server.py    ← 실제 로직 구현
# - models/my-detector-api/Dockerfile
# - models/my-detector-api/requirements.txt
# - gateway-api/api_specs/my-detector.yaml  ← BlueprintFlow 메타데이터

# 다음 단계:
# 1. api_server.py의 process() 함수에 실제 로직 구현
# 2. docker-compose.yml에 서비스 추가
# 3. docker-compose up --build my-detector-api
```

**카테고리 옵션**: detection, ocr, segmentation, preprocessing, analysis, knowledge, ai, control

---

## 2. 참조 논문 추가 (새 API 추가 시 필수)

```bash
# 1. 논문 검색 (WebSearch 사용)
# 검색 쿼리: "[기술명] paper arxiv [년도]"

# 2. 논문 파일 생성
cp docs/papers/TEMPLATE.md docs/papers/XX_[기술명]_[카테고리].md

# 3. 논문 내용 작성 (템플릿 섹션 채우기)
# - 논문 정보 (arXiv, 저자, 게재지)
# - 연구 배경
# - 핵심 방법론
# - AX 시스템 적용

# 4. Docs 페이지 업데이트
# web-ui/src/pages/docs/Docs.tsx의 docStructure에 추가

# 5. papers/README.md 논문 목록 업데이트
```

**참조**: `docs/papers/README.md`

---

## 3. Dashboard 설정 추가 (새 API 추가 시 필수)

### 3-1. APIStatusMonitor.tsx

`web-ui/src/components/monitoring/APIStatusMonitor.tsx`:
- `DEFAULT_APIS` 배열에 API 정보 추가
- `apiToContainerMap`에 컨테이너 매핑 추가
- `apiToSpecIdMap`에 스펙 ID 매핑 추가

### 3-2. APIDetail.tsx

`web-ui/src/pages/admin/APIDetail.tsx`:
- `DEFAULT_APIS` 배열에 API 정보 추가
- `HYPERPARAM_DEFINITIONS`에 하이퍼파라미터 UI 정의 추가
- `DEFAULT_HYPERPARAMS`에 기본값 추가

### 예시 (Line Detector 추가)

```typescript
// DEFAULT_APIS
{ id: 'line_detector', name: 'line_detector', display_name: 'Line Detector',
  base_url: 'http://localhost:5016', port: 5016,
  status: 'unknown', category: 'segmentation',
  description: 'P&ID 라인 검출', icon: '📐', color: '#7c3aed' }

// HYPERPARAM_DEFINITIONS
line_detector: [
  { label: '검출 방식', type: 'select', options: ['lsd', 'hough', 'combined'], description: '...' },
  { label: '라인 유형 분류', type: 'boolean', description: '...' },
]

// DEFAULT_HYPERPARAMS
line_detector: { method: 'lsd', classify_types: true, visualize: true }
```

---

## 4. 웹에서 컨테이너 GPU/메모리 설정

Dashboard에서 직접 컨테이너 GPU/메모리 설정을 변경하고 적용할 수 있습니다:

1. Dashboard → API 상세 페이지 접속
2. "현재 컨테이너 상태" 패널에서 실시간 GPU/CPU 상태 확인
3. 연산 장치를 CPU/CUDA로 변경
4. GPU 메모리 제한 설정 (예: 4g, 6g)
5. 저장 버튼 클릭 → 컨테이너 자동 재생성 (5-10초)

**API 엔드포인트**:
- `GET /admin/container/status/{service}` - 컨테이너 상태 조회
- `POST /admin/container/configure/{service}` - GPU/메모리 설정 및 재생성

---

## 5. GPU Override 시스템

GPU 설정은 `docker-compose.override.yml`에서 동적으로 관리합니다.

### 왜 GPU가 기본적으로 OFF인가?

| 이유 | 설명 |
|------|------|
| **VRAM 고갈** | 8개 API가 동시에 GPU 모드로 시작하면 GPU 메모리 고갈 |
| **필요시 활성화** | 실제 추론 시에만 특정 API의 GPU 활성화가 효율적 |
| **개발 환경 호환** | GPU 없는 환경에서도 바로 실행 가능 |

### GPU 지원 API (8개)

| 서비스명 | 컨테이너 | 용도 |
|----------|----------|------|
| YOLO | yolo-api | 객체 검출 |
| eDOCr2 | edocr2-v2-api | OCR |
| PaddleOCR | paddleocr-api | OCR |
| TrOCR | trocr-api | OCR |
| EDGNet | edgnet-api | 세그멘테이션 |
| ESRGAN | esrgan-api | 업스케일링 |
| Line Detector | line-detector-api | 라인 검출 |
| Blueprint AI BOM | blueprint-ai-bom-backend | BOM 생성 |

### 새 환경 설정 (템플릿 사용)

```bash
# 1. 템플릿 복사
cp docker-compose.override.yml.example docker-compose.override.yml

# 2. 필요한 서비스만 GPU 활성화 (파일 편집)
# 또는 Dashboard에서 동적으로 설정

# 3. 서비스 재시작
docker-compose up -d
```

### 파일 구조

```
docker-compose.yml              # 기본 설정 (GPU 없음)
docker-compose.override.yml     # GPU 설정 (로컬용, .gitignore)
docker-compose.override.yml.example  # 템플릿 (Git 추적)
```

### 수동 GPU 설정 예시

```yaml
# docker-compose.override.yml
services:
  yolo-api:
    deploy:
      resources:
        reservations:
          devices:
          - capabilities: [gpu]
            count: 1
            driver: nvidia
```

**주의**: `docker-compose.override.yml`은 `.gitignore`에 포함되어 각 환경마다 별도 설정 필요.

---

## 6. 기존 방식 (수동)

1. `models/{api-id}-api/api_server.py` 생성
2. `gateway-api/api_specs/{api-id}.yaml` 생성
3. docker-compose.yml에 서비스 추가
4. Dashboard 설정 추가 (위 3 참조)

---

## 7. 파라미터 수정

1. `gateway-api/api_specs/{api-id}.yaml` - 스펙 파일 수정
2. 또는 `nodeDefinitions.ts` - 프론트엔드 직접 수정 (정적 정의가 우선)
3. `*_executor.py` - 백엔드 처리 로직

---

## 8. 테스트 추가

### 프론트엔드 (TypeScript)

```typescript
// src/**/*.test.ts
import { describe, it, expect } from 'vitest';

describe('TestName', () => {
  it('should do something', () => {
    expect(true).toBe(true);
  });
});
```

### 백엔드 (Python)

```python
# tests/test_*.py
import pytest

class TestName:
    def test_something(self):
        assert True
```
