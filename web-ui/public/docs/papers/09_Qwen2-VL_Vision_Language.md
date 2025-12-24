# Qwen2-VL: Enhancing Vision-Language Model's Perception

## 논문 정보
- **제목**: Qwen2-VL: Enhancing Vision-Language Model's Perception of the World at Any Resolution
- **저자**: Peng Wang, Shuai Bai, et al. (Alibaba)
- **게재일**: 2024년 10월 4일
- **arXiv**: [2409.12191](https://arxiv.org/abs/2409.12191)
- **GitHub**: https://github.com/QwenLM/Qwen-VL

## 연구 배경
기존 비전-언어 모델은 고정된 해상도로 이미지를 처리하는 한계가 있었습니다. Qwen2-VL은 동적 해상도 처리를 통해 이 문제를 해결합니다.

## 핵심 혁신

### 1. Naive Dynamic Resolution
- 다양한 해상도의 이미지를 동적으로 처리
- 이미지별 다른 수의 비주얼 토큰 생성
- 정보 손실 최소화

### 2. M-RoPE (Multimodal Rotary Position Embedding)
- 텍스트, 이미지, 비디오의 위치 정보 통합
- 시간, 높이, 너비 컴포넌트로 분해
- 멀티모달 정보의 효과적 융합

### 3. Vision Transformer
- 약 675M 파라미터
- 이미지와 비디오 입력 모두 처리
- 다양한 스케일 적응

## 모델 크기
| 모델 | 파라미터 | 성능 |
|------|----------|------|
| Qwen2-VL-2B | 2B | 기본 |
| Qwen2-VL-7B | 7B | 중간 |
| Qwen2-VL-72B | 72B | GPT-4o, Claude3.5 수준 |

## 성능
- GPT-4o, Claude3.5-Sonnet과 비교 가능한 성능
- 다양한 멀티모달 벤치마크에서 우수한 결과
- 범용 모델 중 최고 수준

## 시리즈 논문
- [Qwen-VL](https://arxiv.org/abs/2308.12966) - 초기 버전
- [Qwen2.5-VL](https://arxiv.org/abs/2502.13923) - 최신 버전

## AX 시스템 적용
- **사용 API**: VL API (Port 5004)
- **용도**: 도면 이해, 정보 추출, 질의응답
- **장점**: 복잡한 도면 컨텍스트 이해, 자연어 질의 지원

## 참고 자료
- GitHub: https://github.com/QwenLM/Qwen-VL
- 공식 페이지: https://qwenlm.github.io/
- Hugging Face: https://huggingface.co/Qwen
