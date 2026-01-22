# 디렉토리 감사 계획서

> **목적**: /home/uproot/ax/poc 하위 모든 디렉토리의 필요/불필요 여부 조사
> **시작일**: 2026-01-17
> **예상 소요**: 장기 작업

---

## 📋 감사 기준

### 필요 여부 판단 기준

| 기준 | 필요 | 불필요 |
|------|------|--------|
| **활성 사용** | 현재 코드에서 참조됨 | 참조 없음 |
| **최근 수정** | 30일 내 수정 | 6개월+ 미수정 |
| **빌드 필수** | 빌드/실행에 필요 | 빌드 무관 |
| **문서화** | 프로젝트 이해에 필수 | 오래된/중복 문서 |
| **테스트** | 테스트 코드/데이터 | 임시 테스트 결과 |
| **모델** | 운영 모델 파일 | 실험용/백업 모델 |

### 조치 분류

- ✅ **유지**: 필수 디렉토리
- ⚠️ **검토**: 일부 정리 필요
- 🗑️ **삭제 후보**: 불필요 가능성 높음
- 📦 **아카이브**: 별도 보관 필요

---

## 💾 용량 분석 (총 ~8.3GB)

| 순위 | 디렉토리 | 용량 | 비율 | 우선 검토 |
|------|----------|------|------|-----------|
| 1 | `offline_models/` | 4.5GB | 54% | ⭐⭐⭐ |
| 2 | `models/` | 1.8GB | 22% | ⭐⭐ |
| 3 | `experiments/` | 656MB | 8% | ⭐⭐⭐ |
| 4 | `data/` | 531MB | 6% | ⭐⭐ |
| 5 | `web-ui/` | 487MB | 6% | ⭐ |
| 6 | `blueprint-ai-bom/` | 203MB | 2% | ⭐ |
| 7 | 기타 | ~130MB | 2% | - |

> **💡 정리 효과**: offline_models + experiments 정리 시 최대 5GB 확보 가능

---

## 📁 조사 대상 디렉토리 (24개)

### Phase 1: 핵심 코드 (우선순위 높음) - ✅ 완료

| # | 디렉토리 | 용량 | 설명 | 상태 | 조치 |
|---|----------|------|------|------|------|
| 1 | `web-ui/` | 487MB | React 프론트엔드 | ✅ 유지 | test-results/playwright-report 정리 가능 |
| 2 | `gateway-api/` | 19MB | FastAPI 게이트웨이 | ✅ 유지 | results/htmlcov 정리 가능 |
| 3 | `models/` | 1.8GB | 20개 API 서비스 | ✅ 유지 | uploads/results/training ~800MB 정리 가능 |
| 4 | `blueprint-ai-bom/` | 1.2GB | BOM 생성 시스템 | ✅ 유지 | models/에 988MB AI 웨이트 포함 |

**상세 결과**: `AUDIT_PHASE1_CORE.md`

### Phase 2: 설정 및 인프라 - ✅ 완료

| # | 디렉토리 | 용량 | 설명 | 상태 | 조치 |
|---|----------|------|------|------|------|
| 5 | `.claude/` | 224KB | Claude Code 설정 | ✅ 유지 | 개발 생산성 필수 |
| 6 | `.github/` | 36KB | GitHub Actions | ✅ 유지 | CI/CD 파이프라인 |
| 7 | `.vscode/` | 12KB | VSCode 설정 | ✅ 유지 | 팀 환경 일관성 |
| 8 | `monitoring/` | 72KB | Grafana/Prometheus | ✅ 유지 | 프로덕션 모니터링 |
| 9 | `scripts/` | 428KB | 유틸리티 스크립트 | ✅ 유지 | 운영/개발 유틸리티 |

**상세 결과**: `AUDIT_PHASE2_INFRA.md`

### Phase 3: 문서 및 연구 - ✅ 완료

| # | 디렉토리 | 용량 | 설명 | 상태 | 조치 |
|---|----------|------|------|------|------|
| 10 | `docs/` | 5.8MB | 프로젝트 문서 | ✅ 유지 | 설치/배포/운영 가이드 |
| 11 | `rnd/` | 52MB | R&D 자료 | ✅ ⚠️ 검토 | experiments/models 39MB |
| 12 | `notion/` | 20KB | Notion 백업 | ✅ ⚠️ 검토 | 레거시, docs/로 통합 고려 |
| 13 | `idea-thinking/` | 36KB | 아이디어 정리 | ✅ 유지 | R&D 연계 |

**상세 결과**: `AUDIT_PHASE3_DOCS.md`

### Phase 4: 데이터 및 모델 ⭐ (용량 대) - ✅ 완료

| # | 디렉토리 | 용량 | 설명 | 상태 | 조치 |
|---|----------|------|------|------|------|
| 14 | `offline_models/` | **4.5GB** | 오프라인 모델 | ✅ 유지 | 오프라인 배포용 필수 |
| 15 | `data/` | **531MB** | Neo4j 데이터 | ✅ 유지 | 운영 데이터 |
| 16 | `samples/` | 644KB | 샘플 파일 | ⚠️ 검토 | web-ui/public/samples와 중복 |

**상세 결과**: `AUDIT_PHASE4_DATA.md`

### Phase 5: 실험 및 임시 ⭐ (정리 후보) - ✅ 완료

| # | 디렉토리 | 용량 | 설명 | 상태 | 조치 |
|---|----------|------|------|------|------|
| 17 | `experiments/` | **656MB** | 실험 코드/모델 | ✅ ⚠️ 검토 | 아카이브 후보 (656MB 절감 가능) |
| 18 | `backend/` | 4KB | 빈 디렉토리 | ✅ 🗑️ 삭제 | 즉시 삭제 가능 |
| 19 | `test-results/` | 8KB | Playwright 출력 | ✅ 유지 | 테스트 인프라 |
| 20 | `api-guide-sample/` | 716KB | API 가이드 문서 | ✅ ⚠️ 검토 | docs/로 통합 고려 |

**상세 결과**: `AUDIT_PHASE5_TEMP.md`

### Phase 6: 기타 - ✅ 완료

| # | 디렉토리 | 용량 | 설명 | 상태 | 조치 |
|---|----------|------|------|------|------|
| 21 | `.todo/` | 168KB | TODO 관리 (현재 사용) | ✅ 유지 | 현재 활발히 사용 중 |
| 22 | `.todos/` | 300KB | 구 TODO (레거시) | ✅ ⚠️ 검토 | 삭제 또는 통합 고려 |
| 23 | `apply-company/` | **52MB** | 회사 지원 자료 | ✅ 유지 | E2E 테스트 의존 |
| 24 | `.git/` | 170MB | Git 저장소 | ✅ 유지 | gc 실행 권장 |

**상세 결과**: `AUDIT_PHASE6_MISC.md`

---

## 📊 조사 템플릿

각 디렉토리 조사 시 아래 형식으로 기록:

```markdown
### [디렉토리명]

**경로**: /home/uproot/ax/poc/[디렉토리]
**용량**: XX MB
**파일 수**: XX개
**최종 수정**: YYYY-MM-DD

#### 구조
- 하위 디렉토리 목록
- 주요 파일 목록

#### 용도
- 현재 사용 목적
- 다른 디렉토리와의 관계

#### 참조 분석
- 이 디렉토리를 참조하는 코드
- 이 디렉토리가 참조하는 외부 리소스

#### 판정
- **결론**: ✅ 유지 / ⚠️ 검토 / 🗑️ 삭제 / 📦 아카이브
- **사유**:
- **조치 사항**:
```

---

## 📈 진행 현황

| Phase | 대상 | 완료 | 진행률 | 예상 용량 절감 |
|-------|------|------|--------|----------------|
| **Phase 1** | **4개** | **4개** | **100%** | **~830MB (런타임 아티팩트)** |
| **Phase 2** | **5개** | **5개** | **100%** | **0 (모두 필수)** |
| **Phase 3** | **4개** | **4개** | **100%** | **~41MB (rnd/models 아카이브 시)** |
| **Phase 4** | **3개** | **3개** | **100%** | **644KB (samples 중복)** |
| **Phase 5** | **4개** | **4개** | **100%** | **656MB (experiments 아카이브 시)** |
| **Phase 6** | **4개** | **4개** | **100%** | **~100MB (git gc 시)** |
| **전체** | **24개** | **24개** | **100%** | **~1.6GB** |

---

## 🎯 최종 요약 (감사 완료)

### 전체 현황

| 항목 | 값 |
|------|-----|
| **총 디렉토리** | 24개 |
| **총 용량** | ~8.3GB |
| **조사 완료** | 100% (24/24) |
| **정리 가능 용량** | ~1.6GB |

### 판정 결과

| 판정 | 디렉토리 수 | 용량 |
|------|------------|------|
| ✅ 필수 유지 | 17개 | ~6.7GB |
| ⚠️ 검토/정리 가능 | 7개 | ~1.6GB |
| 🗑️ 즉시 삭제 가능 | 1개 (backend/) | 4KB |

### 용량 절감 우선순위

| 순위 | 항목 | 절감 가능 | 조건 |
|------|------|----------|------|
| 1 | `models/` 런타임 아티팩트 | ~800MB | uploads/results/training 정리 |
| 2 | `experiments/` 아카이브 | ~656MB | 외부 저장소 이동 |
| 3 | `git gc --aggressive` | ~100MB | 즉시 실행 가능 |
| 4 | `rnd/experiments/models/` | ~39MB | 실험 완료 시 |
| 5 | 기타 | ~5MB | samples/, notion/ 등 |

### 즉시 실행 가능 정리 명령어

```bash
# 1. 빈 디렉토리 삭제 (4KB)
rmdir /home/uproot/ax/poc/backend

# 2. Git 압축 (~100MB 절감)
cd /home/uproot/ax/poc && git gc --aggressive

# 3. 런타임 아티팩트 정리 (~800MB 절감)
rm -rf models/yolo-api/uploads/* models/yolo-api/training/* models/yolo-api/results/*
rm -rf models/edgnet-api/training/* models/edgnet-api/uploads/*
rm -rf models/edocr2-v2-api/results/* models/edocr2-v2-api/uploads/*
rm -rf gateway-api/results/* gateway-api/htmlcov/
rm -rf web-ui/test-results/* web-ui/playwright-report/*
rm -rf blueprint-ai-bom/uploads/* blueprint-ai-bom/results/*
find models/ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
```

### 결정 필요 항목

| 항목 | 용량 | 결정 사항 |
|------|------|----------|
| `experiments/` | 656MB | 외부 저장소 이동 or 삭제 |
| `.todos/` | 300KB | `.todo/`로 통합 or 삭제 |
| `samples/` | 644KB | web-ui/public/samples 사용으로 전환 |
| `notion/` | 20KB | docs/로 통합 or 삭제 |
| `api-guide-sample/` | 716KB | docs/로 통합 |

---

## 📝 조사 결과 파일

각 Phase 완료 시 별도 파일로 결과 기록:

- `AUDIT_PHASE1_CORE.md` - 핵심 코드
- `AUDIT_PHASE2_INFRA.md` - 설정 및 인프라
- `AUDIT_PHASE3_DOCS.md` - 문서 및 연구
- `AUDIT_PHASE4_DATA.md` - 데이터 및 모델
- `AUDIT_PHASE5_TEMP.md` - 실험 및 임시
- `AUDIT_PHASE6_MISC.md` - 기타

---

## ⚠️ 주의사항

1. **삭제 전 백업**: 삭제 결정 시 반드시 백업 후 진행
2. **의존성 확인**: 다른 코드에서 참조하는지 grep으로 확인
3. **Git 히스토리**: 최근 커밋 내역 확인
4. **용량 우선**: 큰 디렉토리부터 정리 시 효과 큼
5. **운영 영향**: 운영 중인 서비스에 영향 없는지 확인

---

## 🚀 시작 명령어

```bash
# 디렉토리 용량 확인
du -sh /home/uproot/ax/poc/*/ | sort -hr

# 최근 수정 파일 확인
find /home/uproot/ax/poc/[DIR] -type f -mtime -30 | head -20

# 참조 검색
grep -r "[DIR]" /home/uproot/ax/poc --include="*.py" --include="*.ts" --include="*.tsx"

# Git 최근 커밋
git log --oneline -10 -- [DIR]
```

---

**작성자**: Claude Code (Opus 4.5)
**버전**: v2.0 (감사 완료)
**완료일**: 2026-01-17
