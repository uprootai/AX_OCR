# PP-OCR: A Practical Ultra Lightweight OCR System

## 논문 정보
- **제목**: PP-OCR: A Practical Ultra Lightweight OCR System
- **저자**: Yuning Du, Chenxia Li, Ruoyu Guo, et al. (Baidu)
- **게재일**: 2020년 9월 21일
- **arXiv**: [2009.09941](https://arxiv.org/abs/2009.09941)
- **GitHub**: https://github.com/PaddlePaddle/PaddleOCR

## 시리즈 논문

### PP-OCR (v1)
- 모델 크기: 3.5M (중국어 6622자), 2.8M (영숫자 63자)
- 경량화된 실용적 OCR 시스템

### PP-OCRv2 (arXiv:2109.03144)
- Collaborative Mutual Learning (CML)
- Lightweight CPU Network (LCNet)
- 정밀도 7% 향상

### PP-OCRv3 (arXiv:2206.03001)
- SVTR 기반 인식기
- LK-PAN, RSE-FPN 텍스트 검출기
- hmean 5% 향상

### PaddleOCR 3.0 (arXiv:2507.05595)
- PP-OCRv5: 다국어 텍스트 인식
- PP-StructureV3: 계층적 문서 파싱
- PP-ChatOCRv4: 핵심 정보 추출

## 핵심 아키텍처

### 텍스트 검출 (Detection)
- DB (Differentiable Binarization) 알고리즘
- 경량화된 MobileNetV3 백본

### 텍스트 인식 (Recognition)
- CRNN 기반 시퀀스 인식
- CTC (Connectionist Temporal Classification) 디코딩

### 방향 분류 (Direction Classification)
- 텍스트 방향 자동 감지 및 보정

## 지원 언어
- 100+ 언어 지원
- 한국어, 중국어, 일본어, 영어 등

## AX 시스템 적용
- **사용 API**: PaddleOCR API (Port 5006)
- **용도**: 다국어 OCR, 도면 텍스트 인식
- **장점**: 경량, 빠른 추론 속도, 다국어 지원

## 참고 자료
- GitHub: https://github.com/PaddlePaddle/PaddleOCR
- 공식 문서: https://paddlepaddle.github.io/PaddleOCR/
