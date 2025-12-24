# Optical Character Recognition on Engineering Drawings

## 논문 정보
- **제목**: Optical character recognition on engineering drawings to achieve automation in production quality control
- **저자**: Javier Villena Toro, Anton Wiberg, Mehdi Tarkian
- **소속**: Linköping University, Design Automation Laboratory
- **게재**: Frontiers in Manufacturing Technology, 2023년 3월 20일
- **DOI**: 10.3389/fmtec.2023.1154132

## 연구 배경 및 목적
- 기계 제품의 생산 품질 관리 자동화를 위해서는 디지털화가 필수적
- 공학 도면(Engineering Drawings)은 생산 정보의 핵심 매체이지만 복잡성으로 인해 컴퓨터 비전 적용이 어려움
- 아날로그 도면과 CAD/CAM 소프트웨어 간 원활한 데이터 전송이 필요

## 방법론: eDOCr 도구

### 5단계 파이프라인
1. **이미지 분할(Image Segmentation)**
   - 도면의 주요 요소(정보 블록, 테이블, GD&T 프레임 등)를 분류 및 식별
   - 프레임, 정보 블록, FCF(Feature Control Frame) 감지 및 제거

2. **정보 블록 파이프라인(Information Block Pipeline)**
   - CRAFT 텍스트 감지기 사용
   - 각 박스별로 텍스트 감지 및 인식
   - 텍스트 정렬 알고리즘으로 단어 정리

3. **GD&T 파이프라인(GD&T Pipeline)**
   - 기하 치수 및 공차(Geometric Dimensioning & Tolerancing) 정보 처리
   - 특수 기호 인식용 이중 인식 모델 사용
   - FCF 내 텍스트 정보 추출

4. **치수 파이프라인(Dimension Pipeline)**
   - 이미지를 작은 패치로 분할하여 텍스트 감지
   - 클러스터링 알고리즘으로 근접 예측 결합
   - 공차 확인 알고리즘으로 치수 정보 분리
   - 후처리를 통해 치수 유형 분류

5. **출력 생성(Output Generation)**
   - 3개의 CSV 파일 생성 (정보 블록, GD&T, 치수)
   - 색상으로 구분된 마스크 이미지 제공

### 핵심 알고리즘
- **계층 트리 알고리즘**: 사각형 간 포함 관계 파악
- **Fire Propagation 알고리즘**: 인접 박스 그룹화
- **클러스터링 알고리즘**: 근접 텍스트 결합 (공차 정보 포함)
- **텍스트 정렬 알고리즘**: 감지된 단어를 행과 열로 정렬
- **공차 확인 알고리즘**: 치수 박스 내 공차 정보 식별

## 주요 결과
- **감지 성능**: 정밀도(Precision) 90%, 재현율(Recall) 90%
- **인식 성능**: F1-점수 94%, 문자 오류율(CER) 8%
- 7개의 테스트 도면에서 평균 성능:
  - 텍스트 감지 재현율: 89%
  - 텍스트 감지 정밀도: 92%
  - F1-점수: 94%
  - 문자 오류율: 8.0%

## 기술적 특징
- **지원 형식**: 래스터 이미지 및 PDF 파일
- **사용 모델**:
  - CRAFT (텍스트 감지)
  - CRNN (텍스트 인식) - keras-ocr 기반
- **훈련 데이터**: 자동 생성 샘플 사용
- **특수 문자 지원**: GD&T 기호 인식 가능

## 기존 연구와의 비교
- **DigiEDraw (Scheibel et al., 2021)**: PDF를 HTML로 변환하여 스크래핑
  - 벡터화된 PDF만 지원
  - GD&T 기호 미지원
- **eDOCr의 장점**:
  - 래스터 이미지 및 PDF 지원
  - GD&T 기호 감지 및 인식
  - 모든 방향의 치수 세트 추출 가능

## 한계점 및 향후 과제
1. **인식 성능**: 자동 생성 샘플 기반 훈련으로 정확도 제한
   - 해결책: 실제 도면 라벨링, 폰트 다양화, 하이퍼파라미터 최적화

2. **클러스터링 임계값**: 도면마다 최적 값이 다름
   - 사용자가 수동으로 조정 필요

3. **벡터 도면 미지원**: 현재는 래스터 이미지만 처리
   - 향후 벡터 도면 지원 및 기하학적 정보 검증 계획

4. **정보 블록 제한**: 프레임에 접촉한 박스 내용만 추출
   - 외부에 표시된 일반 정보 누락 가능

## 응용 분야
- 중소 제조업체의 품질 관리 자동화
- 수동 작업 부담 경감
- 도면 정보와 CAM 소프트웨어 간 원활한 통합
- 과거 도면 디지털화 (연간 2억 5천만 개 도면 생성)

## 오픈소스
- GitHub을 통해 연구 커뮤니티에 공유
- Python 패키지로 제공

## 향후 연구 방향
1. 벡터화된 이미지 지원
2. 인식 성능 개선 (라벨링된 데이터셋 구축)
3. 품질 관리 프로세스 완전 자동화
   - 어떤 측정 장치를 사용할지
   - 부품의 어느 위치를 측정할지
   - 특정 요구사항을 어떻게 확인할지
