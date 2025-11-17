from playwright.sync_api import sync_playwright
import time

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1600, 'height': 1200})

        print("📍 1. 페이지 로딩...")
        page.goto("http://localhost:5173/test/gateway")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        print("📍 2. 샘플 이미지 선택...")
        sample_buttons = page.locator('button:has-text("합성 테스트 도면")')
        if sample_buttons.count() > 0:
            sample_buttons.first.click()
            time.sleep(2)
            print("   ✅ 샘플 이미지 로드됨")

            print("\n📍 3. 분석 실행...")
            # Find and click the process button
            process_button = page.locator('button:has-text("분석 시작")')
            if process_button.is_visible():
                process_button.click()
                print("   ✅ 분석 시작 버튼 클릭")

                # Wait for results (max 60 seconds)
                print("   ⏳ 분석 대기 중...")
                time.sleep(60)  # Wait for processing

                # Scroll down to see results
                print("\n📍 4. 결과 확인...")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)

                # Check for YOLO visualization card
                yolo_viz_card = page.locator('text=YOLO 검출 시각화')
                if yolo_viz_card.is_visible():
                    print("   ✅ YOLO 검출 시각화 카드 발견!")

                    # Take screenshot
                    page.screenshot(path="/home/uproot/ax/poc/test_yolo_viz_result.png", full_page=True)
                    print("   📸 스크린샷 저장")

                    # Check if image is present
                    viz_img = page.locator('img[alt="YOLO Detection Visualization"]')
                    if viz_img.is_visible():
                        print("   ✅ YOLO 시각화 이미지 표시됨!")
                    else:
                        print("   ❌ YOLO 시각화 이미지 없음")
                else:
                    print("   ❌ YOLO 검출 시각화 카드 없음")

                    # Check what's actually there
                    result_cards = page.locator('h3, h2').all_text_contents()
                    print(f"   표시된 카드들: {result_cards[:10]}")

                    # Take screenshot anyway
                    page.screenshot(path="/home/uproot/ax/poc/test_no_yolo_viz.png", full_page=True)

        time.sleep(3)
        browser.close()

if __name__ == "__main__":
    test()
