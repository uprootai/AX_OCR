#!/usr/bin/env python3
"""Blueprint AI BOM 대량 테스트 스크립트

도면 이미지들을 일괄 처리하고 결과를 분석합니다.

사용법:
    python scripts/batch_test.py --input ./test_drawings --output ./test_results
    python scripts/batch_test.py --input ./test_drawings --ground-truth ./test_drawings/labels
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API 설정
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5020")


@dataclass
class TestResult:
    """단일 테스트 결과"""
    filename: str
    session_id: str
    status: str  # success, error
    detection_count: int = 0
    dimension_count: int = 0
    gdt_count: int = 0
    processing_time_ms: float = 0
    error_message: Optional[str] = None

    # 정확도 (Ground Truth가 있는 경우)
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None

    # 검증 통계
    verification_stats: dict = field(default_factory=dict)


@dataclass
class BatchTestReport:
    """배치 테스트 리포트"""
    test_date: str
    total_files: int
    successful: int
    failed: int
    avg_processing_time_ms: float
    total_detections: int
    total_dimensions: int
    results: list = field(default_factory=list)

    # 정확도 요약 (Ground Truth가 있는 경우)
    avg_precision: Optional[float] = None
    avg_recall: Optional[float] = None
    avg_f1_score: Optional[float] = None


class BatchTester:
    """배치 테스트 실행기"""

    def __init__(
        self,
        api_base_url: str = API_BASE_URL,
        ground_truth_dir: Optional[Path] = None
    ):
        self.api_base_url = api_base_url
        self.ground_truth_dir = ground_truth_dir
        self.client = httpx.AsyncClient(timeout=120.0)
        self.results: list[TestResult] = []

    async def close(self):
        await self.client.aclose()

    async def test_single_file(self, file_path: Path) -> TestResult:
        """단일 파일 테스트"""
        logger.info(f"테스트 중: {file_path.name}")
        start_time = time.time()

        try:
            # 1. 이미지 업로드
            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f, "image/jpeg")}
                response = await self.client.post(
                    f"{self.api_base_url}/sessions/upload",
                    files=files
                )
                response.raise_for_status()
                upload_result = response.json()
                session_id = upload_result["session_id"]

            # 2. 전체 분석 실행
            analysis_response = await self.client.post(
                f"{self.api_base_url}/analysis/full/{session_id}",
                json={
                    "run_detection": True,
                    "run_ocr": True,
                    "run_gdt": True,
                    "detection_confidence": 0.4
                }
            )
            analysis_response.raise_for_status()
            analysis_result = analysis_response.json()

            # 3. 검증 통계 조회
            stats_response = await self.client.get(
                f"{self.api_base_url}/verification/stats/{session_id}?item_type=symbol"
            )
            verification_stats = {}
            if stats_response.status_code == 200:
                verification_stats = stats_response.json().get("stats", {})

            processing_time = (time.time() - start_time) * 1000

            result = TestResult(
                filename=file_path.name,
                session_id=session_id,
                status="success",
                detection_count=analysis_result.get("detection_count", 0),
                dimension_count=analysis_result.get("dimension_count", 0),
                gdt_count=analysis_result.get("gdt_count", 0),
                processing_time_ms=processing_time,
                verification_stats=verification_stats
            )

            # 4. Ground Truth 비교 (있는 경우)
            if self.ground_truth_dir:
                result = await self._evaluate_accuracy(result, session_id, file_path)

            logger.info(
                f"완료: {file_path.name} - "
                f"검출 {result.detection_count}개, "
                f"치수 {result.dimension_count}개, "
                f"처리시간 {result.processing_time_ms:.0f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"실패: {file_path.name} - {e}")
            return TestResult(
                filename=file_path.name,
                session_id="",
                status="error",
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )

    async def _evaluate_accuracy(
        self,
        result: TestResult,
        session_id: str,
        file_path: Path
    ) -> TestResult:
        """Ground Truth와 비교하여 정확도 계산"""
        # YOLO 형식 레이블 파일 찾기
        label_file = self.ground_truth_dir / f"{file_path.stem}.txt"

        if not label_file.exists():
            logger.warning(f"레이블 파일 없음: {label_file}")
            return result

        try:
            # 레이블 파싱
            with open(label_file) as f:
                gt_labels = []
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        gt_labels.append({
                            "class_id": int(parts[0]),
                            "x_center": float(parts[1]),
                            "y_center": float(parts[2]),
                            "width": float(parts[3]),
                            "height": float(parts[4])
                        })

            # 세션에서 검출 결과 가져오기
            session_response = await self.client.get(
                f"{self.api_base_url}/sessions/{session_id}"
            )
            if session_response.status_code != 200:
                return result

            session_data = session_response.json()
            detections = session_data.get("detections", [])

            # 간단한 정확도 계산 (클래스 매칭 기반)
            gt_classes = set(label["class_id"] for label in gt_labels)
            det_classes = set(d.get("class_id", -1) for d in detections)

            tp = len(gt_classes & det_classes)
            fp = len(det_classes - gt_classes)
            fn = len(gt_classes - det_classes)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

            result.precision = precision
            result.recall = recall
            result.f1_score = f1

            logger.info(
                f"정확도: P={precision:.2f}, R={recall:.2f}, F1={f1:.2f}"
            )

        except Exception as e:
            logger.warning(f"정확도 계산 실패: {e}")

        return result

    async def run_batch_test(self, input_dir: Path) -> BatchTestReport:
        """배치 테스트 실행"""
        # 지원 확장자
        image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}

        # 이미지 파일 목록
        image_files = [
            f for f in input_dir.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]

        if not image_files:
            logger.error(f"이미지 파일을 찾을 수 없습니다: {input_dir}")
            return BatchTestReport(
                test_date=datetime.now().isoformat(),
                total_files=0,
                successful=0,
                failed=0,
                avg_processing_time_ms=0,
                total_detections=0,
                total_dimensions=0
            )

        logger.info(f"총 {len(image_files)}개 파일 테스트 시작")

        # 순차 실행 (API 부하 고려)
        for file_path in image_files:
            result = await self.test_single_file(file_path)
            self.results.append(result)
            await asyncio.sleep(0.5)  # 간격 두기

        # 리포트 생성
        successful = [r for r in self.results if r.status == "success"]
        failed = [r for r in self.results if r.status == "error"]

        report = BatchTestReport(
            test_date=datetime.now().isoformat(),
            total_files=len(self.results),
            successful=len(successful),
            failed=len(failed),
            avg_processing_time_ms=sum(r.processing_time_ms for r in successful) / len(successful) if successful else 0,
            total_detections=sum(r.detection_count for r in successful),
            total_dimensions=sum(r.dimension_count for r in successful),
            results=[asdict(r) for r in self.results]
        )

        # 정확도 평균 계산
        with_accuracy = [r for r in successful if r.precision is not None]
        if with_accuracy:
            report.avg_precision = sum(r.precision for r in with_accuracy) / len(with_accuracy)
            report.avg_recall = sum(r.recall for r in with_accuracy) / len(with_accuracy)
            report.avg_f1_score = sum(r.f1_score for r in with_accuracy) / len(with_accuracy)

        return report


async def main():
    parser = argparse.ArgumentParser(description="Blueprint AI BOM 대량 테스트")
    parser.add_argument("--input", "-i", type=Path, required=True,
                        help="입력 이미지 디렉토리")
    parser.add_argument("--output", "-o", type=Path, default=Path("./test_results"),
                        help="결과 출력 디렉토리")
    parser.add_argument("--ground-truth", "-g", type=Path,
                        help="Ground Truth 레이블 디렉토리 (YOLO 형식)")
    parser.add_argument("--api-url", type=str, default=API_BASE_URL,
                        help="API 서버 URL")

    args = parser.parse_args()

    # 입력 디렉토리 확인
    if not args.input.exists():
        logger.error(f"입력 디렉토리를 찾을 수 없습니다: {args.input}")
        sys.exit(1)

    # 출력 디렉토리 생성
    args.output.mkdir(parents=True, exist_ok=True)

    # 테스터 초기화
    tester = BatchTester(
        api_base_url=args.api_url,
        ground_truth_dir=args.ground_truth
    )

    try:
        # 테스트 실행
        report = await tester.run_batch_test(args.input)

        # 리포트 저장
        report_file = args.output / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, ensure_ascii=False, indent=2)

        # 요약 출력
        print("\n" + "=" * 60)
        print("테스트 결과 요약")
        print("=" * 60)
        print(f"테스트 일시: {report.test_date}")
        print(f"총 파일 수: {report.total_files}")
        print(f"성공: {report.successful}")
        print(f"실패: {report.failed}")
        print(f"평균 처리 시간: {report.avg_processing_time_ms:.0f}ms")
        print(f"총 검출 수: {report.total_detections}")
        print(f"총 치수 수: {report.total_dimensions}")

        if report.avg_precision is not None:
            print(f"\n정확도:")
            print(f"  Precision: {report.avg_precision:.2%}")
            print(f"  Recall: {report.avg_recall:.2%}")
            print(f"  F1 Score: {report.avg_f1_score:.2%}")

        print(f"\n리포트 저장: {report_file}")
        print("=" * 60)

    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
