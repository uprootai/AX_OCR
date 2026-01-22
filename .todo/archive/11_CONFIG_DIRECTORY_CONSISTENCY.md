# Config Directory 일관성 작업

> **생성일**: 2026-01-19
> **우선순위**: P2 (중요도 중간)
> **예상 작업량**: 6개 API 디렉토리

---

## 현황 분석

### config/ 디렉토리가 있는 API (12개) ✅
| API | 파일 | 비고 |
|-----|------|------|
| design-checker-api | `_active.yaml`, `common/`, `custom/`, `ecs/`, `hychlor/` | 프로파일 기반 |
| doctr-api | `__init__.py`, `defaults.py` | 표준 패턴 |
| easyocr-api | `__init__.py`, `defaults.py` | 표준 패턴 |
| edgnet-api | `__init__.py`, `defaults.py` | 표준 패턴 |
| edocr2-v2-api | `__init__.py`, `defaults.py` | 표준 패턴 |
| line-detector-api | `__init__.py`, `defaults.py` | 표준 패턴 |
| ocr-ensemble-api | `__init__.py` (비어있음) | 불완전 |
| paddleocr-api | `__init__.py`, `defaults.py` | 표준 패턴 |
| surya-ocr-api | `__init__.py`, `defaults.py` | 표준 패턴 |
| tesseract-api | `__init__.py`, `defaults.py` | 표준 패턴 |
| trocr-api | `__init__.py`, `defaults.py` | 표준 패턴 |
| yolo-api | `MODEL_DEFAULTS` | 원본 패턴 |

### config/ 디렉토리가 없는 API (7개) ❌
| API | 포트 | 필요성 | 우선순위 |
|-----|------|--------|----------|
| esrgan-api | 5010 | 낮음 (파라미터 적음) | P3 |
| knowledge-api | 5007 | 중간 (Neo4j 설정) | P2 |
| pid-analyzer-api | 5018 | 높음 (분석 파라미터 多) | P1 |
| pid-composer-api | 5021 | 중간 (SVG 설정) | P2 |
| skinmodel-api | 5003 | 높음 (공차 분석 설정) | P1 |
| vl-api | 5004 | 중간 (VLM 설정) | P2 |
| edocr2-api | 5002 | **삭제 예정** (edocr2-v2로 대체) | - |

---

## 표준 config 패턴

### 디렉토리 구조
```
models/{api-name}-api/config/
├── __init__.py
└── defaults.py
```

### defaults.py 템플릿
```python
"""
{API_NAME} 기본 파라미터 설정

YOLO API의 MODEL_DEFAULTS 패턴 적용
- 용도별 최적 파라미터 중앙 관리
- 코드 중복 제거
- 새 용도 추가 시 설정만 추가
"""

from typing import Dict, Any, Optional


# 용도별 기본 설정
DEFAULTS: Dict[str, Dict[str, Any]] = {
    "general": {
        "name": "일반",
        "description": "기본 설정",
        # API별 파라미터...
    },
    "engineering": {
        "name": "도면용",
        "description": "도면 분석 최적화",
        # API별 파라미터...
    },
    "debug": {
        "name": "디버그",
        "description": "시각화 포함",
        # API별 파라미터...
    },
}

DEFAULT_PROFILE = "general"


def get_defaults(profile: str = DEFAULT_PROFILE, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """프로파일에 맞는 기본 설정 반환"""
    base_config = DEFAULTS.get(profile, DEFAULTS[DEFAULT_PROFILE]).copy()
    if overrides:
        for key, value in overrides.items():
            if value is not None:
                base_config[key] = value
    return base_config


def list_profiles() -> Dict[str, str]:
    """사용 가능한 프로파일 목록"""
    return {
        profile: config.get("description", profile)
        for profile, config in DEFAULTS.items()
    }
```

---

## 작업 목록

### Phase 1: 높은 우선순위 (P1)

#### 1.1 pid-analyzer-api config 추가
```bash
# 파일 생성
mkdir -p models/pid-analyzer-api/config
touch models/pid-analyzer-api/config/__init__.py
# defaults.py 작성 필요 (연결 분석 파라미터)
```

**필요 파라미터**:
- `connection_threshold`: 연결 판정 임계값
- `symbol_expansion`: 심볼 확장 범위
- `line_tolerance`: 라인 허용 오차
- `max_connection_distance`: 최대 연결 거리

#### 1.2 skinmodel-api config 추가
```bash
mkdir -p models/skinmodel-api/config
touch models/skinmodel-api/config/__init__.py
# defaults.py 작성 필요 (공차 분석 파라미터)
```

**필요 파라미터**:
- `tolerance_class`: 공차 등급
- `measurement_unit`: 측정 단위
- `confidence_threshold`: 신뢰도 임계값

### Phase 2: 중간 우선순위 (P2)

#### 2.1 knowledge-api config 추가
- Neo4j 연결 설정
- GraphRAG 파라미터
- 쿼리 최적화 설정

#### 2.2 pid-composer-api config 추가
- SVG 스타일 설정
- 레이어 구성
- 색상 팔레트

#### 2.3 vl-api config 추가
- 모델 선택 (Qwen-VL, Claude Vision 등)
- 프롬프트 템플릿
- 응답 형식 설정

### Phase 3: 낮은 우선순위 (P3)

#### 3.1 esrgan-api config 추가
- 업스케일 배율
- 타일 크기
- 품질 설정

#### 3.2 ocr-ensemble-api config 완성
- 현재 `__init__.py`만 있음
- 가중치 설정 추가 필요
- 엔진 선택 설정

---

## 완료 체크리스트

- [x] pid-analyzer-api/config/defaults.py 생성 ✅ (2026-01-19)
- [x] skinmodel-api/config/defaults.py 생성 ✅ (2026-01-19)
- [x] knowledge-api/config/defaults.py 생성 ✅ (2026-01-19)
- [x] pid-composer-api/config/defaults.py 생성 ✅ (2026-01-19)
- [x] vl-api/config/defaults.py 생성 ✅ (2026-01-19)
- [x] esrgan-api/config/defaults.py 생성 ✅ (2026-01-19)
- [x] ocr-ensemble-api/config/defaults.py 완성 ✅ (이미 존재)
- [ ] edocr2-api 디렉토리 삭제 (deprecated) - 선택적

---

## 관련 파일

- 패턴 참조: `models/doctr-api/config/defaults.py`
- 원본 패턴: `models/yolo-api/config/model_defaults.py`
- 프로파일 시스템: `models/design-checker-api/config/`

---

*마지막 업데이트: 2026-01-19*
