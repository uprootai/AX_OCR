#!/usr/bin/env python3
"""
Customer API Scaffolding Script
고객별 도면 파싱 파이프라인을 표준 구조로 생성

Usage:
    python scripts/create_customer_api.py \\
        --customer-id panasia \\
        --customer-name 파나시아 \\
        --drawing-type pid \\
        --port 5031

생성되는 파일:
    - gateway-api/services/{customer_id}_parser.py
    - gateway-api/routers/{customer_id}_router.py
    - gateway-api/api_specs/{customer_id}.yaml
    - gateway-api/services/{customer_id}_config.py

템플릿: scripts/create_customer_api_templates.py
"""

import argparse
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import List

from create_customer_api_templates import (
    PARSER_TEMPLATE,
    ROUTER_TEMPLATE,
    SPEC_TEMPLATE,
    CONFIG_TEMPLATE,
)

PROJECT_ROOT = Path(__file__).parent.parent
GATEWAY_DIR = PROJECT_ROOT / "gateway-api"
SERVICES_DIR = GATEWAY_DIR / "services"
ROUTERS_DIR = GATEWAY_DIR / "routers"
SPECS_DIR = GATEWAY_DIR / "api_specs"

# 도면 유형별 기본 설정
DRAWING_TYPE_CONFIG = {
    "pid": {
        "description": "P&ID 공정배관계장도",
        "tags": ["pid", "process", "instrumentation"],
    },
    "mechanical": {
        "description": "기계 제작 도면",
        "tags": ["mechanical", "manufacturing", "bearing"],
    },
    "mixed": {
        "description": "복합 도면 (P&ID + 기계)",
        "tags": ["mixed", "combined"],
    },
}

# 포트 자동 할당 시작 (5030+)
DEFAULT_PORT_START = 5030


# =====================
# 유틸리티
# =====================

def to_pascal_case(name: str) -> str:
    """snake_case 또는 kebab-case를 PascalCase로 변환"""
    return "".join(word.capitalize() for word in re.split(r"[-_]", name))


def get_model_pipeline(drawing_type: str) -> str:
    """도면 유형에 따른 모델 파이프라인 반환"""
    pipelines = {
        "pid": '["edocr2", "yolo_detection"]',
        "mechanical": '["yolo_detection", "edocr2", "table_detector"]',
        "mixed": '["yolo_detection", "edocr2", "table_detector"]',
    }
    return pipelines.get(drawing_type, '["edocr2", "yolo_detection"]')


def format_tags_yaml(tags: List[str]) -> str:
    """태그 목록을 YAML 형식으로 변환"""
    return "\n".join(f"    - {tag}" for tag in tags)


def validate_customer_id(customer_id: str) -> bool:
    """customer_id 형식 검증: 소문자 + 숫자 + 언더스코어"""
    return bool(re.match(r'^[a-z][a-z0-9_]*$', customer_id))


def find_next_port() -> int:
    """사용 중이지 않은 다음 포트 탐색 (5030+)"""
    existing_specs = list(SPECS_DIR.glob("*.yaml")) if SPECS_DIR.exists() else []
    used_ports = set()
    for spec in existing_specs:
        content = spec.read_text(encoding="utf-8")
        for match in re.finditer(r"gateway:\s*(\d+)", content):
            used_ports.add(int(match.group(1)))
        for match in re.finditer(r"port:\s*(\d+)", content):
            used_ports.add(int(match.group(1)))
    port = DEFAULT_PORT_START
    while port in used_ports:
        port += 1
    return port


# =====================
# 파일 생성
# =====================

def create_customer_api(
    customer_id: str,
    customer_name: str,
    drawing_type: str,
    port: int,
    overwrite: bool = False,
) -> bool:
    """고객별 파싱 파이프라인 파일 생성"""

    dtype_config = DRAWING_TYPE_CONFIG[drawing_type]
    pascal_id = to_pascal_case(customer_id)
    created_at = datetime.now().strftime("%Y-%m-%d")
    tags_yaml = format_tags_yaml(dtype_config["tags"])
    model_pipeline = get_model_pipeline(drawing_type)

    template_vars = dict(
        customer_id=customer_id,
        customer_name=customer_name,
        drawing_type=drawing_type,
        drawing_type_desc=dtype_config["description"],
        pascal_id=pascal_id,
        created_at=created_at,
        tags_yaml=tags_yaml,
        model_pipeline=model_pipeline,
        port=port,
    )

    files_to_create = [
        (SERVICES_DIR / f"{customer_id}_parser.py", PARSER_TEMPLATE),
        (ROUTERS_DIR / f"{customer_id}_router.py", ROUTER_TEMPLATE),
        (SPECS_DIR / f"{customer_id}.yaml", SPEC_TEMPLATE),
        (SERVICES_DIR / f"{customer_id}_config.py", CONFIG_TEMPLATE),
    ]

    print(f"\n{'='*60}")
    print(f"고객 API 생성: {customer_name} ({customer_id})")
    print(f"{'='*60}")
    print(f"  도면 유형  : {drawing_type} — {dtype_config['description']}")
    print(f"  포트       : {port} (Gateway: 8000)")
    print(f"  Pascal ID  : {pascal_id}Parser")
    print(f"{'='*60}\n")

    created_any = False
    for target_path, template in files_to_create:
        if target_path.exists() and not overwrite:
            print(f"[SKIP] 이미 존재: {target_path}")
            continue
        content = template.format(**template_vars)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        print(f"[OK]   생성됨: {target_path}")
        created_any = True

    print(f"\n{'='*60}")
    print("생성 완료!" if created_any else "모든 파일이 이미 존재합니다 (--overwrite로 덮어쓰기)")
    print(f"{'='*60}")
    print("\n다음 단계:")
    print(f"  1. services/{customer_id}_parser.py — 패턴/로직 구현")
    print(f"  2. services/{customer_id}_config.py — 가격 체계 입력")
    print(f"  3. routers/{customer_id}_router.py — gateway-api/main.py에 router 등록")
    print(f"  4. python scripts/test_coverage.py --customer-id {customer_id} --drawings-dir <path>")
    print()

    return True


# =====================
# CLI
# =====================

def main():
    parser = argparse.ArgumentParser(
        description="고객별 도면 파싱 파이프라인을 표준 구조로 생성합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python scripts/create_customer_api.py --customer-id panasia --customer-name 파나시아 --drawing-type pid
  python scripts/create_customer_api.py --customer-id hanjin --customer-name 한진중공업 --drawing-type mechanical --port 5032
  python scripts/create_customer_api.py --customer-id posco --customer-name POSCO --drawing-type mixed --overwrite
        """,
    )

    parser.add_argument(
        "--customer-id",
        required=True,
        help="고객 ID (소문자 + 언더스코어, 예: panasia, hanjin)",
    )
    parser.add_argument(
        "--customer-name",
        required=True,
        help="고객 이름 (표시용, 예: 파나시아, 한진중공업)",
    )
    parser.add_argument(
        "--drawing-type",
        choices=list(DRAWING_TYPE_CONFIG.keys()),
        default="mechanical",
        help="도면 유형 (pid/mechanical/mixed, 기본: mechanical)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="포트 번호 (기본: 5030부터 자동 할당)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="기존 파일 덮어쓰기",
    )

    args = parser.parse_args()

    if not validate_customer_id(args.customer_id):
        print(
            f"오류: customer-id는 소문자로 시작하고 소문자/숫자/언더스코어만 가능합니다: "
            f"{args.customer_id!r}"
        )
        sys.exit(1)

    port = args.port if args.port is not None else find_next_port()
    if port < 1000 or port > 65535:
        print(f"오류: 포트는 1000-65535 범위여야 합니다: {port}")
        sys.exit(1)

    success = create_customer_api(
        customer_id=args.customer_id,
        customer_name=args.customer_name,
        drawing_type=args.drawing_type,
        port=port,
        overwrite=args.overwrite,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
