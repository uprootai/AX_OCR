# 🤖 모델 파일 다운로드 가이드

## 📥 필수 모델 파일

### 1. YOLO 모델 (필수)
- **파일명**: `best.pt`
- **경로**: `models/yolo/best.pt`
- **크기**: 약 50-100MB
- **용도**: 27개 산업 부품 클래스 검출

### 2. Detectron2 모델 (선택)
- **파일명**: `model_final.pth`
- **경로**: `models/detectron2/model_final.pth`
- **크기**: 약 300-500MB
- **용도**: Mask R-CNN 기반 정밀 검출

## 🎓 학습된 27개 클래스

```
0. 10_BUZZER_HY-256-2(AC220V)_p01
1. 11_HUB-8PORT_Alt 1. EDS-208A(HUB)_p01
2. 13_SWITCHING MODE POWER SUPPLY_TRIO-PS-1AC-24DC-5(SMPS1)_p01
3. 14_SWITCHING MODE POWER SUPPLY_TRIO-PS-1AC-24DC-10(SMPS2)_p01
4. 16_DISCONNECTING SWITCH_(SW1)_p01
5. 17_POWER OUTLET(CONCENT)_(PO)_p01
6. 18_PILOT LAMP(GREEN)_MRP-NA0G_p01
7. 19_AUXILIARY RELAY(1a1b)_PLC-RSC-230UC-21_p01
8. 2,3,4,5_CIRCUIT BREAKER_BK63H 2P_p01
9. 20,32_CPU1513-1PN_6ES7513-1AL01-0AB0) PLC CPU_p01
10. 21_CPU1214C AC-DC-RLY_6ES7214-1BG40-0XB0(PLC CPU)_p01
11. 22_CM1214 RS422-485_6ES7241-1CH32-0XB0(PLC RS422-485)_p01
12. 23,37_CM1243-5 PROFIBUS DP_6GK7243-5DX30-0XE0(PLC DP)_p01
13. 24,25_GRAPHIC PANEL_6AV7240-3MC07-0HA0(GP)_p01
14. 26_TERMINAL BLOCK(32A)_ST4_p01
15. 27_TERMINAL BLOCK(24A)_ST2.5_p01
16. 28_SM1231 AI8 x 13bit_6ES7231-4HF32-0XB0(PLC AI)_p01
17. 29_SM1232 AO4 x 14bit_6ES7232-4HD32-0XB0(PLC AO)_p01
18. 30_SM1221 DI16 x 24VDC_6ES7221-1BH32-0XB0(PLC DI 1)_p01
19. 31_SM1222 DO16 x RLY_6ES7222-1HH32-0XB0(PLC DO 1)_p01
20. 34_BUS INTERFACE_BI(BUS INTERFACE)_p01
21. 35_VALVE CONTROL UNIT_EHS-CM3_p01
22. 38_I-I CONVERTOR_PAS-200(I-I CONVERTER)_p01
23. 39_SELECTOR SWITCH_MRS-N2A2(2STAGE)_p01
24. 6_TRANSFORMER_MST600VA
25. 8_NOISE FILTER_WYFS06T1A (6A)(NF1)_p01
26. 9,9-1_EMERGENCY BUTTON_MRE-NR1R_p01
```

## 🔧 모델 준비 방법

### 방법 1: 사전 학습 모델 사용 (권장)

프로젝트에 맞게 학습된 모델이 있는 경우:

```bash
# 디렉토리 생성
mkdir -p models/yolo
mkdir -p models/detectron2

# 모델 파일 복사
cp /path/to/trained/best.pt models/yolo/
cp /path/to/trained/model_final.pth models/detectron2/
```

### 방법 2: 직접 학습

#### YOLO 모델 학습
```python
from ultralytics import YOLO

# 기본 모델 로드
model = YOLO('yolov8n.pt')  # 또는 yolov8s.pt, yolov8m.pt, yolov8l.pt

# 학습 데이터 준비 (YOLO 형식)
# dataset/
#   ├── images/
#   │   ├── train/
#   │   └── val/
#   └── labels/
#       ├── train/
#       └── val/

# 학습 시작
results = model.train(
    data='path/to/data.yaml',  # 데이터셋 설정 파일
    epochs=100,
    imgsz=640,
    batch=16,
    name='industrial_parts'
)

# 모델 저장
model.save('models/yolo/best.pt')
```

#### data.yaml 예시
```yaml
path: /path/to/dataset
train: images/train
val: images/val

nc: 27  # 클래스 수
names: [
  '10_BUZZER_HY-256-2(AC220V)_p01',
  '11_HUB-8PORT_Alt 1. EDS-208A(HUB)_p01',
  # ... 나머지 클래스들
]
```

### 방법 3: 임시 테스트용 모델

개발/테스트 목적으로 임시 모델 사용:

```python
# 기본 YOLO 모델 다운로드 및 사용
from ultralytics import YOLO

# COCO 데이터셋으로 학습된 기본 모델
model = YOLO('yolov8n.pt')
model.save('models/yolo/best.pt')

# 주의: 이 모델은 80개 COCO 클래스를 검출하므로
# 실제 산업 부품 검출에는 부적합
```

## 📊 모델 성능 요구사항

### 최소 요구사항
- mAP@0.5: > 0.7
- 추론 속도: < 100ms/image (GPU)
- 모델 크기: < 200MB

### 권장 사양
- mAP@0.5: > 0.85
- 추론 속도: < 50ms/image (GPU)
- 모델 크기: < 100MB

## 🔍 모델 검증

모델이 올바르게 설치되었는지 확인:

```python
import torch
from ultralytics import YOLO

# YOLO 모델 테스트
try:
    model = YOLO('models/yolo/best.pt')
    print(f"✅ YOLO 모델 로드 성공")
    print(f"  - 클래스 수: {model.model.nc}")
    print(f"  - 모델 크기: {os.path.getsize('models/yolo/best.pt') / 1024 / 1024:.2f} MB")
except Exception as e:
    print(f"❌ YOLO 모델 로드 실패: {e}")

# Detectron2 모델 테스트 (선택사항)
try:
    checkpoint = torch.load('models/detectron2/model_final.pth', map_location='cpu')
    print(f"✅ Detectron2 모델 로드 성공")
    print(f"  - 모델 크기: {os.path.getsize('models/detectron2/model_final.pth') / 1024 / 1024:.2f} MB")
except Exception as e:
    print(f"⚠️ Detectron2 모델 없음 (선택사항): {e}")
```

## 🚨 주의사항

1. **모델 버전 호환성**
   - YOLOv8/v11 모델 사용
   - Ultralytics 8.0+ 필요

2. **클래스 매핑**
   - 모델의 클래스 순서와 `data.yaml`의 순서가 일치해야 함
   - `classes_info_with_pricing.json`과 동기화 필요

3. **GPU 메모리**
   - 최소 4GB VRAM 권장
   - 배치 크기 조정으로 메모리 사용량 제어 가능

## 📞 지원

모델 관련 문의:
- 학습 데이터셋 구성
- 모델 fine-tuning
- 성능 최적화

---
*모델 버전: v1.0.0*
*최종 업데이트: 2024-09-14*