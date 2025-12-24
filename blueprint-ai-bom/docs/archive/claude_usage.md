# CLAUDE_GUIDE.md
# DrawingBOMExtractor 프로젝트 완벽 가이드 (2025-09-25 업데이트)

## 📋 프로젝트 개요

이 프로젝트는 YOLOv11/YOLOv8 모델을 활용하여 CAD/PDF 도면에서 산업 부품을 자동 검출하고 가격 정보가 포함된 BOM(자료명세서)을 자동 생성하는 AI 기반 시스템입니다.

**핵심 요구사항**: 8502 (원본)와 8503 (모듈화 버전)은 UI/기능적으로 **완벽히 동일**해야 합니다.

## ✅ 최근 진행상황 (2025-09-26 업데이트)

### 완료된 작업
1. **탭 구조 구현**: 8503에 8502와 동일한 탭 구조 성공적으로 구현
   - "📊 통합 결과 (중복 제거)" 탭
   - "🗳️ Voting 기반 통합" 탭
   - "🔍 OCR 키워드 분석" 탭
   - "🤖 YOLOv11X" (및 기타 모델별) 탭

2. **메서드 구현**: `render_symbol_verification` 메서드에서 탭 기반 UI 렌더링

3. **전체 UI 비교 분석 완료**: 8502와 8503의 상세 차이점 모두 식별

### 남은 작업 (우선순위순)
1. **Ground Truth 관련 오류 수정**: ValueError in ground truth loading
2. **탭 내용 완전 구현**: 각 탭별 세부 기능 8502와 완전 매칭
3. **UI 세밀한 매칭**: 픽셀 단위 동일성 확보
4. **사이드바 차이점 수정**: GPU 정보, 초기화 메시지 등

## 🏗️ 아키텍처 구조

### 원본 시스템 (8502 - real_ai_app.py)
- **파일**: `/home/uproot/panasia/DrawingBOMExtractor/real_ai_app.py` (3342 라인)
- **포트**: 8502
- **특징**: 모놀리식 구조, 모든 기능이 하나의 파일에 구현

### 모듈화 시스템 (8503 - app_modular.py)
- **파일**: `/home/uproot/panasia/DrawingBOMExtractor/app_modular.py`
- **포트**: 8503
- **특징**: 모듈화된 구조, 디자인 패턴 적용
- **요구사항**: 8502와 **100% 동일한** UI/기능

## 🎯 핵심 기능 요구사항

### 1. 검출 결과 표시 ("🔍 AI 검출 결과" 섹션)
8502에서는 다음 구조로 표시되어야 함:

```
🔍 AI 검출 결과
📊 YOLOv11X - 4개 검출 (F1: 25.0%, 정밀도: 25.0%, 재현율: 25.0%)

✅ Ground Truth 로드됨: 4개 라벨

[두 개의 이미지]
🟢 Ground Truth (4개)    |    🔴 YOLOv11X 검출 (4개)

[4개 컬럼 메트릭]
총 검출 수: 4 | 평균 신뢰도: 0.979 | Precision: 25.0% | Recall: 25.0%

🎯 F1 Score: 25.0% (TP:1, FP:3, FN:3)

✅ 통합 결과 (중복 제거)
🗳️ Voting 기반 통합
🔍 OCR 키워드 분석
🤖 YOLOv11X
```

### 2. Ground Truth 기능
- `load_ground_truth_for_current_image()` 메서드 필수
- `calculate_detection_metrics()` 메서드 필수
- `draw_ground_truth_only()` 메서드 필수
- `draw_detections_only()` 메서드 필수
- F1 Score, Precision, Recall 계산 필수

### 3. 성능 분석 UI
- Ground Truth vs 검출 결과 이미지 나란히 표시
- TP, FP, FN 계산 및 표시
- IoU 기반 매칭 알고리즘
- 중복 제거 알고리즘

## 📂 파일 구조 매핑

### 8502 (원본) 주요 메서드
```python
class DrawingBOMExtractor:
    def render_detection_results(self):           # 라인 1164-1273
    def load_ground_truth_for_current_image(self): # 라인 1434-1500
    def calculate_detection_metrics(self):         # 성능 메트릭 계산
    def draw_ground_truth_only(self):             # GT 이미지 그리기
    def draw_detections_only(self):               # 검출 결과 이미지 그리기
    def draw_detection_results(self):             # 라인 1274-1315
```

### 8503 (모듈화) 대응 구조
```python
class DrawingBOMExtractorApp:
    def render_detection_results(self):           # 8502와 동일하게 구현 필요
    def load_ground_truth_for_current_image(self): # 8502에서 이식 필요
    def calculate_detection_metrics(self):         # 8502에서 이식 필요
    def draw_ground_truth_only(self):             # 8502에서 이식 필요
    def draw_detections_only(self):               # 8502에서 이식 필요
```

## 🔧 구현 체크리스트 (2025-09-25 업데이트)

### ✅ Phase 1: 탭 구조 구현 (완료)
- [x] 기본 탭 구조 생성: "📊 통합 결과 (중복 제거)", "🗳️ Voting 기반 통합", "🔍 OCR 키워드 분석"
- [x] 동적 모델별 탭: "🤖 YOLOv11X", "🤖 YOLOv11L" 등
- [x] `render_symbol_verification` 메서드에서 탭 렌더링
- [x] 탭별 전용 메서드 생성: `render_voting_tab`, `render_ocr_analysis_tab`, `render_model_specific_tab`

### 🚧 Phase 2: Ground Truth 시스템 (진행중 - 오류 수정 필요)
- [x] 기본 Ground Truth 로딩 시도
- [ ] **긴급**: ValueError 수정 - `invalid literal for int() with base 10: '#'`
- [ ] `load_ground_truth_for_current_image()` 메서드 이식
- [ ] `load_ground_truth_labels()` 메서드 안정화
- [ ] `data.yaml` 로딩 시스템 구현
- [ ] YOLO 형식 라벨 파싱 오류 처리 강화

### ⏳ Phase 3: 성능 메트릭 시스템
- [ ] `calculate_detection_metrics()` 메서드 이식
- [ ] IoU 계산 알고리즘 구현
- [ ] TP/FP/FN 분류 로직 구현
- [ ] F1/Precision/Recall 계산 구현

### ⏳ Phase 4: 이미지 시각화 시스템
- [ ] `draw_ground_truth_only()` 메서드 이식
- [ ] `draw_detections_only()` 메서드 이식
- [ ] `draw_detection_results()` 메서드 업데이트
- [ ] 색상 체계 동일하게 구현

### ⏳ Phase 5: 탭 내용 완전 구현
- [ ] **"📊 통합 결과 (중복 제거)" 탭**: 8502와 완전 동일한 내용
- [ ] **"🗳️ Voting 기반 통합" 탭**: 모델별 투표 시스템, 가중치 계산
- [ ] **"🔍 OCR 키워드 분석" 탭**: OCR 결과, 키워드 매칭, 신뢰도 부스트
- [ ] **"🤖 모델별" 탭**: 각 모델의 개별 검출 결과, 신뢰도, 바운딩박스

### ⏳ Phase 6: UI 세밀한 매칭
- [ ] 검출 결과 표시 구조 완전 매칭
- [ ] 메트릭 표시 위치/형식 동일
- [ ] 확장 패널 제목 형식 동일
- [ ] 이미지 크기/배치 동일
- [ ] 색상/폰트/간격 픽셀 단위 매칭

## 🚨 중요한 제약사항

### 1. 완벽한 UI 매칭 요구사항
- 텍스트 한 글자도 다르면 안됨
- 레이아웃 구조 완전 동일
- 메트릭 수치 표시 형식 동일
- 색상/아이콘 완전 동일

### 2. 기능적 동일성
- Ground Truth 로딩 동작 완전 동일
- 성능 계산 알고리즘 완전 동일
- 이미지 시각화 완전 동일
- 에러 처리 동작 완전 동일

### 3. 데이터 호환성
- session_state 구조 동일
- 검출 결과 데이터 형식 동일
- 파일 경로 구조 동일

## 🔍 분석 방법론

### 8502 분석 단계
1. `render_detection_results` 메서드 완전 분석
2. Ground Truth 관련 모든 메서드 식별
3. 성능 메트릭 계산 로직 분석
4. UI 레이아웃 구조 상세 매핑
5. 데이터 플로우 완전 추적

### 8503 이식 단계
1. 누락된 메서드들 하나씩 이식
2. UI 구조 8502와 완전 매칭
3. 기능별 단위 테스트 실행
4. 전체 통합 테스트 실행
5. Playwright를 통한 UI 검증

## 💡 주의사항

### Ground Truth 파일 위치
- 경로: `test_drawings/labels/*.txt`
- 형식: YOLO 형식 라벨 파일
- 클래스 매핑: `data.yaml` 참조

### 성능 메트릭 계산
- IoU 임계값: 0.5 (기본)
- TP: IoU >= 0.5인 매칭
- FP: 매칭되지 않은 검출
- FN: 매칭되지 않은 Ground Truth

### UI 레이아웃 세부사항
- 이미지 표시 크기: `int(width * 0.25)`
- 컬럼 구조: Ground Truth 있을 때 4개, 없을 때 3개
- 확장 패널 기본 상태: `expanded=True`

## 📊 8502 vs 8503 완전 비교 분석 (2025-09-26)

### 🔴 사이드바 차이점

#### 1. GPU 정보 표시
- **8502**: `GPU: NVIDIA GeForce RTX 3080 Laptop GPU (8.0GB)` (상세 정보)
- **8503**: `GPU 사용 가능` (단순 표시)
- **수정 필요**: GPU 모델명과 메모리 크기 상세 표시

#### 2. 초기화 메시지
- **8502**: `✅ Enhanced OCR Detector 초기화 완료 (Ground Truth 기반)`
- **8503**:
  ```
  ✅ YOLOv11X 모델 로드 완료 (Device: cuda)
  📌 YOLOv11X 검출기 등록 완료
  ✅ YOLOv11L 모델 로드 완료 (Device: cuda)
  📌 YOLOv11L 검출기 등록 완료
  ```
- **수정 필요**: 모델 로드 메시지 위치 변경, Enhanced OCR 메시지 추가

### 🔴 메인 워크플로우 차이점

#### 1. 파일 업로드 후 표시
- **8502**:
  - `🔍 Enhanced OCR 향상 (Ground Truth 기반)` 옵션 표시
  - 상세한 설명: `✅ Enhanced OCR 활성화: 이중 임계값(0.25/0.1) + Ground Truth 매칭 + PaddleOCR 검증`
  - `💡 추가 옵션: 기존 OCR 향상도 병행 사용 가능`
- **8503**:
  - `🔍 Enhanced OCR 텍스트 인식 향상` (단순 표시)
  - 설명: `✅ OCR 향상 활성화: 심볼 내 텍스트 키워드 매칭으로 신뢰도 부스트`
- **수정 필요**: 8502와 동일한 설명 텍스트 사용

#### 2. 검출 중 상태 메시지
- **8502**:
  ```
  🔍 Enhanced OCR 처리 중...
  🔍 모델 로드 중: yolo_v11x from models/yolo/v11x/best.pt
  🔄 모델 로딩 시도: models/yolo/v11x/best.pt
  ✅ 모델을 GPU로 이동했습니다
  ✅ 모델 로드 성공: models/yolo/v11x/best.pt
  📊 yolo_v11x 검출 시작 (YOLO11-main 최적화)
  🔧 설정: 신뢰도=0.90, IoU=0.45, imgsz=1088
  🖼️ 이미지 크기: 1080x1080, 최대 차원: 1088
  🔍 원시 검출 결과 수: 1
  📦 검출된 박스 수: 4
  📊 검출 신뢰도 범위: 0.968 - 0.986
  YOLO 검출 결과 - 총 4개 객체 검출
  🔄 Enhanced OCR v4.0 Rotation (PaddleOCR API) 처리 중... (총 4개 객체)
  진행: 0/4 (0.0%) - 8_NOISE FILTER_WYFS06T1A (6A)(NF1)_p01
  ```
- **8503**: 검출 중 상태 메시지 없음 (바로 결과 표시)
- **수정 필요**: 검출 중 프로그레스 메시지 추가

#### 3. 검출 결과 섹션
- **동일한 부분**:
  - `🔍 AI 검출 결과` 헤더
  - `📊 YOLOv11X - 4개 검출 (F1: 25.0%, 정밀도: 25.0%, 재현율: 25.0%)`
  - Ground Truth 이미지 표시
  - 성능 메트릭 표시

#### 4. 심볼 검증 섹션
- **8502**: 정상적인 탭 구조와 심볼 검증 UI
  - "📊 통합 결과 (중복 제거)" 탭: 전체 검출 결과 통계
  - "🗳️ Voting 기반 통합" 탭: 모델별 투표 결과
  - "🔍 OCR 키워드 분석" 탭: OCR 텍스트 매칭 결과
  - "🤖 YOLOv11X" 등 모델별 탭: 개별 모델 검출 상세
- **8503**:
  - ✅ 탭 구조 성공적으로 표시
  - ❌ ValueError 오류 발생 (Ground Truth 파싱 문제)
  - 탭은 표시되지만 내용 렌더링 실패

### 🔴 BOM 생성 섹션 차이점
- **8502**:
  - 정상적인 BOM 테이블 표시
  - 부품 목록, 수량, 단가, 총액 계산
  - Excel 다운로드 버튼 제공
- **8503**:
  - 오류로 인해 BOM 섹션까지 도달하지 못함
  - ValueError 해결 후 BOM 섹션 정상 작동 필요

### 🔴 상세 워크플로우 차이점 분석

#### Phase 1: 초기 로드 시점
| 항목 | 8502 | 8503 | 차이점 |
|------|------|------|---------|
| GPU 정보 | "GPU: NVIDIA GeForce RTX 3080 Laptop GPU (8.0GB)" | "GPU 사용 가능" | 상세 정보 누락 |
| 초기화 메시지 | "Enhanced OCR Detector 초기화 완료" | YOLO 모델 로드 메시지들 | 메시지 위치/내용 다름 |
| 샘플 이미지 | 정상 표시 | 정상 표시 | 동일 ✅ |

#### Phase 2: 파일 업로드 후
| 항목 | 8502 | 8503 | 차이점 |
|------|------|------|---------|
| Enhanced OCR 체크박스 | "Enhanced OCR 향상 (Ground Truth 기반)" | "Enhanced OCR 텍스트 인식 향상" | 라벨 텍스트 다름 |
| OCR 설명 | 상세한 기술적 설명 | 간단한 설명 | 설명 상세도 차이 |
| 검출 버튼 | "🔍 AI 검출 실행" | "🔍 AI 검출 실행" | 동일 ✅ |

#### Phase 3: 검출 실행 중
| 항목 | 8502 | 8503 | 차이점 |
|------|------|------|---------|
| 프로그레스 메시지 | 단계별 상세 메시지 | 메시지 없음 | 진행 상황 표시 누락 |
| 모델 로드 상태 | "모델을 GPU로 이동했습니다" 등 | 표시 없음 | 로드 상태 누락 |
| OCR 처리 상태 | "Enhanced OCR v4.0 처리 중..." | 표시 없음 | OCR 진행 상태 누락 |

#### Phase 4: 검출 결과 표시
| 항목 | 8502 | 8503 | 차이점 |
|------|------|------|---------|
| 결과 헤더 | "🔍 AI 검출 결과" | "🔍 AI 검출 결과" | 동일 ✅ |
| 성능 메트릭 | F1, Precision, Recall 표시 | F1, Precision, Recall 표시 | 동일 ✅ |
| Ground Truth 비교 | 정상 표시 | 정상 표시 | 동일 ✅ |
| 이미지 나란히 표시 | GT vs 검출 결과 | GT vs 검출 결과 | 동일 ✅ |

#### Phase 5: 심볼 검증
| 항목 | 8502 | 8503 | 차이점 |
|------|------|------|---------|
| 탭 구조 | 4개+ 탭 정상 작동 | 탭은 표시되나 오류 발생 | ValueError 발생 |
| 통합 결과 탭 | 검출 통계 표시 | 오류로 표시 안됨 | 내용 누락 |
| Voting 탭 | 투표 결과 표시 | 오류로 표시 안됨 | 내용 누락 |
| OCR 분석 탭 | 키워드 매칭 표시 | 오류로 표시 안됨 | 내용 누락 |

#### Phase 6: BOM 생성
| 항목 | 8502 | 8503 | 차이점 |
|------|------|------|---------|
| BOM 테이블 | 정상 생성 | 오류로 도달 못함 | 전체 기능 차단 |
| Excel 다운로드 | 가능 | 불가능 | 기능 차단 |
| 가격 계산 | 정상 작동 | 불가능 | 기능 차단 |

### 🔴 심볼 검증 단계 그리드/버튼 UI 상세 차이점

#### 검출된 심볼 버튼 그리드 레이아웃
**8503에서 확인된 UI 구조** (ValueError 발생하지만 UI는 표시):

```
📋 심볼 검증 및 BOM 생성
📄 검출 결과 - 4개 검출

[탭 구조]
📊 통합 결과 (중복 제거)  |  🗳️ Voting 기반 통합  |  🔍 OCR 키워드 분석  |  🤖 YOLOv11X

[상단 통계 패널]
✅ 심볼 검증 및 수정
전체: 4  |  승인됨: 0  |  거부됨: 0  |  대기중: 4

[일괄 작업 버튼 그룹]
✅ 모두 승인  |  ❌ 모두 거부  |  🔄 초기화

[신뢰도 임계값 슬라이더]
신뢰도 임계값: 0.50 (범위: 0.00-1.00)
🎯 임계값 이상 승인

[검출 결과 리스트]
검출 결과 리스트:
0  ⏳  8_NOISE FILTER_WYFS06T1A (6A)(NF1)_p01
```

#### 버튼 위치 및 그리드 구조 분석
1. **탭 버튼 그룹**:
   - 4개 탭이 수평으로 배치
   - "📊 통합 결과", "🗳️ Voting 기반 통합", "🔍 OCR 키워드 분석", "🤖 YOLOv11X"

2. **통계 정보 패널**:
   - 4개 메트릭을 수평으로 배치 (전체/승인됨/거부됨/대기중)

3. **일괄 작업 버튼**:
   - 3개 버튼을 수평으로 배치
   - "모두 승인", "모두 거부", "초기화"

4. **신뢰도 제어**:
   - 슬라이더와 버튼이 세로로 배치
   - 슬라이더 아래에 "임계값 이상 승인" 버튼

5. **검출 결과 개별 항목**:
   - 각 검출 결과가 리스트 형태로 세로 배치
   - 인덱스, 상태 아이콘, 심볼명 형식

#### UI 레이아웃 특징
- **그리드 시스템**: Streamlit의 column 기반 그리드 활용
- **버튼 그룹핑**: 관련 기능별로 버튼들이 논리적으로 그룹화
- **공간 효율성**: 화면 공간을 효율적으로 사용하는 레이아웃
- **사용성**: 일괄 작업과 개별 작업을 명확히 구분

#### 8502와의 예상 차이점
- **탭 내용**: 8502는 각 탭에 실제 데이터가 표시되지만, 8503은 오류로 인해 내용 누락
- **버튼 상태**: 8502는 모든 버튼이 정상 작동하지만, 8503은 ValueError로 일부 기능 제한
- **그리드 반응성**: 8502와 8503의 그리드 반응성 차이 존재 가능성

## 🚨 긴급 해결 필요한 문제들

### 1. Ground Truth 파싱 오류 (최우선)
```
ValueError: invalid literal for int() with base 10: '#'
File: /home/uproot/panasia/DrawingBOMExtractor/app/components/symbol_verification.py:256
```

**해결 방법**:
1. `symbol_verification.py`의 `_load_ground_truth_labels` 메서드에서 '#'으로 시작하는 주석 라인 건너뛰기
2. YOLO 라벨 파일 파싱시 빈 라인과 주석 라인 예외 처리
3. `data.yaml` 파일 존재 여부 확인 및 예외 처리

### 2. 탭 내용 불완전 (중요)
현재 탭 구조는 생성되었지만 각 탭의 실제 내용이 8502와 다름:

**"📊 통합 결과 (중복 제거)" 탭**:
- 현재: 기본 symbol_verification 컴포넌트만 표시
- 필요: 8502와 완전 동일한 검출 결과 통계, 성능 메트릭, Ground Truth 비교

**"🗳️ Voting 기반 통합" 탭**:
- 현재: 빈 탭
- 필요: 모델별 투표 결과, 가중치 계산, 최종 통합 결과

**"🔍 OCR 키워드 분석" 탭**:
- 현재: 빈 탭
- 필요: OCR 결과, 키워드 매칭 상태, 신뢰도 부스트 정보

**"🤖 모델별" 탭**:
- 현재: 빈 탭
- 필요: 개별 모델의 검출 결과, 바운딩박스, 신뢰도 분포

## 🔧 다음 단계별 실행 계획

### Step 1: Ground Truth 오류 수정 (즉시)
```bash
# 파일 확인
head -20 /home/uproot/panasia/DrawingBOMExtractor/test_drawings/labels/*.txt
cat /home/uproot/panasia/DrawingBOMExtractor/test_drawings/data.yaml
```

### Step 2: 8502 탭별 내용 분석
- real_ai_app.py에서 각 탭의 실제 렌더링 코드 찾기
- 탭별 데이터 구조 및 표시 로직 분석
- UI 컴포넌트 및 레이아웃 구조 매핑

### Step 3: 8503 탭 내용 완전 구현
- 각 탭별 render 메서드에 8502와 동일한 로직 구현
- 데이터 처리 및 표시 형식 완전 매칭
- 에러 처리 및 예외 상황 동일하게 처리

### Step 4: UI 세밀 매칭 검증
- Playwright를 통한 양쪽 UI 비교
- 텍스트, 색상, 간격, 정렬 픽셀 단위 검증
- 사용자 인터랙션 동작 완전 매칭

## 🎯 목표 (업데이트)

**최종 목표**: 사용자가 8502와 8503을 비교할 때 어떤 차이점도 발견할 수 없어야 함.

**현재 상태**: 탭 구조 구현 완료 (70%), 탭 내용 구현 필요 (30%)

**예상 완료**: Ground Truth 오류 수정 후 각 탭별 세부 구현 진행

모든 텍스트, 레이아웃, 기능, 동작이 픽셀 단위로 동일해야 합니다.

## 📋 실행 가능한 명령어 모음

### 즉시 실행해야 할 디버깅 명령어
```bash
# 1. Ground Truth 파일들 확인
ls -la /home/uproot/panasia/DrawingBOMExtractor/test_drawings/labels/
head -10 /home/uproot/panasia/DrawingBOMExtractor/test_drawings/labels/*.txt

# 2. data.yaml 파일 확인
cat /home/uproot/panasia/DrawingBOMExtractor/test_drawings/data.yaml

# 3. 8502와 8503 동시 실행 상태 확인
ps aux | grep streamlit

# 4. 8503 에러 로그 확인
curl http://localhost:8503
```

### 8502 분석용 명령어
```bash
# 8502의 탭 관련 코드 찾기
grep -n "tabs\[" /home/uproot/panasia/DrawingBOMExtractor/real_ai_app.py
grep -n "통합 결과" /home/uproot/panasia/DrawingBOMExtractor/real_ai_app.py
grep -n "Voting 기반" /home/uproot/panasia/DrawingBOMExtractor/real_ai_app.py
grep -n "OCR 키워드" /home/uproot/panasia/DrawingBOMExtractor/real_ai_app.py

# 8502의 Ground Truth 관련 메서드 찾기
grep -n "load_ground_truth" /home/uproot/panasia/DrawingBOMExtractor/real_ai_app.py
grep -n "calculate_detection_metrics" /home/uproot/panasia/DrawingBOMExtractor/real_ai_app.py
```

### UI 비교용 Playwright 명령어
```bash
# 양쪽 페이지 동시 스크린샷 비교
# 8502: http://localhost:8502
# 8503: http://localhost:8503
```

## 🔧 코드 레퍼런스

### 현재 구현 상태 (app_modular.py)
```python
# 탭 구조 구현 위치
def render_symbol_verification(self):  # 라인 855
    # 탭 생성 코드
    fixed_tabs = [
        "📊 통합 결과 (중복 제거)",      # 완료
        "🗳️ Voting 기반 통합",          # 빈 탭
        "🔍 OCR 키워드 분석"             # 빈 탭
    ]
    # 모델별 탭: "🤖 YOLOv11X" etc.     # 빈 탭
```

### 필요한 이식 대상 메서드들 (real_ai_app.py에서)
```python
# 이 메서드들을 찾아서 8503으로 이식 필요
def load_ground_truth_for_current_image(self):
def calculate_detection_metrics(self):
def draw_ground_truth_only(self):
def draw_detections_only(self):
def render_voting_results(self):          # Voting 탭용
def render_ocr_analysis_results(self):    # OCR 분석 탭용
def render_model_specific_results(self):  # 모델별 탭용
```

### 오류 수정 대상 파일
```python
# /home/uproot/panasia/DrawingBOMExtractor/app/components/symbol_verification.py:256
# ValueError: invalid literal for int() with base 10: '#'
# 이 라인에서 '#'으로 시작하는 주석 라인 스킵 처리 필요
```

## 🎯 수정 우선순위 (2025-09-26)

### 🔥 Priority 1: 치명적 오류
1. **Ground Truth 파싱 오류 수정**
   - 파일: `/home/uproot/panasia/DrawingBOMExtractor/app/components/symbol_verification.py:256`
   - 해결: '#'으로 시작하는 주석 라인 스킵 처리

### 🟧 Priority 2: 사이드바 차이
1. **GPU 정보 상세 표시**
   - 현재: "GPU 사용 가능"
   - 필요: "GPU: NVIDIA GeForce RTX 3080 Laptop GPU (8.0GB)"

2. **초기화 메시지 통일**
   - 현재: YOLO 모델 로드 메시지
   - 필요: Enhanced OCR Detector 초기화 메시지

### 🟨 Priority 3: 메인 워크플로우
1. **Enhanced OCR 옵션 설명**
   - 8502와 동일한 텍스트 사용
   - Ground Truth 기반 설명 추가

2. **검출 중 상태 메시지**
   - 프로그레스 메시지 추가
   - OCR 처리 상태 표시

### 🟩 Priority 4: 탭 내용 구현
1. **각 탭별 실제 내용 구현**
   - Voting 기반 통합 로직
   - OCR 키워드 분석 로직
   - 모델별 상세 결과

## 📞 완료 보고 체크리스트

다음 모든 항목이 완료되면 사용자에게 보고:
- [ ] Ground Truth 파싱 오류 100% 해결
- [ ] 사이드바 GPU 정보 8502와 완전 매칭
- [ ] 초기화 메시지 8502와 완전 매칭
- [ ] Enhanced OCR 옵션 설명 8502와 완전 매칭
- [ ] 검출 중 상태 메시지 8502와 완전 매칭
- [ ] "📊 통합 결과 (중복 제거)" 탭 8502와 완전 매칭
- [ ] "🗳️ Voting 기반 통합" 탭 8502와 완전 매칭
- [ ] "🔍 OCR 키워드 분석" 탭 8502와 완전 매칭
- [ ] "🤖 모델별" 탭들 8502와 완전 매칭
- [ ] BOM 생성 섹션 8502와 완전 매칭
- [ ] 에러 없이 완전 동작 확인

**목표**: 사용자가 "하나도 빠짐없이 동일하다"고 만족할 수 있는 수준 달성