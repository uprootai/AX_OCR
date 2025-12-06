# Tesseract LSTM OCR

## 프로젝트 정보
- **이름**: Tesseract OCR Engine
- **개발사**: HP Labs (1985-1994), Google (2006-2018)
- **현재 관리**: Tesseract OCR Community
- **GitHub**: https://github.com/tesseract-ocr/tesseract
- **라이선스**: Apache 2.0

## 역사
- **1985-1994**: HP Labs에서 개발
- **2005**: HP에서 오픈소스로 공개
- **2006-2017**: Google에서 개발 및 유지보수
- **2016**: Tesseract 4.0 LSTM 엔진 도입

## 핵심 기술

### LSTM 기반 인식 엔진 (v4.0+)
Tesseract 4.0은 LSTM(Long Short-Term Memory) 신경망 기반 인식 엔진을 도입했습니다.

#### 관련 연구
- **논문**: "High-Performance OCR for Printed English and Fraktur using LSTM Networks"
- 양방향 LSTM 네트워크 적용
- 1D 순환 네트워크 + 베이스라인/x-height 정규화

### 엔진 모드
| 모드 | 설명 |
|------|------|
| 0 | Legacy 엔진만 |
| 1 | LSTM 엔진만 |
| 2 | Legacy + LSTM |
| 3 | 기본 (사용 가능한 것 사용) |

## 지원 언어
- 100+ 언어 지원
- 라틴, 키릴, 그리스, 아랍, 히브리, 인도 문자 등
- 한국어, 중국어, 일본어 지원

## 모델 데이터
- **훈련 데이터**: 약 400,000 텍스트 라인
- **폰트 수**: 약 4,500개
- **모델 크기**: 언어별 상이

## 성능
- 문서 이미지에서 높은 정확도
- Legacy 엔진 대비 크게 향상된 성능
- 더 많은 연산 자원 필요

## AX 시스템 적용
- **사용 API**: Tesseract API (Port 5008)
- **용도**: 문서 OCR, 일반 텍스트 인식
- **장점**: 다국어 지원, 안정적, 오랜 검증 역사

## 참고 자료
- GitHub: https://github.com/tesseract-ocr/tesseract
- 문서: https://tesseract-ocr.github.io/tessdoc/
- 훈련 가이드: https://tesseract-ocr.github.io/tessdoc/tess5/TrainingTesseract-5.html
