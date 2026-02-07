# YOLOv12 업그레이드 계획

> **작성일**: 2026-02-06
> **상태**: ⏳ Ultralytics 공식 릴리스 대기
> **논문**: arXiv 2502.12524 (NeurIPS 2025)

---

## 개요

YOLOv12는 NeurIPS 2025에서 발표된 차세대 YOLO 모델로, Area-Attention과 R-ELAN 등의 혁신적인 기능을 포함합니다.

### 핵심 특징

| 컴포넌트 | 설명 | 효과 |
|----------|------|------|
| **Area-Attention** | 피처맵 수평/수직 영역 분할 | 계산 효율성 ↑ |
| **R-ELAN** | Residual ELAN | 깊은 네트워크 안정성 |
| **FlashAttention** | 메모리 효율 어텐션 | VRAM 사용량 ↓ |

### 예상 성능 개선

| 지표 | YOLOv11 | YOLOv12 (예상) |
|------|---------|----------------|
| 추론 속도 | baseline | +10-15% |
| VRAM 사용량 | baseline | -20% |
| mAP | baseline | +1-2% |

---

## 현재 상태

### Ultralytics 릴리스 상태

```
❌ 공식 패키지 미포함 (2026-02-06 기준)
```

**확인 방법**:
```bash
pip install ultralytics --upgrade
python3 -c "from ultralytics import YOLO; print(YOLO('yolo12n.pt'))"
```

### 현재 시스템

| API | 모델 | 포트 |
|-----|------|------|
| YOLO API | YOLOv11 | 5005 |

---

## 업그레이드 절차

### 1단계: 릴리스 확인

```bash
# Ultralytics 버전 확인
pip show ultralytics

# YOLOv12 모델 가용성 확인
python3 -c "from ultralytics import YOLO; YOLO('yolo12n.pt')"
```

### 2단계: 패키지 업데이트

```bash
cd /home/uproot/ax/poc/models/yolo-api

# requirements.txt 업데이트
# ultralytics>=X.X.X  (YOLOv12 포함 버전)

# 패키지 업그레이드
pip install --upgrade ultralytics
```

### 3단계: 모델 레지스트리 업데이트

**파일**: `models/yolo-api/models/model_registry.yaml`

```yaml
# 새 모델 추가
yolo12n:
  path: yolo12n.pt
  description: YOLOv12 Nano - 속도 최적화
  class_names:
    0: class1
    1: class2
    # ...
```

### 4단계: Docker 이미지 재빌드

```bash
cd /home/uproot/ax/poc

# YOLO API 이미지 재빌드
docker-compose build yolo-api

# 또는 전체 재빌드
docker-compose up -d --build yolo-api
```

### 5단계: 기존 모델 마이그레이션 (선택)

기존 커스텀 모델 (예: `panasia`, `pid_class_aware`)을 YOLOv12로 재학습:

```bash
# 기존 데이터셋으로 YOLOv12 Fine-tuning
python3 scripts/train_yolo12.py \
  --data configs/panasia_data.yaml \
  --model yolo12n.pt \
  --epochs 100 \
  --imgsz 640
```

### 6단계: 성능 벤치마크

```bash
# 추론 속도 비교
python3 scripts/benchmark.py --model yolo11n.pt --images test_images/
python3 scripts/benchmark.py --model yolo12n.pt --images test_images/

# mAP 비교 (동일 데이터셋)
python3 scripts/evaluate.py --model yolo11n.pt --data test_data.yaml
python3 scripts/evaluate.py --model yolo12n.pt --data test_data.yaml
```

---

## 파일 변경 목록

| 파일 | 변경 내용 |
|------|----------|
| `models/yolo-api/requirements.txt` | ultralytics 버전 업데이트 |
| `models/yolo-api/models/model_registry.yaml` | yolo12n/s/m/l 모델 추가 |
| `models/yolo-api/Dockerfile` | 필요시 베이스 이미지 업데이트 |
| `gateway-api/api_specs/yolo.yaml` | model_type에 yolo12 옵션 추가 |
| `web-ui/src/config/nodeDefinitions.ts` | YOLO 노드에 model_type 옵션 추가 |

---

## 위험 요소 및 대응

### 1. 호환성 문제

| 위험 | 대응 |
|------|------|
| API 인터페이스 변경 | Ultralytics 릴리스 노트 확인 |
| 커스텀 모델 비호환 | 재학습 필요 |
| ONNX 익스포트 변경 | 익스포트 스크립트 업데이트 |

### 2. 성능 저하

| 위험 | 대응 |
|------|------|
| 새 모델 성능 저하 | YOLOv11 폴백 유지 |
| VRAM 초과 | 모델 크기 조정 (n → s → m) |

### 3. 의존성 충돌

```bash
# 의존성 충돌 확인
pip check

# 가상 환경에서 테스트
python3 -m venv test_env
source test_env/bin/activate
pip install ultralytics
```

---

## 모니터링

### Ultralytics 릴리스 추적

- **GitHub**: https://github.com/ultralytics/ultralytics/releases
- **PyPI**: https://pypi.org/project/ultralytics/
- **Discord**: Ultralytics Discord 채널

### 알림 설정 (선택)

```bash
# GitHub Watch로 릴리스 알림 설정
# 또는 RSS 피드 구독
```

---

## 타임라인

| 단계 | 예상 시점 | 소요 시간 |
|------|----------|----------|
| Ultralytics 릴리스 | 미정 | - |
| 테스트 환경 검증 | 릴리스 후 1일 | 2-4시간 |
| 프로덕션 업데이트 | 릴리스 후 1주 | 1-2일 |
| 커스텀 모델 재학습 | 필요시 | 4-8시간 |

---

## 참조

- [YOLOv12 논문](https://arxiv.org/abs/2502.12524)
- [Ultralytics 공식 문서](https://docs.ultralytics.com/)
- [현재 시스템 SOTA 분석](./SOTA_GAP_ANALYSIS.md)

---

*작성자*: Claude Code (Opus 4.5)
*최종 업데이트*: 2026-02-06
