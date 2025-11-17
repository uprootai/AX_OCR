from playwright.sync_api import sync_playwright
import time

def test_file_upload_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Navigate to Gateway test page
        print("📍 Step 1: Navigating to Gateway test page...")
        page.goto("http://localhost:5173/test/gateway")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Scroll to file upload section
        print("📍 Step 2: Scrolling to file upload section...")
        page.evaluate("window.scrollTo(0, 800)")
        time.sleep(1)
        
        # Take screenshot of file upload area
        print("📍 Step 3: Taking screenshot of file upload area...")
        page.screenshot(path="screenshot_file_upload.png", full_page=False)
        
        # Check for "파일 선택" button
        print("\n🔍 Checking UI elements:")
        button = page.locator('button:has-text("파일 선택")')
        button_count = button.count()
        print(f"   {'✅' if button_count > 0 else '❌'} '파일 선택' button: {button_count} found")
        
        # Check for "또는" separator
        separator = page.locator('text="또는"')
        sep_count = separator.count()
        print(f"   {'✅' if sep_count > 0 else '❌'} '또는' separator: {sep_count} found")
        
        # Check for upload icon
        upload_area = page.locator('[aria-label="파일 업로드 영역"]')
        area_count = upload_area.count()
        print(f"   {'✅' if area_count > 0 else '❌'} Upload area: {area_count} found")
        
        # Check for FolderOpen icon
        folder_icon = page.locator('svg').filter(has_text="").count()
        print(f"   ℹ️  SVG icons found: {folder_icon}")
        
        # Test button functionality
        print("\n🧪 Testing functionality:")
        if button_count > 0:
            print("   Testing button click...")
            try:
                # Get button text
                button_text = button.inner_text()
                print(f"   Button text: '{button_text}'")
                
                # Check if button is visible
                is_visible = button.is_visible()
                print(f"   {'✅' if is_visible else '❌'} Button visible: {is_visible}")
                
                # Check if button is enabled
                is_enabled = button.is_enabled()
                print(f"   {'✅' if is_enabled else '❌'} Button enabled: {is_enabled}")
                
                # Highlight the button
                button.evaluate("el => el.style.border = '3px solid red'")
                time.sleep(1)
                
                # Take screenshot with highlighted button
                page.screenshot(path="screenshot_button_highlighted.png")
                print("   📸 Screenshot saved: screenshot_button_highlighted.png")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Test file input
        print("\n🧪 Testing file input:")
        file_input = page.locator('input[type="file"]')
        input_count = file_input.count()
        print(f"   {'✅' if input_count > 0 else '❌'} File input found: {input_count}")
        
        if input_count > 0:
            # Check accept attribute
            accept_attr = file_input.get_attribute('accept')
            print(f"   Accept types: {accept_attr}")
        
        # Final screenshot
        print("\n📸 Taking final full-page screenshot...")
        page.screenshot(path="screenshot_full_page.png", full_page=True)
        
        print("\n" + "="*60)
        print("✅ Test completed successfully!")
        print("="*60)
        print("\n📁 Screenshots saved:")
        print("   1. screenshot_file_upload.png - File upload area")
        print("   2. screenshot_button_highlighted.png - Highlighted button")
        print("   3. screenshot_full_page.png - Full page")
        
        time.sleep(2)
        browser.close()

if __name__ == "__main__":
    test_file_upload_ui()
