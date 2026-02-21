"""
Agent Verification Pipeline - Phase 3

3-Level Hybrid 검증 파이프라인:
  L1: Auto-approve (confidence >= threshold)
  L2: LLM Vision (Claude Sonnet으로 크롭/컨텍스트 이미지 분석)
  L3: Playwright visual (미래 - 스텁)

Usage:
  python scripts/agent_verify.py \\
    --session-id <SID> \\
    --item-type symbol \\
    --threshold 0.9 \\
    --dry-run
"""

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import httpx

from agent_verify_prompts import (
    SYSTEM_PROMPT_SYMBOL,
    SYSTEM_PROMPT_DIMENSION,
    build_symbol_prompt,
    build_dimension_prompt,
)

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_THRESHOLD = 0.9
DEFAULT_API_BASE = "http://localhost:5020"
MAX_RETRIES = 3
BACKOFF_BASE = 1.0  # seconds

logger = logging.getLogger("agent_verify")


# ──────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────

@dataclass
class VerifyResult:
    item_id: str
    action: str  # approve / reject / modify / auto_approved / uncertain
    confidence: float
    reason: str
    level: str  # L1 / L2
    modified_class: Optional[str] = None
    modified_value: Optional[str] = None
    modified_unit: Optional[str] = None
    modified_type: Optional[str] = None
    modified_tolerance: Optional[str] = None
    reject_reason: Optional[str] = None


@dataclass
class VerifyStats:
    total: int = 0
    auto_approved: int = 0  # L1
    llm_approved: int = 0  # L2
    llm_rejected: int = 0
    llm_modified: int = 0
    uncertain: int = 0
    errors: int = 0
    results: list = field(default_factory=list)


# ──────────────────────────────────────────────
# AgentVerifier
# ──────────────────────────────────────────────

class AgentVerifier:
    def __init__(
        self,
        api_base: str,
        anthropic_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        threshold: float = DEFAULT_THRESHOLD,
        dry_run: bool = False,
        l1_only: bool = False,
    ):
        self.api_base = api_base.rstrip("/")
        self.anthropic_key = anthropic_key
        self.model = model
        self.threshold = threshold
        self.dry_run = dry_run
        self.l1_only = l1_only

    # ── Main entry ──────────────────────────

    async def run(self, session_id: str, item_type: str, max_items: int = 0) -> VerifyStats:
        stats = VerifyStats()

        # 1. Fetch queue
        queue = await self._fetch_queue(session_id, item_type)
        if not queue:
            logger.info("큐가 비어 있습니다.")
            return stats

        items = queue["queue"]
        if max_items > 0:
            items = items[:max_items]
        stats.total = len(items)

        logger.info(f"총 {stats.total}개 항목 처리 시작 (threshold={self.threshold}, dry_run={self.dry_run})")

        # 2. L1: Auto-approve high confidence
        auto_ids = await self._auto_approve_high_confidence(items, session_id, item_type, stats)

        # 3. L2: LLM verification for remaining
        remaining = [item for item in items if item["id"] not in auto_ids]
        if self.l1_only:
            logger.info(f"L1-only 모드: {len(remaining)}개 항목 건너뜀 (LLM 미사용)")
        else:
            for i, item in enumerate(remaining):
                result = await self._verify_with_llm(session_id, item, item_type)
                self._update_stats(stats, result)
                self._print_progress(i + 1, len(remaining), result)

            if not self.dry_run and result.action != "uncertain":
                success = await self._submit_decision(session_id, result, item_type)
                if not success:
                    stats.errors += 1

        # 4. Summary
        self._print_summary(stats)

        # 5. dry-run: save results to JSON
        if self.dry_run:
            self._save_dry_run_results(session_id, item_type, stats)

        return stats

    # ── L1: Auto-approve ────────────────────

    async def _auto_approve_high_confidence(
        self,
        items: list[dict],
        session_id: str,
        item_type: str,
        stats: VerifyStats,
    ) -> set[str]:
        auto_items = [item for item in items if item.get("confidence", 0) >= self.threshold]
        auto_ids = set()

        if not auto_items:
            return auto_ids

        logger.info(f"L1 Auto-approve: {len(auto_items)}개 (confidence >= {self.threshold})")

        for item in auto_items:
            result = VerifyResult(
                item_id=item["id"],
                action="approve",
                confidence=item["confidence"],
                reason=f"auto-approve: confidence {item['confidence']:.2f} >= {self.threshold}",
                level="L1",
            )
            stats.auto_approved += 1
            stats.results.append(asdict(result))
            auto_ids.add(item["id"])

            if not self.dry_run:
                success = await self._submit_decision(session_id, result, item_type)
                if not success:
                    stats.errors += 1

        logger.info(f"L1 완료: {len(auto_ids)}개 자동 승인")
        return auto_ids

    # ── L2: LLM Vision ─────────────────────

    async def _verify_with_llm(
        self,
        session_id: str,
        item: dict,
        item_type: str,
    ) -> VerifyResult:
        item_id = item["id"]

        try:
            # Fetch full item detail with images
            detail = await self._fetch_item_detail(session_id, item_id, item_type)
            if not detail:
                return VerifyResult(
                    item_id=item_id, action="uncertain", confidence=0.0,
                    reason="항목 상세 조회 실패", level="L2",
                )

            # Build messages
            messages = self._build_llm_messages(detail, item_type)

            # Call Anthropic
            llm_response = await self._call_anthropic(messages, item_type)
            if not llm_response:
                return VerifyResult(
                    item_id=item_id, action="uncertain", confidence=0.0,
                    reason="LLM 응답 실패", level="L2",
                )

            # Parse response
            parsed = self._parse_llm_response(llm_response)
            if not parsed:
                return VerifyResult(
                    item_id=item_id, action="uncertain", confidence=0.0,
                    reason=f"LLM 응답 파싱 실패: {llm_response[:100]}", level="L2",
                )

            return VerifyResult(
                item_id=item_id,
                action=parsed.get("action", "uncertain"),
                confidence=parsed.get("confidence", 0.0),
                reason=parsed.get("reason", ""),
                level="L2",
                modified_class=parsed.get("modified_class"),
                modified_value=parsed.get("modified_value"),
                modified_unit=parsed.get("modified_unit"),
                modified_type=parsed.get("modified_type"),
                modified_tolerance=parsed.get("modified_tolerance"),
            )

        except Exception as e:
            logger.error(f"LLM 검증 실패 [{item_id}]: {e}")
            return VerifyResult(
                item_id=item_id, action="uncertain", confidence=0.0,
                reason=f"예외: {e}", level="L2",
            )

    def _build_llm_messages(self, detail: dict, item_type: str) -> list[dict]:
        """Anthropic messages 형식으로 이미지 + 텍스트 프롬프트를 구성한다."""
        content = []

        # Crop image (always present)
        if detail.get("crop_image"):
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": detail["crop_image"],
                },
            })

        # Context image (always present)
        if detail.get("context_image"):
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": detail["context_image"],
                },
            })

        # Reference images (symbol only, up to 3)
        for ref_img in detail.get("reference_images", []):
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": ref_img,
                },
            })

        # Text prompt
        if item_type == "symbol":
            text = build_symbol_prompt(
                class_name=detail.get("class_name", "unknown"),
                confidence=detail.get("confidence", 0.0),
                reference_count=len(detail.get("reference_images", [])),
                drawing_type=detail.get("metadata", {}).get("drawing_type", "unknown"),
            )
        else:
            text = build_dimension_prompt(
                value=detail.get("value", ""),
                unit=detail.get("unit", "mm"),
                dimension_type=detail.get("dimension_type", "length"),
                tolerance=detail.get("tolerance"),
                confidence=detail.get("confidence", 0.0),
            )

        content.append({"type": "text", "text": text})

        return [{"role": "user", "content": content}]

    async def _call_anthropic(self, messages: list[dict], item_type: str) -> Optional[str]:
        """Anthropic API를 호출하고 텍스트 응답을 반환한다."""
        system_prompt = SYSTEM_PROMPT_SYMBOL if item_type == "symbol" else SYSTEM_PROMPT_DIMENSION

        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        ANTHROPIC_API_URL,
                        headers={
                            "x-api-key": self.anthropic_key,
                            "Content-Type": "application/json",
                            "anthropic-version": "2023-06-01",
                        },
                        json={
                            "model": self.model,
                            "max_tokens": 1000,
                            "system": system_prompt,
                            "messages": messages,
                        },
                    )

                if response.status_code == 429:
                    wait = BACKOFF_BASE * (2 ** attempt)
                    logger.warning(f"Rate limited, retrying in {wait}s...")
                    await asyncio.sleep(wait)
                    continue

                if response.status_code != 200:
                    logger.error(f"Anthropic API error: {response.status_code} {response.text[:200]}")
                    return None

                data = response.json()
                return data["content"][0]["text"]

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt < MAX_RETRIES - 1:
                    wait = BACKOFF_BASE * (2 ** attempt)
                    logger.warning(f"Network error: {e}, retrying in {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"Anthropic API 네트워크 오류: {e}")
                    return None

        return None

    # ── API Calls ───────────────────────────

    async def _fetch_queue(self, session_id: str, item_type: str) -> Optional[dict]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.api_base}/verification/agent/queue/{session_id}",
                    params={"item_type": item_type},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.error(f"큐 조회 실패: {e}")
            return None

    async def _fetch_item_detail(self, session_id: str, item_id: str, item_type: str) -> Optional[dict]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.api_base}/verification/agent/item/{session_id}/{item_id}",
                    params={"item_type": item_type},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.error(f"항목 상세 조회 실패 [{item_id}]: {e}")
            return None

    async def _submit_decision(
        self,
        session_id: str,
        result: VerifyResult,
        item_type: str,
    ) -> bool:
        """검증 결과를 서버에 전송한다."""
        body: dict = {"action": result.action}

        if result.action == "modify":
            if result.modified_class:
                body["modified_class"] = result.modified_class
            if result.modified_value:
                body["modified_value"] = result.modified_value
            if result.modified_unit:
                body["modified_unit"] = result.modified_unit
            if result.modified_type:
                body["modified_type"] = result.modified_type
            if result.modified_tolerance:
                body["modified_tolerance"] = result.modified_tolerance

        if result.action == "reject" and result.reject_reason:
            body["reject_reason"] = result.reject_reason

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.api_base}/verification/agent/decide/{session_id}/{result.item_id}",
                    params={"item_type": item_type},
                    json=body,
                )
                resp.raise_for_status()
                return resp.json().get("success", False)
        except Exception as e:
            logger.error(f"결정 전송 실패 [{result.item_id}]: {e}")
            return False

    # ── Response Parsing ────────────────────

    def _parse_llm_response(self, text: str) -> Optional[dict]:
        """LLM 텍스트 응답에서 JSON 객체를 추출한다."""
        # 1. 전체 텍스트가 JSON인 경우
        text = text.strip()
        try:
            parsed = json.loads(text)
            if self._validate_response(parsed):
                return parsed
        except json.JSONDecodeError:
            pass

        # 2. ```json ... ``` 블록 추출
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(1))
                if self._validate_response(parsed):
                    return parsed
            except json.JSONDecodeError:
                pass

        # 3. 첫 번째 { ... } 블록 추출
        match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
                if self._validate_response(parsed):
                    return parsed
            except json.JSONDecodeError:
                pass

        return None

    def _validate_response(self, parsed: dict) -> bool:
        return parsed.get("action") in ("approve", "reject", "modify")

    # ── Stats / Output ──────────────────────

    def _update_stats(self, stats: VerifyStats, result: VerifyResult):
        stats.results.append(asdict(result))
        if result.action == "approve":
            stats.llm_approved += 1
        elif result.action == "reject":
            stats.llm_rejected += 1
        elif result.action == "modify":
            stats.llm_modified += 1
        else:
            stats.uncertain += 1

    def _print_progress(self, current: int, total: int, result: VerifyResult):
        icons = {
            "approve": "\u2705", "reject": "\u274c", "modify": "\u270f\ufe0f",
            "uncertain": "\u2753", "auto_approved": "\u26a1",
        }
        icon = icons.get(result.action, "?")
        logger.info(
            f"  [{current}/{total}] {icon} {result.item_id[:8]}.. "
            f"→ {result.action} (conf={result.confidence:.2f}) {result.reason}"
        )

    def _print_summary(self, stats: VerifyStats):
        print("\n" + "=" * 60)
        print("Agent Verification Summary")
        print("=" * 60)
        print(f"  Total items:      {stats.total}")
        print(f"  L1 Auto-approved: {stats.auto_approved}")
        print(f"  L2 LLM approved:  {stats.llm_approved}")
        print(f"  L2 LLM rejected:  {stats.llm_rejected}")
        print(f"  L2 LLM modified:  {stats.llm_modified}")
        print(f"  Uncertain:        {stats.uncertain}")
        print(f"  Errors:           {stats.errors}")
        if self.dry_run:
            print("  Mode:             DRY RUN (no decisions submitted)")
        print("=" * 60)

    def _save_dry_run_results(self, session_id: str, item_type: str, stats: VerifyStats):
        out_dir = Path("./dry_run_results")
        out_dir.mkdir(exist_ok=True)
        ts = int(time.time())
        filename = out_dir / f"verify_{session_id}_{item_type}_{ts}.json"

        data = {
            "session_id": session_id,
            "item_type": item_type,
            "model": self.model,
            "threshold": self.threshold,
            "total": stats.total,
            "auto_approved": stats.auto_approved,
            "llm_approved": stats.llm_approved,
            "llm_rejected": stats.llm_rejected,
            "llm_modified": stats.llm_modified,
            "uncertain": stats.uncertain,
            "results": stats.results,
        }
        filename.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        logger.info(f"Dry-run 결과 저장: {filename}")


# ──────────────────────────────────────────────
# API Key Resolution
# ──────────────────────────────────────────────

async def _resolve_api_key(api_key: Optional[str], api_base: str) -> Optional[str]:
    """API 키를 CLI 인자 → 환경변수 → BOM API 순으로 해결한다."""
    if api_key:
        return api_key

    env_key = os.environ.get("ANTHROPIC_API_KEY")
    if env_key:
        return env_key

    # Try Blueprint AI BOM settings
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{api_base}/api/v1/settings/api-keys/anthropic")
            if resp.status_code == 200:
                data = resp.json()
                key = data.get("api_key") or data.get("key")
                if key:
                    logger.info("BOM API에서 Anthropic API 키 획득")
                    return key
    except Exception:
        pass

    return None


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Agent Verification Pipeline - 검출/OCR 결과를 LLM Agent로 자동 검증",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Dry-run (서버 연결 확인, 결정 전송 안 함)
  python scripts/agent_verify.py --session-id abc123 --item-type symbol --dry-run

  # 실제 검증 실행
  python scripts/agent_verify.py --session-id abc123 --item-type dimension --threshold 0.9

  # 최대 20개만 처리
  python scripts/agent_verify.py --session-id abc123 --item-type symbol --max-items 20
""",
    )
    parser.add_argument("--session-id", required=True, help="검증 대상 세션 ID")
    parser.add_argument(
        "--item-type", required=True, choices=["symbol", "dimension"],
        help="검증 항목 타입",
    )
    parser.add_argument("--dry-run", action="store_true", help="LLM 호출만 하고 결정 전송 생략")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD, help=f"L1 auto-approve 임계값 (기본: {DEFAULT_THRESHOLD})")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Anthropic 모델 (기본: {DEFAULT_MODEL})")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help=f"Blueprint AI BOM API URL (기본: {DEFAULT_API_BASE})")
    parser.add_argument("--api-key", default=None, help="Anthropic API 키 (미지정 시 환경변수/BOM API 사용)")
    parser.add_argument("--max-items", type=int, default=0, help="처리할 최대 항목 수 (0=무제한)")
    parser.add_argument("--l1-only", action="store_true", help="L1 auto-approve만 실행 (LLM 호출 없음, API 키 불필요)")
    parser.add_argument("--verbose", "-v", action="store_true", help="상세 로그 출력")
    return parser.parse_args()


async def main():
    args = parse_args()

    # Logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # Resolve API key
    api_key = await _resolve_api_key(args.api_key, args.api_base)
    if not api_key and not args.l1_only:
        logger.error(
            "Anthropic API 키를 찾을 수 없습니다.\n"
            "  --api-key 인자, ANTHROPIC_API_KEY 환경변수, 또는 BOM API 설정을 확인하세요.\n"
            "  L1 auto-approve만 실행하려면 --l1-only 플래그를 사용하세요."
        )
        sys.exit(1)

    # Run
    verifier = AgentVerifier(
        api_base=args.api_base,
        anthropic_key=api_key,
        model=args.model,
        threshold=args.threshold,
        dry_run=args.dry_run,
        l1_only=args.l1_only,
    )

    stats = await verifier.run(
        session_id=args.session_id,
        item_type=args.item_type,
        max_items=args.max_items,
    )

    # Exit code
    if stats.errors > 0 and stats.errors == stats.total:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
