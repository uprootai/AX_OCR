#!/usr/bin/env python3
"""Customer Onboarding CLI - 신규 고객 프로젝트 자동 셋업

8개 API를 순차 호출하여 프로젝트 생성 → BOM 임포트 → 분석 → 검증 → 견적 내보내기까지
자동 수행하는 CLI 도구.

Usage:
    # 프리셋 목록 확인
    python scripts/onboard.py --list-presets

    # Dry-run (API 호출 없이 계획만 출력)
    python scripts/onboard.py --name "Test" --customer "Test" --type general --dry-run

    # YAML 설정 파일 기반
    python scripts/onboard.py --config project.yaml

    # 직접 인자 (BOM 견적)
    python scripts/onboard.py \\
        --preset techcross_bwms \\
        --name "TECHCROSS BWMS 2026-Q1" \\
        --bom-pdf /data/bom.pdf \\
        --drawing-folder /data/drawings/

    # 실패 지점부터 재개
    python scripts/onboard.py --resume-project <project-id> --resume-from 5

    # 인터랙티브 모드
    python scripts/onboard.py --interactive
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path

from onboard_config import (
    OnboardConfig,
    CUSTOMER_PRESETS,
    config_from_args,
    list_presets,
    load_config,
    validate_config,
)
from onboard_steps import OnboardingPipeline, PipelineState, PHASE_NAMES

logger = logging.getLogger("onboard")

DEFAULT_API_BASE = "http://localhost:5020"


# ──────────────────────────────────────────────
# CLI Argument Parser
# ──────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="onboard",
        description="Customer Onboarding CLI - 신규 고객 프로젝트 자동 셋업",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python scripts/onboard.py --list-presets
  python scripts/onboard.py --name "Test" --customer "Test" --type general --dry-run
  python scripts/onboard.py --config project.yaml
  python scripts/onboard.py --preset techcross_bwms --name "Q1 견적" --bom-pdf bom.pdf
  python scripts/onboard.py --resume-project <id> --resume-from 5
  python scripts/onboard.py --interactive
""",
    )

    # Mode selection
    mode = parser.add_argument_group("Mode")
    mode.add_argument("--interactive", "-i", action="store_true", help="인터랙티브 모드 (단계별 프롬프트)")
    mode.add_argument("--config", "-c", type=str, help="YAML/JSON 설정 파일 경로")
    mode.add_argument("--list-presets", action="store_true", help="사용 가능한 프리셋 목록 출력")

    # Project info
    proj = parser.add_argument_group("Project")
    proj.add_argument("--name", type=str, help="프로젝트 이름")
    proj.add_argument("--customer", type=str, help="고객사명")
    proj.add_argument("--type", type=str, choices=["bom_quotation", "pid_detection", "general"], help="프로젝트 타입")
    proj.add_argument("--description", type=str, help="프로젝트 설명")
    proj.add_argument("--preset", type=str, help=f"고객 프리셋 ({', '.join(CUSTOMER_PRESETS.keys())})")

    # BOM paths
    bom = parser.add_argument_group("BOM (bom_quotation only)")
    bom.add_argument("--bom-pdf", type=str, help="BOM PDF 파일 경로")
    bom.add_argument("--drawing-folder", type=str, help="도면 폴더 경로")

    # Analysis
    analysis = parser.add_argument_group("Analysis")
    analysis.add_argument("--features", nargs="+", help="활성화할 기능 목록")
    analysis.add_argument("--template", type=str, help="템플릿 이름")
    analysis.add_argument("--root-drawing", type=str, help="분석 대상 루트 어셈블리 도면번호")
    analysis.add_argument("--force-rerun", action="store_true", help="이미 분석된 세션도 재실행")

    # Verification
    verify = parser.add_argument_group("Verification")
    verify.add_argument("--verify", action="store_true", help="Agent 검증 활성화")
    verify.add_argument("--verify-item-type", choices=["symbol", "dimension", "both"], default="both", help="검증 항목 타입")
    verify.add_argument("--verify-threshold", type=float, default=0.9, help="L1 auto-approve 임계값")
    verify.add_argument("--verify-l1-only", action="store_true", help="L1만 실행 (LLM 미사용)")

    # Export
    export = parser.add_argument_group("Export")
    export.add_argument("--export-format", choices=["pdf", "excel"], default="pdf", help="내보내기 형식")
    export.add_argument("--export-notes", type=str, help="견적서 비고")

    # Control
    ctrl = parser.add_argument_group("Control")
    ctrl.add_argument("--dry-run", action="store_true", help="API 호출 없이 계획만 출력")
    ctrl.add_argument("--resume-project", type=str, help="재개할 프로젝트 ID")
    ctrl.add_argument("--resume-from", type=int, default=0, help="재개 시작 단계 (1-8)")
    ctrl.add_argument("--api-base", type=str, default=DEFAULT_API_BASE, help=f"API 기본 URL (기본: {DEFAULT_API_BASE})")
    ctrl.add_argument("--verbose", "-v", action="store_true", help="상세 로그 출력")

    return parser


# ──────────────────────────────────────────────
# Interactive Mode
# ──────────────────────────────────────────────

def run_interactive() -> OnboardConfig:
    """Prompt user step by step and build config."""
    print("\n" + "=" * 60)
    print("  Customer Onboarding - Interactive Mode")
    print("=" * 60)

    config = OnboardConfig()

    # Preset selection
    print("\n사용 가능한 프리셋:")
    preset_names = list(CUSTOMER_PRESETS.keys())
    for i, name in enumerate(preset_names, 1):
        p = CUSTOMER_PRESETS[name]
        print(f"  {i}. {name} ({p['project_type']}) - {p.get('description', '')}")
    print(f"  {len(preset_names) + 1}. 커스텀 (직접 입력)")

    choice = input(f"\n프리셋 선택 [1-{len(preset_names) + 1}]: ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(preset_names):
            from onboard_config import _apply_preset
            _apply_preset(config, preset_names[idx])
            print(f"  → 프리셋 '{preset_names[idx]}' 적용됨")
    except (ValueError, IndexError):
        pass

    # Project info
    config.name = input(f"\n프로젝트 이름 [{config.name}]: ").strip() or config.name
    config.customer = input(f"고객사명 [{config.customer}]: ").strip() or config.customer

    if not config.project_type or config.project_type == "general":
        ptype = input("프로젝트 타입 (bom_quotation/pid_detection/general) [general]: ").strip()
        config.project_type = ptype or "general"

    config.description = input(f"설명 [{config.description}]: ").strip() or config.description

    # BOM paths (bom_quotation only)
    if config.project_type == "bom_quotation":
        config.bom_pdf_path = input("\nBOM PDF 경로 (없으면 Enter): ").strip()
        config.drawing_folder = input("도면 폴더 경로 (없으면 Enter): ").strip()

    # Verification
    verify_input = input(f"\nAgent 검증 활성화? (y/n) [{'y' if config.verify else 'n'}]: ").strip().lower()
    if verify_input == "y":
        config.verify = True
    elif verify_input == "n":
        config.verify = False

    # Export format
    fmt = input(f"내보내기 형식 (pdf/excel) [{config.export_format}]: ").strip()
    if fmt in ("pdf", "excel"):
        config.export_format = fmt

    # Dry-run
    dry = input("\nDry-run 모드? (y/n) [n]: ").strip().lower()
    config.dry_run = dry == "y"

    return config


# ──────────────────────────────────────────────
# Display Helpers
# ──────────────────────────────────────────────

def print_plan(config: OnboardConfig):
    """Print execution plan before running."""
    print("\n" + "=" * 60)
    print("  Onboarding Execution Plan")
    print("=" * 60)

    print(f"\n  Project:    {config.name}")
    print(f"  Customer:   {config.customer}")
    print(f"  Type:       {config.project_type}")
    if config.preset:
        print(f"  Preset:     {config.preset}")
    if config.description:
        print(f"  Description:{config.description}")
    if config.features:
        print(f"  Features:   {', '.join(config.features)}")

    print(f"\n  {'Phase':<8} {'Step':<25} {'Action'}")
    print(f"  {'─'*8} {'─'*25} {'─'*30}")

    is_bom = config.project_type == "bom_quotation"
    resume_id = config.resume_project_id

    steps = [
        (1, "Create Project", "SKIP (resume)" if resume_id else "POST /projects"),
        (2, "Import BOM", f"Upload {Path(config.bom_pdf_path).name}" if config.bom_pdf_path else ("SKIP" if not is_bom else "SKIP (no file)")),
        (3, "Match Drawings", f"Folder: {config.drawing_folder}" if config.drawing_folder else ("SKIP" if not is_bom else "SKIP (no folder)")),
        (4, "Create Sessions", "POST /projects/{id}/create-sessions"),
        (5, "Start Batch", "POST /analysis/batch/{id}"),
        (6, "Poll Status", f"GET /analysis/batch/{{id}}/status (timeout: 30min)"),
        (7, "Verify", f"agent_verify.py ({config.verify_item_type})" if config.verify else "SKIP (disabled)"),
        (8, "Export", f"POST /quotation/export ({config.export_format})"),
    ]

    start = config.resume_from_step or 1
    for phase, name, action in steps:
        marker = "  " if phase >= start else ">>"
        if phase < start:
            action = "SKIP (resume)"
        print(f"  {marker} {phase:<6} {name:<25} {action}")

    if config.dry_run:
        print(f"\n  Mode: DRY RUN (API 호출 없음)")
    print("\n" + "=" * 60)


def print_results(state: PipelineState):
    """Print final pipeline results."""
    elapsed = state.finished_at - state.started_at if state.finished_at else 0

    print("\n" + "=" * 60)
    print("  Onboarding Results")
    print("=" * 60)
    print(f"  Project ID: {state.project_id}")
    print(f"  Elapsed:    {elapsed:.1f}s")
    print()

    for r in state.results:
        icon = "SKIP" if r.get("skipped") else ("OK" if r["success"] else "FAIL")
        phase = r["phase"]
        name = r["name"]
        sec = r.get("elapsed", 0)
        print(f"  Phase {phase}: {name:<25} [{icon}] ({sec:.1f}s)")
        if r.get("error"):
            print(f"           Error: {r['error']}")
        # Show key data
        data = r.get("data", {})
        for key in ("project_id", "total_items", "part_count", "matched", "created", "completed", "download_url"):
            if key in data and data[key]:
                print(f"           {key}: {data[key]}")

    # Overall status
    failed = [r for r in state.results if not r["success"] and not r.get("skipped")]
    if failed:
        last_fail = failed[-1]
        print(f"\n  Status: FAILED at Phase {last_fail['phase']}")
        print(f"  Resume: python scripts/onboard.py --resume-project {state.project_id} --resume-from {last_fail['phase']}")
    else:
        print(f"\n  Status: SUCCESS")

    print("=" * 60)


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

async def async_main():
    parser = build_parser()
    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # Mode: list presets
    if args.list_presets:
        print(list_presets())
        return

    # Mode: interactive
    if args.interactive:
        config = run_interactive()
    # Mode: config file
    elif args.config:
        config = load_config(args.config)
        # CLI overrides
        if args.dry_run:
            config.dry_run = True
        if args.verbose:
            config.verbose = True
        if args.api_base != DEFAULT_API_BASE:
            config.api_base = args.api_base
    # Mode: direct args
    else:
        config = config_from_args(args)

    # Validate
    errors = validate_config(config)
    if errors:
        print("\nValidation Errors:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    # Print plan
    print_plan(config)

    # Dry-run confirmation
    if not config.dry_run:
        try:
            answer = input("\n실행하시겠습니까? (y/n) [y]: ").strip().lower()
            if answer == "n":
                print("취소되었습니다.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\n취소되었습니다.")
            return

    # Load existing state if resuming
    state = None
    if config.resume_project_id:
        state = OnboardingPipeline.load_state(config.resume_project_id)
        if state:
            logger.info(f"기존 상태 로드: phase {state.current_phase}, project {state.project_id}")

    # Run pipeline
    pipeline = OnboardingPipeline(
        api_base=config.api_base,
        dry_run=config.dry_run,
        verbose=config.verbose,
    )

    state = await pipeline.run(config, state)

    # Print results
    print_results(state)

    # Exit code
    failed = [r for r in state.results if not r["success"] and not r.get("skipped")]
    if failed:
        sys.exit(1)


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
