# Scripts Directory

프로젝트 관리 및 배포 스크립트 모음

## 📁 디렉토리 구조

```
scripts/
├── deployment/          # 배포 관련 스크립트
│   ├── install.sh      # 시스템 설치
│   └── export_images.sh # Docker 이미지 내보내기
├── management/          # 관리 스크립트
│   ├── backup.sh       # 백업
│   ├── restore.sh      # 복원
│   ├── check_system.sh # 시스템 체크
│   └── health_check.sh # 헬스체크
├── tests/              # 테스트 스크립트
└── README.md
```

## 🚀 주요 스크립트

### 배포

```bash
# 시스템 설치
./scripts/deployment/install.sh

# Docker 이미지 내보내기
./scripts/deployment/export_images.sh
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
```

## 📝 참고

- 학습 관련 스크립트는 각 API의 `training/` 디렉토리에 있습니다
  - `models/edgnet-api/training/scripts/`
  - `models/yolo-api/training/scripts/`
  - `models/skinmodel-api/training/scripts/`
