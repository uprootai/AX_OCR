# AX 실증산단 프로젝트 문서 인덱스

**작성일**: 2025-11-03
**버전**: v1.0
**프로젝트**: YOLOv11 기반 공학 도면 분석 시스템

---

## 📚 문서 목록

### 🎯 필수 문서 (시작하기)

| 문서명 | 파일 | 설명 | 대상 |
|--------|------|------|------|
| **프로젝트 개요** | `README.md` | 전체 시스템 개요 및 마이크로서비스 구성 | 모든 사용자 |
| **빠른 시작** | `YOLOV11_QUICKSTART.md` | YOLOv11 5분 빠른 시작 가이드 | 개발자 |
| **합성 데이터 빠른 시작** | `SYNTHETIC_DATA_QUICKSTART.md` | 합성 데이터 생성 빠른 가이드 | 개발자 |
| **통합 실행 가이드** | `KOREAN_EXECUTION_GUIDE.md` | 한국어 완전 실행 가이드 | 개발자/운영자 |

### 📖 상세 기술 문서

| 문서명 | 파일 | 설명 | 대상 |
|--------|------|------|------|
| **YOLOv11 제안서** | `YOLOV11_PROPOSAL.md` | VL API vs YOLO 비교 및 제안 | 의사결정자 |
| **의사결정 매트릭스** | `DECISION_MATRIX.md` | 솔루션 선택 기준 및 평가 | 의사결정자 |
| **구현 가이드** | `YOLOV11_IMPLEMENTATION_GUIDE.md` | 상세 구현 방법 (데이터/학습/추론) | 개발자 |
| **합성 데이터 전략** | `SYNTHETIC_DATA_STRATEGY.md` | 합성 데이터 생성 전략 및 방법론 | 개발자/연구자 |
| **최종 구현 보고서** | `FINAL_IMPLEMENTATION_SUMMARY.md` | 전체 구현 결과 및 성과 요약 | 모든 사용자 |

### 🛠️ 운영 문서

| 문서명 | 파일 | 설명 | 대상 |
|--------|------|------|------|
| **API 사용 매뉴얼** | `API_USAGE_MANUAL.md` | 전체 API 엔드포인트 상세 설명 | API 사용자 |
| **트러블슈팅 가이드** | `TROUBLESHOOTING_GUIDE.md` | 문제 해결 방법 | 개발자/운영자 |
| **문서 인덱스** | `DOCUMENTATION_INDEX.md` | 이 문서 (전체 문서 가이드) | 모든 사용자 |

### 🔍 기술 분석 문서

| 문서명 | 파일 | 설명 | 대상 |
|--------|------|------|------|
| **Bbox 검증 보고서** | `BBOX_VERIFICATION_REPORT.md` | 바운딩 박스 정확도 검증 | 개발자 |
| **Bbox 불일치 수정** | `BBOX_INDEX_MISMATCH_FIX.md` | 인덱스 불일치 문제 해결 | 개발자 |

---

## 🗺️ 문서 사용 로드맵

### 👤 사용자별 추천 문서

#### 의사결정자 / PM
1. `README.md` - 프로젝트 전체 개요
2. `YOLOV11_PROPOSAL.md` - 솔루션 제안 및 비교
3. `DECISION_MATRIX.md` - 의사결정 근거
4. `FINAL_IMPLEMENTATION_SUMMARY.md` - 구현 결과

#### 개발자 (처음 시작)
1. `README.md` - 프로젝트 개요
2. `YOLOV11_QUICKSTART.md` - 빠른 시작 (5분)
3. `KOREAN_EXECUTION_GUIDE.md` - 상세 실행 방법
4. `SYNTHETIC_DATA_QUICKSTART.md` - 합성 데이터 생성
5. `API_USAGE_MANUAL.md` - API 사용법

#### 개발자 (심화)
1. `YOLOV11_IMPLEMENTATION_GUIDE.md` - 상세 구현 가이드
2. `SYNTHETIC_DATA_STRATEGY.md` - 합성 데이터 전략
3. `TROUBLESHOOTING_GUIDE.md` - 문제 해결

#### API 사용자 / 프론트엔드 개발자
1. `README.md` - 시스템 개요
2. `API_USAGE_MANUAL.md` - API 상세 사용법
3. `TROUBLESHOOTING_GUIDE.md` - 에러 해결

#### 시스템 관리자 / DevOps
1. `KOREAN_EXECUTION_GUIDE.md` - 실행 가이드
2. `TROUBLESHOOTING_GUIDE.md` - 문제 해결
3. `README.md` - Docker Compose 설정

---

## 📋 단계별 학습 경로

### Phase 1: 이해하기 (1-2시간)
```
1. README.md (10분)
   ↓
2. YOLOV11_PROPOSAL.md (20분)
   ↓
3. FINAL_IMPLEMENTATION_SUMMARY.md (30분)
```

**목표**: 프로젝트 전체 이해

---

### Phase 2: 실행하기 (2-3시간)
```
1. YOLOV11_QUICKSTART.md (5분 읽기)
   ↓
2. KOREAN_EXECUTION_GUIDE.md (10분 읽기)
   ↓
3. 실제 실행 (1-2시간)
   - 합성 데이터 생성
   - 모델 학습
   - API 서버 실행
   ↓
4. TROUBLESHOOTING_GUIDE.md (문제 발생 시)
```

**목표**: 시스템 실행 및 검증

---

### Phase 3: 개발하기 (1-2주)
```
1. YOLOV11_IMPLEMENTATION_GUIDE.md
   ↓
2. SYNTHETIC_DATA_STRATEGY.md
   ↓
3. API_USAGE_MANUAL.md
   ↓
4. 실제 데이터 수집 및 학습
```

**목표**: 프로덕션 모델 개발

---

### Phase 4: 배포하기 (1주)
```
1. KOREAN_EXECUTION_GUIDE.md (섹션 5: 통합 시스템)
   ↓
2. API_USAGE_MANUAL.md
   ↓
3. Docker Compose 배포
   ↓
4. TROUBLESHOOTING_GUIDE.md (모니터링)
```

**목표**: 프로덕션 배포

---

## 🔍 주제별 문서 찾기

### 학습 (Training)
- 빠른 시작: `YOLOV11_QUICKSTART.md`
- 상세 가이드: `YOLOV11_IMPLEMENTATION_GUIDE.md` (섹션 3)
- 실행 방법: `KOREAN_EXECUTION_GUIDE.md` (섹션 3)
- 문제 해결: `TROUBLESHOOTING_GUIDE.md` (섹션 2)

### 합성 데이터
- 빠른 시작: `SYNTHETIC_DATA_QUICKSTART.md`
- 전략: `SYNTHETIC_DATA_STRATEGY.md`
- 실행 방법: `KOREAN_EXECUTION_GUIDE.md` (섹션 3.1)
- 문제 해결: `TROUBLESHOOTING_GUIDE.md` (섹션 6.1)

### API 사용
- 전체 API: `API_USAGE_MANUAL.md`
- 실행: `KOREAN_EXECUTION_GUIDE.md` (섹션 4)
- 문제 해결: `TROUBLESHOOTING_GUIDE.md` (섹션 3)

### Docker / 배포
- 개요: `README.md` (섹션: 빠른 시작)
- 실행: `KOREAN_EXECUTION_GUIDE.md` (섹션 4-5)
- 문제 해결: `TROUBLESHOOTING_GUIDE.md` (섹션 4)

### 성능 평가
- 예상 성능: `FINAL_IMPLEMENTATION_SUMMARY.md` (섹션: 성능 로드맵)
- 평가 방법: `YOLOV11_IMPLEMENTATION_GUIDE.md` (섹션 5)
- 실행: `KOREAN_EXECUTION_GUIDE.md` (섹션 6)

---

## 📊 문서 통계

### 전체 문서 개수
- **필수 문서**: 4개
- **상세 기술 문서**: 5개
- **운영 문서**: 3개
- **기술 분석 문서**: 2개
- **총**: 14개

### 총 페이지 수 (추정)
- 약 200+ 페이지 (A4 기준)

### 주요 토픽
- YOLOv11 구현: 5개 문서
- 합성 데이터: 3개 문서
- API 사용: 2개 문서
- 트러블슈팅: 1개 문서
- 기타: 3개 문서

---

## 🎯 빠른 참조

### 즉시 시작하려면
```bash
# 1. 이 문서 읽기
cat YOLOV11_QUICKSTART.md

# 2. 합성 데이터 생성
python scripts/generate_synthetic_random.py --count 1000

# 3. 학습 실행
./scripts/train_with_synthetic.sh
```

**상세 내용**: `YOLOV11_QUICKSTART.md`, `KOREAN_EXECUTION_GUIDE.md`

---

### API 사용법 찾기
```bash
# Swagger UI
open http://localhost:5005/docs

# 또는 문서 확인
cat API_USAGE_MANUAL.md
```

---

### 문제 해결
```bash
# 트러블슈팅 가이드
cat TROUBLESHOOTING_GUIDE.md

# 에러 코드별 검색
grep "CUDA out of memory" TROUBLESHOOTING_GUIDE.md
```

---

## 📝 문서 작성 기준

### 스타일 가이드
- **언어**: 한국어 (기술 용어는 영문 병기)
- **형식**: Markdown (GitHub Flavored)
- **코드 블록**: 실행 가능한 예제 제공
- **구조**: 섹션 번호 + 제목

### 업데이트 정책
- **주기**: 주요 변경 시 즉시 업데이트
- **버전**: 날짜 기반 (YYYY-MM-DD)
- **리뷰**: 최소 1명 이상 검토

---

## 🔗 외부 참조

### 공식 문서
- **Ultralytics YOLOv11**: https://docs.ultralytics.com/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Docker**: https://docs.docker.com/

### 연구 논문
- YOLOv11: (링크 추가 예정)
- Engineering Drawing Analysis: (관련 논문)

### 관련 프로젝트
- eDOCr: (내부 문서)
- EDGNet: (내부 문서)

---

## 📞 문서 관련 문의

### 문서 오류 신고
- **방법**: GitHub Issues 또는 dev@uproot.com
- **포함 내용**: 문서명, 섹션, 오류 내용

### 문서 추가 요청
- **방법**: GitHub Issues 또는 내부 Slack
- **포함 내용**: 필요한 문서 주제 및 목적

### 기여 방법
1. 문서 작성 (Markdown)
2. Pull Request 생성
3. 리뷰 후 병합

---

## 🎓 추가 학습 자료

### 온라인 강좌
- Ultralytics YOLOv8/v11 Tutorial (YouTube)
- FastAPI 완벽 가이드 (Udemy)

### 커뮤니티
- Ultralytics Discord
- FastAPI Gitter

### 블로그
- 프로젝트 블로그 (내부)
- Ultralytics 공식 블로그

---

## 🗂️ 문서 구조도

```
AX 실증산단 프로젝트
│
├── 📘 시작하기
│   ├── README.md
│   ├── YOLOV11_QUICKSTART.md
│   ├── SYNTHETIC_DATA_QUICKSTART.md
│   └── KOREAN_EXECUTION_GUIDE.md
│
├── 📗 기술 문서
│   ├── YOLOV11_PROPOSAL.md
│   ├── DECISION_MATRIX.md
│   ├── YOLOV11_IMPLEMENTATION_GUIDE.md
│   ├── SYNTHETIC_DATA_STRATEGY.md
│   └── FINAL_IMPLEMENTATION_SUMMARY.md
│
├── 📙 운영 문서
│   ├── API_USAGE_MANUAL.md
│   ├── TROUBLESHOOTING_GUIDE.md
│   └── DOCUMENTATION_INDEX.md (이 문서)
│
└── 📕 기술 분석
    ├── BBOX_VERIFICATION_REPORT.md
    └── BBOX_INDEX_MISMATCH_FIX.md
```

---

## ✅ 문서 완성도 체크리스트

- [x] README.md - 프로젝트 개요
- [x] YOLOV11_QUICKSTART.md - 빠른 시작
- [x] SYNTHETIC_DATA_QUICKSTART.md - 합성 데이터 빠른 시작
- [x] KOREAN_EXECUTION_GUIDE.md - 통합 실행 가이드
- [x] YOLOV11_PROPOSAL.md - 제안서
- [x] DECISION_MATRIX.md - 의사결정 매트릭스
- [x] YOLOV11_IMPLEMENTATION_GUIDE.md - 구현 가이드
- [x] SYNTHETIC_DATA_STRATEGY.md - 합성 데이터 전략
- [x] FINAL_IMPLEMENTATION_SUMMARY.md - 최종 보고서
- [x] API_USAGE_MANUAL.md - API 매뉴얼
- [x] TROUBLESHOOTING_GUIDE.md - 트러블슈팅
- [x] DOCUMENTATION_INDEX.md - 문서 인덱스
- [x] BBOX_VERIFICATION_REPORT.md - Bbox 검증
- [x] BBOX_INDEX_MISMATCH_FIX.md - Bbox 수정

**완성도**: 14/14 (100%) ✅

---

## 🎉 문서 활용 팁

### 검색하기
```bash
# 전체 문서에서 키워드 검색
grep -r "CUDA" *.md

# 특정 섹션 찾기
grep -A 5 "## 3. YOLOv11 학습" KOREAN_EXECUTION_GUIDE.md
```

### PDF 변환
```bash
# Markdown → PDF (pandoc 사용)
pandoc KOREAN_EXECUTION_GUIDE.md -o guide.pdf

# 또는 온라인 도구 사용
# https://www.markdowntopdf.com/
```

### 오프라인 사용
```bash
# 전체 문서 다운로드
git clone <repository>
cd poc

# 로컬에서 열기
typora *.md  # Typora 에디터 사용
# 또는
code *.md    # VS Code 사용
```

---

**작성자**: AX 실증사업팀
**최종 업데이트**: 2025-11-03
**문의**: dev@uproot.com

---

**이 인덱스는 프로젝트 문서의 마스터 가이드입니다.**
**새로운 문서 추가 시 반드시 이 인덱스를 업데이트하세요.**
