#!/usr/bin/env python3
"""
Bbox 매핑 검증 테스트
시각화 라벨과 JSON 응답이 정확히 일치하는지 확인
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def test_bbox_mapping():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # API 응답 캡처
        api_response = None

        async def capture_response(response):
            nonlocal api_response
            if '/api/v2/ocr' in response.url and response.request.method == 'POST':
                try:
                    api_response = await response.json()
                    print(f"✅ API 응답 캡처 완료")
                except Exception as e:
                    print(f"⚠️ 응답 파싱 실패: {e}")

        page.on('response', capture_response)

        print("=" * 80)
        print("Bbox 매핑 검증 테스트")
        print("=" * 80)

        # UI 접속
        print("\n📱 UI 접속 중...")
        await page.goto('http://localhost:5175/test/edocr2')
        await page.wait_for_load_state('networkidle')
        print("✅ 페이지 로드 완료")

        # v2 선택
        print("\n🔧 v2 선택...")
        try:
            v2_locator = page.locator('text=v2').first
            await v2_locator.click(timeout=5000)
            await asyncio.sleep(1)
            print("✅ v2 선택 완료")
        except Exception as e:
            print(f"⚠️ v2 선택 실패: {e}")

        # 시각화 활성화
        print("\n🎨 시각화 활성화...")
        try:
            checkboxes = page.locator('input[type="checkbox"]')
            count = await checkboxes.count()

            for i in range(count):
                checkbox = checkboxes.nth(i)
                parent_label = checkbox.locator('..')
                text = await parent_label.text_content()

                if text and ('시각화' in text or 'Visualiz' in text):
                    is_checked = await checkbox.is_checked()
                    if not is_checked:
                        await checkbox.check()
                    print(f"✅ 시각화 체크박스 활성화")
                    break

            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"⚠️ 시각화 활성화 실패: {e}")

        # 파일 업로드
        print("\n📤 파일 업로드...")
        test_file = '/home/uproot/ax/poc/edocr2-api/uploads/20251029_065210_sample3_s60me_shaft.jpg'
        file_input = page.locator('input[type="file"]')
        await file_input.set_input_files(test_file)
        await asyncio.sleep(1)
        print(f"✅ 파일 업로드: {test_file.split('/')[-1]}")

        # OCR 실행
        print("\n🚀 OCR 실행...")
        await page.click('button:has-text("OCR 실행")')

        # 결과 대기
        print("\n⏳ 결과 대기 중 (최대 60초)...")
        try:
            await page.wait_for_selector('text=Full JSON Response', timeout=60000)
            print("✅ OCR 완료!")
        except Exception as e:
            print(f"⚠️ 결과 대기 타임아웃: {e}")

        await asyncio.sleep(3)

        # 분석
        print("\n" + "=" * 80)
        print("📊 매핑 검증 결과")
        print("=" * 80)

        if not api_response:
            print("❌ API 응답을 캡처하지 못했습니다!")
            print("💡 브라우저를 10초간 유지합니다...")
            await asyncio.sleep(10)
            await browser.close()
            return

        data = api_response.get('data', {})
        dimensions = data.get('dimensions', [])
        vis_url = data.get('visualization_url', '')

        print(f"\n✅ Dimensions 개수: {len(dimensions)}")
        print(f"✅ 시각화 URL: {vis_url}")

        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("JSON 응답과 시각화 라벨 매핑 확인:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        for i, dim in enumerate(dimensions[:10]):  # 처음 10개만
            dim_type = dim.get('type', '')
            value = dim.get('value', 0)
            unit = dim.get('unit', '')
            bbox = dim.get('bbox', {})

            x, y, w, h = bbox.get('x', 0), bbox.get('y', 0), bbox.get('width', 0), bbox.get('height', 0)

            print(f"\n  D{i}: {dim_type} {value}{unit}")
            print(f"      bbox: x={x}, y={y}, w={w}, h={h}")
            print(f"      → 시각화 이미지의 '초록색 D{i}' 라벨이 이 위치에 있어야 함")

        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ 검증 방법:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("1. 위 JSON 데이터를 확인하세요")
        print("2. 화면에 표시된 시각화 이미지를 확인하세요")
        print("3. JSON의 D0이 시각화의 D0 라벨과 일치하는지 확인하세요")
        print("4. 모든 라벨(D0, D1, D2...)이 올바른 위치에 있는지 확인하세요")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        # 스크린샷
        screenshot_path = '/home/uproot/ax/poc/bbox_mapping_test_result.png'
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"\n📸 스크린샷 저장: {screenshot_path}")

        print("\n💡 브라우저를 20초간 유지합니다. 직접 확인하세요!")
        await asyncio.sleep(20)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_bbox_mapping())
