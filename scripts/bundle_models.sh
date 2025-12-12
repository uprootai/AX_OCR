#!/bin/bash
# 오프라인 환경을 위한 모델 번들링 스크립트
# 모든 AI 모델을 사전 다운로드하여 offline_models/ 디렉토리에 저장

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MODELS_DIR="${PROJECT_ROOT}/offline_models"

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "============================================"
echo "🤖 AI 모델 오프라인 번들링"
echo "============================================"
echo ""

# 디렉토리 생성
mkdir -p "${MODELS_DIR}/yolo"
mkdir -p "${MODELS_DIR}/paddleocr"
mkdir -p "${MODELS_DIR}/trocr"
mkdir -p "${MODELS_DIR}/esrgan"
mkdir -p "${MODELS_DIR}/easyocr"
mkdir -p "${MODELS_DIR}/surya"
mkdir -p "${MODELS_DIR}/doctr"

# =============================================
# 1. YOLO 모델 다운로드
# =============================================
log "1. YOLO 모델 다운로드..."

# Python으로 YOLO 모델 다운로드
python3 << 'EOF'
import os
import sys

try:
    from ultralytics import YOLO

    models_dir = os.environ.get('MODELS_DIR', 'offline_models/yolo')

    # 기본 모델 다운로드
    models = ['yolo11n.pt', 'yolo11s.pt']

    for model_name in models:
        print(f"  Downloading {model_name}...")
        try:
            model = YOLO(model_name)
            # 모델 파일 복사 (현재 디렉토리에 다운로드됨)
            import shutil
            if os.path.exists(model_name):
                shutil.copy(model_name, f"{models_dir}/{model_name}")
                os.remove(model_name)  # 원본 삭제
                print(f"  ✅ {model_name} downloaded")
            else:
                print(f"  ⚠️ {model_name} not found in current directory")
        except Exception as e:
            print(f"  ⚠️ Failed to download {model_name}: {e}")

    print("YOLO models ready")
except ImportError:
    print("⚠️ ultralytics not installed, skipping YOLO")
except Exception as e:
    print(f"⚠️ YOLO download failed: {e}")
EOF

log_success "YOLO 모델 완료"

# =============================================
# 2. PaddleOCR 모델 다운로드
# =============================================
log "2. PaddleOCR 모델 다운로드..."

python3 << 'EOF'
import os
import sys
import logging
logging.disable(logging.WARNING)

try:
    from paddleocr import PaddleOCR

    models_dir = os.environ.get('MODELS_DIR', 'offline_models/paddleocr')

    # 영어 모델
    print("  Downloading English model...")
    ocr_en = PaddleOCR(lang='en', use_angle_cls=True)
    print("  ✅ English model downloaded")

    # 한국어 모델
    print("  Downloading Korean model...")
    ocr_ko = PaddleOCR(lang='korean', use_angle_cls=True)
    print("  ✅ Korean model downloaded")

    # 모델 파일 복사
    import shutil
    paddle_cache = os.path.expanduser("~/.paddleocr")
    if os.path.exists(paddle_cache):
        for item in os.listdir(paddle_cache):
            src = os.path.join(paddle_cache, item)
            dst = os.path.join(models_dir, item)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        print(f"  Models copied to {models_dir}")

    print("PaddleOCR models ready")
except ImportError:
    print("⚠️ paddleocr not installed, skipping PaddleOCR")
except Exception as e:
    print(f"⚠️ PaddleOCR download failed: {e}")
EOF

log_success "PaddleOCR 모델 완료"

# =============================================
# 3. TrOCR 모델 다운로드 (HuggingFace)
# =============================================
log "3. TrOCR 모델 다운로드..."

python3 << 'EOF'
import os
import sys

try:
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel

    models_dir = os.environ.get('MODELS_DIR', 'offline_models/trocr')

    model_names = [
        "microsoft/trocr-base-printed",
        "microsoft/trocr-base-handwritten"
    ]

    for model_name in model_names:
        short_name = model_name.split("/")[-1]
        save_path = os.path.join(models_dir, short_name)

        print(f"  Downloading {model_name}...")
        try:
            processor = TrOCRProcessor.from_pretrained(model_name)
            model = VisionEncoderDecoderModel.from_pretrained(model_name)

            # 로컬에 저장
            processor.save_pretrained(save_path)
            model.save_pretrained(save_path)
            print(f"  ✅ {short_name} saved to {save_path}")
        except Exception as e:
            print(f"  ⚠️ Failed: {e}")

    print("TrOCR models ready")
except ImportError:
    print("⚠️ transformers not installed, skipping TrOCR")
except Exception as e:
    print(f"⚠️ TrOCR download failed: {e}")
EOF

log_success "TrOCR 모델 완료"

# =============================================
# 4. ESRGAN 모델 다운로드
# =============================================
log "4. ESRGAN 모델 다운로드..."

ESRGAN_URL="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
ESRGAN_PATH="${MODELS_DIR}/esrgan/RealESRGAN_x4plus.pth"

if [ ! -f "$ESRGAN_PATH" ]; then
    log "  Downloading RealESRGAN_x4plus.pth..."
    curl -L -o "$ESRGAN_PATH" "$ESRGAN_URL" 2>/dev/null || wget -O "$ESRGAN_PATH" "$ESRGAN_URL" 2>/dev/null || {
        log_warn "ESRGAN 다운로드 실패 - 수동 다운로드 필요"
        log_warn "URL: $ESRGAN_URL"
    }
else
    log "  ESRGAN 모델 이미 존재"
fi

log_success "ESRGAN 모델 완료"

# =============================================
# 5. EasyOCR 모델 다운로드
# =============================================
log "5. EasyOCR 모델 다운로드..."

python3 << 'EOF'
import os
import sys

try:
    import easyocr

    models_dir = os.environ.get('MODELS_DIR', 'offline_models/easyocr')

    # 한국어+영어 모델 다운로드
    print("  Downloading Korean+English model...")
    reader = easyocr.Reader(['ko', 'en'], gpu=False, download_enabled=True)
    print("  ✅ Korean+English model downloaded")

    # 모델 파일 복사
    import shutil
    easyocr_cache = os.path.expanduser("~/.EasyOCR")
    if os.path.exists(easyocr_cache):
        for item in os.listdir(easyocr_cache):
            src = os.path.join(easyocr_cache, item)
            dst = os.path.join(models_dir, item)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        print(f"  Models copied to {models_dir}")

    print("EasyOCR models ready")
except ImportError:
    print("⚠️ easyocr not installed, skipping EasyOCR")
except Exception as e:
    print(f"⚠️ EasyOCR download failed: {e}")
EOF

log_success "EasyOCR 모델 완료"

# =============================================
# 6. Surya OCR 모델 다운로드
# =============================================
log "6. Surya OCR 모델 다운로드..."

python3 << 'EOF'
import os
import sys

try:
    # Surya uses HuggingFace Hub
    from huggingface_hub import snapshot_download

    models_dir = os.environ.get('MODELS_DIR', 'offline_models/surya')

    # Surya 모델들
    surya_models = [
        "vikp/surya_rec",     # Recognition model
        "vikp/surya_det3",    # Detection model
        "vikp/surya_layout3", # Layout model
        "vikp/surya_order"    # Reading order model
    ]

    for model_name in surya_models:
        short_name = model_name.split("/")[-1]
        save_path = os.path.join(models_dir, "huggingface", "hub", f"models--{model_name.replace('/', '--')}")

        print(f"  Downloading {model_name}...")
        try:
            snapshot_download(
                repo_id=model_name,
                local_dir=save_path,
                local_dir_use_symlinks=False
            )
            print(f"  ✅ {short_name} downloaded")
        except Exception as e:
            print(f"  ⚠️ Failed: {e}")

    print("Surya OCR models ready")
except ImportError:
    print("⚠️ huggingface_hub not installed, skipping Surya OCR")
except Exception as e:
    print(f"⚠️ Surya OCR download failed: {e}")
EOF

log_success "Surya OCR 모델 완료"

# =============================================
# 7. DocTR 모델 다운로드
# =============================================
log "7. DocTR 모델 다운로드..."

python3 << 'EOF'
import os
import sys

try:
    from doctr.models import ocr_predictor

    models_dir = os.environ.get('MODELS_DIR', 'offline_models/doctr')

    # DocTR 모델 다운로드 (자동으로 캐시에 저장)
    print("  Downloading DocTR models...")
    predictor = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True)
    print("  ✅ DocTR models downloaded")

    # 캐시 복사
    import shutil
    doctr_cache = os.path.expanduser("~/.cache/doctr")
    if os.path.exists(doctr_cache):
        for item in os.listdir(doctr_cache):
            src = os.path.join(doctr_cache, item)
            dst = os.path.join(models_dir, item)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        print(f"  Models copied to {models_dir}")

    print("DocTR models ready")
except ImportError:
    print("⚠️ doctr not installed, skipping DocTR")
except Exception as e:
    print(f"⚠️ DocTR download failed: {e}")
EOF

log_success "DocTR 모델 완료"

# =============================================
# 8. 번들 정보 생성
# =============================================
log "8. 번들 정보 생성..."

cat > "${MODELS_DIR}/README.md" << 'EOF'
# 오프라인 AI 모델 번들

이 디렉토리에는 온프레미스 환경에서 인터넷 없이 실행하기 위한 AI 모델이 포함되어 있습니다.

## 디렉토리 구조

```
offline_models/
├── yolo/           # YOLO 객체 검출 모델
├── paddleocr/      # PaddleOCR 텍스트 인식 모델
├── trocr/          # TrOCR 필기체 인식 모델
├── esrgan/         # ESRGAN 이미지 업스케일링 모델
├── easyocr/        # EasyOCR 다국어 OCR 모델
├── surya/          # Surya OCR (90+ 언어, 레이아웃 분석)
└── doctr/          # DocTR (2단계 OCR 파이프라인)
```

## 사용 방법

### Docker Compose 오프라인 모드

```bash
# 오프라인 모델을 사용하여 전체 서비스 실행
docker-compose -f docker-compose.yml -f docker-compose.offline.yml up -d
```

### 환경변수 설정

오프라인 모드 활성화:
```bash
# HuggingFace 오프라인 모드
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1

# 각 API 오프라인 모드
export YOLO_OFFLINE_MODE=true
export PADDLEOCR_OFFLINE_MODE=true
export TROCR_OFFLINE_MODE=true
export ESRGAN_OFFLINE_MODE=true
export EASYOCR_OFFLINE_MODE=true
export SURYA_OFFLINE_MODE=true
export DOCTR_OFFLINE_MODE=true
```

## 생성일

EOF

echo "생성일: $(date '+%Y-%m-%d %H:%M:%S')" >> "${MODELS_DIR}/README.md"

# 디렉토리 크기 계산
echo "" >> "${MODELS_DIR}/README.md"
echo "## 모델 크기" >> "${MODELS_DIR}/README.md"
echo "" >> "${MODELS_DIR}/README.md"
echo '```' >> "${MODELS_DIR}/README.md"
du -sh "${MODELS_DIR}"/* 2>/dev/null >> "${MODELS_DIR}/README.md" || echo "크기 계산 실패" >> "${MODELS_DIR}/README.md"
echo '```' >> "${MODELS_DIR}/README.md"

log_success "번들 정보 생성 완료"

# =============================================
# 결과 출력
# =============================================
echo ""
echo "============================================"
echo "✅ 모델 번들링 완료!"
echo "============================================"
echo ""
echo "📁 번들 위치: ${MODELS_DIR}"
echo ""
echo "📊 디렉토리 크기:"
du -sh "${MODELS_DIR}"/* 2>/dev/null || echo "크기 계산 실패"
echo ""
echo "총 크기:"
du -sh "${MODELS_DIR}" 2>/dev/null || echo "크기 계산 실패"
echo ""
echo "============================================"
echo "다음 단계:"
echo "  1. offline_models/ 디렉토리를 배포 패키지에 포함"
echo "  2. 오프라인 모드로 실행:"
echo "     docker-compose -f docker-compose.yml -f docker-compose.offline.yml up -d"
echo "  3. 오프라인 환경에서 테스트"
echo "============================================"
