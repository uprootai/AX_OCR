#!/usr/bin/env python3
"""
eDOCr v2 bbox 정보 테스트
Playwright를 사용하여 UI에서 OCR 실행 후 bbox 정보 확인
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def test_edocr2_bbox():
    async with async_playwright() as p:
        # 브라우저 시작 (headless=False로 보이게)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("📱 웹 UI 접속 중...")
        await page.goto('http://localhost:5175/test/edocr2')
        await page.wait_for_load_state('networkidle')

        print("✅ 페이지 로드 완료")

        # v2 선택 (Badge 또는 버튼)
        print("🔧 v2 선택...")
        try:
            # v2 버튼 찾기 (여러 방법 시도)
            v2_button = page.locator('text=v2').first
            await v2_button.click(timeout=5000)
        except:
            print("  v2 버튼을 기본 방법으로 찾을 수 없음, Badge 시도...")
            await page.locator('[class*="badge"]:has-text("v2")').click(timeout=5000)
        await asyncio.sleep(1)

        # 시각화 체크박스 활성화
        print("🎨 시각화 옵션 활성화...")
        visualize_checkbox = page.locator('input[type="checkbox"]').filter(has_text='시각화')
        if await visualize_checkbox.count() > 0:
            await visualize_checkbox.first.check()
        else:
            # label 텍스트로 찾기
            await page.locator('label:has-text("시각화")').locator('input').check()

        await asyncio.sleep(0.5)

        # 파일 업로드
        print("📤 파일 업로드...")
        file_input = page.locator('input[type="file"]')
        await file_input.set_input_files('/home/uproot/ax/poc/edocr2-api/uploads/20251029_065210_sample3_s60me_shaft.jpg')
        await asyncio.sleep(1)

        # OCR 실행 버튼 클릭
        print("🚀 OCR 실행...")
        await page.click('button:has-text("OCR 실행")')

        # 결과 대기 (최대 60초)
        print("⏳ 결과 대기 중...")
        try:
            # 여러 가능한 완료 신호 확인
            await page.wait_for_selector('text=시각화 결과', timeout=60000)
            print("✅ OCR 완료!")
        except:
            print("⚠️ 시각화 결과 텍스트를 찾을 수 없음, 다른 방법 시도...")
            # Full JSON Response 카드 대기
            try:
                await page.wait_for_selector('text=Full JSON Response', timeout=10000)
                print("✅ JSON 결과 확인!")
            except:
                # 에러 메시지 확인
                error_elem = page.locator('[class*="error"]').first
                if await error_elem.count() > 0:
                    error_text = await error_elem.text_content()
                    print(f"❌ 에러 발생: {error_text}")
                    await asyncio.sleep(5)
                    await browser.close()
                    return
                print("⚠️ 결과 표시를 확인할 수 없지만 계속 진행...")

        # JSON 결과 추출
        print("\n📊 결과 분석 중...")

        # JSON Viewer에서 데이터 추출 시도
        await asyncio.sleep(2)

        # dimensions 데이터 확인
        page_content = await page.content()

        # JSON 데이터를 직접 파싱하기 위해 네트워크 응답 캡처
        # 또는 localStorage/전역 변수에서 가져오기
        result_json = await page.evaluate('''() => {
            // React 상태에서 데이터 가져오기 시도
            const jsonViewers = document.querySelectorAll('[data-testid="json-viewer"], .json-viewer');
            if (jsonViewers.length > 0) {
                // JSON 텍스트 추출
                const text = jsonViewers[0].textContent;
                try {
                    // JSON 파싱 시도
                    return JSON.parse(text);
                } catch (e) {
                    return null;
                }
            }
            return null;
        }''')

        if not result_json:
            print("⚠️ JSON 데이터를 직접 추출할 수 없습니다. 수동으로 확인하세요.")
            print("💡 페이지를 5초간 유지합니다...")
            await asyncio.sleep(5)
        else:
            print("\n✅ 결과 데이터:")
            print(json.dumps(result_json, indent=2, ensure_ascii=False)[:500])

            # dimensions 검증
            if 'dimensions' in result_json:
                dims = result_json['dimensions']
                print(f"\n📏 Dimensions: {len(dims)}개")

                for i, dim in enumerate(dims[:3]):  # 처음 3개만
                    print(f"\n  D{i}:")
                    print(f"    type: {dim.get('type')}")
                    print(f"    value: {dim.get('value')} {dim.get('unit')}")

                    bbox = dim.get('bbox', {})
                    if bbox:
                        print(f"    bbox: x={bbox.get('x')}, y={bbox.get('y')}, "
                              f"w={bbox.get('width')}, h={bbox.get('height')}")

                        if 'width' in bbox and 'height' in bbox:
                            print("    ✅ bbox에 width, height 포함!")
                        else:
                            print("    ❌ bbox에 width, height 없음!")

        # 시각화 이미지 확인
        print("\n🖼️ 시각화 이미지 확인...")
        vis_image = page.locator('img[alt="OCR Visualization"]')
        if await vis_image.count() > 0:
            print("✅ 시각화 이미지 표시됨")

            # 이미지 클릭해서 확대 모달 테스트
            print("🔍 확대 모달 테스트...")
            await vis_image.click()
            await asyncio.sleep(1)

            # 모달 확인
            modal = page.locator('.fixed.inset-0')
            if await modal.count() > 0:
                print("✅ 확대 모달 열림")

                # ESC로 닫기
                await page.keyboard.press('Escape')
                await asyncio.sleep(0.5)
                print("✅ 모달 닫힘")
            else:
                print("❌ 확대 모달이 열리지 않음")
        else:
            print("❌ 시각화 이미지가 표시되지 않음")

        print("\n✅ 테스트 완료! 5초 후 브라우저 종료...")
        await asyncio.sleep(5)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_edocr2_bbox())
