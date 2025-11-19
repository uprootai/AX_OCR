from playwright.sync_api import sync_playwright
import time

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1400, 'height': 1200})

        print("📍 1. 페이지 로딩...")
        page.goto("http://localhost:5173/test/gateway")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Scroll to file upload section
        print("📍 2. 파일 업로드 섹션으로 스크롤...")
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)

        # Take initial screenshot
        page.screenshot(path="/home/uproot/ax/poc/test_initial_view.png")
        print("✅ 초기 화면 스크린샷 저장")

        # Check for sample buttons
        print("\n📍 3. 샘플 이미지 버튼 확인...")
        sample_buttons = page.locator('button:has-text("합성 테스트 도면")')
        count = sample_buttons.count()
        print(f"   샘플 버튼 개수: {count}")

        if count > 0:
            # Click first sample button
            print("\n📍 4. 첫 번째 샘플 버튼 클릭...")
            sample_buttons.first.click()
            time.sleep(3)  # Wait for image to load

            # Check if file preview appeared
            file_preview = page.locator('text=업로드된 파일')
            if file_preview.is_visible():
                print("✅ 파일 미리보기 표시됨!")

                # Check for image preview
                img = page.locator('img[alt*="미리보기"]')
                if img.is_visible():
                    print("✅ 이미지 미리보기 표시됨!")
                else:
                    print("❌ 이미지 미리보기 없음")

                # Check file info
                filename = page.locator('text=파일명').locator('..').locator('span.font-medium').nth(0)
                if filename.is_visible():
                    print(f"   파일명: {filename.text_content()}")

                file_type = page.locator('text=타입').locator('..').locator('span.font-medium')
                if file_type.is_visible():
                    print(f"   파일 타입: {file_type.text_content()}")

                # Check for X button
                remove_button = page.locator('button[aria-label="파일 제거"]')
                if remove_button.is_visible():
                    print("✅ X 버튼 (파일 제거) 표시됨!")
                else:
                    print("❌ X 버튼 없음")

                # Take screenshot with file loaded
                page.screenshot(path="/home/uproot/ax/poc/test_file_loaded.png")
                print("\n✅ 파일 로드된 화면 스크린샷 저장")

                # Test X button
                print("\n📍 5. X 버튼 클릭 테스트...")
                if remove_button.is_visible():
                    remove_button.click()
                    time.sleep(1)

                    # Check if file was removed
                    if not file_preview.is_visible():
                        print("✅ 파일 제거 성공! 드롭존으로 돌아감")
                        page.screenshot(path="/home/uproot/ax/poc/test_after_remove.png")
                    else:
                        print("❌ 파일 제거 실패")
            else:
                print("❌ 파일 미리보기 표시 안됨")
        else:
            print("❌ 샘플 버튼 없음")

        print("\n✅ 테스트 완료!")
        time.sleep(2)
        browser.close()

if __name__ == "__main__":
    test()
