from playwright.sync_api import sync_playwright
import time

def test_sample_selector():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("="*70)
        print(" 📋 SAMPLE IMAGE SELECTOR TEST")
        print("="*70)
        
        # Navigate
        print("\n1️⃣  NAVIGATION")
        page.goto("http://localhost:5173/test/gateway")
        page.wait_for_load_state("networkidle")
        print("   └─ ✅ Page loaded\n")
        
        # Scroll to upload section
        print("2️⃣  UPLOAD SECTION")
        heading = page.locator('h3:has-text("1. 파일 업로드")')
        heading.scroll_into_view_if_needed()
        time.sleep(1)
        print("   └─ ✅ Scrolled to upload section\n")
        
        # Check for sample section
        print("3️⃣  SAMPLE IMAGE SECTION")
        sample_label = page.locator('text="또는 샘플 이미지로 빠르게 테스트"')
        if sample_label.count() > 0:
            print("   ├─ ✅ Sample section label found")
        else:
            print("   ├─ ❌ Sample section label NOT found")
        
        # Check for sample buttons
        sample_buttons = page.locator('button:has-text("합성 테스트 도면")')
        button_count = sample_buttons.count()
        print(f"   ├─ ✅ Sample buttons found: {button_count}")
        
        # Take screenshot
        page.screenshot(path="screenshot_sample_buttons.png")
        print("   └─ 📸 Screenshot saved\n")
        
        # Test clicking first sample
        print("4️⃣  SAMPLE SELECTION TEST")
        if button_count > 0:
            print("   ├─ Clicking first sample button...")
            first_button = sample_buttons.first
            first_button.click()
            time.sleep(3)
            
            # Check if file preview appears
            file_preview = page.locator('text="synthetic_random_synthetic_test_000003.jpg"')
            if file_preview.count() > 0:
                print("   ├─ ✅ File loaded successfully!")
            else:
                print("   ├─ ❌ File NOT loaded")
            
            # Take screenshot after loading
            page.screenshot(path="screenshot_sample_loaded.png")
            print("   └─ 📸 Screenshot saved\n")
        
        print("="*70)
        print(" ✅ SAMPLE SELECTOR TEST COMPLETED!")
        print("="*70)
        
        time.sleep(3)
        browser.close()

if __name__ == "__main__":
    test_sample_selector()
