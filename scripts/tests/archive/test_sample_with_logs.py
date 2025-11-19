from playwright.sync_api import sync_playwright
import time

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1400, 'height': 1200})

        # Listen to console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))

        # Listen to page errors
        page.on("pageerror", lambda err: print(f"❌ Page Error: {err}"))

        print("📍 1. 페이지 로딩...")
        page.goto("http://localhost:5173/test/gateway")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        print("📍 2. 샘플 버튼 클릭...")
        sample_buttons = page.locator('button:has-text("합성 테스트 도면")')
        print(f"   샘플 버튼 개수: {sample_buttons.count()}")

        if sample_buttons.count() > 0:
            sample_buttons.first.click()
            print("   버튼 클릭됨, 5초 대기...")
            time.sleep(5)

            # Print console messages
            print("\n📋 Console Messages:")
            for msg in console_messages[-20:]:  # Last 20 messages
                print(f"   {msg}")

            # Check if file preview appeared
            file_preview = page.locator('text=업로드된 파일')
            if file_preview.is_visible():
                print("\n✅ 파일 미리보기 표시됨!")
            else:
                print("\n❌ 파일 미리보기 표시 안됨")

            # Take screenshot
            page.screenshot(path="/home/uproot/ax/poc/test_with_console.png")

        time.sleep(3)
        browser.close()

if __name__ == "__main__":
    test()
