# 백로그 — Epic 인덱스

> 마지막 업데이트: 2026-02-27
> Epic/Story 기반 작업 관리 (BMAD-Lite)

---

## Active Epics

| ID | Epic | 고객 | 기간 | Stories | 상태 |
|----|------|------|------|---------|------|
| E01 | [성과발표회 PPT 완성](epics/e01-presentation/EPIC.md) | 내부 | ~03-06 | 3 | 🔵 Active |
| E02 | [테크로스 P&ID 설계 검증](epics/e02-techcross/EPIC.md) | 테크로스 | ~03-21 | 6 | 🔵 Active |
| E03 | [동서기연 BOM 추출 자동화](epics/e03-dsebearing/EPIC.md) | 동서기연 | ~03-21 | 3 | 🔵 Active |

## Future Epics

| ID | Epic | 고객 | 메모 | 상태 |
|----|------|------|------|------|
| E04 | AX 테스트 컴플렉스 온보딩 | 10개 중소기업 | 2025.09~2028.12, 249억 규모 | ⬜ Draft |
| E05 | SaaS 전환 (Kubernetes) | 내부 | 중장기, 온프레미스→SaaS 병행 | ⬜ Draft |

## 기술 개선 (Epic 미배정)

| 작업 | 메모 |
|------|------|
| DocLayout-YOLO Fine-tuning | 8클래스, 29이미지, 라벨링 필요 |
| YOLOv12 업그레이드 | v11→v12 정확도 개선 기대 |

---

## 참조: 고객 온보딩 표준 프로세스

### 다음 고객 프로젝트를 위한 체크리스트

| 단계 | 작업 | 상태 |
|------|------|------|
| 1 | 고객 도면 폴더 수신 | ⬜ |
| 2 | 프로젝트 생성 (`POST /projects`) | ⬜ |
| 3 | BOM PDF 업로드 + 파싱 (`/import-bom`) | ⬜ |
| 4 | 도면 파일 업로드 (`/upload-batch`) | ⬜ |
| 5 | 도면-BOM 매칭 (`/match-drawings`) | ⬜ |
| 6 | 배치 분석 실행 (`/analysis/batch`) | ⬜ |
| 7 | GT 라벨 등록 (선택) | ⬜ |
| 8 | 견적 검토 + 단가 조정 | ⬜ |
| 9 | 납품 패키지 생성 | ⬜ |

### 납품 패키지 생성 프로세스 (표준화)

```bash
# 1. 디렉토리 생성
mkdir -p exports/{customer}-delivery/{images,data}

# 2. 프로젝트 Export
curl -s http://localhost:5020/projects/{project_id}/export \
  -o exports/{customer}-delivery/data/project_{customer}.json

# 3. Docker 이미지 저장 (최초 1회만, 이후 재사용)
docker save blueprint-ai-bom-backend:latest | gzip > images/blueprint-ai-bom-backend.tar.gz
docker save blueprint-ai-bom-frontend:latest | gzip > images/blueprint-ai-bom-frontend.tar.gz

# 4. 설치 파일 복사 (템플릿)
cp dsebearing-delivery/{docker-compose.yml,setup.sh,setup.ps1,README.md} {customer}-delivery/

# 5. 체크섬 생성
cd {customer}-delivery && sha256sum **/* > CHECKSUMS.sha256
```

---

## 참조 문서

| 문서 | 위치 |
|------|------|
| **현재 작업** | `.todo/ACTIVE.md` |
| **완료 아카이브** | `.todo/COMPLETED.md` |
| **Epic 폴더** | `.todo/epics/` |
| **템플릿** | `.todo/templates/` |
| **아키텍처 결정** | `.todo/decisions/` |
| 새 API 추가 가이드 | `.claude/skills/api-creation-guide.md` |
| 모듈화 가이드 | `.claude/skills/modularization-guide.md` |

---

*마지막 업데이트: 2026-02-27 (BMAD-Lite Epic 인덱스 도입)*
