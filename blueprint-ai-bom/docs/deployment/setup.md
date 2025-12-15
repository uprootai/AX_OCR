# 🚀 DrawingBOMExtractor 설치 가이드

## 📋 필수 파일 및 디렉토리 구조

### 🔴 Git Clone 후 추가 필요 파일

다음 파일들은 `.gitignore`에 등록되어 있어 별도로 준비해야 합니다:

#### 1. **모델 파일** (필수)
```
models/
├── yolo/
│   └── best.pt              # YOLOv8/v11 통합 모델 (약 50-100MB)
└── detectron2/
    └── model_final.pth      # Detectron2 모델 (선택사항, 약 300-500MB)
```

#### 2. **테스트 데이터** (필수)
```
test_drawings/
├── labels/                  # Ground Truth 라벨 디렉토리
│   ├── img_00031.txt        # YOLO 형식 라벨
│   ├── img_00035.txt
│   ├── img_00042.txt
│   ├── img_00046.txt
│   ├── img_00058.txt
│   ├── classes.txt          # 클래스 이름 목록
│   └── README.md
├── img_00031.jpg            # 테스트 이미지 (약 37KB)
├── img_00035.jpg            # 테스트 이미지 (약 49KB)
├── img_00042.jpg            # 테스트 이미지 (약 38KB)
├── img_00046.jpg            # 테스트 이미지 (약 57KB)
├── img_00058.jpg            # 테스트 이미지 (약 40KB)
├── -MCP_1_PANEL BODY_1.pdf  # 테스트 PDF (약 418KB)
├── test_drawing.pdf         # 테스트 PDF (약 35KB)
├── data.yaml                # 데이터셋 설정
└── classes.txt              # 클래스 목록
```

⚠️ **주의**: `.gitignore`에 `*.jpg`, `*.pdf`, `test_drawings/` 디렉토리가 포함되어 있어
테스트 이미지와 PDF 파일들이 Git에 커밋되지 않습니다.

**다운로드 방법:**
- YOLO 모델: 사전 학습된 27개 클래스 모델 필요
- Detectron2: 선택사항 (없으면 YOLO로 대체 실행)

#### 3. **클래스 예시 이미지** (선택사항)
```
class_examples/
├── class_00_10_BUZZER_HY-256-2(AC220V)_p01.jpg
├── class_01_11_HUB-8PORT_Alt 1. EDS-208A(HUB)_p01.jpg
└── ... (27개 클래스별 예시 이미지)
```

**생성 방법:**
```bash
python extract_class_examples.py
```
※ 학습 데이터셋이 있는 경우에만 가능

#### 4. **디렉토리 생성** (자동 생성됨)
```
uploads/        # 사용자 업로드 파일
results/        # 처리 결과
```

## 📦 설치 단계

### 1. 저장소 클론
```bash
git clone https://github.com/your-repo/DrawingBOMExtractor.git
cd DrawingBOMExtractor
```

### 2. Python 환경 설정
```bash
# 가상환경 생성 (Python 3.8+)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows

# 패키지 설치
pip install -r requirements.txt
```

### 3. 시스템 의존성 설치

#### Ubuntu/Debian:
```bash
# PDF 처리를 위한 poppler 설치
sudo apt-get update
sudo apt-get install -y poppler-utils

# GPU 사용 시 (선택사항)
# CUDA 11.8+ 및 cuDNN 설치 필요
```

#### macOS:
```bash
brew install poppler
```

#### Windows:
- [Poppler for Windows](https://blog.alivate.com.au/poppler-windows/) 다운로드 및 PATH 추가

### 4. 테스트 데이터 준비

#### 옵션 A: 제공된 테스트 데이터 사용
```bash
# 테스트 데이터 다운로드 (예시)
wget -O test_data.zip https://your-server/test_drawings.zip
unzip test_data.zip -d test_drawings/

# 또는 별도 저장소에서 복사
cp -r /path/to/test_drawings/* test_drawings/
```

#### 옵션 B: 최소 테스트 데이터 생성
```bash
# 필수 디렉토리 생성
mkdir -p test_drawings/labels

# 더미 이미지 생성 (개발용)
echo "Test image needed" > test_drawings/README.txt

# 최소 1개 이상의 테스트 이미지 필요
# JPG/PNG 형식, 1080x1080 해상도 권장
```

### 5. 모델 파일 배치

#### 옵션 A: 기존 모델 파일 복사
```bash
# YOLO 모델 (필수)
mkdir -p models/yolo
cp /path/to/your/best.pt models/yolo/best.pt

# Detectron2 모델 (선택사항)
mkdir -p models/detectron2
cp /path/to/your/model_final.pth models/detectron2/model_final.pth
```

#### 옵션 B: 사전 학습 모델 다운로드
```bash
# YOLO 모델 다운로드 (예시)
wget -O models/yolo/best.pt https://your-model-server/best.pt

# 또는 YOLOv8 기본 모델 사용
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
# 이후 27개 클래스로 fine-tuning 필요
```

### 6. 설정 파일 확인

#### `models/registry.json` 확인:
```json
{
  "models": {
    "yolo_v11l": {
      "path": "models/yolo/best.pt",
      "active": true
    }
  }
}
```

#### `classes_info_with_pricing.json` 확인:
- 27개 부품 클래스 정보와 가격이 포함되어 있는지 확인

### 7. 실행

#### Streamlit 앱 실행:
```bash
streamlit run real_ai_app.py
```

#### Docker 실행 (선택사항):
```bash
docker-compose up -d
```

## 🔍 체크리스트

실행 전 확인 사항:

- [ ] Python 3.8+ 설치
- [ ] `requirements.txt`의 모든 패키지 설치
- [ ] `models/yolo/best.pt` 파일 존재
- [ ] `classes_info_with_pricing.json` 파일 존재
- [ ] `test_drawings/` 폴더와 테스트 이미지 존재 (최소 1개 이상)
- [ ] `test_drawings/labels/` 폴더와 라벨 파일 존재
- [ ] Poppler 설치 (PDF 처리용)
- [ ] GPU 사용 시: CUDA/cuDNN 설치

## 🆘 문제 해결

### 1. "모델 파일을 찾을 수 없습니다" 오류
```bash
# 모델 경로 확인
ls -la models/yolo/best.pt

# 경로가 다른 경우 registry.json 수정
```

### 2. "PDF 처리 라이브러리가 설치되지 않았습니다" 오류
```bash
# Poppler 설치 확인
which pdftoppm  # Linux/Mac
where pdftoppm  # Windows

# PyMuPDF 재설치
pip install --upgrade PyMuPDF
```

### 3. "NumPy is not available" 오류
```bash
# NumPy 버전 확인 (2.0 미만이어야 함)
pip install "numpy>=1.24.0,<2.0.0"
```

### 4. GPU 메모리 부족
```python
# real_ai_app.py에서 device 설정 변경
self.device = {'device': 'cpu'}  # GPU 대신 CPU 사용
```

## 📝 환경 변수 (선택사항)

`.env` 파일 생성:
```bash
# GPU 설정
CUDA_VISIBLE_DEVICES=0

# 모델 경로 (기본값 override)
YOLO_MODEL_PATH=models/yolo/best.pt
DETECTRON2_MODEL_PATH=models/detectron2/model_final.pth

# Streamlit 설정
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

## 🎯 테스트

설치 확인:
```bash
# 1. 라이브러리 import 테스트
python -c "import streamlit, ultralytics, cv2, torch; print('All libraries OK')"

# 2. 모델 로드 테스트
python -c "from ultralytics import YOLO; model = YOLO('models/yolo/best.pt'); print('Model loaded')"

# 3. Streamlit 실행 테스트
streamlit run real_ai_app.py --server.headless true
```

## 📞 지원

문제 발생 시:
1. `requirements.txt` 버전 확인
2. Python 버전 확인 (3.8+)
3. 에러 로그 첨부하여 이슈 생성

---
*Last Updated: 2024-09-14*