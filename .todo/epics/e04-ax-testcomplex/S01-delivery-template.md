# S01: 범용 납품 패키지 템플릿화

> **목표**: 동서기연 전용 납품 패키지를 고객명만 바꾸면 되는 범용 구조로 리팩토링
> **우선순위**: 높음 (S02~S05의 기반)

---

## 현재 상태 (As-Is)

동서기연 납품 패키지가 `exports/dsebearing-delivery/`에 완성되어 있으나,
고객명·프로젝트ID·포트 등이 하드코딩되어 있어 다른 고객에 재사용하려면 수작업 필요.

```
dsebearing-delivery/
├── README.md              ← 동서기연 전용 내용
├── docker-compose.yml     ← 서비스명 하드코딩
├── setup.sh / setup.ps1   ← 경로 하드코딩
├── data/project_dsebearing.json
├── images/                ← Docker 이미지 TAR
└── CHECKSUMS.sha256
```

## 목표 상태 (To-Be)

```
delivery-template/
├── README.md.template     ← {{CUSTOMER_NAME}}, {{PROJECT_ID}} 플레이스홀더
├── docker-compose.yml.template
├── setup.sh.template
├── setup.ps1.template
├── images/                ← 공용 Docker 이미지 (1회 빌드, 전체 재사용)
└── generate-package.sh    ← 고객명 입력 → 완성 패키지 자동 생성
```

## 작업 항목

| # | 작업 | 산출물 |
|---|------|--------|
| 1 | 동서기연 패키지에서 고객별 변수 식별 | 변수 목록 문서 |
| 2 | 템플릿 파일 생성 (플레이스홀더 적용) | `*.template` 파일 |
| 3 | `generate-package.sh` 스크립트 작성 | 자동 생성 CLI |
| 4 | Docker 이미지 공용화 (태그 전략) | 이미지 관리 정책 |
| 5 | 생성된 패키지 검증 (더미 고객으로 테스트) | 테스트 결과 |

## 수용 기준

- [ ] `./generate-package.sh --customer "파나시아" --project-id abc123` 실행 시 완성 패키지 생성
- [ ] 생성된 패키지로 `docker compose up -d` → 서비스 정상 기동
- [ ] README에 고객명/연락처가 자동 반영
- [ ] 기존 동서기연 패키지와 동일 품질 (체크섬, 설치 스크립트 동작)
