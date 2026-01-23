"""
DSE Bearing 다중 도면 테스트
모든 테스트 이미지로 파이프라인 검증
"""
import asyncio
import httpx
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 설정
GATEWAY_URL = "http://localhost:8000"
DSE_API_BASE = f"{GATEWAY_URL}/api/v1/dsebearing"
TEST_IMAGE_DIR = Path("/home/uproot/ax/poc/apply-company/dsebearing/test_images")

# 테스트 결과 저장
results: List[Dict[str, Any]] = []


async def test_single_drawing(client: httpx.AsyncClient, image_path: Path) -> Dict[str, Any]:
    """단일 도면 테스트"""
    result = {
        "image": image_path.name,
        "size_mb": image_path.stat().st_size / 1024 / 1024,
        "titleblock": None,
        "partslist": None,
        "dimensions": None,
        "quote": None,
        "errors": [],
        "score": 0,
    }

    print(f"\n{'='*60}")
    print(f"테스트: {image_path.name}")
    print(f"{'='*60}")

    # Step 1: Title Block 파싱
    try:
        with open(image_path, "rb") as f:
            files = {"file": (image_path.name, f, "image/png")}
            data = {"profile": "bearing"}
            response = await client.post(f"{DSE_API_BASE}/titleblock", files=files, data=data)

        if response.status_code == 200:
            tb = response.json()
            result["titleblock"] = tb
            print(f"✅ Title Block: {tb.get('drawing_number', 'N/A')} Rev.{tb.get('revision', 'N/A')}")
            print(f"   품명: {tb.get('part_name', 'N/A')}")
            print(f"   재질: {tb.get('material', 'N/A')}")
            print(f"   신뢰도: {tb.get('confidence', 0):.2f}")

            # 점수 계산
            if tb.get("drawing_number"):
                result["score"] += 20
            if tb.get("revision"):
                result["score"] += 5
            if tb.get("part_name"):
                result["score"] += 10
            if tb.get("material"):
                result["score"] += 5
        else:
            result["errors"].append(f"Title Block 파싱 실패: {response.status_code}")
            print(f"❌ Title Block 실패: {response.status_code}")
    except Exception as e:
        result["errors"].append(f"Title Block 예외: {str(e)}")
        print(f"❌ Title Block 예외: {e}")

    # Step 2: Parts List 파싱
    try:
        with open(image_path, "rb") as f:
            files = {"file": (image_path.name, f, "image/png")}
            data = {"profile": "bearing"}
            response = await client.post(f"{DSE_API_BASE}/partslist", files=files, data=data)

        if response.status_code == 200:
            pl = response.json()
            items = pl.get("items", [])
            result["partslist"] = pl
            print(f"✅ Parts List: {len(items)}개 항목")
            for item in items[:3]:
                print(f"   - {item.get('no', '?')}: {item.get('description', 'N/A')} ({item.get('material', 'N/A')})")
            if len(items) > 3:
                print(f"   ... 외 {len(items) - 3}개")

            # 점수 계산
            if len(items) > 0:
                result["score"] += 20
            if len(items) >= 3:
                result["score"] += 10
        else:
            result["errors"].append(f"Parts List 파싱 실패: {response.status_code}")
            print(f"❌ Parts List 실패: {response.status_code}")
    except Exception as e:
        result["errors"].append(f"Parts List 예외: {str(e)}")
        print(f"❌ Parts List 예외: {e}")

    # Step 3: Dimension 파싱
    try:
        with open(image_path, "rb") as f:
            files = {"file": (image_path.name, f, "image/png")}
            data = {"dimension_type": "bearing"}
            response = await client.post(f"{DSE_API_BASE}/dimensionparser", files=files, data=data)

        if response.status_code == 200:
            dims = response.json()
            dim_list = dims.get("dimensions", [])
            result["dimensions"] = dims
            print(f"✅ Dimensions: {len(dim_list)}개 치수")
            for dim in dim_list[:3]:
                print(f"   - {dim.get('raw_text', 'N/A')}: {dim.get('type', 'unknown')}")

            # 점수 계산
            if len(dim_list) > 0:
                result["score"] += 10
        else:
            result["errors"].append(f"Dimension 파싱 실패: {response.status_code}")
            print(f"❌ Dimension 실패: {response.status_code}")
    except Exception as e:
        result["errors"].append(f"Dimension 예외: {str(e)}")
        print(f"❌ Dimension 예외: {e}")

    # Step 4: 견적 생성 (Parts List가 있는 경우)
    if result["partslist"] and result["partslist"].get("items"):
        try:
            quote_parts = []
            for item in result["partslist"]["items"]:
                quote_parts.append({
                    "no": item.get("no", ""),
                    "description": item.get("description", ""),
                    "material": item.get("material", "SF45A"),
                    "qty": item.get("qty", 1),
                    "weight": item.get("weight") or 10.0
                })

            response = await client.post(
                f"{DSE_API_BASE}/quotegenerator",
                json={"customer_id": "DSE", "parts": quote_parts}
            )

            if response.status_code == 200:
                quote = response.json()
                result["quote"] = quote
                print(f"✅ 견적 생성: {quote.get('quote_number', 'N/A')}")
                print(f"   총액: {quote.get('total', 0):,.0f} KRW")

                # 점수 계산
                if quote.get("total", 0) > 0:
                    result["score"] += 20
            else:
                result["errors"].append(f"견적 생성 실패: {response.status_code}")
                print(f"❌ 견적 생성 실패: {response.status_code}")
        except Exception as e:
            result["errors"].append(f"견적 생성 예외: {str(e)}")
            print(f"❌ 견적 생성 예외: {e}")

    print(f"\n📊 점수: {result['score']}/100")
    if result["errors"]:
        print(f"⚠️ 오류: {len(result['errors'])}개")

    return result


async def run_all_tests():
    """모든 도면 테스트 실행"""
    print("=" * 60)
    print("DSE Bearing 다중 도면 테스트")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 테스트 이미지 목록
    test_images = list(TEST_IMAGE_DIR.glob("*.png"))
    print(f"\n테스트 이미지: {len(test_images)}개")
    for img in test_images:
        print(f"  - {img.name} ({img.stat().st_size / 1024 / 1024:.2f} MB)")

    # API 연결 확인
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.get(f"{DSE_API_BASE}/prices/materials")
            if response.status_code != 200:
                print(f"\n❌ API 연결 실패: {response.status_code}")
                return
            print(f"\n✅ API 연결됨")
        except Exception as e:
            print(f"\n❌ API 연결 실패: {e}")
            return

        # 각 이미지 테스트
        for image_path in test_images:
            result = await test_single_drawing(client, image_path)
            results.append(result)

    # 최종 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)

    total_score = 0
    for r in results:
        status = "✅" if r["score"] >= 50 else "⚠️" if r["score"] >= 30 else "❌"
        print(f"{status} {r['image']}: {r['score']}/100점")
        total_score += r["score"]

    avg_score = total_score / len(results) if results else 0
    print(f"\n📊 평균 점수: {avg_score:.1f}/100")
    print(f"📊 총 오류: {sum(len(r['errors']) for r in results)}개")

    # 결과 저장
    output_file = TEST_IMAGE_DIR.parent / "test_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "average_score": avg_score,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {output_file}")

    return avg_score


if __name__ == "__main__":
    score = asyncio.run(run_all_tests())
    print(f"\n최종 평균 점수: {score:.1f}/100")
