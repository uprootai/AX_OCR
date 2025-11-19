from playwright.sync_api import sync_playwright
import time

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={'width': 1600, 'height': 1200})

        page.goto("http://localhost:5173/test/gateway")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Load sample image
        sample_buttons = page.locator('button:has-text("합성 테스트 도면")')
        sample_buttons.first.click()
        time.sleep(3)

        # Find buttons
        all_buttons = page.locator('button').all()
        print(f"\n발견된 버튼들:")
        for i, btn in enumerate(all_buttons):
            text = btn.inner_text()
            if text and len(text) < 50:
                print(f"  {i}: '{text}'")

        # Try to find process button
        play_button = page.locator('button:has-text("처리")')
        if play_button.count() > 0:
            print(f"\n✅ '처리' 버튼 발견: {play_button.count()}개")

        # Try icon-based search
        play_icon_button = page.locator('button').filter(has=page.locator('svg'))
        print(f"\n아이콘 버튼: {play_icon_button.count()}개")

        time.sleep(2)
        browser.close()

if __name__ == "__main__":
    test()
