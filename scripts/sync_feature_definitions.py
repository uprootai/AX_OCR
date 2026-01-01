#!/usr/bin/env python3
"""
Feature Definition 동기화 스크립트

web-ui/src/config/features/featureDefinitions.ts (SSOT)를
blueprint-ai-bom/frontend/src/config/features/featureDefinitions.ts로 동기화합니다.

Usage:
    python scripts/sync_feature_definitions.py [--check] [--verbose]

Options:
    --check     동기화 상태만 확인 (파일 수정 안함)
    --verbose   상세 출력
"""

import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent

# SSOT (Single Source of Truth) 파일 경로
SSOT_FILE = PROJECT_ROOT / "web-ui/src/config/features/featureDefinitions.ts"

# 동기화 대상 파일들
SYNC_TARGETS = [
    PROJECT_ROOT / "blueprint-ai-bom/frontend/src/config/features/featureDefinitions.ts",
]

# 동기화 주석 패턴
SYNC_COMMENT_PATTERN = r"(\* 마지막 동기화:.*)"
SYNC_COMMENT_TEMPLATE = "* 마지막 동기화: {date} (web-ui에서 복사)"


def get_file_hash(file_path: Path) -> str:
    """파일 내용의 해시값 반환 (헤더 주석 제외, 코드만 비교)"""
    if not file_path.exists():
        return ""

    content = file_path.read_text(encoding="utf-8")

    # 헤더 주석 블록(/** ... */) 이후의 코드만 비교
    # 첫 번째 export 또는 코드 시작 부분부터 비교
    code_start = content.find("// ============================================================")
    if code_start == -1:
        code_start = content.find("export ")

    if code_start > 0:
        content = content[code_start:]

    # 공백 정규화
    content = "\n".join(line.strip() for line in content.split("\n"))
    return content.strip()


def files_are_in_sync(source: Path, target: Path) -> bool:
    """두 파일이 동기화되어 있는지 확인"""
    source_hash = get_file_hash(source)
    target_hash = get_file_hash(target)
    return source_hash == target_hash


def sync_file(source: Path, target: Path, verbose: bool = False) -> bool:
    """
    source 파일을 target으로 동기화

    Returns:
        True if sync was performed, False if already in sync
    """
    if not source.exists():
        print(f"  [ERROR] SSOT 파일이 없습니다: {source}")
        return False

    # 타겟 디렉토리 확인
    target.parent.mkdir(parents=True, exist_ok=True)

    # 이미 동기화되어 있는지 확인
    if files_are_in_sync(source, target):
        if verbose:
            print(f"  [OK] 이미 동기화됨: {target.name}")
        return False

    # 파일 복사
    shutil.copy2(source, target)

    # 동기화 주석 업데이트
    content = target.read_text(encoding="utf-8")

    # SSOT 참조 주석 변경
    content = content.replace(
        "* - blueprint-ai-bom/frontend/src/config/features/featureDefinitions.ts",
        "* - web-ui/src/config/features/featureDefinitions.ts (SSOT)"
    )

    # 마지막 동기화 날짜 추가/업데이트
    today = datetime.now().strftime("%Y-%m-%d")
    new_sync_comment = SYNC_COMMENT_TEMPLATE.format(date=today)

    if re.search(SYNC_COMMENT_PATTERN, content):
        content = re.sub(SYNC_COMMENT_PATTERN, new_sync_comment, content)
    else:
        # 동기화 주석이 없으면 추가
        content = content.replace(
            "*   (별도 프로젝트이므로 수동 동기화 필요, 동일 내용 유지)",
            f"*   (별도 프로젝트이므로 수동 동기화 필요, 동일 내용 유지)\n *\n {new_sync_comment}"
        )

    target.write_text(content, encoding="utf-8")

    if verbose:
        print(f"  [SYNCED] {target.name}")

    return True


def check_sync_status(verbose: bool = False) -> bool:
    """
    모든 파일의 동기화 상태 확인

    Returns:
        True if all files are in sync
    """
    if not SSOT_FILE.exists():
        print(f"[ERROR] SSOT 파일이 없습니다: {SSOT_FILE}")
        return False

    all_synced = True

    print(f"\n{'='*60}")
    print(f"Feature Definition 동기화 상태 확인")
    print(f"{'='*60}")
    print(f"\nSSOT: {SSOT_FILE.relative_to(PROJECT_ROOT)}")
    print(f"\n동기화 대상:")

    for target in SYNC_TARGETS:
        relative_target = target.relative_to(PROJECT_ROOT)

        if not target.exists():
            print(f"  [MISSING] {relative_target}")
            all_synced = False
        elif files_are_in_sync(SSOT_FILE, target):
            print(f"  [OK] {relative_target}")
        else:
            print(f"  [OUT OF SYNC] {relative_target}")
            all_synced = False

    print()

    if all_synced:
        print("[SUCCESS] 모든 파일이 동기화되어 있습니다.")
    else:
        print("[WARNING] 동기화가 필요한 파일이 있습니다.")
        print("         다음 명령으로 동기화하세요:")
        print("         python scripts/sync_feature_definitions.py")

    print(f"{'='*60}\n")

    return all_synced


def main():
    parser = argparse.ArgumentParser(
        description="Feature Definition 파일을 동기화합니다."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="동기화 상태만 확인 (파일 수정 안함)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="상세 출력"
    )

    args = parser.parse_args()

    if args.check:
        is_synced = check_sync_status(verbose=args.verbose)
        exit(0 if is_synced else 1)

    # 동기화 실행
    print(f"\n{'='*60}")
    print(f"Feature Definition 동기화 실행")
    print(f"{'='*60}")
    print(f"\nSSOT: {SSOT_FILE.relative_to(PROJECT_ROOT)}")
    print(f"\n동기화 중...")

    synced_count = 0

    for target in SYNC_TARGETS:
        if sync_file(SSOT_FILE, target, verbose=args.verbose):
            synced_count += 1
            print(f"  [SYNCED] {target.relative_to(PROJECT_ROOT)}")
        else:
            print(f"  [SKIPPED] {target.relative_to(PROJECT_ROOT)} (이미 동기화됨)")

    print(f"\n{'='*60}")
    if synced_count > 0:
        print(f"[SUCCESS] {synced_count}개 파일 동기화 완료")
    else:
        print("[INFO] 모든 파일이 이미 동기화되어 있습니다.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
