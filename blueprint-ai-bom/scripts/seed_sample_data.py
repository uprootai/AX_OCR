#!/usr/bin/env python3
"""Blueprint AI BOM 샘플 데이터 Seed 스크립트 (하드코딩)

프로젝트 상세 페이지 시연을 위한 샘플 프로젝트 3개를 생성합니다.

사용법:
    python scripts/seed_sample_data.py              # 기본 실행 (이미 있으면 스킵)
    python scripts/seed_sample_data.py --clean       # 기존 샘플 삭제 후 재생성
    python scripts/seed_sample_data.py --dry-run     # 실행 계획만 확인
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import requests

# ── 로깅 ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ── 상수 ──
API_BASE = "http://localhost:5020"
SAMPLE_PREFIX = "[샘플]"
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # /home/uproot/ax/poc

# ── 파일 경로 (호스트) ──
PID_IMAGES = [
    PROJECT_ROOT / "web-ui/public/samples/bwms_pid_sample.png",
    PROJECT_ROOT / "web-ui/public/samples/bwms_pid_techcross_sample.png",
]

BOM_PDF = (
    PROJECT_ROOT
    / "apply-company/dsebearing/PJT/01_BOM"
    / "BOM_Z24018_110104001_BRG_R1(25.05.16)-350번 재질 SS400.pdf"
)

DSE_IMAGES = [
    PROJECT_ROOT / "apply-company/dsebearing/test_images/bearing_assy_t1_page1.png",
    PROJECT_ROOT / "apply-company/dsebearing/test_images/casing_assy_t1_page1.png",
    PROJECT_ROOT / "apply-company/dsebearing/test_images/cylinder_cv_page1.png",
    PROJECT_ROOT / "apply-company/dsebearing/test_images/ring_assy_t1_page1.png",
    PROJECT_ROOT / "apply-company/dsebearing/test_images/thrust_bearing_assy_page1.png",
]

GENERAL_IMAGES = [
    PROJECT_ROOT / "web-ui/public/samples/sample2_interm_shaft.jpg",
    PROJECT_ROOT / "web-ui/public/samples/sample3_s60me_shaft.jpg",
]

DRAWING_FOLDER_CONTAINER = "/app/data/dsebearing/PJT/04_부품도면"

# ── 프로젝트 정의 ──
PROJECTS = [
    {
        "name": f"{SAMPLE_PREFIX} BWMS P&ID 검출 데모",
        "customer": "파나시아 (샘플)",
        "description": "BWMS P&ID 도면 검출 데모 프로젝트. P&ID 심볼 검출 및 GT 비교 기능을 시연합니다.",
    },
    {
        "name": f"{SAMPLE_PREFIX} DSE 베어링 BOM 견적",
        "customer": "동서기연 (샘플)",
        "description": "DSE 베어링 BOM 견적 데모 프로젝트. BOM 파싱, 도면 매칭, 세션 생성, 견적 워크플로우를 시연합니다.",
    },
    {
        "name": f"{SAMPLE_PREFIX} 일반 도면 분석",
        "customer": "데모 (샘플)",
        "description": "일반 기계 도면 분석 데모 프로젝트. 치수 추출 및 검증 기능을 시연합니다.",
    },
]


# ── 헬퍼 함수 ──


def check_health() -> bool:
    """API 서버 헬스체크"""
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        if r.status_code == 200:
            logger.info("API 서버 정상 (localhost:5020)")
            return True
        logger.error(f"헬스체크 실패: status={r.status_code}")
        return False
    except requests.ConnectionError:
        logger.error("API 서버에 연결할 수 없습니다 (localhost:5020)")
        return False


def check_files() -> list[str]:
    """필요한 파일 존재 확인. 누락 파일 목록 반환."""
    missing = []
    all_files = PID_IMAGES + [BOM_PDF] + DSE_IMAGES + GENERAL_IMAGES
    for f in all_files:
        if not f.exists():
            missing.append(str(f))
    return missing


def get_existing_samples() -> dict[str, dict]:
    """기존 샘플 프로젝트 조회. {name: project_data}"""
    r = requests.get(f"{API_BASE}/projects", timeout=10)
    r.raise_for_status()
    data = r.json()

    # projects 키가 있으면 해당 리스트, 아니면 data 자체가 리스트
    projects = data if isinstance(data, list) else data.get("projects", [])

    return {
        p["name"]: p
        for p in projects
        if p.get("name", "").startswith(SAMPLE_PREFIX)
    }


def delete_project(project_id: str, name: str) -> bool:
    """프로젝트 삭제"""
    try:
        r = requests.delete(f"{API_BASE}/projects/{project_id}", timeout=10)
        if r.status_code in (200, 204):
            logger.info(f"  삭제 완료: {name} ({project_id})")
            return True
        logger.warning(f"  삭제 실패: {name} status={r.status_code}")
        return False
    except Exception as e:
        logger.warning(f"  삭제 중 오류: {name} - {e}")
        return False


def create_project(name: str, customer: str, description: str) -> str | None:
    """프로젝트 생성. 성공 시 project_id 반환."""
    r = requests.post(
        f"{API_BASE}/projects",
        json={"name": name, "customer": customer, "description": description},
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    project_id = data.get("project_id")
    logger.info(f"  프로젝트 생성: {name} → {project_id}")
    return project_id


def upload_image(
    project_id: str,
    file_path: Path,
    drawing_type: str = "auto",
    features: str = "",
) -> dict | None:
    """이미지 업로드 → 세션 생성"""
    if not file_path.exists():
        logger.warning(f"  파일 없음: {file_path.name}")
        return None

    mime = "image/png" if file_path.suffix == ".png" else "image/jpeg"
    with open(file_path, "rb") as f:
        r = requests.post(
            f"{API_BASE}/sessions/upload",
            files={"file": (file_path.name, f, mime)},
            params={
                "project_id": project_id,
                "drawing_type": drawing_type,
                "features": features,
            },
            timeout=30,
        )
    r.raise_for_status()
    data = r.json()
    session_id = data.get("session_id", "?")
    logger.info(f"  업로드: {file_path.name} → session={session_id}")
    return data


def import_bom(project_id: str, pdf_path: Path) -> dict | None:
    """BOM PDF 업로드 및 파싱"""
    if not pdf_path.exists():
        logger.warning(f"  BOM PDF 없음: {pdf_path}")
        return None

    with open(pdf_path, "rb") as f:
        r = requests.post(
            f"{API_BASE}/projects/{project_id}/import-bom",
            files={"file": (pdf_path.name, f, "application/pdf")},
            timeout=60,
        )
    r.raise_for_status()
    data = r.json()
    total = data.get("total_items", 0)
    logger.info(f"  BOM 임포트: {total}개 아이템 파싱 완료")
    return data


def match_drawings(project_id: str, folder: str) -> dict | None:
    """도면 매칭"""
    r = requests.post(
        f"{API_BASE}/projects/{project_id}/match-drawings",
        json={"drawing_folder": folder},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    matched = data.get("matched_count", 0)
    total = data.get("total_items", 0)
    logger.info(f"  도면 매칭: {matched}/{total}개 매칭")
    return data


def create_sessions(project_id: str, only_matched: bool = True) -> dict | None:
    """매칭된 도면에서 세션 일괄 생성"""
    r = requests.post(
        f"{API_BASE}/projects/{project_id}/create-sessions",
        json={"only_matched": only_matched},
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    created = data.get("created_count", 0)
    logger.info(f"  세션 생성: {created}개 생성 완료")
    return data


# ── 프로젝트별 시드 ──


def seed_pid_project(existing: dict[str, dict], dry_run: bool = False) -> str | None:
    """[샘플] BWMS P&ID 검출 데모"""
    proj = PROJECTS[0]
    name = proj["name"]
    logger.info(f"\n{'='*60}")
    logger.info(f"[1/3] {name}")
    logger.info(f"{'='*60}")

    if name in existing:
        logger.info(f"  이미 존재 → SKIP (id={existing[name].get('project_id')})")
        return existing[name].get("project_id")

    if dry_run:
        logger.info(f"  [DRY-RUN] 프로젝트 생성 + P&ID 이미지 2장 업로드 예정")
        return None

    project_id = create_project(name, proj["customer"], proj["description"])
    if not project_id:
        return None

    for img in PID_IMAGES:
        upload_image(
            project_id,
            img,
            drawing_type="pid",
            features="verification,gt_comparison",
        )

    return project_id


def seed_dse_bom_project(existing: dict[str, dict], dry_run: bool = False) -> str | None:
    """[샘플] DSE 베어링 BOM 견적"""
    proj = PROJECTS[1]
    name = proj["name"]
    logger.info(f"\n{'='*60}")
    logger.info(f"[2/3] {name}")
    logger.info(f"{'='*60}")

    if name in existing:
        logger.info(f"  이미 존재 → SKIP (id={existing[name].get('project_id')})")
        return existing[name].get("project_id")

    if dry_run:
        logger.info("  [DRY-RUN] 프로젝트 생성 + BOM 임포트 + 도면 매칭 + 세션 생성 + 이미지 5장 업로드 예정")
        return None

    # 1. 프로젝트 생성
    project_id = create_project(name, proj["customer"], proj["description"])
    if not project_id:
        return None

    # 2. BOM PDF 임포트
    bom_result = import_bom(project_id, BOM_PDF)
    if not bom_result:
        logger.warning("  BOM 임포트 실패, 계속 진행")

    # 3. 도면 매칭
    match_result = match_drawings(project_id, DRAWING_FOLDER_CONTAINER)
    if not match_result:
        logger.warning("  도면 매칭 실패, 계속 진행")

    # 4. 세션 일괄 생성 (매칭된 것만)
    logger.info("  세션 생성 중... (PDF→PNG 변환으로 시간이 걸릴 수 있습니다)")
    session_result = create_sessions(project_id, only_matched=True)
    if not session_result:
        logger.warning("  세션 생성 실패, 계속 진행")

    # 5. DSE 테스트 이미지 추가 업로드
    for img in DSE_IMAGES:
        upload_image(
            project_id,
            img,
            drawing_type="mechanical",
            features="verification,gt_comparison,bom_generation,dimension_extraction",
        )

    return project_id


def seed_general_project(existing: dict[str, dict], dry_run: bool = False) -> str | None:
    """[샘플] 일반 도면 분석"""
    proj = PROJECTS[2]
    name = proj["name"]
    logger.info(f"\n{'='*60}")
    logger.info(f"[3/3] {name}")
    logger.info(f"{'='*60}")

    if name in existing:
        logger.info(f"  이미 존재 → SKIP (id={existing[name].get('project_id')})")
        return existing[name].get("project_id")

    if dry_run:
        logger.info("  [DRY-RUN] 프로젝트 생성 + 기계 도면 2장 업로드 예정")
        return None

    project_id = create_project(name, proj["customer"], proj["description"])
    if not project_id:
        return None

    for img in GENERAL_IMAGES:
        upload_image(
            project_id,
            img,
            drawing_type="mechanical",
            features="verification,dimension_extraction",
        )

    return project_id


# ── 메인 ──


def main():
    parser = argparse.ArgumentParser(
        description="Blueprint AI BOM 샘플 데이터 Seed 스크립트",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="기존 샘플 프로젝트 삭제 후 재생성",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실행 계획만 확인 (실제 API 호출 없음)",
    )
    args = parser.parse_args()

    logger.info("Blueprint AI BOM 샘플 데이터 Seed")
    logger.info(f"  API: {API_BASE}")
    logger.info(f"  프로젝트 루트: {PROJECT_ROOT}")
    logger.info(f"  모드: {'DRY-RUN' if args.dry_run else 'CLEAN' if args.clean else '기본 (존재 시 SKIP)'}")

    # 1. 헬스체크
    if not args.dry_run and not check_health():
        logger.error("API 서버가 실행 중이 아닙니다. 종료합니다.")
        sys.exit(1)

    # 2. 파일 존재 확인
    missing = check_files()
    if missing:
        logger.warning(f"누락 파일 {len(missing)}개:")
        for f in missing:
            logger.warning(f"  - {f}")
        if not args.dry_run:
            logger.error("필요한 파일이 없습니다. 종료합니다.")
            sys.exit(1)

    # 3. 기존 샘플 프로젝트 조회
    if args.dry_run:
        existing = {}
    else:
        existing = get_existing_samples()
        if existing:
            logger.info(f"\n기존 샘플 프로젝트 {len(existing)}개:")
            for name, p in existing.items():
                logger.info(f"  - {name} (id={p.get('project_id')})")

    # 4. --clean: 기존 샘플 삭제
    if args.clean and existing:
        logger.info("\n기존 샘플 프로젝트 삭제 중...")
        for name, p in existing.items():
            delete_project(p["project_id"], name)
        existing = {}

    # 5. 프로젝트 순차 생성
    results = {}
    start_time = time.time()

    results["pid"] = seed_pid_project(existing, args.dry_run)
    results["dse_bom"] = seed_dse_bom_project(existing, args.dry_run)
    results["general"] = seed_general_project(existing, args.dry_run)

    elapsed = time.time() - start_time

    # 6. 결과 요약
    logger.info(f"\n{'='*60}")
    logger.info("결과 요약")
    logger.info(f"{'='*60}")

    created = sum(1 for v in results.values() if v is not None)
    skipped = sum(1 for v in results.values() if v is None)

    for label, pid in results.items():
        status = f"id={pid}" if pid else "SKIP/DRY-RUN"
        logger.info(f"  {label}: {status}")

    logger.info(f"\n  생성/존재: {created}개, 스킵: {skipped}개")
    logger.info(f"  소요 시간: {elapsed:.1f}초")

    if not args.dry_run and created > 0:
        logger.info(f"\n확인: http://localhost:5173/projects 에서 '{SAMPLE_PREFIX}' 프로젝트를 확인하세요.")


if __name__ == "__main__":
    main()
