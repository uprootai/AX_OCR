# TODO - 사용자 작업 필요 항목

이 디렉토리는 **자동화할 수 없는 사용자 작업**을 정리합니다.

---

## 📋 전체 개선 로드맵

### ✅ 자동 완료 (Claude Code)
- [x] eDOCr2 v2 서비스 복구
- [x] VL 전략 환경 설정
- [x] API 인증 시스템 구조
- [x] Rate limiting 구현
- [x] Retry + Circuit breaker
- [x] 모니터링 설정 (Prometheus)

### 🔴 사용자 작업 필요 (우선순위 1)
- [ ] **GD&T 도면 수집** → `docs/archive/PRIORITY_1_GDT_DRAWINGS.md`
- [ ] **VL API 키 발급** → `docs/archive/PRIORITY_1_VL_API_KEYS.md`

### 🟡 사용자 작업 필요 (우선순위 2)
- [ ] **Skin Model 학습 데이터** → `docs/archive/PRIORITY_2_SKIN_MODEL_DATA.md`
- [ ] **보안 정책 결정** → `docs/archive/PRIORITY_2_SECURITY_POLICY.md`

### 🟢 사용자 작업 필요 (우선순위 3)
- [ ] **GPU 하드웨어 설정** → `docs/archive/PRIORITY_3_GPU_SETUP.md`
- [ ] **프로덕션 배포 준비** → `docs/archive/PRIORITY_3_PRODUCTION.md`

---

## 📂 파일 구조

```
TODO/
├── README.md (이 파일)
├── USER_ACTION_QUICKSTART.md        # 사용자 작업 빠른 시작
├── QUICK_REFERENCE.md                # 빠른 참조 카드
├── STARTUP_GUIDE.md                  # 스타트업 가이드
│
├── 2025-11-13-*.md (5개 최신 작업 기록)
│
├── RnD/                              # 연구개발 자료
└── check/                            # 제출용 신청서
```

**참고**: 우선순위 가이드(PRIORITY_*)는 `docs/archive/`로 이동되었습니다.

---

## 🚀 빠른 시작

### 1단계: 우선순위 1 완료 (1-2주)
```bash
# 1. GD&T 도면 수집
cat docs/archive/PRIORITY_1_GDT_DRAWINGS.md

# 2. VL API 키 발급
cat docs/archive/PRIORITY_1_VL_API_KEYS.md
```

### 2단계: 우선순위 2 완료 (2-4주)
```bash
# 3. Skin Model 데이터 준비
cat docs/archive/PRIORITY_2_SKIN_MODEL_DATA.md

# 4. 보안 정책 결정
cat docs/archive/PRIORITY_2_SECURITY_POLICY.md
```

### 3단계: 우선순위 3 완료 (1-2개월)
```bash
# 5. GPU 설정
cat docs/archive/PRIORITY_3_GPU_SETUP.md

# 6. 프로덕션 배포
cat docs/archive/PRIORITY_3_PRODUCTION.md
```

---

## ✅ 완료 후 체크리스트

### 우선순위 1 완료 시
- [ ] GD&T 도면 10개 이상 수집
- [ ] VL API 키 발급 및 환경변수 설정
- [ ] GD&T Recall 테스트 (목표: 75%+)
- [ ] Dimension Recall 테스트 (목표: 90%+)

### 우선순위 2 완료 시
- [ ] Skin Model 학습 데이터 1000개 이상
- [ ] API 인증 시스템 활성화
- [ ] Rate limiting 설정 (100 req/min)

### 우선순위 3 완료 시
- [ ] GPU 설정 완료 (처리 시간 10초 이하)
- [ ] 모니터링 대시보드 접속 가능
- [ ] 프로덕션 배포 완료

---

**작성일**: 2025-11-08
**자동화 완료**: eDOCr2 v2 복구, 인증/보안 구조, Retry/Circuit breaker, 모니터링
**사용자 작업**: 6개 항목 (GD&T 도면, VL API, Skin Model 데이터, 보안 정책, GPU, 배포)
