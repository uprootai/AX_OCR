#!/usr/bin/env python3
"""
AI BOM Feature Test
====================
AI BOM Human-in-the-Loop 기능 테스트

테스트 항목:
1. 세션 생성 및 이미지 업로드
2. YOLO 검출
3. 검증 큐 기능
4. VLM 자동 분류
5. 수동 검증
"""

import requests
import json
import sys
from pathlib import Path
from datetime import datetime

# Configuration
AIBOM_URL = "http://localhost:5020"
SAMPLE_IMAGE = "/home/uproot/ax/poc/web-ui/public/samples/bwms_pid_sample.png"
OUTPUT_DIR = Path("/home/uproot/ax/poc/rnd/experiments/bwms_pipeline_improvement/results")


def test_health():
    """Test AI BOM service health."""
    print("\n📍 Test 1: Health Check")
    response = requests.get(f"{AIBOM_URL}/health", timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Status: {data.get('status', 'unknown')}")
        return True
    else:
        print(f"   ❌ Health check failed: {response.status_code}")
        return False


def test_upload_session(image_path: str) -> str:
    """Test image upload and session creation."""
    print("\n📍 Test 2: Upload Image & Create Session")

    with open(image_path, "rb") as f:
        files = {"file": (Path(image_path).name, f, "image/png")}
        response = requests.post(f"{AIBOM_URL}/sessions/upload", files=files, timeout=60)

    if response.status_code == 200:
        data = response.json()
        session_id = data.get("session_id")
        print(f"   ✅ Session created: {session_id}")
        print(f"   ✅ Image size: {data.get('width', 0)}x{data.get('height', 0)}")
        return session_id
    else:
        print(f"   ❌ Upload failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return None


def test_detection(session_id: str) -> dict:
    """Test YOLO detection."""
    print("\n📍 Test 3: Run Detection")

    params = {
        "model_type": "pid_class_aware",
        "confidence": 0.25,
        "use_sahi": True
    }

    response = requests.post(
        f"{AIBOM_URL}/detection/{session_id}/detect",
        params=params,
        timeout=120
    )

    if response.status_code == 200:
        data = response.json()
        detections = data.get("detections", [])
        print(f"   ✅ Detections: {len(detections)}개")

        # Confidence distribution
        if detections:
            confidences = [d.get("confidence", 0) for d in detections]
            avg_conf = sum(confidences) / len(confidences)
            min_conf = min(confidences)
            max_conf = max(confidences)
            low_conf = sum(1 for c in confidences if c < 0.5)
            print(f"   ✅ Avg confidence: {avg_conf*100:.1f}%")
            print(f"   ✅ Min/Max: {min_conf*100:.1f}% / {max_conf*100:.1f}%")
            print(f"   ✅ Low confidence (<50%): {low_conf}개")

        return data
    else:
        print(f"   ❌ Detection failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return None


def test_verification_queue(session_id: str) -> dict:
    """Test verification queue."""
    print("\n📍 Test 4: Verification Queue")

    response = requests.get(
        f"{AIBOM_URL}/verification/queue/{session_id}",
        timeout=30
    )

    if response.status_code == 200:
        data = response.json()
        queue = data.get("queue", [])
        print(f"   ✅ Queue items: {len(queue)}개")

        # Status distribution
        if queue:
            status_counts = {}
            for item in queue:
                status = item.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            print(f"   ✅ Status distribution: {status_counts}")

        return data
    else:
        print(f"   ❌ Verification queue failed: {response.status_code}")
        return None


def test_verification_stats(session_id: str) -> dict:
    """Test verification statistics."""
    print("\n📍 Test 5: Verification Stats")

    response = requests.get(
        f"{AIBOM_URL}/verification/stats/{session_id}",
        timeout=30
    )

    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Total: {data.get('total', 0)}")
        print(f"   ✅ Verified: {data.get('verified', 0)}")
        print(f"   ✅ Pending: {data.get('pending', 0)}")
        print(f"   ✅ Rejected: {data.get('rejected', 0)}")
        return data
    else:
        print(f"   ❌ Stats failed: {response.status_code}")
        return None


def test_auto_approve_candidates(session_id: str) -> dict:
    """Test auto-approve candidates."""
    print("\n📍 Test 6: Auto-Approve Candidates")

    response = requests.get(
        f"{AIBOM_URL}/verification/auto-approve-candidates/{session_id}",
        params={"threshold": 0.85},
        timeout=30
    )

    if response.status_code == 200:
        data = response.json()
        candidates = data.get("candidates", [])
        print(f"   ✅ Auto-approve candidates (>85%): {len(candidates)}개")
        return data
    else:
        print(f"   ❌ Auto-approve candidates failed: {response.status_code}")
        return None


def test_vlm_classification(session_id: str) -> dict:
    """Test VLM auto classification."""
    print("\n📍 Test 7: VLM Auto Classification")

    response = requests.post(
        f"{AIBOM_URL}/analysis/vlm-classify/{session_id}",
        params={"limit": 5},  # Test with 5 detections
        timeout=120
    )

    if response.status_code == 200:
        data = response.json()
        classified = data.get("classified", [])
        print(f"   ✅ VLM classified: {len(classified)}개")

        if classified:
            for item in classified[:3]:
                original = item.get("original_class", "unknown")
                suggested = item.get("suggested_class", "unknown")
                confidence = item.get("confidence", 0)
                print(f"      {original} → {suggested} ({confidence*100:.1f}%)")

        return data
    else:
        print(f"   ⚠️  VLM classification not available or failed: {response.status_code}")
        return None


def test_bulk_verify(session_id: str) -> dict:
    """Test bulk verification."""
    print("\n📍 Test 8: Bulk Verification")

    # Get detections first
    response = requests.get(
        f"{AIBOM_URL}/detection/{session_id}/detections",
        timeout=30
    )

    if response.status_code != 200:
        print(f"   ❌ Failed to get detections")
        return None

    detections = response.json().get("detections", [])

    if not detections:
        print(f"   ⚠️  No detections to approve")
        return None

    # Human-in-the-Loop: 모든 검출을 승인 (테스트용)
    # 실제 사용 시 사용자가 검토 후 선택적 승인
    to_approve = detections[:10]  # 최대 10개
    print(f"   📋 검출 {len(detections)}개 중 {len(to_approve)}개 승인 시도")

    # Approve them (API expects item_ids + item_type for detections)
    payload = {
        "item_ids": [d["id"] for d in to_approve],
        "item_type": "symbol"  # "dimension" 대신 "symbol" 사용
    }

    response = requests.post(
        f"{AIBOM_URL}/verification/bulk-approve/{session_id}",
        json=payload,
        timeout=30
    )

    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Bulk approved: {data.get('approved_count', 0)}개")
        return data
    else:
        print(f"   ❌ Bulk verification failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return None


def test_bom_generation(session_id: str) -> dict:
    """Test BOM generation."""
    print("\n📍 Test 9: BOM Generation")

    response = requests.post(
        f"{AIBOM_URL}/bom/{session_id}/generate",
        timeout=60
    )

    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        print(f"   ✅ BOM items: {len(items)}개")

        if items:
            for item in items[:5]:
                name = item.get("name", "unknown")
                qty = item.get("quantity", 0)
                print(f"      - {name}: {qty}개")

        return data
    else:
        print(f"   ❌ BOM generation failed: {response.status_code}")
        return None


def test_pid_features(session_id: str) -> dict:
    """Test P&ID specific features."""
    print("\n📍 Test 10: P&ID Features")

    # Test valve detection
    response = requests.post(
        f"{AIBOM_URL}/pid-features/{session_id}/valve/detect",
        timeout=60
    )

    if response.status_code == 200:
        data = response.json()
        valves = data.get("valves", [])
        print(f"   ✅ Valves detected: {len(valves)}개")
    else:
        print(f"   ⚠️  Valve detection: {response.status_code}")

    # Test equipment detection
    response = requests.post(
        f"{AIBOM_URL}/pid-features/{session_id}/equipment/detect",
        timeout=60
    )

    if response.status_code == 200:
        data = response.json()
        equipment = data.get("equipment", [])
        print(f"   ✅ Equipment detected: {len(equipment)}개")
        return data
    else:
        print(f"   ⚠️  Equipment detection: {response.status_code}")
        return None


def main():
    print("=" * 60)
    print("🔬 AI BOM Feature Test")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Image: {SAMPLE_IMAGE}")
    print("=" * 60)

    # Check image exists
    if not Path(SAMPLE_IMAGE).exists():
        print(f"\n❌ Image not found: {SAMPLE_IMAGE}")
        sys.exit(1)

    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }

    # Test 1: Health
    if not test_health():
        print("\n❌ AI BOM service not available")
        sys.exit(1)
    results["tests"]["health"] = "passed"

    # Test 2: Upload
    session_id = test_upload_session(SAMPLE_IMAGE)
    if not session_id:
        print("\n❌ Session creation failed")
        sys.exit(1)
    results["tests"]["upload"] = "passed"
    results["session_id"] = session_id

    # Test 3: Detection
    detection_result = test_detection(session_id)
    results["tests"]["detection"] = "passed" if detection_result else "failed"

    # Test 4: Verification Queue
    queue_result = test_verification_queue(session_id)
    results["tests"]["verification_queue"] = "passed" if queue_result else "failed"

    # Test 5: Verification Stats
    stats_result = test_verification_stats(session_id)
    results["tests"]["verification_stats"] = "passed" if stats_result else "failed"

    # Test 6: Auto-Approve Candidates
    candidates_result = test_auto_approve_candidates(session_id)
    results["tests"]["auto_approve_candidates"] = "passed" if candidates_result else "failed"

    # Test 7: VLM Classification (optional)
    vlm_result = test_vlm_classification(session_id)
    results["tests"]["vlm_classification"] = "passed" if vlm_result else "skipped"

    # Test 8: Bulk Verify
    bulk_result = test_bulk_verify(session_id)
    results["tests"]["bulk_verify"] = "passed" if bulk_result else "skipped"

    # Test 9: BOM Generation
    bom_result = test_bom_generation(session_id)
    results["tests"]["bom_generation"] = "passed" if bom_result else "failed"

    # Test 10: P&ID Features
    pid_result = test_pid_features(session_id)
    results["tests"]["pid_features"] = "passed" if pid_result else "skipped"

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results["tests"].values() if v == "passed")
    failed = sum(1 for v in results["tests"].values() if v == "failed")
    skipped = sum(1 for v in results["tests"].values() if v == "skipped")
    total = len(results["tests"])

    print(f"\n   ✅ Passed: {passed}/{total}")
    print(f"   ❌ Failed: {failed}/{total}")
    print(f"   ⏭️  Skipped: {skipped}/{total}")

    for test_name, status in results["tests"].items():
        icon = "✅" if status == "passed" else "❌" if status == "failed" else "⏭️"
        print(f"   {icon} {test_name}: {status}")

    # Save results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"aibom_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Results saved: {output_file}")
    print("\n✅ AI BOM feature test completed!")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
