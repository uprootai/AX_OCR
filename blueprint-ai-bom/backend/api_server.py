"""
Blueprint AI BOM - Backend API Server

AI 기반 도면 분석 및 BOM 생성 API
"""

import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.session_router import router as session_router_api, set_session_service
from routers.workflow_session_router import router as workflow_session_router_api, set_session_service as set_workflow_session_service
from routers.session_io_router import router as session_io_router_api, set_session_service as set_session_io_service
from routers.session_images_router import router as session_images_router_api, set_session_service as set_session_images_service
from routers.detection_router import router as detection_router_api, set_detection_service
from routers.bom_router import router as bom_router_api, set_bom_service
# Analysis 라우터 패키지 (5개 모듈로 분할됨)
from routers.analysis import (
    core_router,
    dimension_router,
    line_router,
    region_router,
    gdt_router,
    batch_router,
    set_core_services,
    set_line_services,
    set_region_services,
    set_gdt_services,
)
from routers.verification_router import router as verification_router_api, set_verification_services
from routers.agent_verification_router import router as agent_verification_router_api, set_agent_verification_services
from routers.classification_router import router as classification_router_api, set_classification_services
from routers.relation_router import router as relation_router_api, set_relation_services
from routers.feedback_router import router as feedback_router_api, set_feedback_services
from routers.midterm_router import router as midterm_router_api, set_session_service as set_midterm_session_service
# Long-term 기능 라우터 (longterm_router.py에서 5개 모듈로 분리)
from routers.analysis import (
    drawing_region_router,
    notes_router,
    revision_router,
    vlm_router,
    viewlabels_router,
    set_drawing_region_services,
    set_notes_services,
    set_revision_services,
    set_vlm_services,
    set_viewlabels_services,
)
from routers.pid_features_router import router as pid_features_router_api, set_pid_features_service
from routers.settings_router import router as settings_router_api
# Phase 2: 프로젝트/템플릿 라우터
from routers.project_router import router as project_router_api
from routers.project_bom_router import router as project_bom_router_api
from routers.quotation_router import router as quotation_router_api
from routers.pricing_router import router as pricing_router_api
from routers.template_router import router as template_router_api
# Phase 2E: Export 라우터
from routers.export_router import router as export_router_api, set_export_services
# Project I/O 라우터 (프로젝트 단위 Export/Import)
from routers.project_io_router import router as project_io_router_api, set_project_io_services
# Reference Sets (커스텀 참조 도면) 라우터
from routers.reference_router import router as reference_router_api
# 신규 라우터: GT, Config & System
from routers.gt_router import router as gt_router_api
from routers.config_router import router as config_router_api, set_config_services
from services.session_service import SessionService
from services.detection_service import DetectionService
from services.bom_service import BOMService
from services.dimension_service import DimensionService
from services.line_detector_service import LineDetectorService
from services.dimension_relation_service import DimensionRelationService
from services.connectivity_analyzer import ConnectivityAnalyzer  # Phase 6: P&ID 연결 분석
from services.region_segmenter import RegionSegmenter  # Phase 5: 영역 분할
from services.gdt_parser import GDTParser  # Phase 7: GD&T 파싱
from services.table_service import TableService  # 테이블 추출
from services.crop_service import CropService  # Agent Verification 크롭 서비스
from services.export_service import get_export_service  # Phase 2E: Export
from services.project_service import get_project_service  # 프로젝트 서비스

# 기본 경로 설정 (Docker에서는 /app 기준)
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
RESULTS_DIR = BASE_DIR / "results"
CONFIG_DIR = BASE_DIR / "config"
MODELS_DIR = BASE_DIR / "models"

# 디렉토리 생성
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)
(UPLOAD_DIR / "gt_labels").mkdir(exist_ok=True)  # GT 라벨 업로드용

# Phase 2: 프로젝트/템플릿 데이터 디렉토리
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
(DATA_DIR / "projects").mkdir(exist_ok=True)
(DATA_DIR / "templates").mkdir(exist_ok=True)
# Phase 2E: Export 디렉토리
EXPORT_DIR = BASE_DIR / "exports"
EXPORT_DIR.mkdir(exist_ok=True)
# Reference Sets (커스텀 참조 도면) 디렉토리
REFERENCE_SETS_DIR = DATA_DIR / "reference_sets"
REFERENCE_SETS_DIR.mkdir(exist_ok=True)

# FastAPI 앱 생성
app = FastAPI(
    title="Blueprint AI BOM API",
    description="AI 기반 도면 분석 및 BOM 생성 솔루션 + P&ID 분석 기능",
    version="10.6.0",  # v10.6: P&ID 분석 기능 (밸브, 장비, 체크리스트)
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서비스 인스턴스 생성
session_service = SessionService(UPLOAD_DIR, RESULTS_DIR)

# YOLO 모델 경로 (존재하면 로드)
model_path = MODELS_DIR / "best.pt"
if not model_path.exists():
    model_path = None

detection_service = DetectionService(model_path=model_path)
bom_service = BOMService(output_dir=RESULTS_DIR)
dimension_service = DimensionService()  # v2: 치수 OCR 서비스
table_service = TableService()  # 테이블 추출
line_detector_service = LineDetectorService()  # v2: 선 검출 서비스
relation_service = DimensionRelationService()  # Phase 2: 치수선 기반 관계 추출
connectivity_analyzer = ConnectivityAnalyzer()  # Phase 6: P&ID 연결 분석
region_segmenter = RegionSegmenter()  # Phase 5: 영역 분할
gdt_parser = GDTParser()  # Phase 7: GD&T 파싱

# 라우터에 서비스 주입
set_session_service(session_service, UPLOAD_DIR)
set_workflow_session_service(session_service)  # 워크플로우 잠금 세션
set_session_io_service(session_service, UPLOAD_DIR)  # 세션 Export/Import
set_session_images_service(session_service, UPLOAD_DIR)  # 다중 이미지 관리
set_detection_service(detection_service, session_service)
set_bom_service(bom_service, session_service)
# Analysis 패키지 서비스 주입 (5개 라우터)
set_core_services(dimension_service, detection_service, session_service, relation_service, table_service)
set_line_services(line_detector_service, connectivity_analyzer)
set_region_services(region_segmenter)
set_gdt_services(gdt_parser)
set_verification_services(session_service)  # v3: Active Learning 검증
crop_service = CropService(session_service)
set_agent_verification_services(session_service, crop_service)  # Agent Verification
set_classification_services(session_service)  # v4: VLM 분류
set_relation_services(session_service, line_detector_service)  # Phase 2: 치수선 기반 관계
set_feedback_services(session_service)  # Phase 8: 피드백 루프
set_midterm_session_service(session_service)  # 중기 로드맵: 용접, 거칠기, 수량, 벌룬
# 장기 로드맵: 영역, 노트, 리비전, VLM, 뷰라벨 (5개 모듈)
set_drawing_region_services(session_service)
set_notes_services(session_service)
set_revision_services(session_service)
set_vlm_services(session_service)
set_viewlabels_services(session_service)
set_pid_features_service(session_service)  # P&ID 분석 기능: 밸브, 장비, 체크리스트
# Phase 2E: Export 서비스 초기화
export_service = get_export_service(EXPORT_DIR, UPLOAD_DIR)
project_service = get_project_service(DATA_DIR)
set_export_services(session_service, export_service, project_service=project_service)
# Config & System 라우터 서비스 주입
set_config_services(session_service)
# Project I/O 서비스 주입
set_project_io_services(session_service, UPLOAD_DIR)

# 라우터 등록 (prefix 없이 - 라우터 내부에 이미 prefix 있음)
app.include_router(session_router_api, tags=["Session"])
app.include_router(workflow_session_router_api, tags=["Workflow Session"])
app.include_router(session_io_router_api, tags=["Session I/O"])
app.include_router(session_images_router_api, tags=["Session Images"])
app.include_router(detection_router_api, tags=["Detection"])
app.include_router(bom_router_api, tags=["BOM"])
# Analysis 패키지 라우터 등록 (5개 모듈)
app.include_router(core_router, tags=["Analysis Core"])
app.include_router(dimension_router, tags=["Dimensions"])
app.include_router(line_router, tags=["Lines & Connectivity"])
app.include_router(region_router, tags=["Regions"])
app.include_router(gdt_router, tags=["GD&T & Title Block"])
app.include_router(batch_router, tags=["Batch Analysis"])
app.include_router(verification_router_api, tags=["Verification"])  # v3: Active Learning
app.include_router(agent_verification_router_api, tags=["Verification - Agent"])  # Agent Verification
app.include_router(classification_router_api, tags=["Classification"])  # v4: VLM 분류
app.include_router(relation_router_api, tags=["Relations"])  # Phase 2: 치수선 기반 관계
app.include_router(feedback_router_api, tags=["Feedback"])  # Phase 8: 피드백 루프
app.include_router(midterm_router_api, tags=["Mid-term Features"])  # 중기 로드맵: 용접, 거칠기, 수량, 벌룬
# 장기 로드맵 라우터 등록 (5개 모듈로 분리)
app.include_router(drawing_region_router, tags=["Drawing Regions"])
app.include_router(notes_router, tags=["Notes Extraction"])
app.include_router(revision_router, tags=["Revision Comparison"])
app.include_router(vlm_router, tags=["VLM Classification"])
app.include_router(viewlabels_router, tags=["View Labels"])
app.include_router(pid_features_router_api, tags=["P&ID Features"])  # P&ID 분석 기능: 밸브, 장비, 체크리스트
app.include_router(settings_router_api, tags=["Settings"])  # API 키 설정
# Phase 2: 프로젝트/템플릿 라우터
app.include_router(project_router_api, tags=["Projects"])  # 프로젝트 CRUD
app.include_router(project_bom_router_api, tags=["Projects - BOM"])  # BOM 계층/매칭/세션 생성
app.include_router(project_io_router_api, tags=["Projects - I/O"])  # 프로젝트 Export/Import
app.include_router(quotation_router_api, tags=["Projects - Quotation"])  # 견적 집계/내보내기
app.include_router(pricing_router_api, tags=["Projects - Pricing & GT"])  # 단가 설정/GT 관리
app.include_router(template_router_api, tags=["Templates"])  # 템플릿 관리
app.include_router(export_router_api, tags=["Export"])  # Phase 2E: Export
app.include_router(reference_router_api, tags=["Reference Sets"])  # 커스텀 참조 도면
# 신규 라우터: GT, Config & System
app.include_router(gt_router_api, tags=["Ground Truth"])
app.include_router(config_router_api, tags=["Config & System"])


@app.get("/")
async def root():
    """API 상태 확인"""
    return {
        "name": "Blueprint AI BOM API",
        "version": "8.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=5020,
        reload=True
    )
