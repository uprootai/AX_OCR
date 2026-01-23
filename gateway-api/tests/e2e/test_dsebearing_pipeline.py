"""
DSE Bearing E2E Pipeline Test
실제 도면 이미지로 전체 파이프라인 테스트
"""
import asyncio
import httpx
import base64
import json
from pathlib import Path
from datetime import datetime

# 설정
GATEWAY_URL = "http://localhost:8000"
DSE_API_BASE = f"{GATEWAY_URL}/api/v1/dsebearing"
TEST_IMAGE_DIR = Path("/home/uproot/ax/poc/apply-company/dsebearing/test_images")


async def test_full_pipeline():
    """전체 파이프라인 E2E 테스트"""
    print("=" * 60)
    print("DSE Bearing E2E Pipeline Test")
    print("=" * 60)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 테스트 이미지 선택
    test_image = TEST_IMAGE_DIR / "ring_assy_t1_page1.png"
    if not test_image.exists():
        print(f"❌ 테스트 이미지 없음: {test_image}")
        return False

    print(f"📷 테스트 이미지: {test_image.name}")
    print(f"   크기: {test_image.stat().st_size / 1024 / 1024:.2f} MB")
    print()

    async with httpx.AsyncClient(timeout=120.0) as client:
        # Step 1: Title Block 파싱
        print("=" * 40)
        print("Step 1: Title Block 파싱")
        print("=" * 40)

        with open(test_image, "rb") as f:
            files = {"file": (test_image.name, f, "image/png")}
            data = {"profile": "bearing"}

            response = await client.post(
                f"{DSE_API_BASE}/titleblock",
                files=files,
                data=data
            )

        if response.status_code == 200:
            titleblock = response.json()
            print(f"✅ Title Block 파싱 성공")
            print(f"   도면번호: {titleblock.get('drawing_number', 'N/A')}")
            print(f"   Rev: {titleblock.get('revision', 'N/A')}")
            print(f"   품명: {titleblock.get('part_name', 'N/A')}")
            print(f"   재질: {titleblock.get('material', 'N/A')}")
            print(f"   신뢰도: {titleblock.get('confidence', 0):.2f}")
        else:
            print(f"❌ Title Block 파싱 실패: {response.status_code}")
            titleblock = {}
        print()

        # Step 2: Parts List 파싱
        print("=" * 40)
        print("Step 2: Parts List 파싱")
        print("=" * 40)

        with open(test_image, "rb") as f:
            files = {"file": (test_image.name, f, "image/png")}
            data = {"profile": "bearing"}

            response = await client.post(
                f"{DSE_API_BASE}/partslist",
                files=files,
                data=data
            )

        if response.status_code == 200:
            partslist = response.json()
            items = partslist.get("items", [])
            print(f"✅ Parts List 파싱 성공: {len(items)}개 항목")
            for item in items[:5]:  # 최대 5개만 표시
                print(f"   - {item.get('no', '?')}: {item.get('description', 'N/A')} ({item.get('material', 'N/A')}) x{item.get('qty', 1)}")
            if len(items) > 5:
                print(f"   ... 외 {len(items) - 5}개")
            print(f"   신뢰도: {partslist.get('confidence', 0):.2f}")
        else:
            print(f"❌ Parts List 파싱 실패: {response.status_code}")
            partslist = {"items": []}
        print()

        # Step 3: Dimension Parser
        print("=" * 40)
        print("Step 3: Dimension 파싱")
        print("=" * 40)

        with open(test_image, "rb") as f:
            files = {"file": (test_image.name, f, "image/png")}
            data = {"dimension_type": "bearing"}

            response = await client.post(
                f"{DSE_API_BASE}/dimensionparser",
                files=files,
                data=data
            )

        if response.status_code == 200:
            dimensions = response.json()
            dim_list = dimensions.get("dimensions", [])
            print(f"✅ Dimension 파싱 성공: {len(dim_list)}개 치수")
            for dim in dim_list[:3]:  # 최대 3개만 표시
                print(f"   - {dim.get('raw_text', 'N/A')}: {dim.get('type', 'unknown')}")
            if len(dim_list) > 3:
                print(f"   ... 외 {len(dim_list) - 3}개")
        else:
            print(f"❌ Dimension 파싱 실패: {response.status_code}")
            dimensions = {}
        print()

        # Step 4: BOM Matcher
        print("=" * 40)
        print("Step 4: BOM 매칭")
        print("=" * 40)

        bom_data = {
            "titleblock_data": json.dumps(titleblock),
            "partslist_data": json.dumps({"parts": partslist.get("items", [])}),
            "dimension_data": json.dumps(dimensions),
            "customer_id": "DSE",
            "generate_quote": "true"
        }

        response = await client.post(
            f"{DSE_API_BASE}/bommatcher",
            data=bom_data
        )

        if response.status_code == 200:
            bom_result = response.json()
            matched = bom_result.get("matched_items", [])
            print(f"✅ BOM 매칭 성공: {len(matched)}개 항목")
            print(f"   매칭 신뢰도: {bom_result.get('match_confidence', 0):.2f}")
        else:
            print(f"❌ BOM 매칭 실패: {response.status_code}")
            print(f"   응답: {response.text[:200]}")
        print()

        # Step 5: Quote Generator
        print("=" * 40)
        print("Step 5: 견적 생성")
        print("=" * 40)

        # Parts List 항목을 견적용 형식으로 변환
        quote_parts = []
        for item in partslist.get("items", []):
            quote_parts.append({
                "no": item.get("no", ""),
                "description": item.get("description", ""),
                "material": item.get("material", "SF45A"),
                "qty": item.get("qty", 1),
                "weight": item.get("weight") or 10.0  # 기본 무게
            })

        if quote_parts:
            response = await client.post(
                f"{DSE_API_BASE}/quotegenerator",
                json={
                    "customer_id": "DSE",
                    "parts": quote_parts
                }
            )

            if response.status_code == 200:
                quote = response.json()
                print(f"✅ 견적 생성 성공")
                print(f"   견적번호: {quote.get('quote_number', 'N/A')}")
                print(f"   항목 수: {len(quote.get('items', []))}")
                print(f"   소계: {quote.get('subtotal', 0):,.0f} KRW")
                print(f"   할인: {quote.get('discount', 0):,.0f} KRW")
                print(f"   세금: {quote.get('tax', 0):,.0f} KRW")
                print(f"   총액: {quote.get('total', 0):,.0f} KRW")
            else:
                print(f"❌ 견적 생성 실패: {response.status_code}")
        else:
            print("⚠️ 견적 생성 스킵 (Parts List 항목 없음)")
        print()

    print("=" * 60)
    print("E2E 테스트 완료")
    print("=" * 60)
    return True


async def test_api_health():
    """API 헬스체크"""
    print("API 연결 확인...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Materials API로 헬스체크
            response = await client.get(f"{DSE_API_BASE}/prices/materials")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Gateway API 연결됨 ({len(data.get('materials', []))}개 재질)")
                return True
            else:
                print(f"❌ API 응답 오류: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 연결 실패: {e}")
            return False


if __name__ == "__main__":
    async def main():
        if await test_api_health():
            print()
            await test_full_pipeline()
        else:
            print("API 서버가 실행 중인지 확인하세요.")

    asyncio.run(main())
