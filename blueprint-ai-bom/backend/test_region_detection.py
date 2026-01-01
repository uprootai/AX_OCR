#!/usr/bin/env python3
"""
실제 도면으로 영역 검출 테스트

Blueprint AI BOM의 RegionSegmenter + DocLayout-YOLO 통합 테스트
"""

import asyncio
import sys
import time
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent))

from PIL import Image
import cv2
import numpy as np


async def test_region_detection():
    """실제 도면으로 영역 검출 테스트"""

    print("=" * 70)
    print("Blueprint AI BOM - 영역 검출 테스트 (DocLayout-YOLO 통합)")
    print("=" * 70)

    # 1. 모듈 임포트
    print("\n[1] 모듈 임포트...")
    from services.region_segmenter import region_segmenter, USE_DOCLAYOUT
    from services.layout_analyzer import get_layout_analyzer
    from schemas.region import RegionSegmentationConfig

    print(f"    USE_DOCLAYOUT: {USE_DOCLAYOUT}")

    analyzer = get_layout_analyzer()
    print(f"    DocLayout-YOLO 사용 가능: {analyzer.is_available}")

    # 2. 테스트 이미지 찾기
    print("\n[2] 테스트 이미지 검색...")

    base_path = Path(__file__).parent.parent.parent
    test_images = []

    # 샘플 이미지 경로들
    sample_dirs = [
        base_path / "web-ui/public/samples",
        base_path / "blueprint-ai-bom/test_drawings",
        base_path / "samples",
    ]

    for sample_dir in sample_dirs:
        if sample_dir.exists():
            for ext in ["*.jpg", "*.png", "*.jpeg"]:
                test_images.extend(sample_dir.glob(ext))

    # 중복 제거 및 정렬
    test_images = sorted(set(test_images))[:6]  # 최대 6개

    print(f"    발견된 테스트 이미지: {len(test_images)}개")
    for img in test_images:
        print(f"      - {img.name}")

    if not test_images:
        print("    [ERROR] 테스트 이미지 없음!")
        return

    # 3. 결과 저장 디렉토리
    output_dir = Path(__file__).parent / "test_results"
    output_dir.mkdir(exist_ok=True)
    print(f"\n[3] 결과 저장 위치: {output_dir}")

    # 4. 영역 검출 테스트
    print("\n[4] 영역 검출 실행...")
    print("-" * 70)

    all_results = []

    for i, image_path in enumerate(test_images, 1):
        print(f"\n[{i}/{len(test_images)}] {image_path.name}")

        session_id = f"test_session_{i}"

        # 설정
        config = RegionSegmentationConfig(
            confidence_threshold=0.15,
            detect_title_block=True,
            detect_bom_table=True,
            detect_legend=True,
            detect_notes=True,
            merge_overlapping=True,
            overlap_threshold=0.5,
            auto_assign_strategy=True,
        )

        start_time = time.time()

        try:
            # 영역 분할 실행
            result = await region_segmenter.segment(
                session_id=session_id,
                image_path=str(image_path),
                config=config,
                use_vlm=False,  # VLM 없이 DocLayout-YOLO + 휴리스틱만
            )

            elapsed = time.time() - start_time

            print(f"    처리 시간: {elapsed:.2f}초 ({result.processing_time_ms:.0f}ms)")
            print(f"    검출 영역: {result.total_regions}개")
            print(f"    영역 통계: {result.region_stats}")

            # 결과 시각화
            visualize_result(
                image_path=str(image_path),
                regions=result.regions,
                output_path=output_dir / f"{image_path.stem}_regions.jpg"
            )

            all_results.append({
                "image": image_path.name,
                "regions": result.total_regions,
                "stats": result.region_stats,
                "time_ms": result.processing_time_ms,
            })

        except Exception as e:
            print(f"    [ERROR] {e}")
            import traceback
            traceback.print_exc()

    # 5. 요약
    print("\n" + "=" * 70)
    print("테스트 결과 요약")
    print("=" * 70)

    total_regions = sum(r["regions"] for r in all_results)
    avg_time = sum(r["time_ms"] for r in all_results) / len(all_results) if all_results else 0

    print(f"\n총 이미지: {len(all_results)}개")
    print(f"총 검출 영역: {total_regions}개")
    print(f"평균 처리 시간: {avg_time:.0f}ms")

    # 영역 타입별 통계
    type_totals = {}
    for r in all_results:
        for region_type, count in r["stats"].items():
            type_totals[region_type] = type_totals.get(region_type, 0) + count

    print(f"\n영역 타입별 검출:")
    for region_type, count in sorted(type_totals.items(), key=lambda x: -x[1]):
        print(f"  - {region_type}: {count}개")

    print(f"\n결과 이미지: {output_dir}")
    print("=" * 70)

    return all_results


def visualize_result(image_path: str, regions: list, output_path: Path):
    """검출 결과 시각화"""

    # 이미지 로드
    image = cv2.imread(image_path)
    if image is None:
        print(f"    [WARN] 이미지 로드 실패: {image_path}")
        return

    # 영역 타입별 색상
    colors = {
        "title_block": (0, 255, 0),      # 초록
        "main_view": (255, 0, 0),        # 파랑
        "bom_table": (0, 0, 255),        # 빨강
        "notes": (255, 255, 0),          # 시안
        "detail_view": (255, 0, 255),    # 마젠타
        "section_view": (0, 255, 255),   # 노랑
        "legend": (128, 0, 255),         # 보라
        "unknown": (128, 128, 128),      # 회색
    }

    # 영역 그리기
    for region in regions:
        bbox = region.bbox
        x1, y1, x2, y2 = int(bbox.x1), int(bbox.y1), int(bbox.x2), int(bbox.y2)

        region_type = region.region_type.value
        color = colors.get(region_type, (128, 128, 128))

        # 박스 그리기
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 3)

        # 라벨 그리기
        label = f"{region_type} ({region.confidence:.2f})"

        # 라벨 배경
        (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(image, (x1, y1 - label_h - 10), (x1 + label_w + 10, y1), color, -1)

        # 라벨 텍스트
        cv2.putText(image, label, (x1 + 5, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # 저장
    cv2.imwrite(str(output_path), image)
    print(f"    저장: {output_path.name}")


async def test_doclayout_direct():
    """DocLayout-YOLO 직접 테스트 (비교용)"""

    print("\n" + "=" * 70)
    print("DocLayout-YOLO 직접 테스트 (비교용)")
    print("=" * 70)

    from services.layout_analyzer import get_layout_analyzer

    analyzer = get_layout_analyzer()
    if not analyzer.is_available:
        print("[SKIP] DocLayout-YOLO 사용 불가")
        return

    # 테스트 이미지
    base_path = Path(__file__).parent.parent.parent
    sample_image = base_path / "web-ui/public/samples/sample2_interm_shaft.jpg"

    if not sample_image.exists():
        # 대체 이미지 찾기
        for sample_dir in [base_path / "web-ui/public/samples", base_path / "samples"]:
            if sample_dir.exists():
                images = list(sample_dir.glob("*.jpg")) + list(sample_dir.glob("*.png"))
                if images:
                    sample_image = images[0]
                    break

    if not sample_image.exists():
        print("[ERROR] 테스트 이미지 없음")
        return

    print(f"\n테스트 이미지: {sample_image.name}")

    # DocLayout-YOLO 직접 추론
    start = time.time()
    detections = analyzer.detect(str(sample_image))
    elapsed = (time.time() - start) * 1000

    print(f"추론 시간: {elapsed:.0f}ms")
    print(f"검출 수: {len(detections)}")

    print("\n검출 결과:")
    for det in detections:
        print(f"  - {det.class_name} → {det.region_type} (conf: {det.confidence:.2f})")
        print(f"    bbox: {det.bbox}")

    # 통계
    stats = analyzer.get_stats(detections)
    print(f"\n통계: {stats}")


if __name__ == "__main__":
    # DocLayout-YOLO 직접 테스트
    asyncio.run(test_doclayout_direct())

    # 통합 테스트
    asyncio.run(test_region_detection())
