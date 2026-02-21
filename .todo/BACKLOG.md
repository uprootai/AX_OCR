# 백로그 (향후 작업)

> 마지막 업데이트: 2026-02-21
> 미래 작업 및 참조 문서

---

## 현재 상태 요약

| 항목 | 값 |
|------|-----|
| **동서기연 배치 분석** | 53/53 세션 완료 (100%) |
| **동서기연 납품 패키지** | ✅ 생성 완료 (4.5GB) |
| **총 치수 추출** | 2,710개 (평균 51.1개/세션) |
| **빌드** | ✅ 정상 |
| **ESLint** | 0 errors |
| **노드 정의** | 29개 |
| **API 서비스** | 21개 |
| **P1/P2/P3 작업** | 모두 완료 ✅ |

---

## 신규 고객 온보딩 준비

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

## ~~Agent-Native Verification UI~~ ✅ 완료 (2026-02-21)

> **상세 문서**: [AGENT_NATIVE_VERIFICATION_UI.md](AGENT_NATIVE_VERIFICATION_UI.md)

Phase 1-4 모두 완료. E2E 검증: 147 dimension 항목 전체 처리 (118 approve, 29 reject).
커밋: `0b3fe6d`

---

## 기술 개선 (우선순위 미정)

### DocLayout-YOLO Fine-tuning
- 준비 완료 (8클래스, 29이미지, 라벨링 필요)
- 문서: `models/yolo-api/yolo_training/`

### YOLOv12 업그레이드
- 계획 문서: `YOLOV12_UPGRADE_PLAN.md`
- 현행 v11 → v12 전환 시 정확도 개선 기대

### Claude Code Agent Teams 도입 검토
- 현재 불필요 — subagent 방식으로 충분
- 도입 시점: 프론트/백엔드/AI 동시 대규모 변경 시

---

## 참조 문서

| 문서 | 위치 |
|------|------|
| **현재 작업** | `.todo/ACTIVE.md` |
| **완료 아카이브** | `.todo/COMPLETED.md` |
| **패턴 확산 작업** | `.todo/PENDING_PATTERN_PROPAGATION.md` |
| 새 API 추가 가이드 | `.claude/skills/api-creation-guide.md` |
| 모듈화 가이드 | `.claude/skills/modularization-guide.md` |

---

*마지막 업데이트: 2026-02-21 (Agent Verification UI Phase 1-4 완료)*
