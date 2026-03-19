---
name: dimension-eval
description: "Dimension Lab eval runner. OD/ID/W 분류 정확도 자동 검증 및 벤치마크. 트리거 — eval, 평가, 벤치마크, 정확도 테스트"
user-invocable: true
disable-model-invocation: true
allowed-tools: [Read, Bash, Grep, Glob]
skill-type: workflow
---

# Dimension Lab Eval Runner

OD/ID/W 분류 방법론의 정확도를 자동 검증하는 eval 시스템.

## 구조

```
blueprint-ai-bom/tests/eval/
├── dimension_eval_cases.json   # 테스트 케이스 (GT 포함, 8개)
├── run_dimension_eval.py       # Eval runner (httpx async)
└── test_images/                # 테스트 이미지 (수동 배치)
```

## 실행 방법

### 사전 조건
1. Backend 서버 실행 중 (`localhost:5020`)
2. 테스트 이미지가 `test_images/` 에 배치됨
3. `httpx` 설치됨 (`pip install httpx`)

### 기본 실행
```bash
cd /home/uproot/ax/poc
python3 blueprint-ai-bom/tests/eval/run_dimension_eval.py
```

### 벤치마크 비교 (이전 결과 대비)
```bash
# 1차 실행 -> 결과 저장
python3 blueprint-ai-bom/tests/eval/run_dimension_eval.py
cp /tmp/dimension_eval_results.json /tmp/dimension_eval_baseline.json

# 분류 로직 수정 후 2차 실행 -> 비교
python3 blueprint-ai-bom/tests/eval/run_dimension_eval.py --benchmark /tmp/dimension_eval_baseline.json
```

### 옵션
- `--cases <path>`: 커스텀 케이스 파일 (기본: dimension_eval_cases.json)
- `--base-url <url>`: 백엔드 URL (기본: http://localhost:5020)
- `--benchmark <path>`: 이전 결과 JSON 과 비교
- `--output <path>`: 결과 저장 경로 (기본: /tmp/dimension_eval_results.json)

## 결과 해석

### 셀 스코어 (0.0 ~ 1.0)
- **1.0**: OD, ID, W 모두 GT와 일치 (tolerance +-0.5)
- **0.67**: 3개 중 2개 일치
- **0.33**: 3개 중 1개 일치
- **0.0**: 모두 불일치 또는 추출 실패

### 리포트 섹션
1. **Case별 결과**: 각 테스트 케이스의 method별 pass/fail
2. **Method별 정확도**: 10개 method의 전체 정확도 순위
3. **Engine별 정확도**: 7개 OCR 엔진의 전체 정확도 순위
4. **Overall**: 전체 perfect cell 비율

### 벤치마크 모드
이전 결과와 비교하여 method별 정확도 변화를 표시:
- **+**: 개선 (녹색)
- **-**: 저하 (빨간색)

## 테스트 케이스 추가

`dimension_eval_cases.json` 에 항목 추가:

```json
{
  "case_id": "bearing_XXXX",
  "description": "설명",
  "session_name": "XXXX",
  "ground_truth": { "od": 100.0, "id": 50.0, "w": 20.0 },
  "image_path": "test_images/bearing_XXXX.png",
  "expected_methods": {
    "catalog": { "should_pass": true },
    "full_pipeline": { "should_pass": true }
  }
}
```

## 반복 워크플로우

1. `run_dimension_eval.py` 실행 -> 베이스라인 저장
2. 분류 로직 수정 (예: `opencv_classifier.py`, `dimension_parser.py`)
3. `--benchmark` 모드로 재실행 -> 정확도 변화 확인
4. 악화된 method 있으면 롤백 또는 수정

## API 흐름 (내부)

1. `POST /sessions/upload` (multipart) -> session_id
2. `POST /analysis/dimensions/{session_id}/ground-truth` -> GT 저장
3. `POST /analysis/dimensions/full-compare` -> 7엔진 x 10방법 매트릭스
4. 로컬에서 GT 대비 스코어링
