# docTR: Document Text Recognition

## 프로젝트 정보
- **이름**: docTR (Document Text Recognition)
- **개발사**: Mindee
- **공개일**: 2021년 12월
- **GitHub**: [mindee/doctr](https://github.com/mindee/doctr)
- **라이선스**: Apache 2.0

## 개요
docTR은 딥러닝 기반의 고성능 OCR 라이브러리로, 텍스트 검출과 인식을 위한 2단계 파이프라인을 제공합니다.

## 핵심 특징

### 2단계 OCR 파이프라인
1. **텍스트 검출**: 이미지에서 단어 위치 감지
2. **텍스트 인식**: 검출된 영역에서 문자 인식

### 주요 장점
- 3줄의 코드로 문서 로드 및 텍스트 추출
- Google Vision / AWS Textract 수준의 성능
- TensorFlow 2 및 PyTorch 지원

## 구현된 아키텍처

### 텍스트 검출
| 모델 | 논문 |
|------|------|
| DBNet | Real-time Scene Text Detection with Differentiable Binarization |
| LinkNet | LinkNet: Exploiting Encoder Representations |
| FAST | Faster Arbitrarily-Shaped Text Detector |

### 텍스트 인식
| 모델 | 논문 |
|------|------|
| CRNN | An End-to-End Trainable Neural Network for Image-based Sequence Recognition |
| SAR | Show, Attend and Read |
| MASTER | Multi-Aspect Non-local Network |
| ViTSTR | Vision Transformer for Scene Text Recognition |

## 성능
- 공개 문서 데이터셋에서 SOTA 수준
- Google Vision, AWS Textract와 비교 가능

## 인용
```bibtex
@misc{doctr2021,
    title={docTR: Document Text Recognition},
    author={Mindee},
    year={2021},
    publisher={GitHub},
    howpublished={\url{https://github.com/mindee/doctr}}
}
```

## AX 시스템 적용
- **사용 API**: DocTR API (Port 5014)
- **용도**: 문서 OCR, 2단계 파이프라인
- **장점**: 다양한 백본 선택 가능, SOTA 성능

## 참고 자료
- GitHub: https://github.com/mindee/doctr
- 문서: https://mindee.github.io/doctr/
- 공식: https://www.mindee.com/platform/doctr

---
*참고: docTR은 전용 학술 논문 없이 GitHub 프로젝트로 관리됩니다. 내부적으로 DBNet, CRNN 등의 논문 구현을 사용합니다.*
