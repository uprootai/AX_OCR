# EasyOCR: Ready-to-use OCR

## 프로젝트 정보
- **이름**: EasyOCR
- **개발사**: JaidedAI
- **GitHub**: [JaidedAI/EasyOCR](https://github.com/JaidedAI/EasyOCR)
- **라이선스**: Apache 2.0
- **PyPI**: https://pypi.org/project/easyocr/

## 개요
EasyOCR은 80개 이상의 언어를 지원하는 범용 OCR 파이썬 모듈로, 자연 장면 텍스트와 문서 내 밀집 텍스트를 모두 인식할 수 있습니다.

## 지원 문자 체계
- Latin (라틴)
- Chinese (중국어)
- Arabic (아랍어)
- Devanagari (데바나가리)
- Cyrillic (키릴)
- 기타 80+ 언어

## 핵심 아키텍처

### 텍스트 검출: CRAFT
- **논문**: Character Region Awareness for Text Detection
- **저자**: Youngmin Baek et al. (CLOVA AI)
- **특징**: 문자 영역 인식 기반 텍스트 검출

### 텍스트 인식: CRNN
- **논문**: An End-to-End Trainable Neural Network for Image-based Sequence Recognition
- **구성**:
  - Feature Extraction: ResNet / VGG
  - Sequence Labeling: BiLSTM
  - Decoding: CTC
- **네트워크**: None-VGG-BiLSTM-CTC

### 프레임워크
- PyTorch 기반

## 설계 철학
> "최신 SOTA 모델을 EasyOCR에 플러그인할 수 있게 하자. 우리는 천재가 아니라, 그들의 작업을 대중에게 무료로 빠르게 제공하려는 것이다."

## 관련 프로젝트
- CRAFT: https://github.com/clovaai/CRAFT-pytorch
- deep-text-recognition-benchmark: https://github.com/clovaai/deep-text-recognition-benchmark

## 성능
- CPU 친화적 설계
- 빠른 추론 속도
- 80+ 언어 지원

## AX 시스템 적용
- **사용 API**: EasyOCR API (Port 5015)
- **용도**: 다국어 OCR, 범용 텍스트 인식
- **장점**: 간편한 사용, CPU 친화적, 넓은 언어 지원

## 참고 자료
- GitHub: https://github.com/JaidedAI/EasyOCR
- Demo: https://www.jaided.ai/easyocr/
- 문서: https://www.jaided.ai/easyocr/documentation/

---
*참고: EasyOCR은 전용 학술 논문 없이 GitHub 프로젝트로 관리됩니다. CRAFT와 CRNN 논문의 구현을 사용합니다.*
