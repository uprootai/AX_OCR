"""
Docker Services Constants - SSOT for service name mappings
모든 API ID 변형(언더스코어/하이픈)을 포함해야 함
"""

# Docker 서비스 이름 매핑 (API ID -> 컨테이너 이름)
DOCKER_SERVICE_MAPPING = {
    # Orchestrator
    "gateway": "gateway-api",
    # Detection
    "yolo": "yolo-api",
    # OCR
    "edocr2": "edocr2-v2-api",
    "edocr2-v2": "edocr2-v2-api",
    "paddleocr": "paddleocr-api",
    "tesseract": "tesseract-api",
    "trocr": "trocr-api",
    "surya_ocr": "surya-ocr-api",
    "surya-ocr": "surya-ocr-api",
    "doctr": "doctr-api",
    "easyocr": "easyocr-api",
    "ocr_ensemble": "ocr-ensemble-api",
    "ocr-ensemble": "ocr-ensemble-api",
    # Segmentation
    "edgnet": "edgnet-api",
    "line_detector": "line-detector-api",
    "line-detector": "line-detector-api",
    # Preprocessing
    "esrgan": "esrgan-api",
    # Analysis
    "skinmodel": "skinmodel-api",
    "pid_analyzer": "pid-analyzer-api",
    "pid-analyzer": "pid-analyzer-api",
    "design_checker": "design-checker-api",
    "design-checker": "design-checker-api",
    "blueprint_ai_bom": "blueprint-ai-bom-backend",
    "blueprint-ai-bom": "blueprint-ai-bom-backend",
    "blueprint-ai-bom-backend": "blueprint-ai-bom-backend",
    "blueprint-ai-bom-frontend": "blueprint-ai-bom-frontend",
    # Knowledge
    "knowledge": "knowledge-api",
    # AI
    "vl": "vl-api",
}

# GPU 지원 서비스 목록
GPU_ENABLED_SERVICES = {
    "yolo",
    "edocr2",
    "edocr2-v2",
    "paddleocr",
    "trocr",
    "edgnet",
    "esrgan",
    "line_detector",
    "line-detector",
    "blueprint_ai_bom",
    "blueprint-ai-bom",
}


def get_container_name(service: str) -> str:
    """서비스명에서 컨테이너명 가져오기"""
    return DOCKER_SERVICE_MAPPING.get(service, f"{service}-api")


def is_gpu_enabled_service(service: str) -> bool:
    """GPU 지원 서비스 여부 확인"""
    return service in GPU_ENABLED_SERVICES
