# Surya: Multilingual OCR with Layout Analysis

## 프로젝트 정보
- **이름**: Surya OCR
- **개발자**: Vik Paruchuri (Datalab)
- **GitHub**: [datalab-to/surya](https://github.com/datalab-to/surya)
- **라이선스**: GPL-3.0
- **인용**: Paruchuri (2024)

## 개요
Surya는 힌두 태양신의 이름을 딴 다국어 OCR 툴킷으로, 90개 이상의 언어에서 텍스트 검출, OCR, 레이아웃 분석, 읽기 순서 감지를 지원합니다.

## 핵심 기능

### 지원 기능
1. **텍스트 검출** - 모든 언어에서 단어 위치 감지
2. **텍스트 인식** - 90+ 언어 OCR
3. **레이아웃 분석** - 문서 구조 파악
4. **읽기 순서 감지** - 텍스트 읽기 순서 결정
5. **테이블 인식** - 표 구조 추출

## 아키텍처

### 텍스트 검출 모델
- **기반**: EfficientViT (수정된 버전)
- **훈련**: 4x A6000에서 3일
- **방식**: Semantic Segmentation

### 텍스트 인식 모델
- **기반**: Donut 아키텍처
- **훈련**: 4x A6000에서 2주
- **언어**: 90+ 언어 지원

## 성능 벤치마크

| 데이터셋 | Precision | Recall |
|----------|-----------|--------|
| DocLayNet | 0.782 | - |
| BCE | 0.751 | - |

### 언어별 성능
- Sinhala: WER 2.61% (최고 성능)
- 다국어 지원에서 우수한 성능

## 특징
- **정확도 우선**: 높은 Precision, trade-off로 낮은 Recall
- **다국어**: 90+ 언어 지원
- **통합 파이프라인**: 검출 + 인식 + 레이아웃

## AX 시스템 적용
- **사용 API**: Surya OCR API (Port 5013)
- **용도**: 다국어 문서 OCR, 레이아웃 분석
- **장점**: 90+ 언어 지원, 레이아웃 분석 내장

## 관련 연구
- EfficientViT - 텍스트 검출 백본
- Donut - 텍스트 인식 백본

## 참고 자료
- GitHub: https://github.com/datalab-to/surya
- Demo: https://huggingface.co/spaces/vikp/surya

---
*참고: Surya는 전용 학술 논문 없이 GitHub 프로젝트로 관리됩니다.*
