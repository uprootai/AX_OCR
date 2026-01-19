# Scripts Directory

> 프로젝트 관리, 배포, 유틸리티 스크립트 모음
> **최종 업데이트**: 2026-01-19

---

## 디렉토리 구조

```
scripts/
├── README.md                      # 이 파일
├── deployment/                    # 배포 스크립트
│   ├── install.sh                # 시스템 설치
│   └── export_images.sh          # Docker 이미지 내보내기
├── management/                    # 관리 스크립트
│   ├── backup.sh                 # 백업
│   ├── restore.sh                # 복원
│   ├── check_system.sh           # 시스템 체크
│   └── health_check.sh           # 헬스체크
├── tests/                         # 테스트 스크립트
│   ├── test_real_workflow.py     # 실제 워크플로우 테스트
│   ├── test_full_pipeline.py     # 전체 파이프라인 테스트
│   └── ...
├── create_api.py                  # API 스캐폴딩 도구
├── sync_feature_definitions.py    # Feature 동기화 도구
├── bundle_models.sh               # 오프라인 모델 번들링
├── setup_gpu_environment.sh       # GPU 환경 설정
└── generate_bwms_pid_sample.py    # BWMS P&ID 샘플 생성
```

---

## 주요 스크립트

### API 관리

```bash
# 새 API 서비스 생성
python scripts/create_api.py my-api --port 5025 --category detection

# Feature Definition 동기화 (web-ui → blueprint-ai-bom)
python scripts/sync_feature_definitions.py
python scripts/sync_feature_definitions.py --check  # 확인만
```

### 배포

```bash
# 시스템 설치
./scripts/deployment/install.sh

# Docker 이미지 내보내기
./scripts/deployment/export_images.sh

# 오프라인 모델 번들링
./scripts/bundle_models.sh
```

### 관리

```bash
# 시스템 상태 체크
./scripts/management/check_system.sh

# 헬스체크
./scripts/management/health_check.sh

# 백업
./scripts/management/backup.sh

# 복원
./scripts/management/restore.sh

# GPU 환경 설정
./scripts/setup_gpu_environment.sh
```

### 테스트

```bash
# 실제 워크플로우 테스트
python scripts/tests/test_real_workflow.py

# 전체 파이프라인 테스트
python scripts/tests/test_full_pipeline.py
```

---

## 학습 스크립트 위치

학습 관련 스크립트는 각 API의 `training/scripts/` 디렉토리에 있습니다:

| API | 위치 |
|-----|------|
| EDGNet | `models/edgnet-api/training/scripts/` |
| YOLO | `models/yolo-api/training/scripts/` |
| SkinModel | `models/skinmodel-api/training/scripts/` |
| PID2Graph | `rnd/benchmarks/pid2graph/training/` |

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-01-19 | 학습 스크립트를 각 API의 training/ 디렉토리로 이동, 중복 제거 |
| 2025-11-20 | 초기 구조 생성 |

---

*최종 업데이트*: 2026-01-19
