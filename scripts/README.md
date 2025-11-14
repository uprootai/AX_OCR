# 🔧 스크립트 가이드 (Scripts Guide)

> **테스트, 유틸리티, 배포 스크립트 모음**
>
> 최종 업데이트: 2025-11-12

---

## 📁 **디렉토리 구조**

```
scripts/
├── test/           # 활성 테스트 스크립트 (4개)
├── archive/        # 아카이브된 스크립트 (13개)
├── deploy/         # 배포 스크립트
└── README.md       # 이 파일
```

**참고**: scripts/utils/ 디렉토리는 제거되었으며, 모든 구버전 스크립트는 archive/로 이동되었습니다.

---

## 🧪 **test/ - 테스트 스크립트**

### **활성 테스트 스크립트**

#### **1. test_apis.py**
```bash
# Python으로 전체 API 헬스 체크
python scripts/test/test_apis.py
```
- 모든 마이크로서비스 헬스 체크
- 응답 시간 측정
- JSON 형식 결과 출력

#### **2. test_apis.sh**
```bash
# Shell로 전체 API 헬스 체크
bash scripts/test/test_apis.sh
```
- curl 기반 간단한 헬스 체크
- 서버 실행 여부 확인

#### **3. test_ocr_performance_comparison.py**
```bash
# OCR v1 vs v2 성능 비교
python scripts/test/test_ocr_performance_comparison.py \
  --dataset test_samples/ \
  --output comparison_report.json
```
- v1과 v2 성능 비교
- Precision, Recall, F1-Score 측정
- JSON 보고서 생성

#### **4. test_cer_calculation.py**
```bash
# Character Error Rate 계산
python scripts/test/test_cer_calculation.py \
  --ground_truth gt.json \
  --predicted pred.json
```
- CER (Character Error Rate) 계산
- OCR 정확도 평가

---

## 📦 **archive/ - 아카이브된 스크립트 (13개)**

이전에 사용되던 스크립트들이 보관되어 있습니다:

### **데모 및 벤치마크**
- `demo_full_system.py` - 전체 시스템 데모
- `benchmark_system.py` - 성능 벤치마크
- `test_improvements.py` - 통합 테스트
- `example_gateway_integration.py` - Gateway 통합 예제
- `apply_enhancements.sh` - 개선사항 적용 스크립트

### **OCR 테스트**
- `test_ocr_visualization.py` - OCR 결과 시각화
- `test_edocr2_bbox_detailed.py` - eDOCr BBox 테스트
- `test_bbox_mapping_verification.py` - BBox 매핑 검증
- `test_pdf_conversion.py` - PDF 변환
- `test_detailed_analysis.py` - 상세 분석

### **유틸리티**
- `verify_bbox_api.py` - BBox API 검증
- `test_tooltip.py` - 툴팁 테스트
- `test_yolo_prototype.py` - YOLO 프로토타입

**사용법**: 필요시 `scripts/archive/` 디렉토리에서 스크립트를 복사하여 사용할 수 있습니다.

---

## 🚀 **deploy/ - 배포 스크립트 (추후 추가 예정)**

```bash
# 전체 시스템 배포
bash scripts/deploy/deploy.sh

# 개별 서비스 배포
bash scripts/deploy/deploy_service.sh edocr2-api

# 프로덕션 배포
bash scripts/deploy/deploy_production.sh
```

---

## 📊 **테스트 시나리오**

### **시나리오 1: 전체 시스템 헬스 체크**

```bash
# 1. Docker 컨테이너 실행 확인
docker ps

# 2. Python 기반 헬스 체크
python scripts/test/test_apis.py

# 3. Shell 기반 빠른 체크
bash scripts/test/test_apis.sh
```

---

### **시나리오 2: OCR 성능 검증**

```bash
# 1. v1과 v2 성능 비교
python scripts/test/test_ocr_performance_comparison.py \
  --dataset test_samples/

# 2. 결과 시각화
python scripts/test/test_ocr_visualization.py \
  --image test_samples/sample1.pdf \
  --version v2

# 3. CER 계산
python scripts/test/test_cer_calculation.py \
  --ground_truth ground_truth.json \
  --predicted ocr_result.json
```

---

### **시나리오 3: BBox 검증**

```bash
# 1. BBox API 검증
python scripts/utils/verify_bbox_api.py \
  --endpoint http://localhost:5002/api/v2/ocr

# 2. 상세 BBox 테스트
python scripts/test/test_edocr2_bbox_detailed.py \
  --image sample.png

# 3. 매핑 검증
python scripts/test/test_bbox_mapping_verification.py \
  --ocr_result result.json
```

---

## 🔍 **스크립트 작성 가이드**

### **테스트 스크립트 작성 규칙**

1. **명명 규칙**: `test_<기능명>.py`
2. **위치**: `scripts/test/`
3. **필수 요소**:
   - argparse로 인자 처리
   - 명확한 docstring
   - 결과 로깅

**템플릿:**
```python
#!/usr/bin/env python3
"""
<스크립트 설명>
"""

import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="<설명>")
    parser.add_argument("--input", required=True, help="입력 파일")
    parser.add_argument("--output", help="출력 파일")
    args = parser.parse_args()

    logger.info(f"Processing {args.input}...")
    # 테스트 로직
    logger.info("Done!")

if __name__ == "__main__":
    main()
```

---

### **유틸리티 스크립트 작성 규칙**

1. **명명 규칙**: `<동사>_<대상>.py` (예: `verify_bbox_api.py`)
2. **위치**: `scripts/utils/`
3. **특징**: 재사용 가능한 단위 기능

---

## 📝 **스크립트 추가 체크리스트**

새로운 스크립트를 추가할 때:

- [ ] 적절한 디렉토리에 배치 (test/ 또는 utils/)
- [ ] 명확한 docstring 작성
- [ ] argparse로 인자 처리
- [ ] 로깅 설정
- [ ] 이 README.md에 문서화
- [ ] 예제 사용법 추가
- [ ] Git 커밋

---

## 🐛 **문제 해결**

### **스크립트 실행 권한 오류**

```bash
chmod +x scripts/test/test_apis.sh
```

### **모듈 import 오류**

```bash
# 프로젝트 루트에서 실행
cd /home/uproot/ax/poc
python scripts/test/test_apis.py
```

### **API 연결 실패**

```bash
# 서비스 실행 확인
docker ps

# 포트 충돌 확인
sudo lsof -i :5001
sudo lsof -i :5002
```

---

## 📞 **문의 & 기여**

- 스크립트 버그 리포트: [GitHub Issues](링크 추가 필요)
- 새 스크립트 제안: [CONTRIBUTING.md](../docs/developer/CONTRIBUTING.md)

---

**최종 업데이트**: 2025-11-13
**작성자**: Claude Code
**버전**: v1.1 (아카이브 반영)
