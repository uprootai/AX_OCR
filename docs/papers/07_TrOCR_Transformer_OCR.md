# TrOCR: Transformer-based Optical Character Recognition

## 논문 정보
- **제목**: TrOCR: Transformer-based Optical Character Recognition with Pre-trained Models
- **저자**: Minghao Li, Tengchao Lv, Lei Cui, et al. (Microsoft)
- **게재**: AAAI 2023
- **arXiv**: [2109.10282](https://arxiv.org/abs/2109.10282)
- **GitHub**: https://github.com/microsoft/unilm/tree/master/trocr

## 연구 배경
기존 OCR 시스템은 CNN 기반 이미지 인코더와 RNN 기반 텍스트 디코더를 사용했으나, TrOCR은 순수 Transformer 아키텍처를 사용하여 사전 학습된 모델의 장점을 활용합니다.

## 핵심 아키텍처

### Encoder-Decoder 구조
1. **Image Encoder**: Vision Transformer (ViT)
   - BEiT 가중치로 초기화
   - 16x16 고정 크기 패치로 이미지 분할
   - 절대 위치 임베딩 추가

2. **Text Decoder**: Text Transformer
   - RoBERTa 가중치로 초기화
   - 자기회귀적 토큰 생성

### 핵심 장점
- CNN 백본 불필요
- 이미지 특화 귀납적 편향 없음
- 대규모 합성 데이터로 사전 학습 가능
- 외부 언어 모델 불필요

## 모델 변형
| 모델 | 용도 | Hugging Face |
|------|------|--------------|
| TrOCR-small | 인쇄체 | microsoft/trocr-small-printed |
| TrOCR-base | 손글씨 | microsoft/trocr-base-handwritten |
| TrOCR-large | 인쇄체 | microsoft/trocr-large-printed |

## 성능
- 인쇄체, 손글씨, 장면 텍스트 인식에서 SOTA 달성
- IAM 손글씨 데이터셋에서 우수한 성능

## AX 시스템 적용
- **사용 API**: TrOCR API (Port 5009)
- **용도**: 손글씨 텍스트 인식, 고품질 OCR
- **장점**: Transformer 기반, 사전 학습 모델 활용

## 참고 자료
- GitHub: https://github.com/microsoft/unilm/tree/master/trocr
- Hugging Face: https://huggingface.co/microsoft/trocr-base-handwritten
