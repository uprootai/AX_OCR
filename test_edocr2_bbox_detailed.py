#!/usr/bin/env python3
"""
eDOCr v2 bbox 상세 검증 테스트
네트워크 응답을 직접 캡처하여 bbox 정보 확인
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def test_edocr2_bbox_detailed():
    # API 응답 저장용
    api_responses = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # 네트워크 응답 캡처
        async def handle_response(response):
            if '/api/v2/ocr' in response.url and response.request.method == 'POST':
                try:
                    body = await response.json()
                    api_responses.append({
                        'url': response.url,
                        'status': response.status,
                        'body': body
                    })
                    print(f"✅ API 응답 캡처: {response.status}")
                except Exception as e:
                    print(f"⚠️ 응답 파싱 실패: {e}")

        page.on('response', handle_response)

        print("📱 웹 UI 접속 중...")
        await page.goto('http://localhost:5175/test/edocr2')
        await page.wait_for_load_state('networkidle')
        print("✅ 페이지 로드 완료")

        # v2 선택
        print("🔧 v2 선택...")
        try:
            v2_button = page.locator('text=v2').first
            await v2_button.click(timeout=5000)
            await asyncio.sleep(1)
        except Exception as e:
            print(f"⚠️ v2 선택 실패: {e}")

        # 시각화 활성화
        print("🎨 시각화 옵션 활성화...")
        try:
            # 모든 체크박스 찾기
            checkboxes = page.locator('input[type="checkbox"]')
            count = await checkboxes.count()
            print(f"  체크박스 {count}개 발견")

            # 시각화 관련 체크박스 찾기
            for i in range(count):
                checkbox = checkboxes.nth(i)
                parent = checkbox.locator('..')
                text = await parent.text_content()
                if '시각화' in text or 'visualization' in text.lower():
                    await checkbox.check()
                    print(f"  ✅ 시각화 체크박스 활성화")
                    break
        except Exception as e:
            print(f"⚠️ 시각화 활성화 시도 중 오류: {e}")

        await asyncio.sleep(0.5)

        # 파일 업로드
        print("📤 파일 업로드...")
        file_input = page.locator('input[type="file"]')
        test_file = '/home/uproot/ax/poc/edocr2-api/uploads/20251029_065210_sample3_s60me_shaft.jpg'
        await file_input.set_input_files(test_file)
        await asyncio.sleep(1)

        # OCR 실행
        print("🚀 OCR 실행...")
        await page.click('button:has-text("OCR 실행")')

        # 결과 대기 (최대 60초)
        print("⏳ 결과 대기 중 (최대 60초)...")
        try:
            await page.wait_for_selector('text=Full JSON Response', timeout=60000)
            print("✅ OCR 완료!")
        except Exception as e:
            print(f"⚠️ 대기 중 타임아웃: {e}")

        await asyncio.sleep(3)

        # 캡처된 API 응답 분석
        print("\n" + "="*80)
        print("📊 API 응답 분석")
        print("="*80)

        if not api_responses:
            print("❌ API 응답을 캡처하지 못했습니다!")
            print("💡 페이지를 10초간 유지합니다...")
            await asyncio.sleep(10)
            await browser.close()
            return

        for idx, resp in enumerate(api_responses):
            print(f"\n[응답 #{idx+1}]")
            print(f"URL: {resp['url']}")
            print(f"Status: {resp['status']}")

            result = resp['body']

            # dimensions 검증
            if 'dimensions' in result:
                dims = result['dimensions']
                print(f"\n✅ Dimensions: {len(dims)}개")

                # 처음 3개의 dimension bbox 검증
                for i, dim in enumerate(dims[:3]):
                    print(f"\n  📍 D{i}:")
                    print(f"    type: {dim.get('type')}")
                    print(f"    value: {dim.get('value')} {dim.get('unit')}")

                    bbox = dim.get('bbox')
                    if bbox:
                        print(f"    bbox: {json.dumps(bbox, indent=6)}")

                        # bbox 필드 검증
                        required_fields = ['x', 'y', 'width', 'height']
                        has_all_fields = all(field in bbox for field in required_fields)

                        if has_all_fields:
                            print(f"    ✅ bbox에 모든 필드 포함! (x={bbox['x']}, y={bbox['y']}, w={bbox['width']}, h={bbox['height']})")
                        else:
                            missing = [f for f in required_fields if f not in bbox]
                            print(f"    ❌ bbox에 누락된 필드: {missing}")
                    else:
                        print(f"    ❌ bbox 없음!")

                # 모든 dimensions bbox 필드 검증
                print(f"\n  🔍 전체 Dimensions bbox 검증:")
                all_have_bbox = all('bbox' in d for d in dims)
                all_have_complete_bbox = all(
                    'bbox' in d and
                    all(field in d['bbox'] for field in ['x', 'y', 'width', 'height'])
                    for d in dims
                )

                print(f"    모든 dimension에 bbox 있음: {'✅' if all_have_bbox else '❌'}")
                print(f"    모든 bbox에 x,y,w,h 있음: {'✅' if all_have_complete_bbox else '❌'}")
            else:
                print("❌ dimensions 필드 없음!")

            # GD&T 검증
            if 'gdt' in result:
                gdt_list = result['gdt']
                print(f"\n✅ GD&T: {len(gdt_list)}개")

                if gdt_list:
                    for i, gdt in enumerate(gdt_list[:2]):
                        print(f"\n  📍 G{i}:")
                        print(f"    type: {gdt.get('type')}")
                        print(f"    value: {gdt.get('value')}")

                        bbox = gdt.get('bbox')
                        if bbox:
                            print(f"    bbox: {json.dumps(bbox, indent=6)}")
                            required_fields = ['x', 'y', 'width', 'height']
                            has_all_fields = all(field in bbox for field in required_fields)
                            print(f"    {'✅' if has_all_fields else '❌'} bbox 완전성")

            # 시각화 URL 확인
            if 'visualization_url' in result:
                vis_url = result['visualization_url']
                print(f"\n✅ 시각화 URL: {vis_url}")
            else:
                print("\n⚠️ visualization_url 없음")

        # 시각화 이미지 확인
        print("\n" + "="*80)
        print("🖼️ 시각화 이미지 확인")
        print("="*80)

        vis_image = page.locator('img[alt="OCR Visualization"]')
        vis_count = await vis_image.count()
        print(f"시각화 이미지 수: {vis_count}")

        if vis_count > 0:
            src = await vis_image.first.get_attribute('src')
            print(f"✅ 이미지 src: {src}")

            # 스크린샷 저장
            screenshot_path = '/home/uproot/ax/poc/test_verification_screenshot.png'
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 스크린샷 저장: {screenshot_path}")
        else:
            print("❌ 시각화 이미지 없음")

        print("\n" + "="*80)
        print("✅ 테스트 완료! 5초 후 브라우저 종료...")
        print("="*80)
        await asyncio.sleep(5)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_edocr2_bbox_detailed())
