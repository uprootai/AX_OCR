# ESRGAN: Enhanced Super-Resolution Generative Adversarial Networks

## 논문 정보
- **제목**: ESRGAN: Enhanced Super-Resolution Generative Adversarial Networks
- **저자**: Xintao Wang, Ke Yu, Shixiang Wu, et al.
- **게재**: ECCV 2018 PIRM Workshop (1위 수상)
- **arXiv**: [1809.00219](https://arxiv.org/abs/1809.00219)
- **GitHub**: https://github.com/xinntao/ESRGAN

## 연구 배경
SRGAN(Super-Resolution GAN)은 사실적인 텍스처를 생성할 수 있지만, 종종 불쾌한 아티팩트가 동반됩니다. ESRGAN은 이를 개선하여 더 자연스러운 이미지를 생성합니다.

## 핵심 개선 사항

### 1. 네트워크 아키텍처
- **RRDB (Residual-in-Residual Dense Block)**
  - Batch Normalization 제거
  - 더 깊고 복잡한 구조
  - 향상된 특징 추출

### 2. Relativistic Discriminator
- 절대값 대신 상대적 실제성 예측
- 더 안정적인 학습
- 향상된 이미지 품질

### 3. Perceptual Loss 개선
- 활성화 전 특징 사용
- 밝기 일관성 향상
- 텍스처 복원 개선

## 관련 연구

### ESRGAN+ (arXiv:2001.08073)
- ESRGAN 추가 개선
- 더 사실적인 이미지 생성

### Real-ESRGAN (arXiv:2107.10833)
- 실제 이미지 복원에 최적화
- 순수 합성 데이터로 학습
- 실용적인 애플리케이션 지원

## 성능
- PIRM2018-SR Challenge Region 3 우승
- 4x 업스케일링에서 우수한 시각적 품질
- 자연스러운 텍스처 생성

## AX 시스템 적용
- **사용 API**: ESRGAN API (Port 5010)
- **용도**: 저해상도 도면 이미지 업스케일링
- **배율**: 4x 업스케일링 지원
- **장점**: OCR 정확도 향상을 위한 전처리

## 참고 자료
- GitHub (ESRGAN): https://github.com/xinntao/ESRGAN
- GitHub (Real-ESRGAN): https://github.com/xinntao/Real-ESRGAN
- BasicSR: https://github.com/XPixelGroup/BasicSR
