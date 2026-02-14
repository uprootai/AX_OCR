#!/usr/bin/env python3
"""기존 세션 features 일괄 업데이트 스크립트

프로젝트 타입에 맞는 features/drawing_type을 기존 세션에 적용합니다.

Usage:
    python fix_session_features.py [--dry-run] [--base-url http://localhost:5020]
"""

import argparse
import json
import sys
import urllib.request
import urllib.error

# 프로젝트별 프리셋 (project_service.py의 PROJECT_TYPE_PRESETS와 동일)
PROJECT_PRESETS = {
    "bom_quotation": {
        "drawing_type": "dimension_bom",
        "features": ["dimension_ocr", "table_extraction", "bom_generation", "title_block_ocr"],
    },
    "pid_detection": {
        "drawing_type": "pid",
        "features": ["symbol_detection", "pid_connectivity", "gt_comparison"],
    },
}

# 대상 프로젝트 (project_id → project_type)
TARGET_PROJECTS = {
    "2d0b6705": "bom_quotation",  # 동서기연 터빈 베어링
    "2d8f8d57": "pid_detection",  # 파나시아 BWMS P&ID
}


def api_get(base_url: str, path: str):
    """GET 요청"""
    url = f"{base_url}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def api_patch(base_url: str, path: str, data: dict):
    """PATCH 요청"""
    url = f"{base_url}{path}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method="PATCH")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def main():
    parser = argparse.ArgumentParser(description="기존 세션 features 일괄 업데이트")
    parser.add_argument("--dry-run", action="store_true", help="실제 업데이트 없이 대상만 표시")
    parser.add_argument("--base-url", default="http://localhost:5020", help="API 기본 URL")
    args = parser.parse_args()

    total_updated = 0
    total_skipped = 0

    for project_id, project_type in TARGET_PROJECTS.items():
        preset = PROJECT_PRESETS[project_type]
        print(f"\n{'='*60}")
        print(f"프로젝트: {project_id} ({project_type})")
        print(f"  drawing_type: {preset['drawing_type']}")
        print(f"  features: {preset['features']}")
        print(f"{'='*60}")

        # 세션 목록 조회
        try:
            sessions = api_get(args.base_url, f"/sessions?project_id={project_id}&limit=100")
        except urllib.error.URLError as e:
            print(f"  [ERROR] 세션 목록 조회 실패: {e}")
            continue

        print(f"  세션 {len(sessions)}개 발견")

        for session in sessions:
            sid = session.get("session_id", "")
            current_features = session.get("features", [])
            current_dt = session.get("drawing_type", "")

            # 이미 올바른 설정인 경우 건너뛰기
            if current_features == preset["features"] and current_dt == preset["drawing_type"]:
                total_skipped += 1
                continue

            print(f"  [{sid[:8]}] {current_dt}/{current_features} → {preset['drawing_type']}/{preset['features']}")

            if not args.dry_run:
                try:
                    api_patch(args.base_url, f"/sessions/{sid}", {
                        "features": preset["features"],
                        "drawing_type": preset["drawing_type"],
                    })
                    total_updated += 1
                except urllib.error.URLError as e:
                    print(f"    [ERROR] 업데이트 실패: {e}")
            else:
                total_updated += 1

    print(f"\n{'='*60}")
    prefix = "[DRY-RUN] " if args.dry_run else ""
    print(f"{prefix}완료: {total_updated}개 업데이트, {total_skipped}개 건너뜀")


if __name__ == "__main__":
    main()
