# .todos - 작업 추적

> **최종 업데이트**: 2025-12-28 | **버전**: v16.0

---

## 현재 상태

```
시스템: AX POC v16.0
기능: 18/20 (90%)   빌드: ✅ 통과   API: 18/18 healthy
최근 완료: Line Detector v1.1 (스타일 분류, 영역 검출)
```

---

## TECHCROSS POC (진행 중)

### 진행 현황

| Phase | 작업 | 상태 | 상세 |
|-------|------|------|------|
| **완료** | Line Detector 스타일 분류 | ✅ | 6종 스타일 (실선/점선/일점쇄선 등) |
| **완료** | 점선 박스 영역 검출 | ✅ | "SIGNAL FOR BWMS" 영역 자동 검출 |
| Phase 1 | BWMS 장비 태그 인식 | 📋 | ECU, HGU, FMU 등 11종 |
| Phase 1 | Equipment List 자동 생성 | 📋 | Excel 출력 |
| Phase 2 | Valve Signal List 생성 | 📋 | 밸브 카테고리 분류 |
| Phase 2 | BWMS 설계 규칙 검증 | 📋 | 9개 규칙 구현 |
| Phase 3 | 체크리스트 UI | 📋 | 60개 항목 |
| Phase 3 | PDF 리포트 | 📋 | 종합 검토 결과 |

### 다음 작업 (즉시 개발 가능)

```
1. BWMS 장비 태그 패턴 인식 (2-3시간)
   - OCR 결과에서 ECU-001, HGU-002 등 추출
   - 정규식 기반 패턴 매칭

2. Equipment List Excel 출력 (3-4시간)
   - 인식된 장비 목록 → Excel 파일 생성
   - openpyxl 사용
```

### 블로커

| 항목 | 상태 | 대응 |
|------|------|------|
| 체크리스트 xlsm 손상 | ⏳ | 파일 재요청 완료, 회신 대기 |
| BWMS 심볼 학습 데이터 | ⏳ | OCR 기반 우선 구현 |
| POR 원본 문서 | ⏳ | 질문 14번 회신 대기 |

---

## 파일 목록

### TECHCROSS 관련 (신규)

| 파일 | 용도 |
|------|------|
| `TECHCROSS_개발_로드맵.md` | **전체 개발 계획 및 상세 설명** |
| `TECHCROSS_Phase1_즉시개발.md` | **Phase 1 상세 구현 가이드 (코드 포함)** |

### 기존 문서

| 파일 | 용도 |
|------|------|
| `REMAINING_WORK_PLAN.md` | 전체 작업 계획 |
| `2025-12-24_blueprint_ai_bom_feature_roadmap.md` | Blueprint AI BOM 로드맵 |
| `2025-12-24_v8_post_commit_tasks.md` | 테스트 목록 |
| `2025-12-19_blueprint_ai_bom_expansion_proposal.md` | 확장 제안 |
| `2025-12-14_export_architecture.md` | Export 아키텍처 |

### 관련 문서 (apply-company/)

| 파일 | 용도 |
|------|------|
| `TECHCROSS_POC_개발_우선순위.md` | 우선순위 정리 |
| `TECHLOSS_미구현기능_평가.md` | Gap 분석 |
| `TECHCROSS_질문목록_이메일용.txt` | 고객 질문 |

---

## 장기 (필요 시)

| 기능 | 조건 |
|------|------|
| BWMS 전용 YOLO 모델 | 샘플 데이터 확보 후 |
| P&ID 거리 계산 알고리즘 | 스케일 정보 확보 후 |
| 용접 기호 파싱 | 기계 도면 케이스 |
| 표면 거칠기 파싱 | 기계 도면 케이스 |

---

## 빠른 시작

```bash
# TECHCROSS 개발 시작
# 1. 로드맵 확인
cat .todos/TECHCROSS_개발_로드맵.md

# 2. Phase 1 구현 가이드
cat .todos/TECHCROSS_Phase1_즉시개발.md

# 3. 관련 질문 확인
cat apply-company/techloss/about-email-details/TECHCROSS_질문목록_이메일용.txt
```
