#!/usr/bin/env python3
"""
Customer Drawing Coverage Test Script
고객 샘플 도면을 기존 모델에 테스트하고 커버리지 리포트 생성

Usage:
    python scripts/test_coverage.py \\
        --drawings-dir /path/to/samples \\
        --customer-id panasia \\
        --output-report reports/panasia_coverage.json

테스트 대상:
    - YOLO Detection  (http://localhost:8000/api/v1/detect)
    - eDOCr2 OCR      (http://localhost:8000/api/v1/ocr)
    - Table Detector  (http://localhost:8000/api/v1/table)

출력:
    - JSON 리포트 (per-image stats + aggregate + coverage score)
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

import urllib.request
import urllib.error
import urllib.parse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Gateway API 기본 URL
GATEWAY_URL = "http://localhost:8000"

# 지원 이미지 확장자
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}

# 커버리지 임계값 (%)
COVERAGE_THRESHOLDS = {
    "excellent": 80,
    "good": 60,
    "fair": 40,
    "poor": 0,
}


# =====================
# HTTP 멀티파트 헬퍼
# (httpx 미의존 — stdlib만 사용)
# =====================

def _build_multipart(file_path: Path) -> tuple[bytes, str]:
    """
    multipart/form-data 페이로드 생성 (stdlib 사용)

    Returns:
        (body_bytes, content_type_header)
    """
    boundary = "----AXCoverageBoundary7f3a9b"
    filename = file_path.name
    mime_type = "image/png" if file_path.suffix.lower() == ".png" else "image/jpeg"

    with open(file_path, "rb") as f:
        file_data = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type


def _post_image(endpoint: str, image_path: Path, timeout: int = 60) -> Dict[str, Any]:
    """
    이미지 파일을 multipart/form-data로 POST 전송

    Args:
        endpoint: 전체 URL (예: http://localhost:8000/api/v1/detect)
        image_path: 이미지 파일 경로
        timeout: 타임아웃 (초)

    Returns:
        응답 JSON 딕셔너리 (오류 시 {"error": ..., "success": False})
    """
    try:
        body, content_type = _build_multipart(image_path)
        req = urllib.request.Request(
            endpoint,
            data=body,
            headers={"Content-Type": content_type},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        return {
            "success": False,
            "error": f"HTTP {e.code}: {error_body[:200]}",
            "status_code": e.code,
        }
    except urllib.error.URLError as e:
        return {
            "success": False,
            "error": f"Connection error: {e.reason}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def _get_json(endpoint: str, timeout: int = 10) -> Dict[str, Any]:
    """GET 요청 후 JSON 반환"""
    try:
        req = urllib.request.Request(endpoint, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"success": False, "error": str(e)}


# =====================
# 게이트웨이 헬스체크
# =====================

def check_gateway_health(gateway_url: str) -> Dict[str, bool]:
    """
    Gateway API 및 하위 서비스 헬스체크

    Returns:
        {"gateway": bool, "yolo": bool, "edocr2": bool, "table": bool}
    """
    health = {}

    result = _get_json(f"{gateway_url}/health")
    health["gateway"] = result.get("status") == "healthy" or "error" not in result

    # 각 모델 서비스 헬스 (Gateway 프록시 경유)
    for service_key, path in [
        ("yolo", "/api/v1/detect/health"),
        ("edocr2", "/api/v1/ocr/health"),
        ("table", "/api/v1/table/health"),
    ]:
        r = _get_json(f"{gateway_url}{path}")
        health[service_key] = "error" not in r

    return health


# =====================
# 모델별 테스트
# =====================

def test_yolo(image_path: Path, gateway_url: str) -> Dict[str, Any]:
    """
    YOLO Detection 테스트

    Returns:
        {
            "success": bool,
            "detection_count": int,
            "avg_confidence": float,
            "labels": List[str],
            "processing_time": float,
            "error": str | None,
        }
    """
    start = time.time()
    result = _post_image(f"{gateway_url}/api/v1/detect", image_path)
    elapsed = time.time() - start

    if not result.get("success", False) or "error" in result:
        return {
            "success": False,
            "detection_count": 0,
            "avg_confidence": 0.0,
            "labels": [],
            "processing_time": round(elapsed, 3),
            "error": result.get("error", "Unknown error"),
        }

    data = result.get("data", result)
    detections = data.get("detections", data.get("results", []))
    if not isinstance(detections, list):
        detections = []

    confidences = [
        float(d.get("confidence", d.get("score", 0.0)))
        for d in detections
        if isinstance(d, dict)
    ]
    labels = list({
        d.get("label", d.get("class", d.get("name", "")))
        for d in detections
        if isinstance(d, dict)
    })

    return {
        "success": True,
        "detection_count": len(detections),
        "avg_confidence": round(sum(confidences) / len(confidences), 4) if confidences else 0.0,
        "labels": labels,
        "processing_time": round(elapsed, 3),
        "error": None,
    }


def test_edocr2(image_path: Path, gateway_url: str) -> Dict[str, Any]:
    """
    eDOCr2 OCR 테스트

    Returns:
        {
            "success": bool,
            "text_count": int,
            "total_chars": int,
            "avg_confidence": float,
            "sample_texts": List[str],
            "processing_time": float,
            "error": str | None,
        }
    """
    start = time.time()
    result = _post_image(f"{gateway_url}/api/v1/ocr", image_path)
    elapsed = time.time() - start

    if not result.get("success", False) or "error" in result:
        return {
            "success": False,
            "text_count": 0,
            "total_chars": 0,
            "avg_confidence": 0.0,
            "sample_texts": [],
            "processing_time": round(elapsed, 3),
            "error": result.get("error", "Unknown error"),
        }

    data = result.get("data", result)

    # 텍스트 추출 (다양한 응답 구조 대응)
    texts = []
    confidences = []

    # 구조 1: data.regions[].texts[]
    for region in data.get("regions", []):
        for t in region.get("texts", []):
            if isinstance(t, dict):
                text = t.get("text", "").strip()
                conf = t.get("confidence", t.get("score", None))
            else:
                text = str(t).strip()
                conf = None
            if text:
                texts.append(text)
            if conf is not None:
                confidences.append(float(conf))

    # 구조 2: data.texts[]
    if not texts:
        for t in data.get("texts", []):
            if isinstance(t, dict):
                text = t.get("text", "").strip()
                conf = t.get("confidence", t.get("score", None))
            else:
                text = str(t).strip()
                conf = None
            if text:
                texts.append(text)
            if conf is not None:
                confidences.append(float(conf))

    sample_texts = texts[:5]  # 처음 5개만 샘플

    return {
        "success": True,
        "text_count": len(texts),
        "total_chars": sum(len(t) for t in texts),
        "avg_confidence": round(sum(confidences) / len(confidences), 4) if confidences else 0.0,
        "sample_texts": sample_texts,
        "processing_time": round(elapsed, 3),
        "error": None,
    }


def test_table_detector(image_path: Path, gateway_url: str) -> Dict[str, Any]:
    """
    Table Detector 테스트

    Returns:
        {
            "success": bool,
            "table_count": int,
            "total_cells": int,
            "avg_confidence": float,
            "processing_time": float,
            "error": str | None,
        }
    """
    start = time.time()
    result = _post_image(f"{gateway_url}/api/v1/table", image_path)
    elapsed = time.time() - start

    if not result.get("success", False) or "error" in result:
        return {
            "success": False,
            "table_count": 0,
            "total_cells": 0,
            "avg_confidence": 0.0,
            "processing_time": round(elapsed, 3),
            "error": result.get("error", "Unknown error"),
        }

    data = result.get("data", result)
    tables = data.get("tables", [])
    if not isinstance(tables, list):
        tables = []

    total_cells = sum(
        len(t.get("cells", t.get("rows", [])))
        for t in tables
        if isinstance(t, dict)
    )
    confidences = [
        float(t.get("confidence", t.get("score", 0.0)))
        for t in tables
        if isinstance(t, dict) and "confidence" in t or "score" in t
    ]

    return {
        "success": True,
        "table_count": len(tables),
        "total_cells": total_cells,
        "avg_confidence": round(sum(confidences) / len(confidences), 4) if confidences else 0.0,
        "processing_time": round(elapsed, 3),
        "error": None,
    }


# =====================
# 커버리지 계산
# =====================

def calculate_image_score(yolo: Dict, ocr: Dict, table: Dict) -> float:
    """
    단일 이미지 커버리지 점수 계산 (0-100)

    가중치:
      - YOLO: 40% (물체 감지)
      - OCR:  40% (텍스트 추출)
      - Table: 20% (테이블 구조)
    """
    score = 0.0

    # YOLO (40점)
    if yolo.get("success"):
        count = yolo.get("detection_count", 0)
        conf = yolo.get("avg_confidence", 0.0)
        # 감지 1개 이상 + 신뢰도 0.3 이상 = 기본 점수
        if count > 0:
            score += 20.0
        if conf >= 0.3:
            score += 10.0
        if conf >= 0.6:
            score += 10.0

    # OCR (40점)
    if ocr.get("success"):
        text_count = ocr.get("text_count", 0)
        conf = ocr.get("avg_confidence", 0.0)
        if text_count >= 5:
            score += 20.0
        elif text_count > 0:
            score += 10.0
        if conf >= 0.5:
            score += 10.0
        elif conf > 0.0:
            score += 5.0
        if text_count >= 20:
            score += 10.0

    # Table (20점)
    if table.get("success"):
        tbl_count = table.get("table_count", 0)
        if tbl_count > 0:
            score += 15.0
        if tbl_count >= 2:
            score += 5.0

    return round(min(score, 100.0), 2)


def calculate_coverage_label(score: float) -> str:
    """점수 → 레이블 변환"""
    if score >= COVERAGE_THRESHOLDS["excellent"]:
        return "excellent"
    if score >= COVERAGE_THRESHOLDS["good"]:
        return "good"
    if score >= COVERAGE_THRESHOLDS["fair"]:
        return "fair"
    return "poor"


# =====================
# 집계
# =====================

def aggregate_results(image_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    이미지별 결과를 집계하여 aggregate stats 계산

    Returns:
        {
            "total_images": int,
            "yolo": { "success_rate": float, "avg_detection_count": float, ... },
            "ocr": { ... },
            "table": { ... },
            "overall_score": float,
            "coverage_label": str,
        }
    """
    total = len(image_results)
    if total == 0:
        return {
            "total_images": 0,
            "yolo": {},
            "ocr": {},
            "table": {},
            "overall_score": 0.0,
            "coverage_label": "poor",
        }

    def _avg(values: List[float]) -> float:
        return round(sum(values) / len(values), 4) if values else 0.0

    yolo_results = [r["yolo"] for r in image_results]
    ocr_results = [r["ocr"] for r in image_results]
    table_results = [r["table"] for r in image_results]

    yolo_agg = {
        "success_rate": round(sum(1 for r in yolo_results if r.get("success")) / total * 100, 2),
        "avg_detection_count": _avg([r.get("detection_count", 0) for r in yolo_results]),
        "avg_confidence": _avg([r.get("avg_confidence", 0.0) for r in yolo_results if r.get("success")]),
    }

    ocr_agg = {
        "success_rate": round(sum(1 for r in ocr_results if r.get("success")) / total * 100, 2),
        "avg_text_count": _avg([r.get("text_count", 0) for r in ocr_results]),
        "avg_total_chars": _avg([r.get("total_chars", 0) for r in ocr_results]),
        "avg_confidence": _avg([r.get("avg_confidence", 0.0) for r in ocr_results if r.get("success")]),
    }

    table_agg = {
        "success_rate": round(sum(1 for r in table_results if r.get("success")) / total * 100, 2),
        "avg_table_count": _avg([r.get("table_count", 0) for r in table_results]),
        "images_with_tables": sum(1 for r in table_results if r.get("table_count", 0) > 0),
    }

    scores = [r.get("coverage_score", 0.0) for r in image_results]
    overall_score = _avg(scores)

    return {
        "total_images": total,
        "yolo": yolo_agg,
        "ocr": ocr_agg,
        "table": table_agg,
        "overall_score": overall_score,
        "coverage_label": calculate_coverage_label(overall_score),
    }


# =====================
# 메인 테스트 루프
# =====================

def run_coverage_test(
    drawings_dir: Path,
    customer_id: str,
    gateway_url: str,
    output_report: Optional[Path],
    skip_health_check: bool = False,
) -> Dict[str, Any]:
    """
    커버리지 테스트 실행

    Args:
        drawings_dir: 샘플 도면 디렉토리
        customer_id: 고객 ID
        gateway_url: Gateway API URL
        output_report: 리포트 저장 경로
        skip_health_check: 헬스체크 생략 여부

    Returns:
        커버리지 리포트 딕셔너리
    """
    # 이미지 파일 탐색
    image_paths = sorted([
        p for p in drawings_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ])

    if not image_paths:
        logger.warning(f"이미지 파일 없음: {drawings_dir}")
        return {
            "customer_id": customer_id,
            "error": f"No images found in {drawings_dir}",
            "overall_score": 0.0,
        }

    logger.info(f"발견된 이미지: {len(image_paths)}개")

    # 헬스체크
    health_status: Dict[str, bool] = {}
    if not skip_health_check:
        logger.info("Gateway 헬스체크 중...")
        health_status = check_gateway_health(gateway_url)
        for svc, ok in health_status.items():
            status_str = "OK" if ok else "UNAVAILABLE"
            logger.info(f"  [{status_str}] {svc}")

    # 이미지별 테스트
    image_results: List[Dict[str, Any]] = []

    for idx, img_path in enumerate(image_paths, start=1):
        logger.info(f"[{idx}/{len(image_paths)}] {img_path.name}")

        yolo = test_yolo(img_path, gateway_url)
        ocr = test_edocr2(img_path, gateway_url)
        table = test_table_detector(img_path, gateway_url)

        score = calculate_image_score(yolo, ocr, table)
        label = calculate_coverage_label(score)

        image_result = {
            "filename": img_path.name,
            "file_size_kb": round(img_path.stat().st_size / 1024, 1),
            "coverage_score": score,
            "coverage_label": label,
            "yolo": yolo,
            "ocr": ocr,
            "table": table,
        }

        image_results.append(image_result)

        logger.info(
            f"  YOLO={yolo.get('detection_count', 'ERR')} detections, "
            f"OCR={ocr.get('text_count', 'ERR')} texts, "
            f"Table={table.get('table_count', 'ERR')} tables "
            f"→ score={score:.1f}% ({label})"
        )

    # 집계
    aggregate = aggregate_results(image_results)

    # 리포트 구성
    report = {
        "generated_at": datetime.now().isoformat(),
        "customer_id": customer_id,
        "gateway_url": gateway_url,
        "drawings_dir": str(drawings_dir),
        "health_status": health_status,
        "aggregate": aggregate,
        "images": image_results,
        "overall_score": aggregate["overall_score"],
        "coverage_label": aggregate["coverage_label"],
        "recommendations": _generate_recommendations(aggregate),
    }

    # 저장
    if output_report:
        output_report.parent.mkdir(parents=True, exist_ok=True)
        output_report.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info(f"\n리포트 저장됨: {output_report}")

    _print_summary(report)
    return report


def _generate_recommendations(aggregate: Dict[str, Any]) -> List[str]:
    """집계 결과 기반 개선 권고사항 생성"""
    recs = []

    yolo = aggregate.get("yolo", {})
    ocr = aggregate.get("ocr", {})
    table = aggregate.get("table", {})
    score = aggregate.get("overall_score", 0.0)

    if yolo.get("success_rate", 0) < 70:
        recs.append("YOLO 모델 fine-tuning 필요: 해당 고객 도면 유형에 맞는 학습 데이터 수집 권장")

    if yolo.get("avg_confidence", 0) < 0.4:
        recs.append("YOLO 신뢰도 낮음: confidence threshold 조정 또는 추가 학습 필요")

    if ocr.get("success_rate", 0) < 70:
        recs.append("OCR 성공률 낮음: eDOCr2 전처리 파라미터 조정 필요")

    if ocr.get("avg_text_count", 0) < 10:
        recs.append("OCR 텍스트 추출량 적음: 이미지 해상도 확인 또는 전처리 적용 권장")

    if table.get("images_with_tables", 0) == 0:
        recs.append("테이블 감지 없음: Table Detector 모델 학습 데이터에 해당 도면 추가 권장")

    if score >= COVERAGE_THRESHOLDS["excellent"]:
        recs.append("커버리지 우수: 커스터마이징 파이프라인 즉시 배포 가능")
    elif score >= COVERAGE_THRESHOLDS["good"]:
        recs.append("커버리지 양호: 소규모 파싱 규칙 보완 후 배포 권장")
    elif score >= COVERAGE_THRESHOLDS["fair"]:
        recs.append("커버리지 보통: 모델 fine-tuning 후 재테스트 권장")
    else:
        recs.append("커버리지 낮음: 대규모 커스터마이징 필요, 프로젝트팀 협의 권장")

    return recs


def _print_summary(report: Dict[str, Any]) -> None:
    """콘솔 요약 출력"""
    agg = report.get("aggregate", {})
    score = report.get("overall_score", 0.0)
    label = report.get("coverage_label", "unknown")

    print(f"\n{'='*60}")
    print(f"커버리지 테스트 결과 — {report['customer_id']}")
    print(f"{'='*60}")
    print(f"  전체 이미지    : {agg.get('total_images', 0)}개")
    print(f"  YOLO 성공률    : {agg.get('yolo', {}).get('success_rate', 0):.1f}%")
    print(f"  OCR 성공률     : {agg.get('ocr', {}).get('success_rate', 0):.1f}%")
    print(f"  Table 성공률   : {agg.get('table', {}).get('success_rate', 0):.1f}%")
    print(f"  ─────────────────────────────")
    print(f"  커버리지 점수  : {score:.1f}% ({label.upper()})")
    print(f"{'='*60}")

    recs = report.get("recommendations", [])
    if recs:
        print("\n권고사항:")
        for i, rec in enumerate(recs, start=1):
            print(f"  {i}. {rec}")
    print()


# =====================
# CLI
# =====================

def main():
    parser = argparse.ArgumentParser(
        description="고객 샘플 도면을 기존 모델에 테스트하고 커버리지 리포트를 생성합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python scripts/test_coverage.py \\
      --drawings-dir /data/panasia/samples \\
      --customer-id panasia \\
      --output-report reports/panasia_coverage.json

  python scripts/test_coverage.py \\
      --drawings-dir ./samples \\
      --customer-id dsebearing \\
      --gateway-url http://localhost:8000 \\
      --skip-health-check
        """,
    )

    parser.add_argument(
        "--drawings-dir",
        required=True,
        type=Path,
        help="샘플 도면 이미지 디렉토리",
    )
    parser.add_argument(
        "--customer-id",
        required=True,
        help="고객 ID (예: panasia, dsebearing)",
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default=None,
        help="리포트 저장 경로 (JSON, 기본: reports/{customer_id}_coverage.json)",
    )
    parser.add_argument(
        "--gateway-url",
        default=GATEWAY_URL,
        help=f"Gateway API URL (기본: {GATEWAY_URL})",
    )
    parser.add_argument(
        "--skip-health-check",
        action="store_true",
        help="헬스체크 생략 (서비스 미실행 환경에서도 구조 테스트 가능)",
    )

    args = parser.parse_args()

    # 디렉토리 검증
    drawings_dir = args.drawings_dir.resolve()
    if not drawings_dir.exists():
        print(f"오류: 디렉토리가 존재하지 않습니다: {drawings_dir}")
        sys.exit(1)
    if not drawings_dir.is_dir():
        print(f"오류: 경로가 디렉토리가 아닙니다: {drawings_dir}")
        sys.exit(1)

    # 리포트 경로 기본값
    output_report = args.output_report
    if output_report is None:
        output_report = Path("reports") / f"{args.customer_id}_coverage.json"

    report = run_coverage_test(
        drawings_dir=drawings_dir,
        customer_id=args.customer_id,
        gateway_url=args.gateway_url,
        output_report=output_report,
        skip_health_check=args.skip_health_check,
    )

    overall_score = report.get("overall_score", 0.0)
    label = report.get("coverage_label", "unknown")

    logger.info(f"완료: {overall_score:.1f}% ({label})")
    sys.exit(0)


if __name__ == "__main__":
    main()
