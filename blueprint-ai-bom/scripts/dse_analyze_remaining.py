#!/usr/bin/env python3
"""DSE Bearing — 기존 12개 세션 순차 분석 (서버 블로킹 회피)

이미 생성된 세션의 primary + sub-images를 외부에서 API로 순차 호출.
서버 내부 배치와 달리, 각 분석 간 서버 응답을 기다리므로 블로킹 문제 없음.

Usage:
    python3 dse_analyze_remaining.py                  # 미분석만 처리
    python3 dse_analyze_remaining.py --force           # 전부 재분석
    python3 dse_analyze_remaining.py --sub-only        # sub-image만
    python3 dse_analyze_remaining.py --primary-only    # primary만
"""

import requests
import time
import sys
import json
import threading
from datetime import datetime

BASE = "http://localhost:5020"
PROJECT_ID = "b97237fd"
TIMEOUT_ANALYSIS = 600  # 10분
TIMEOUT_DEFAULT = 30


def wait_for_backend(max_wait=30):
    for _ in range(max_wait):
        try:
            r = requests.get(f"{BASE}/health", timeout=3)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def get_sessions():
    resp = requests.get(
        f"{BASE}/sessions",
        params={"project_id": PROJECT_ID, "limit": 50},
        timeout=TIMEOUT_DEFAULT,
    )
    resp.raise_for_status()
    return resp.json()


def get_session_images(session_id):
    resp = requests.get(
        f"{BASE}/sessions/{session_id}/images",
        timeout=TIMEOUT_DEFAULT,
    )
    resp.raise_for_status()
    data = resp.json()
    return data if isinstance(data, list) else data.get("images", [])


def fire_analysis(session_id):
    """Thread: fire analysis (blocks until done)"""
    try:
        requests.post(f"{BASE}/analysis/run/{session_id}", timeout=TIMEOUT_ANALYSIS)
    except Exception:
        pass


def poll_status(session_id, max_wait=600):
    """Poll session status until analysis completes."""
    for _ in range(max_wait // 5):
        time.sleep(5)
        try:
            resp = requests.get(f"{BASE}/sessions/{session_id}", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status", "")
                if status in ("verified", "completed", "error"):
                    return data
        except Exception:
            continue
    return None


def analyze_primary(session_id, fname):
    """Primary 이미지 분석 (fire-and-forget + polling)"""
    t0 = time.time()

    thread = threading.Thread(target=fire_analysis, args=(session_id,))
    thread.start()

    detail = poll_status(session_id)
    elapsed = time.time() - t0

    thread.join(timeout=5)

    if detail:
        dims = detail.get("dimensions", [])
        dets = detail.get("detections", [])
        print(f"  Primary: OK ({elapsed:.0f}s) — dims={len(dims)}, dets={len(dets)}")
        return True
    else:
        print(f"  Primary: TIMEOUT ({elapsed:.0f}s)")
        return False


def analyze_sub_image(session_id, image_id, img_name):
    """Sub-image 분석 (동기 호출)"""
    t0 = time.time()
    try:
        resp = requests.post(
            f"{BASE}/analysis/run/{session_id}/image/{image_id}",
            timeout=TIMEOUT_ANALYSIS,
        )
        elapsed = time.time() - t0

        if resp.status_code != 200:
            print(f"    {img_name}: FAIL ({elapsed:.0f}s) — {resp.text[:80]}")
            return False

        data = resp.json()
        od = data.get("od", "-")
        id_ = data.get("id", "-")
        w = data.get("width", "-")
        dims = data.get("dimension_count", 0)
        grade = data.get("quality_grade", "?")
        summary = data.get("validation_summary", "")
        corrections = data.get("corrections", [])

        grade_icon = {"pass": "✓", "warn": "⚠", "fail": "✗"}.get(grade, "?")
        corr_str = f" [보정:{len(corrections)}]" if corrections else ""
        print(
            f"    {img_name}: OK ({elapsed:.0f}s) — dims={dims}, "
            f"OD={od}, ID={id_}, W={w} "
            f"[{grade_icon}{grade}]{corr_str}"
        )
        if grade == "fail" and summary:
            print(f"      ⚠ 품질 실패: {summary}")
        return True
    except Exception as e:
        elapsed = time.time() - t0
        print(f"    {img_name}: ERROR ({elapsed:.0f}s) — {e}")
        return False


def main():
    force = "--force" in sys.argv
    sub_only = "--sub-only" in sys.argv
    primary_only = "--primary-only" in sys.argv

    print(f"{'='*60}")
    print(f"DSE Bearing 순차 분석 (외부 API 호출)")
    print(f"프로젝트: {PROJECT_ID}")
    print(f"옵션: force={force}, sub_only={sub_only}, primary_only={primary_only}")
    print(f"시작: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}\n")

    if not wait_for_backend(10):
        print("ERROR: Backend 접속 불가")
        sys.exit(1)

    sessions = get_sessions()
    print(f"총 {len(sessions)}개 세션\n")

    completed = 0
    failed = 0
    skipped = 0

    for idx, s in enumerate(sessions, 1):
        sid = s["session_id"]
        fname = s.get("filename", "")[:55]
        status = s.get("status", "")
        print(f"\n[{idx}/{len(sessions)}] {fname}")
        print(f"  session: {sid[:12]}...  status: {status}")

        # --- Primary 분석 ---
        if not sub_only:
            if status in ("verified", "completed") and not force:
                print(f"  Primary: SKIP (status={status})")
                skipped += 1
            else:
                ok = analyze_primary(sid, fname)
                if ok:
                    completed += 1
                else:
                    failed += 1

                # 서버 회복 대기
                time.sleep(2)
                if not wait_for_backend(60):
                    print("  WARNING: Backend 응답 지연, 60초 대기...")
                    if not wait_for_backend(120):
                        print("  ERROR: Backend 복구 안 됨, 중단")
                        break

        # --- Sub-images 분석 ---
        if not primary_only:
            try:
                sub_images = get_session_images(sid)
            except Exception as e:
                print(f"  Sub-images 조회 실패: {e}")
                sub_images = []

            for img in sub_images:
                image_id = img.get("image_id", "")
                img_name = img.get("filename", "")[:40]
                has_dims = bool(img.get("dimensions"))

                if has_dims and not force:
                    od = img.get("od", "-")
                    id_ = img.get("id", "-")
                    w = img.get("width", "-")
                    print(f"    {img_name}: SKIP (OD={od}, ID={id_}, W={w})")
                    skipped += 1
                    continue

                ok = analyze_sub_image(sid, image_id, img_name)
                if ok:
                    completed += 1
                else:
                    failed += 1

                # 서버 회복 대기
                time.sleep(1)
                if not wait_for_backend(30):
                    wait_for_backend(60)

    print(f"\n{'='*60}")
    print(f"완료: {completed}성공, {skipped}스킵, {failed}실패")
    print(f"종료: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
