"""Customer Onboarding - 8-Phase Pipeline Steps

Async HTTP-based pipeline that orchestrates the 8 onboarding phases:
  Phase 1: Create project
  Phase 2: Import BOM PDF (bom_quotation only)
  Phase 3: Match drawings (bom_quotation only)
  Phase 4: Create sessions from BOM
  Phase 5: Start batch analysis
  Phase 6: Poll batch status until complete
  Phase 7: Agent verification (optional, subprocess)
  Phase 8: Export quotation

Usage:
    from onboard_steps import OnboardingPipeline
    pipeline = OnboardingPipeline(api_base="http://localhost:5020")
    result = await pipeline.run(config)
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any

import httpx

from onboard_config import OnboardConfig

logger = logging.getLogger("onboard")

MAX_RETRIES = 3
BACKOFF_BASE = 2.0
POLL_INTERVAL = 5.0
POLL_TIMEOUT = 1800  # 30 minutes

PHASE_NAMES = {
    1: "Create Project",
    2: "Import BOM",
    3: "Match Drawings",
    4: "Create Sessions",
    5: "Start Batch Analysis",
    6: "Poll Batch Status",
    7: "Agent Verification",
    8: "Export Quotation",
}


# ──────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────

@dataclass
class StepResult:
    """Result of a single pipeline step."""
    phase: int
    name: str
    success: bool
    data: dict = field(default_factory=dict)
    error: str = ""
    elapsed: float = 0.0
    skipped: bool = False


@dataclass
class PipelineState:
    """Full pipeline state (serializable for resume)."""
    project_id: str = ""
    current_phase: int = 0
    results: list = field(default_factory=list)
    started_at: float = 0.0
    finished_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "current_phase": self.current_phase,
            "results": self.results,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PipelineState":
        state = cls()
        state.project_id = data.get("project_id", "")
        state.current_phase = data.get("current_phase", 0)
        state.results = data.get("results", [])
        state.started_at = data.get("started_at", 0.0)
        state.finished_at = data.get("finished_at", 0.0)
        return state


# ──────────────────────────────────────────────
# OnboardingPipeline
# ──────────────────────────────────────────────

class OnboardingPipeline:
    """8-phase onboarding pipeline using existing BOM APIs."""

    def __init__(
        self,
        api_base: str = "http://localhost:5020",
        dry_run: bool = False,
        verbose: bool = False,
    ):
        self.api_base = api_base.rstrip("/")
        self.dry_run = dry_run
        self.verbose = verbose

    # ── Main Entry ─────────────────────────────

    async def run(self, config: OnboardConfig, state: Optional[PipelineState] = None) -> PipelineState:
        """Execute the full 8-phase pipeline."""
        if state is None:
            state = PipelineState(started_at=time.time())

        start_phase = config.resume_from_step or 1
        project_id = config.resume_project_id or state.project_id

        phases = [
            (1, self.phase1_create_project),
            (2, self.phase2_import_bom),
            (3, self.phase3_match_drawings),
            (4, self.phase4_create_sessions),
            (5, self.phase5_start_batch),
            (6, self.phase6_poll_status),
            (7, self.phase7_verify),
            (8, self.phase8_export),
        ]

        for phase_num, phase_fn in phases:
            if phase_num < start_phase:
                continue

            state.current_phase = phase_num
            t0 = time.time()

            result = await phase_fn(config, project_id)
            result.elapsed = time.time() - t0

            state.results.append({
                "phase": result.phase,
                "name": result.name,
                "success": result.success,
                "skipped": result.skipped,
                "elapsed": round(result.elapsed, 1),
                "error": result.error,
                "data": result.data,
            })

            # Update project_id from phase 1
            if phase_num == 1 and result.success and not project_id:
                project_id = result.data.get("project_id", "")
                state.project_id = project_id

            # Save state after each phase
            if project_id:
                state.project_id = project_id
                self._save_state(state)

            if not result.success and not result.skipped:
                logger.error(f"Phase {phase_num} 실패: {result.error}")
                logger.info(f"재개 명령: --resume-project {project_id} --resume-from {phase_num}")
                break

        state.finished_at = time.time()
        if project_id:
            self._save_state(state)
        return state

    # ── Phase 1: Create Project ────────────────

    async def phase1_create_project(self, config: OnboardConfig, project_id: str) -> StepResult:
        """POST /projects → project_id"""
        if project_id:
            return StepResult(
                phase=1, name=PHASE_NAMES[1], success=True, skipped=True,
                data={"project_id": project_id, "message": "기존 프로젝트 사용"},
            )

        body = {
            "name": config.name,
            "customer": config.customer,
            "project_type": config.project_type,
        }
        if config.description:
            body["description"] = config.description
        if config.features:
            body["default_features"] = config.features

        resp = await self._request("POST", "/projects", json_body=body)
        if not resp:
            return StepResult(phase=1, name=PHASE_NAMES[1], success=False, error="프로젝트 생성 실패")

        # In dry-run mode, generate a placeholder ID
        if resp.get("dry_run"):
            pid = f"dry-run-{int(time.time())}"
        else:
            pid = resp.get("project_id", "")
        return StepResult(
            phase=1, name=PHASE_NAMES[1], success=bool(pid),
            data={"project_id": pid, "name": config.name},
            error="" if pid else "project_id 없음",
        )

    # ── Phase 2: Import BOM ────────────────────

    async def phase2_import_bom(self, config: OnboardConfig, project_id: str) -> StepResult:
        """POST /projects/{id}/import-bom (file upload)"""
        if config.project_type != "bom_quotation":
            return StepResult(
                phase=2, name=PHASE_NAMES[2], success=True, skipped=True,
                data={"message": f"BOM import 불필요 (타입: {config.project_type})"},
            )
        if not config.bom_pdf_path:
            return StepResult(
                phase=2, name=PHASE_NAMES[2], success=True, skipped=True,
                data={"message": "BOM PDF 경로 미지정, 건너뜀"},
            )

        pdf_path = Path(config.bom_pdf_path)
        if not pdf_path.exists():
            return StepResult(
                phase=2, name=PHASE_NAMES[2], success=False,
                error=f"BOM PDF 파일 없음: {config.bom_pdf_path}",
            )

        resp = await self._upload_file(
            f"/projects/{project_id}/import-bom",
            pdf_path,
            field_name="file",
        )
        if not resp:
            return StepResult(phase=2, name=PHASE_NAMES[2], success=False, error="BOM import 실패")

        return StepResult(
            phase=2, name=PHASE_NAMES[2], success=True,
            data={
                "total_items": resp.get("total_items", 0),
                "part_count": resp.get("part_count", 0),
                "source_file": pdf_path.name,
            },
        )

    # ── Phase 3: Match Drawings ────────────────

    async def phase3_match_drawings(self, config: OnboardConfig, project_id: str) -> StepResult:
        """POST /projects/{id}/match-drawings"""
        if config.project_type != "bom_quotation":
            return StepResult(
                phase=3, name=PHASE_NAMES[3], success=True, skipped=True,
                data={"message": f"도면 매칭 불필요 (타입: {config.project_type})"},
            )
        if not config.drawing_folder:
            return StepResult(
                phase=3, name=PHASE_NAMES[3], success=True, skipped=True,
                data={"message": "도면 폴더 미지정, 건너뜀"},
            )

        body = {"drawing_folder": config.drawing_folder}
        resp = await self._request("POST", f"/projects/{project_id}/match-drawings", json_body=body)
        if not resp:
            return StepResult(phase=3, name=PHASE_NAMES[3], success=False, error="도면 매칭 실패")

        return StepResult(
            phase=3, name=PHASE_NAMES[3], success=True,
            data={
                "matched": resp.get("matched_count", 0),
                "unmatched": resp.get("unmatched_count", 0),
                "total": resp.get("total_items", 0),
            },
        )

    # ── Phase 4: Create Sessions ───────────────

    async def phase4_create_sessions(self, config: OnboardConfig, project_id: str) -> StepResult:
        """POST /projects/{id}/create-sessions"""
        body: dict[str, Any] = {"only_matched": True}
        if config.template_name:
            body["template_name"] = config.template_name
        if config.root_drawing_number:
            body["root_drawing_number"] = config.root_drawing_number

        resp = await self._request("POST", f"/projects/{project_id}/create-sessions", json_body=body)
        if not resp:
            return StepResult(phase=4, name=PHASE_NAMES[4], success=False, error="세션 생성 실패")

        created = resp.get("created_count", 0)
        return StepResult(
            phase=4, name=PHASE_NAMES[4], success=True,
            data={
                "created": created,
                "skipped": resp.get("skipped_count", 0),
                "message": resp.get("message", ""),
            },
        )

    # ── Phase 5: Start Batch Analysis ──────────

    async def phase5_start_batch(self, config: OnboardConfig, project_id: str) -> StepResult:
        """POST /analysis/batch/{id}"""
        body: dict[str, Any] = {}
        if config.root_drawing_number:
            body["root_drawing_number"] = config.root_drawing_number
        if config.force_rerun:
            body["force_rerun"] = True

        resp = await self._request("POST", f"/analysis/batch/{project_id}", json_body=body)
        if not resp:
            return StepResult(phase=5, name=PHASE_NAMES[5], success=False, error="배치 분석 시작 실패")

        return StepResult(
            phase=5, name=PHASE_NAMES[5], success=True,
            data={
                "total": resp.get("total", 0),
                "status": resp.get("status", ""),
                "message": resp.get("message", ""),
            },
        )

    # ── Phase 6: Poll Batch Status ─────────────

    async def phase6_poll_status(self, config: OnboardConfig, project_id: str) -> StepResult:
        """GET /analysis/batch/{id}/status (polling loop)"""
        if self.dry_run:
            return StepResult(
                phase=6, name=PHASE_NAMES[6], success=True, skipped=True,
                data={"message": "dry-run: 폴링 건너뜀"},
            )

        start = time.time()
        last_completed = -1

        while (time.time() - start) < POLL_TIMEOUT:
            resp = await self._request("GET", f"/analysis/batch/{project_id}/status")
            if not resp:
                return StepResult(phase=6, name=PHASE_NAMES[6], success=False, error="상태 조회 실패")

            status = resp.get("status", "idle")
            total = resp.get("total", 0)
            completed = resp.get("completed", 0)
            failed = resp.get("failed", 0)
            skipped = resp.get("skipped", 0)
            done = completed + failed + skipped

            # Progress display
            if completed != last_completed:
                pct = round(done / total * 100, 1) if total > 0 else 0
                elapsed = time.time() - start
                eta = (elapsed / done * (total - done)) if done > 0 else 0
                drawing = resp.get("current_drawing", "")
                logger.info(
                    f"  [{done}/{total}] {pct}% | "
                    f"completed={completed} failed={failed} skipped={skipped} | "
                    f"ETA {eta:.0f}s | {drawing}"
                )
                last_completed = completed

            if status in ("completed", "cancelled", "idle"):
                return StepResult(
                    phase=6, name=PHASE_NAMES[6],
                    success=(status == "completed"),
                    data={
                        "status": status,
                        "completed": completed,
                        "failed": failed,
                        "skipped": skipped,
                        "total": total,
                        "elapsed_sec": round(time.time() - start, 1),
                    },
                    error="" if status == "completed" else f"배치 상태: {status}",
                )

            await asyncio.sleep(POLL_INTERVAL)

        return StepResult(
            phase=6, name=PHASE_NAMES[6], success=False,
            error=f"배치 분석 타임아웃 ({POLL_TIMEOUT}초)",
        )

    # ── Phase 7: Agent Verification ────────────

    async def phase7_verify(self, config: OnboardConfig, project_id: str) -> StepResult:
        """Run agent_verify.py as subprocess (optional)."""
        if not config.verify:
            return StepResult(
                phase=7, name=PHASE_NAMES[7], success=True, skipped=True,
                data={"message": "검증 비활성화"},
            )

        # Find agent_verify.py relative to this script
        script_dir = Path(__file__).parent
        verify_script = script_dir / "agent_verify.py"
        if not verify_script.exists():
            return StepResult(
                phase=7, name=PHASE_NAMES[7], success=False,
                error=f"agent_verify.py를 찾을 수 없습니다: {verify_script}",
            )

        cmd = [
            sys.executable,
            str(verify_script),
            "--project-id", project_id,
            "--item-type", config.verify_item_type,
            "--threshold", str(config.verify_threshold),
            "--api-base", config.api_base,
        ]
        if config.dry_run:
            cmd.append("--dry-run")
        if config.verify_l1_only:
            cmd.append("--l1-only")
        if config.verbose:
            cmd.append("--verbose")

        logger.info(f"  실행: {' '.join(cmd)}")

        if self.dry_run:
            return StepResult(
                phase=7, name=PHASE_NAMES[7], success=True, skipped=True,
                data={"message": "dry-run: 검증 건너뜀", "command": " ".join(cmd)},
            )

        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=POLL_TIMEOUT, cwd=str(script_dir),
            )
            success = proc.returncode == 0
            return StepResult(
                phase=7, name=PHASE_NAMES[7], success=success,
                data={"returncode": proc.returncode, "stdout_tail": proc.stdout[-500:] if proc.stdout else ""},
                error=proc.stderr[-300:] if not success and proc.stderr else "",
            )
        except subprocess.TimeoutExpired:
            return StepResult(
                phase=7, name=PHASE_NAMES[7], success=False,
                error=f"검증 타임아웃 ({POLL_TIMEOUT}초)",
            )

    # ── Phase 8: Export Quotation ──────────────

    async def phase8_export(self, config: OnboardConfig, project_id: str) -> StepResult:
        """POST /projects/{id}/quotation/export"""
        body: dict[str, Any] = {"format": config.export_format}
        if config.customer:
            body["customer_name"] = config.customer
        if config.export_notes:
            body["notes"] = config.export_notes

        resp = await self._request("POST", f"/projects/{project_id}/quotation/export", json_body=body)
        if not resp:
            return StepResult(phase=8, name=PHASE_NAMES[8], success=False, error="견적 내보내기 실패")

        return StepResult(
            phase=8, name=PHASE_NAMES[8], success=True,
            data={
                "format": config.export_format,
                "download_url": resp.get("download_url", ""),
                "file_path": resp.get("file_path", ""),
            },
        )

    # ── HTTP Helpers ───────────────────────────

    async def _request(
        self,
        method: str,
        path: str,
        json_body: Optional[dict] = None,
    ) -> Optional[dict]:
        """HTTP request with retry and dry-run support."""
        url = f"{self.api_base}{path}"

        if self.dry_run:
            logger.info(f"  [DRY-RUN] {method} {url}")
            if json_body:
                logger.info(f"    Body: {json.dumps(json_body, ensure_ascii=False)[:200]}")
            return {"dry_run": True, "url": url}

        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    if method == "GET":
                        resp = await client.get(url)
                    elif method == "POST":
                        resp = await client.post(url, json=json_body)
                    else:
                        resp = await client.request(method, url, json=json_body)

                if resp.status_code < 400:
                    return resp.json()

                error_detail = resp.text[:200]
                if resp.status_code == 409:
                    logger.warning(f"Conflict (409): {error_detail}")
                    return resp.json()  # batch already running
                if resp.status_code >= 500 and attempt < MAX_RETRIES - 1:
                    wait = BACKOFF_BASE * (2 ** attempt)
                    logger.warning(f"서버 오류 {resp.status_code}, {wait}초 후 재시도...")
                    await asyncio.sleep(wait)
                    continue

                logger.error(f"{method} {url} → {resp.status_code}: {error_detail}")
                return None

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt < MAX_RETRIES - 1:
                    wait = BACKOFF_BASE * (2 ** attempt)
                    logger.warning(f"네트워크 오류: {e}, {wait}초 후 재시도...")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"네트워크 오류 (최대 재시도 초과): {e}")
                    return None

        return None

    async def _upload_file(
        self,
        path: str,
        file_path: Path,
        field_name: str = "file",
    ) -> Optional[dict]:
        """Upload a file via multipart/form-data."""
        url = f"{self.api_base}{path}"

        if self.dry_run:
            logger.info(f"  [DRY-RUN] POST {url} (file: {file_path.name})")
            return {"dry_run": True, "url": url, "file": file_path.name}

        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=300.0) as client:
                    with open(file_path, "rb") as f:
                        files = {field_name: (file_path.name, f, "application/pdf")}
                        resp = await client.post(url, files=files)

                if resp.status_code < 400:
                    return resp.json()

                if resp.status_code >= 500 and attempt < MAX_RETRIES - 1:
                    wait = BACKOFF_BASE * (2 ** attempt)
                    logger.warning(f"서버 오류 {resp.status_code}, {wait}초 후 재시도...")
                    await asyncio.sleep(wait)
                    continue

                logger.error(f"POST {url} → {resp.status_code}: {resp.text[:200]}")
                return None

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt < MAX_RETRIES - 1:
                    wait = BACKOFF_BASE * (2 ** attempt)
                    logger.warning(f"네트워크 오류: {e}, {wait}초 후 재시도...")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"파일 업로드 실패: {e}")
                    return None

        return None

    # ── State Persistence ──────────────────────

    def _save_state(self, state: PipelineState):
        """Save pipeline state to JSON for resume."""
        if not state.project_id:
            return
        state_file = Path(f"onboard_state_{state.project_id}.json")
        state_file.write_text(
            json.dumps(state.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if self.verbose:
            logger.debug(f"상태 저장: {state_file}")

    @staticmethod
    def load_state(project_id: str) -> Optional[PipelineState]:
        """Load pipeline state from JSON."""
        state_file = Path(f"onboard_state_{project_id}.json")
        if not state_file.exists():
            return None
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
            return PipelineState.from_dict(data)
        except Exception as e:
            logger.warning(f"상태 파일 로드 실패: {e}")
            return None
