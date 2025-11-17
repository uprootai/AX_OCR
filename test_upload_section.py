from playwright.sync_api import sync_playwright
import time

def test_upload_section():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("📍 Navigating to Gateway test page...")
        page.goto("http://localhost:5173/test/gateway")
        page.wait_for_load_state("networkidle")
        time.sleep(1)
        
        # Find and scroll to "1. 파일 업로드" heading
        print("📍 Scrolling to file upload section...")
        heading = page.locator('h3:has-text("1. 파일 업로드")')
        if heading.count() > 0:
            heading.scroll_into_view_if_needed()
            time.sleep(1)
        
        # Take screenshot
        print("📍 Taking screenshot...")
        page.screenshot(path="screenshot_upload_section.png")
        
        # Highlight the upload area
        upload_area = page.locator('[aria-label="파일 업로드 영역"]')
        if upload_area.count() > 0:
            upload_area.evaluate("el => el.style.outline = '4px solid #3b82f6'")
            time.sleep(0.5)
        
        # Highlight the button
        button = page.locator('button:has-text("파일 선택")')
        if button.count() > 0:
            button.evaluate("el => el.style.outline = '4px solid #ef4444'")
            time.sleep(0.5)
        
        # Take final screenshot
        page.screenshot(path="screenshot_highlighted.png")
        print("✅ Screenshots saved!")
        
        time.sleep(2)
        browser.close()

if __name__ == "__main__":
    test_upload_section()
