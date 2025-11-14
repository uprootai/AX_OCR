# 🔴 우선순위 1-1: GD&T 도면 수집

**목적**: GD&T 인식률 0% → 75% 개선을 위한 테스트 도면 확보
**소요 시간**: 2-3일
**담당자**: 사용자 (도메인 전문가)

---

## 📋 현재 문제

### 테스트 결과
- **GD&T Recall**: 0% (목표: 75%)
- **원인**: 
  1. 테스트 도면에 GD&T 심볼이 없거나 희미함
  2. Recognizer 모델이 복잡한 심볼 인식 실패

### 필요한 것
GD&T 심볼이 **명확하고 다양한** 공학 도면 10-20개

---

## ✅ 작업 가이드

### 1단계: 도면 요구사항 확인

#### 필수 조건
- ✅ **GD&T 심볼 포함**: 최소 3개 이상/도면
- ✅ **해상도**: 150-300 DPI
- ✅ **선명도**: 심볼이 흐릿하지 않음
- ✅ **형식**: PDF, JPG, PNG

#### 권장 GD&T 심볼 타입
- ⏤ (Flatness - 평면도)
- ⌭ (Cylindricity - 원통도)
- ⊕ (Position - 위치도)
- ∥ (Parallelism - 평행도)
- ⊥ (Perpendicularity - 직각도)
- ∠ (Angularity - 경사도)
- ○ (Runout - 런아웃)

### 2단계: 도면 소스

#### 옵션 1: 내부 도면 (권장)
```bash
위치: /home/uproot/ax/reference/02. 수요처 및 도메인 자료/2. 도면(샘플)/
```

**작업**:
1. 기존 샘플 도면 검토
2. GD&T 심볼 포함 도면 선별
3. 10개 이상 복사 → `/home/uproot/ax/poc/test_data/gdt_drawings/`

#### 옵션 2: 표준 도면 다운로드
- **ASME Y14.5**: https://www.asme.org/codes-standards
- **ISO 1101**: https://www.iso.org/standard/
- **교육 자료**: 
  - Iowa State: https://www.me.iastate.edu/
  - DeAnza College: https://www.deanza.edu/

#### 옵션 3: 제작 요청
- 설계팀에 GD&T 샘플 도면 제작 요청
- 다양한 심볼 포함 요청

### 3단계: 도면 배치

```bash
# 디렉토리 생성
mkdir -p /home/uproot/ax/poc/test_data/gdt_drawings

# 도면 복사
cp /path/to/your/drawings/*.pdf /home/uproot/ax/poc/test_data/gdt_drawings/

# 확인
ls -lh /home/uproot/ax/poc/test_data/gdt_drawings/
```

### 4단계: 테스트 실행

```bash
# 자동 테스트 스크립트 실행 (Claude가 작성함)
cd /home/uproot/ax/poc
python TODO/scripts/test_gdt_recognition.py

# 결과 확인
cat test_results/gdt_recognition_report.txt
```

---

## 📊 성공 기준

### 최소 요구사항
- [ ] **도면 수**: 10개 이상
- [ ] **GD&T 심볼**: 평균 5개/도면
- [ ] **Recall**: 75% 이상

### 이상적 목표
- [ ] **도면 수**: 20개 이상
- [ ] **GD&T 심볼**: 평균 10개/도면
- [ ] **Recall**: 85% 이상

---

## 🔍 품질 체크리스트

도면을 추가하기 전에 확인:

```bash
# 1. 파일 크기 (5MB 이하 권장)
du -h your_drawing.pdf

# 2. 이미지 해상도 (JPG/PNG인 경우)
identify -verbose your_drawing.jpg | grep -i resolution

# 3. PDF 페이지 수 (1페이지 권장)
pdfinfo your_drawing.pdf | grep Pages
```

### 좋은 도면 예시
```
✅ drawing_with_gdt_001.pdf
   - 크기: 2.3MB
   - 해상도: 300 DPI
   - GD&T 심볼: 7개 (⏤, ⊕, ∥, ⊥)
   - 선명도: 우수
```

### 나쁜 도면 예시
```
❌ scanned_drawing.jpg
   - 크기: 15MB
   - 해상도: 72 DPI (너무 낮음)
   - GD&T 심볼: 흐릿함
   - 선명도: 불량
```

---

## 🚨 주의사항

1. **저작권**: 외부 도면 사용 시 라이선스 확인
2. **기밀 정보**: 회사 기밀 도면 제외
3. **개인정보**: 설계자 이름, 연락처 제거

---

## 📞 지원

### 도면 찾기 어려운 경우
1. **설계팀 연락**: GD&T 샘플 도면 요청
2. **온라인 검색**: "GD&T sample drawings PDF"
3. **교육 자료**: 대학 강의 자료 활용

### 테스트 실패 시
1. 도면 품질 재확인 (해상도, 선명도)
2. `TODO/scripts/test_gdt_recognition.py` 로그 확인
3. 실패한 도면 별도 폴더로 분리

---

## ✅ 완료 확인

모든 작업 완료 후:

```bash
# 1. 도면 개수 확인
ls /home/uproot/ax/poc/test_data/gdt_drawings/*.pdf | wc -l
# 출력: 10 이상이어야 함

# 2. 테스트 실행
python TODO/scripts/test_gdt_recognition.py

# 3. 결과 보고서 확인
cat test_results/gdt_recognition_report.txt
# GD&T Recall: 75% 이상이면 성공!
```

---

**작성일**: 2025-11-08
**예상 소요 시간**: 2-3일
**다음 단계**: `PRIORITY_1_VL_API_KEYS.md`
