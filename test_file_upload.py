from playwright.sync_api import sync_playwright
import time

def test_file_upload():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Navigate to Gateway test page
        print("1. Navigating to Gateway test page...")
        page.goto("http://localhost:5173/test/gateway")
        page.wait_for_load_state("networkidle")
        
        # Take screenshot of initial state
        print("2. Taking screenshot of file upload area...")
        page.screenshot(path="screenshot_upload_area.png")
        
        # Check if "파일 선택" button exists
        print("3. Checking for '파일 선택' button...")
        button = page.locator('button:has-text("파일 선택")')
        if button.count() > 0:
            print("   ✅ '파일 선택' button found!")
        else:
            print("   ❌ '파일 선택' button NOT found!")
            
        # Check for upload icon
        print("4. Checking for upload area...")
        upload_area = page.locator('[aria-label="파일 업로드 영역"]')
        if upload_area.count() > 0:
            print("   ✅ Upload area found!")
        else:
            print("   ❌ Upload area NOT found!")
        
        # Try to click the button
        print("5. Testing button click...")
        try:
            button.click(timeout=5000)
            print("   ✅ Button clickable!")
        except Exception as e:
            print(f"   ⚠️  Button click failed: {e}")
        
        # Take final screenshot
        print("6. Taking final screenshot...")
        page.screenshot(path="screenshot_after_click.png")
        
        print("\n✅ Test completed! Screenshots saved:")
        print("   - screenshot_upload_area.png")
        print("   - screenshot_after_click.png")
        
        time.sleep(2)
        browser.close()

if __name__ == "__main__":
    test_file_upload()
