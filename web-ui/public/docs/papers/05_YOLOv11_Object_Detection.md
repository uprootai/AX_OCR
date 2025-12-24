# YOLOv11: An Overview of the Key Architectural Enhancements

## 논문 정보
- **제목**: YOLOv11: An Overview of the Key Architectural Enhancements
- **저자**: Ultralytics Team
- **게재일**: 2024년 10월 23일
- **arXiv**: [2410.17725](https://arxiv.org/abs/2410.17725)
- **공식 문서**: https://docs.ultralytics.com/

## 연구 배경
YOLO(You Only Look Once)는 실시간 객체 검출의 대표적인 모델 시리즈로, YOLOv11은 Ultralytics에서 개발한 최신 버전입니다.

## 핵심 아키텍처

### 주요 컴포넌트
1. **C3k2 (Cross Stage Partial with kernel size 2)**
   - 효율적인 특징 추출을 위한 블록 구조
   - 채널 상호작용 증가, 지연 시간 최소화

2. **SPPF (Spatial Pyramid Pooling - Fast)**
   - 다양한 스케일의 특징 통합
   - 빠른 연산 속도 유지

3. **C2PSA (Convolutional block with Parallel Spatial Attention)**
   - 병렬 공간 주의 메커니즘
   - 컨텍스트 정보 효과적 활용

### 지원 태스크
- 객체 검출 (Object Detection)
- 인스턴스 분할 (Instance Segmentation)
- 포즈 추정 (Pose Estimation)
- 방향 객체 검출 (Oriented Object Detection - OBB)

## 모델 크기
| 모델 | 파라미터 | mAP | FPS |
|------|----------|-----|-----|
| YOLOv11n | 2.6M | 39.5 | 높음 |
| YOLOv11s | 9.4M | 47.0 | 높음 |
| YOLOv11m | 20.1M | 51.5 | 중간 |
| YOLOv11l | 25.3M | 53.4 | 중간 |
| YOLOv11x | 56.9M | 54.7 | 낮음 |

## AX 시스템 적용
- **사용 API**: YOLO API (Port 5005)
- **용도**: 기계 도면에서 심볼 검출 (14가지 클래스)
- **클래스**: 치수선, GD&T 기호, 용접 기호, 표면 거칠기 등

## 관련 논문
- [Ultralytics YOLO Evolution](https://arxiv.org/abs/2510.09653) - YOLO26, YOLO11, YOLOv8, YOLOv5 개요
- [YOLOv1 to YOLOv11 Survey](https://arxiv.org/abs/2508.02067) - YOLO 시리즈 종합 서베이

## 참고 자료
- GitHub: https://github.com/ultralytics/ultralytics
- 공식 문서: https://docs.ultralytics.com/
